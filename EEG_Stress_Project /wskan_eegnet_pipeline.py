#!/usr/bin/env python3
"""WS-KAN-EEGNet on prepared binary EEG epochs with subject-held-out evaluation.

NPZ: X=(epochs, channels, samples), y=(epochs,), channels=(channels,)
CSV manifest: subject_id,label (one row per epoch)
Labels must be prepared and validated separately; this script does not infer them.
"""
import argparse, json, random
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
from sklearn.metrics import precision_score, recall_score, f1_score


ROOT = Path(__file__).resolve().parent


def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def get_device(name):
    if name != "auto": return torch.device(name)
    if torch.cuda.is_available(): return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class HaarWavelet(nn.Module):
    """Fixed one-level Haar approximation/detail transform over time."""
    def __init__(self):
        super().__init__()
        s = 1.0 / np.sqrt(2.0)
        self.register_buffer("filters", torch.tensor([[[s, s]], [[s, -s]]],
                                                     dtype=torch.float32))
    def forward(self, x):
        # x: B,1,C,T. Apply two filters independently to every channel.
        b, _, c, _ = x.shape
        z = x.squeeze(1)  # B,C,T
        filt = self.filters.to(dtype=x.dtype).repeat(c, 1, 1)
        z = nn.functional.conv1d(z, filt, stride=2, groups=c)
        return z.reshape(b, c, 2, -1).permute(0, 2, 1, 3)


class KANLinear(nn.Module):
    """KAN-style layer using learnable triangular (piecewise-linear B-spline) bases."""
    def __init__(self, in_features, out_features, grid_size=5):
        super().__init__()
        self.base = nn.Linear(in_features, out_features)
        self.weight = nn.Parameter(torch.empty(out_features, in_features, grid_size))
        self.register_buffer("grid", torch.linspace(-2., 2., grid_size))
        self.grid_size = grid_size
        nn.init.normal_(self.weight, mean=0., std=0.02)
    def forward(self, x):
        x = torch.tanh(x) * 2.
        step = 4. / (self.grid_size - 1)
        basis = torch.relu(1. - torch.abs(
            (x.unsqueeze(-1) - self.grid.view(1, 1, -1)) / step))
        return self.base(x) + torch.einsum("big,oig->bo", basis, self.weight)


class WSKANEEGNet(nn.Module):
    """Haar wavelet bands -> EEGNet-style CNN -> KAN classifier."""
    def __init__(self, channels, samples, dropout=0.5):
        super().__init__()
        self.wavelet = HaarWavelet()
        self.temporal = nn.Sequential(
            nn.Conv2d(2, 16, (1, 15), padding=(0, 7), bias=False),
            nn.BatchNorm2d(16), nn.ELU())
        self.spatial = nn.Sequential(
            nn.Conv2d(16, 32, (channels, 1), groups=16, bias=False),
            nn.BatchNorm2d(32), nn.ELU(),
            nn.AvgPool2d((1, 4)), nn.Dropout(dropout))
        self.separable = nn.Sequential(
            nn.Conv2d(32, 32, (1, 9), padding=(0, 4), groups=32, bias=False),
            nn.Conv2d(32, 64, (1, 1), bias=False),
            nn.BatchNorm2d(64), nn.ELU(),
            nn.AvgPool2d((1, 4)), nn.Dropout(dropout))
        with torch.no_grad():
            dummy = torch.zeros(1, channels, samples)
            dim = self.features(dummy).shape[1]
        self.projection = nn.Sequential(nn.Linear(dim, 64), nn.LayerNorm(64),
                                        nn.ELU(), nn.Dropout(dropout))
        self.kan = KANLinear(64, 2, grid_size=5)
    def features(self, x):
        x = self.wavelet(x.unsqueeze(1))       # B,2,C,T/2
        x = self.temporal(x)
        x = self.spatial(x)                    # B,32,1,T/8
        x = self.separable(x)                  # B,64,1,T/32
        return x.flatten(1)
    def forward(self, x):
        return self.kan(self.projection(self.features(x)))


def main():
    parser = argparse.ArgumentParser(
        description="Train and evaluate WS-KAN-EEGNet on prepared EEG epochs."
    )
    parser.add_argument(
        "--epochs-file", type=Path,
        default=ROOT / "processed/epochs/EEG_Recordings_epochs.npz",
        help="NPZ containing X, y, and channels.",
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=ROOT / "processed/labels/EEG_Recordings_epoch_manifest.csv",
        help="CSV with subject_id and label columns, aligned to the NPZ.",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "results/WSKAN_EEGNet_subject_holdout",
    )
    parser.add_argument(
        "--model-path", type=Path,
        default=ROOT / "models/WSKAN_EEGNet.pt",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs.")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--device", choices=("auto", "cpu", "mps", "cuda"), default="auto"
    )
    args = parser.parse_args()

    if args.epochs < 1 or args.batch_size < 1:
        parser.error("--epochs and --batch-size must be positive.")
    if not 0 < args.test_size < 1:
        parser.error("--test-size must be between 0 and 1.")
    if not args.epochs_file.is_file():
        parser.error(f"Epoch file not found: {args.epochs_file}")
    if not args.manifest.is_file():
        parser.error(f"Manifest not found: {args.manifest}")

    seed_all(args.seed)
    with np.load(args.epochs_file, allow_pickle=False) as data:
        missing = {"X", "y", "channels"} - set(data.files)
        if missing:
            parser.error(f"Epoch file is missing arrays: {sorted(missing)}")
        X = np.asarray(data["X"], dtype=np.float32)
        y = np.asarray(data["y"], dtype=np.int64)
        channels = data["channels"].astype(str).tolist()

    if X.ndim != 3 or len(y) != len(X) or len(channels) != X.shape[1]:
        parser.error("Expected X=(epochs, channels, samples) with matching y/channels.")
    if not np.isfinite(X).all():
        parser.error("Epoch data contains NaN or infinite values.")
    if set(np.unique(y)) != {0, 1}:
        parser.error(f"Expected both binary labels 0 and 1; found {np.unique(y).tolist()}.")

    manifest = pd.read_csv(args.manifest)
    missing_columns = {"subject_id", "label"} - set(manifest.columns)
    if missing_columns:
        parser.error(f"Manifest is missing columns: {sorted(missing_columns)}")
    if len(manifest) != len(y):
        parser.error(f"Manifest has {len(manifest)} rows but NPZ has {len(y)} epochs.")
    manifest_y = pd.to_numeric(manifest["label"], errors="raise").to_numpy(
        dtype=np.int64
    )
    if not np.array_equal(manifest_y, y):
        parser.error("Manifest labels do not match the NPZ labels.")
    subjects = manifest["subject_id"].astype("string").str.strip()
    if subjects.isna().any() or subjects.eq("").any():
        parser.error("Manifest contains missing subject IDs.")
    groups = subjects.to_numpy()

    test_split = GroupShuffleSplit(
        n_splits=1, test_size=args.test_size, random_state=args.seed
    )
    train_val_idx, test_idx = next(test_split.split(X, y, groups=groups))
    val_split = GroupShuffleSplit(
        n_splits=1, test_size=0.2, random_state=args.seed + 1
    )
    train_rel, val_rel = next(
        val_split.split(
            X[train_val_idx], y[train_val_idx], groups=groups[train_val_idx]
        )
    )
    train_idx = train_val_idx[train_rel]
    val_idx = train_val_idx[val_rel]
    for name, indices in (("training", train_idx), ("validation", val_idx), ("test", test_idx)):
        if set(np.unique(y[indices])) != {0, 1}:
            parser.error(
                f"The {name} subject split does not contain both labels; "
                "try a different --seed or --test-size."
            )

    device = get_device(args.device)
    mean = X[train_idx].mean(axis=(0, 2), keepdims=True)
    std = X[train_idx].std(axis=(0, 2), keepdims=True)
    std = np.maximum(std, 1e-6)
    X = np.ascontiguousarray((X - mean) / std, dtype=np.float32)

    def dataset(indices):
        return TensorDataset(
            torch.from_numpy(X[indices]),
            torch.from_numpy(y[indices]),
        )

    train_loader = DataLoader(
        dataset(train_idx), batch_size=args.batch_size, shuffle=True
    )
    val_loader = DataLoader(
        dataset(val_idx), batch_size=args.batch_size, shuffle=False
    )
    test_loader = DataLoader(
        dataset(test_idx), batch_size=args.batch_size, shuffle=False
    )
    model = WSKANEEGNet(X.shape[1], X.shape[2]).to(device)
    class_counts = np.bincount(y[train_idx], minlength=2)
    class_weights = len(train_idx) / (2.0 * class_counts)
    criterion = nn.CrossEntropyLoss(
        weight=torch.tensor(class_weights, dtype=torch.float32, device=device)
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    best_loss = float("inf")
    best_state = None
    for epoch in range(args.epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        val_loss = 0.0
        val_count = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                batch_loss = criterion(model(xb), yb)
                val_loss += batch_loss.item() * len(yb)
                val_count += len(yb)
        val_loss /= val_count
        print(f"Epoch {epoch + 1}/{args.epochs}: validation loss={val_loss:.4f}")
        if val_loss < best_loss:
            best_loss = val_loss
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }

    if best_state is None:
        raise RuntimeError("Training did not produce a model checkpoint.")
    model.load_state_dict(best_state)
    model.eval()
    actual, predicted = [], []
    with torch.no_grad():
        for xb, yb in test_loader:
            logits = model(xb.to(device))
            predicted.extend(logits.argmax(dim=1).cpu().tolist())
            actual.extend(yb.tolist())

    scores = {
        "protocol": "group_shuffle_subject_holdout",
        "seed": args.seed,
        "epochs_requested": args.epochs,
        "epochs_total": int(len(y)),
        "epochs_train": int(len(train_idx)),
        "epochs_validation": int(len(val_idx)),
        "epochs_test": int(len(test_idx)),
        "subjects_total": int(subjects.nunique()),
        "subjects_train": int(subjects.iloc[train_idx].nunique()),
        "subjects_validation": int(subjects.iloc[val_idx].nunique()),
        "subjects_test": int(subjects.iloc[test_idx].nunique()),
        "channels": channels,
        "device": str(device),
        "accuracy": float(accuracy_score(actual, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(actual, predicted)),
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
        "confusion_matrix_labels_0_1": confusion_matrix(
            actual, predicted, labels=[0, 1]
        ).tolist(),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path = args.output_dir / "metrics.json"
    predictions_path = args.output_dir / "predictions.csv"
    model_payload = {
        "model_state_dict": best_state,
        "channels": channels,
        "samples": int(X.shape[2]),
        "normalization_mean": mean,
        "normalization_std": std,
        "scores": scores,
    }
    torch.save(model_payload, args.model_path)
    pd.DataFrame(
        {
            "epoch_index": test_idx,
            "subject_id": subjects.iloc[test_idx].to_numpy(),
            "true_label": actual,
            "predicted_label": predicted,
        }
    ).to_csv(predictions_path, index=False)
    scores["metrics_file"] = str(metrics_path)
    scores["predictions_file"] = str(predictions_path)
    scores["model_file"] = str(args.model_path)
    metrics_path.write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()