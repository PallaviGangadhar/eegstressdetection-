#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


class CNNLSTM(nn.Module):
    def __init__(self, n_channels=20, n_classes=2):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv1d(n_channels, 32, kernel_size=7, padding=3),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
        )
        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=32,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        x = self.cnn(x)
        x = x.transpose(1, 2)
        _, (h, _) = self.lstm(x)
        x = torch.cat((h[-2], h[-1]), dim=1)
        return self.classifier(x)


def load_subjects(data_dir):
    data_dir = Path(data_dir)
    files = sorted(data_dir.glob("*.npz"))
    if not files:
        raise FileNotFoundError(f"No .npz files found in {data_dir}")

    subjects = {}
    for f in files:
        with np.load(f, allow_pickle=False) as z:
            X = z["X"].astype(np.float32)
            y = z["y"].astype(np.int64)
            subject = str(z["subject"].item()) if "subject" in z.files else f.stem
        subjects[subject] = (X, y)
    return subjects


def normalize_train_test(X_train, X_test):
    mean = X_train.mean(axis=(0, 2), keepdims=True)
    std = X_train.std(axis=(0, 2), keepdims=True)
    std = np.where(std < 1e-6, 1.0, std)
    X_train = (X_train - mean) / std
    X_test = (X_test - mean) / std
    return X_train.astype(np.float32), X_test.astype(np.float32)


def make_loader(X, y, batch_size, shuffle=True):
    dataset = TensorDataset(
        torch.from_numpy(X).float(),
        torch.from_numpy(y).long(),
    )
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, help="Directory containing processed subject NPZ files")
    parser.add_argument("--out-dir", default="results_cnn_lstm_loso")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    subjects = load_subjects(data_dir)
    ids = list(subjects.keys())
    print(f"Loaded subjects: {ids}")

    rows = []
    all_true = []
    all_pred = []

    for fold, test_id in enumerate(ids, start=1):
        train_ids = [sid for sid in ids if sid != test_id]
        X_train = np.concatenate([subjects[sid][0] for sid in train_ids], axis=0)
        y_train = np.concatenate([subjects[sid][1] for sid in train_ids], axis=0)
        X_test, y_test = subjects[test_id]

        if len(np.unique(y_train)) < 2:
            print(f"Fold {fold}/{len(ids)} test={test_id}: skipped (training set has only one class)")
            continue

        print(f"\nFold {fold}/{len(ids)}: test={test_id}")
        print(f"  train windows={len(y_train)} baseline={int((y_train == 0).sum())} horror={int((y_train == 1).sum())}")
        print(f"  test windows={len(y_test)} baseline={int((y_test == 0).sum())} horror={int((y_test == 1).sum())}")

        X_train_n, X_test_n = normalize_train_test(X_train, X_test)
        class_counts = np.bincount(y_train, minlength=2).astype(np.float32)
        weights = np.zeros(2, dtype=np.float32)
        present = class_counts > 0
        weights[present] = class_counts.sum() / (present.sum() * class_counts[present])
        criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, device=device))

        model = CNNLSTM(n_channels=X_train.shape[1]).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
        train_loader = make_loader(X_train_n, y_train, args.batch_size, shuffle=True)

        for epoch in range(1, args.epochs + 1):
            model.train()
            running_loss = 0.0
            seen = 0
            for xb, yb in train_loader:
                xb, yb = xb.to(device), yb.to(device)
                optimizer.zero_grad(set_to_none=True)
                logits = model(xb)
                loss = criterion(logits, yb)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                running_loss += float(loss.item()) * len(yb)
                seen += len(yb)
            avg_loss = running_loss / max(seen, 1)
            print(f"  epoch {epoch:02d}/{args.epochs} loss={avg_loss:.4f}")

        model.eval()
        with torch.no_grad():
            logits = model(torch.from_numpy(X_test_n).to(device))
            pred = logits.argmax(dim=1).cpu().numpy()

        all_true.extend(y_test.tolist())
        all_pred.extend(pred.tolist())

        acc = accuracy_score(y_test, pred)
        bacc = balanced_accuracy_score(y_test, pred) if len(np.unique(y_test)) == 2 else float("nan")
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, pred, labels=[0, 1], average="macro", zero_division=0
        )
        cm = confusion_matrix(y_test, pred, labels=[0, 1]).tolist()

        row = {
            "fold": fold,
            "test_subject": test_id,
            "n_test_windows": len(y_test),
            "test_baseline": int((y_test == 0).sum()),
            "test_horror": int((y_test == 1).sum()),
            "accuracy": float(acc),
            "balanced_accuracy": float(bacc) if np.isfinite(bacc) else None,
            "macro_precision": float(precision),
            "macro_recall": float(recall),
            "macro_f1": float(f1),
            "confusion_matrix_labels_0_1": json.dumps(cm),
        }
        rows.append(row)
        print(f"  TEST {test_id}: accuracy={acc:.3f}, balanced_accuracy={bacc:.3f}, macro-F1={f1:.3f}, CM={cm}")

        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "test_subject": test_id,
                "n_channels": int(X_train.shape[1]),
                "n_timepoints": int(X_train.shape[2]),
                "class_weights": weights.tolist(),
            },
            out_dir / f"cnn_lstm_loso_{test_id}.pt",
        )

    if not rows:
        raise SystemExit("No folds completed; check the data and make sure each subject has at least one sample of each class.")

    with open(out_dir / "fold_metrics.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    cm = confusion_matrix(all_true, all_pred, labels=[0, 1]).tolist()
    summary = {
        "completed_folds": len(rows),
        "subjects_total": len(ids),
        "window_weighted_accuracy": float(accuracy_score(all_true, all_pred)),
        "window_weighted_balanced_accuracy": float(balanced_accuracy_score(all_true, all_pred)) if len(set(all_true)) == 2 else None,
        "window_weighted_confusion_matrix_labels_0_1": cm,
        "note": "Preliminary baseline-vs-horror phase classification; not verified stress detection. Some subjects may contain only one class, so LOSO metrics should be interpreted cautiously.",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print("\nOVERALL HELD-OUT-WINDOW RESULTS")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved fold metrics: {out_dir / 'fold_metrics.csv'}")
    print(f"Saved summary: {out_dir / 'summary.json'}")


if __name__ == "__main__":
    main()

