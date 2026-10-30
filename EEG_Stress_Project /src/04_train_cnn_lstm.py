import argparse
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score,
    classification_report, confusion_matrix, f1_score
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
EPOCH_DIR = ROOT / "processed" / "epochs"
RESULT_DIR = ROOT / "results" / "cross_dataset"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_data(name):
    path = EPOCH_DIR / f"{name}_epochs.npz"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}\n"
            "Preprocess this dataset and save its archive before training."
        )

    with np.load(path, allow_pickle=False) as z:
        X = z["X"].astype(np.float32)
        y = z["y"].astype(np.int64)
        channels = z["channels"].astype(str).tolist()
        sfreq = float(z["sfreq"])

    if X.ndim != 3 or len(X) != len(y):
        raise ValueError(f"Unexpected shapes: X={X.shape}, y={y.shape}")
    if set(np.unique(y)) != {0, 1}:
        raise ValueError(f"{name}: expected labels 0 and 1; got {np.unique(y)}")

    # Standardize each epoch/channel using that epoch's own samples.
    # This avoids fitting a scaler on target labels or target data.
    mean = X.mean(axis=-1, keepdims=True)
    std = X.std(axis=-1, keepdims=True)
    X = (X - mean) / np.maximum(std, 1e-6)
    return X, y, channels, sfreq


class CNNLSTM(nn.Module):
    def __init__(self, channels, n_classes=2):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv1d(channels, 32, kernel_size=7, padding=3),
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
            hidden_size=48,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(96, n_classes)
        )

    def forward(self, x):
        x = self.cnn(x)
        x = x.transpose(1, 2)
        _, (h, _) = self.lstm(x)
        x = torch.cat((h[-2], h[-1]), dim=1)
        return self.classifier(x)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.001)
    args = parser.parse_args()

    Xs, ys, source_channels, source_sfreq = load_data(args.source)
    Xt, yt, target_channels, target_sfreq = load_data(args.target)

    if Xs.shape[1:] != Xt.shape[1:]:
        raise ValueError(
            f"Incompatible epoch shapes: source {Xs.shape[1:]}, "
            f"target {Xt.shape[1:]}. Harmonize channels and sample counts first."
        )
    if source_channels != target_channels:
        raise ValueError(
            f"Channel order mismatch.\nSource: {source_channels}\n"
            f"Target: {target_channels}\n"
            "Do not proceed until channels are mapped and reordered correctly."
        )
    if source_sfreq != target_sfreq:
        raise ValueError(
            f"Sampling rates differ: source={source_sfreq}, target={target_sfreq}"
        )

    # For cross-dataset mode, train/validation split is source-only.
    # Target data are used only for final evaluation.
    X_train, X_val, y_train, y_val = train_test_split(
        Xs, ys, test_size=0.2, random_state=42, stratify=ys
    )

    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train)),
        batch_size=args.batch_size, shuffle=True
    )
    val_loader = DataLoader(
        TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val)),
        batch_size=args.batch_size, shuffle=False
    )

    model = CNNLSTM(channels=Xs.shape[1]).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    best_val = -1.0
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())

        model.eval()
        val_true, val_pred = [], []
        with torch.no_grad():
            for xb, yb in val_loader:
                pred = model(xb.to(DEVICE)).argmax(1).cpu().numpy()
                val_true.extend(yb.numpy())
                val_pred.extend(pred)

        val_bacc = balanced_accuracy_score(val_true, val_pred)
        print(
            f"Epoch {epoch:02d}/{args.epochs} | "
            f"loss={np.mean(losses):.4f} | "
            f"source validation balanced accuracy={val_bacc:.4f}"
        )
        if val_bacc > best_val:
            best_val = val_bacc
            torch.save(model.state_dict(), RESULT_DIR / "best_cnn_lstm.pt")

    model.load_state_dict(torch.load(
        RESULT_DIR / "best_cnn_lstm.pt", map_location=DEVICE, weights_only=True
    ))
    model.eval()
    predictions = []
    with torch.no_grad():
        for start in range(0, len(Xt), args.batch_size):
            xb = torch.from_numpy(Xt[start:start + args.batch_size]).to(DEVICE)
            predictions.extend(model(xb).argmax(1).cpu().numpy())

    predictions = np.asarray(predictions)
    report = classification_report(
        yt, predictions, labels=[0, 1],
        target_names=["relaxation-like", "stress-like"],
        zero_division=0
    )
    print(f"\nTrain dataset: {args.source}")
    print(f"Test dataset: {args.target}")
    print(f"Accuracy: {accuracy_score(yt, predictions):.4f}")
    print(f"Balanced accuracy: {balanced_accuracy_score(yt, predictions):.4f}")
    print(f"Macro F1: {f1_score(yt, predictions, average='macro'):.4f}")
    print("Confusion matrix:\n", confusion_matrix(yt, predictions, labels=[0, 1]))
    print(report)

    output = RESULT_DIR / f"{args.source}_to_{args.target}_cnn_lstm.txt"
    output.write_text(
        f"Source: {args.source}\nTarget: {args.target}\n"
        f"Accuracy: {accuracy_score(yt, predictions):.6f}\n"
        f"Balanced accuracy: {balanced_accuracy_score(yt, predictions):.6f}\n"
        f"Macro F1: {f1_score(yt, predictions, average='macro'):.6f}\n"
        f"Confusion matrix:\n{confusion_matrix(yt, predictions, labels=[0, 1])}\n\n"
        f"{report}\n"
    )
    print("Saved:", output)


if __name__ == "__main__":
    main()
