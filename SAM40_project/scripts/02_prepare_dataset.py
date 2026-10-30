
from pathlib import Path
import re
import numpy as np
import pandas as pd
from scipy.io import loadmat
import h5py

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted"
LABEL_FILE = ROOT / "outputs" / "reports" / "labels.csv"
OUT = ROOT / "outputs" / "preprocessed"
OUT.mkdir(parents=True, exist_ok=True)

FS = 128
CHANNELS = 32
WINDOW_SECONDS = 2
STRIDE_SECONDS = 1
WINDOW = FS * WINDOW_SECONDS
STRIDE = FS * STRIDE_SECONDS

def load_variables(path):
    try:
        values = loadmat(path)
        return {
            k: v for k, v in values.items()
            if not k.startswith("__")
        }
    except (NotImplementedError, ValueError):
        with h5py.File(path, "r") as f:
            values = {}
            def visit(name, obj):
                if isinstance(obj, h5py.Dataset):
                    values[name] = np.asarray(obj)
            f.visititems(visit)
        return values

def get_eeg(path):
    variables = load_variables(path)
    candidates = []

    for name, value in variables.items():
        if not isinstance(value, np.ndarray):
            continue
        if not np.issubdtype(value.dtype, np.number):
            continue

        a = np.asarray(value)
        if a.ndim != 2:
            continue

        if CHANNELS in a.shape:
            candidates.append((name, a))

    if len(candidates) != 1:
        details = [(name, a.shape) for name, a in candidates]
        raise ValueError(
            f"Expected one unambiguous 32-channel array; got {details}. "
            "Inspect this MAT file and specify its EEG variable explicitly."
        )

    name, x = candidates[0]
    x = np.asarray(x, dtype=np.float64)

    if x.shape[0] != CHANNELS and x.shape[1] == CHANNELS:
        x = x.T

    if x.shape[0] != CHANNELS:
        raise ValueError(f"Unexpected EEG shape: {x.shape}")

    if not np.isfinite(x).all():
        raise ValueError("NaN/Inf values found; inspect artifacts before repair.")

    return name, x

def make_windows(x):
    windows = []
    for start in range(0, x.shape[1] - WINDOW + 1, STRIDE):
        segment = x[:, start:start + WINDOW].copy()

        # Normalize each channel within this window.
        mean = segment.mean(axis=1, keepdims=True)
        std = segment.std(axis=1, keepdims=True)
        std[std < 1e-8] = 1.0
        segment = (segment - mean) / std

        windows.append(segment.T.astype(np.float32))

    return windows

labels = pd.read_csv(LABEL_FILE)
required = {"filename", "subject_id", "task", "rating"}
if not required.issubset(labels.columns):
    raise ValueError(f"labels.csv needs columns: {sorted(required)}")

X_all, y_all, subjects_all = [], [], []
metadata = []

for row in labels.itertuples(index=False):
    path = DATA / row.filename

    if not path.is_file():
        print("MISSING:", path)
        continue

    task = str(row.task).strip().lower()

    if task == "relax":
        label = 0
    else:
        rating = pd.to_numeric(row.rating, errors="coerce")
        if pd.isna(rating) or not 1 <= rating <= 10:
            print("INVALID RATING:", row.filename, row.rating)
            continue
        label = 1 if rating <= 5 else 2

    try:
        variable, eeg = get_eeg(path)
        windows = make_windows(eeg)

        if not windows:
            raise ValueError("Recording too short for one window.")

        X_all.extend(windows)
        y_all.extend([label] * len(windows))
        subjects_all.extend([str(row.subject_id)] * len(windows))

        metadata.append({
            "filename": row.filename,
            "subject_id": row.subject_id,
            "task": row.task,
            "rating": row.rating,
            "label": label,
            "variable": variable,
            "channels": eeg.shape[0],
            "samples": eeg.shape[1],
            "windows": len(windows),
            "status": "success"
        })

        print("OK:", row.filename, "windows:", len(windows))

    except Exception as exc:
        print("SKIPPED:", row.filename, exc)
        metadata.append({
            "filename": row.filename,
            "subject_id": row.subject_id,
            "task": row.task,
            "rating": row.rating,
            "label": label,
            "variable": "",
            "channels": "",
            "samples": "",
            "windows": 0,
            "status": f"failed: {exc}"
        })

if not X_all:
    raise RuntimeError("No valid windows. Check paths, labels and MAT variables.")

X = np.stack(X_all)
y = np.asarray(y_all, dtype=np.int64)
subjects = np.asarray(subjects_all)

np.savez_compressed(
    OUT / "sam40_windows.npz",
    X=X, y=y, subjects=subjects,
    sampling_rate=FS,
    window_seconds=WINDOW_SECONDS,
    stride_seconds=STRIDE_SECONDS
)

pd.DataFrame(metadata).to_csv(
    ROOT / "outputs" / "reports" / "preprocessing_manifest.csv",
    index=False
)

print("\nDataset shape:", X.shape)
print("Labels:", dict(zip(*np.unique(y, return_counts=True))))
print("Participants:", len(np.unique(subjects)))
print("Saved:", OUT / "sam40_windows.npz")
