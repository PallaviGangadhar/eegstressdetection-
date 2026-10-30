import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import mne

from config import *


def read_raw(path):
    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".edf":
        return mne.io.read_raw_edf(
            path, preload=True, verbose="ERROR"
        )

    elif ext == ".bdf":
        return mne.io.read_raw_bdf(
            path, preload=True, verbose="ERROR"
        )

    elif ext == ".gdf":
        return mne.io.read_raw_gdf(
            path, preload=True, verbose="ERROR"
        )

    elif ext == ".set":
        return mne.io.read_raw_eeglab(
            path, preload=True, verbose="ERROR"
        )

    elif ext == ".fif":
        return mne.io.read_raw_fif(
            path, preload=True, verbose="ERROR"
        )

    elif ext == ".mat":
        raise ValueError(
            "MAT files need a dataset-specific loader. "
            "Inspect the variables and array dimensions first."
        )

    raise ValueError(
        f"Unsupported EEG file format: {ext}"
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--metadata",
        required=True
    )
    parser.add_argument(
        "--allow-unlabeled",
        action="store_true",
        help="Preprocess recordings with unknown labels, storing label -1 as an explicit sentinel.",
    )

    args = parser.parse_args()

    metadata = pd.read_csv(args.metadata)

    required = {
        "dataset",
        "file_path",
        "subject_id",
        "label"
    }

    if required - set(metadata.columns):
        raise ValueError(
            f"Metadata must contain {sorted(required)}"
        )

    if not COMMON_CHANNELS:
        raise ValueError(
            "Set COMMON_CHANNELS in src/config.py "
            "after inspecting the inventory reports."
        )

    dataset_names = metadata["dataset"].astype(str).unique()

    if len(dataset_names) != 1:
        raise ValueError(
            "Use a separate metadata CSV for each dataset."
        )

    dataset_name = dataset_names[0]

    EPOCHS_DIR.mkdir(parents=True, exist_ok=True)
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    CHANNEL_MAP_DIR.mkdir(parents=True, exist_ok=True)

    epoch_length = int(
        EPOCH_SECONDS * TARGET_SFREQ
    )

    step_length = int(
        (EPOCH_SECONDS - OVERLAP_SECONDS)
        * TARGET_SFREQ
    )

    if step_length <= 0:
        raise ValueError(
            "Overlap must be shorter than epoch duration."
        )

    all_epochs = []
    manifest = []

    for _, row in metadata.iterrows():

        path = Path(str(row["file_path"]))

        if not path.is_absolute():
            path = Path.cwd() / path

        if not path.exists():
            raise FileNotFoundError(path)

        if pd.isna(row["label"]) and not args.allow_unlabeled:
            raise ValueError(
                f"Missing label for {path}. Supply documented labels or pass "
                "--allow-unlabeled to preprocess without assigning one."
            )

        label = -1 if pd.isna(row["label"]) else int(row["label"])

        if label != -1 and label not in (0, 1):
            raise ValueError(
                f"Expected binary label 0 or 1, or unknown label -1: {path}"
            )

        raw = read_raw(path)

        raw.rename_channels(
            lambda name: name.strip()
        )

        missing_channels = [
            ch for ch in COMMON_CHANNELS
            if ch not in raw.ch_names
        ]

        if missing_channels:
            raw.close()

            raise ValueError(
                f"{path} is missing channels: "
                f"{missing_channels}"
            )

        raw.pick_channels(
            COMMON_CHANNELS,
            ordered=True
        )

        raw.load_data()

        raw.filter(
            l_freq=LOW_CUT_HZ,
            h_freq=HIGH_CUT_HZ,
            method="fir",
            verbose="ERROR"
        )

        if not np.isclose(
            raw.info["sfreq"],
            TARGET_SFREQ
        ):
            raw.resample(
                TARGET_SFREQ,
                npad="auto",
                verbose="ERROR"
            )

        # MNE EEG data are ordinarily represented in volts.
        # Convert to microvolts for easier numerical inspection.
        signal_uv = raw.get_data() * 1e6

        raw.close()

        if not np.isfinite(signal_uv).all():
            raise ValueError(
                f"Non-finite signal values in {path}"
            )

        epoch_id = 0

        for start in range(
            0,
            signal_uv.shape[1] - epoch_length + 1,
            step_length
        ):

            end = start + epoch_length

            epoch = signal_uv[:, start:end]

            all_epochs.append(
                epoch.astype(np.float32)
            )

            manifest.append({
                "dataset": dataset_name,
                "file_path": str(path),
                "subject_id": str(row["subject_id"]),
                "label": label,
                "label_status": "unknown" if label == -1 else "labeled",
                "epoch_id": epoch_id,
                "start_seconds":
                    start / TARGET_SFREQ,
                "end_seconds":
                    end / TARGET_SFREQ
            })

            epoch_id += 1

        print(
            f"{path.name}: {epoch_id} epochs created"
        )

    if not all_epochs:
        raise RuntimeError(
            "No epochs generated. Check file durations."
        )

    X = np.stack(all_epochs)

    y = np.asarray(
        [item["label"] for item in manifest],
        dtype=np.int64
    )

    np.savez_compressed(
        EPOCHS_DIR / f"{dataset_name}_epochs.npz",
        X=X,
        y=y,
        channels=np.asarray(COMMON_CHANNELS),
        sfreq=np.asarray(TARGET_SFREQ)
    )

    pd.DataFrame(manifest).to_csv(
        LABELS_DIR
        / f"{dataset_name}_epoch_manifest.csv",
        index=False
    )

    pd.DataFrame({
        "channel_order": range(len(COMMON_CHANNELS)),
        "channel_name": COMMON_CHANNELS
    }).to_csv(
        CHANNEL_MAP_DIR
        / f"{dataset_name}_channel_map.csv",
        index=False
    )

    print("Preprocessing complete.")
    print("Epoch tensor shape:", X.shape)
    print("Saved dataset:", dataset_name)


if __name__ == "__main__":
    main()