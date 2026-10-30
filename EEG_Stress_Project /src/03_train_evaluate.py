import argparse
import json
import random

import numpy as np
import pandas as pd
import torch

from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

from config import *
from models import EEGNetBaseline


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def calculate_metrics(y_true, predictions, probabilities=None):

    results = {
        "n": int(len(y_true)),
        "accuracy": float(
            accuracy_score(y_true, predictions)
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(y_true, predictions)
        ),
        "precision": float(
            precision_score(
                y_true, predictions, zero_division=0
            )
        ),
        "recall": float(
            recall_score(
                y_true, predictions, zero_division=0
            )
        ),
        "f1": float(
            f1_score(
                y_true, predictions, zero_division=0
            )
        ),
        "confusion_matrix_labels_0_1":
            confusion_matrix(
                y_true, predictions, labels=[0, 1]
            ).tolist()
    }

    if (
        probabilities is not None
        and len(np.unique(y_true)) == 2
    ):
        results["roc_auc"] = float(
            roc_auc_score(y_true, probabilities)
        )
    else:
        results["roc_auc"] = None

    return results


def extract_features(X):
    """
    X shape:
        (epochs, channels, samples)

    Features are calculated independently
    for each epoch and channel.
    """

    mean = X.mean(axis=2)
    std = X.std(axis=2)

    rms = np.sqrt(
        np.mean(X ** 2, axis=2)
    )

    line_length = np.mean(
        np.abs(np.diff(X, axis=2)),
        axis=2
    )

    peak_to_peak = np.ptp(
        X, axis=2
    )

    return np.concatenate(
        [
            mean,
            std,
            rms,
            line_length,
            peak_to_peak
        ],
        axis=1
    )


def validate_binary_labels(labels, dataset_name, role):
    observed = set(np.unique(labels).tolist())
    metadata_path = DATA_DIR / dataset_name / "metadata" / "recordings.csv"
    if -1 in observed:
        raise SystemExit(
            f"ERROR: {role} dataset {dataset_name} contains unknown labels (-1). "
            f"Add documented 0/1 labels to {metadata_path}, then rerun "
            "01_inventory.py and 02_preprocess_segment.py. "
            "--allow-unlabeled is for preprocessing only; it cannot be used for training."
        )
    if observed != {0, 1}:
        raise SystemExit(
            f"ERROR: {role} dataset {dataset_name} must contain both verified binary labels "
            f"0 and 1; found {sorted(observed)}. Check the dataset annotations "
            "before training."
        )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        required=True
    )

    parser.add_argument(
        "--target",
        required=True
    )

    args = parser.parse_args()

    seed_all(RANDOM_SEED)

    source_path = (
        EPOCHS_DIR / f"{args.source}_epochs.npz"
    )

    target_path = (
        EPOCHS_DIR / f"{args.target}_epochs.npz"
    )

    source_manifest_path = (
        LABELS_DIR
        / f"{args.source}_epoch_manifest.csv"
    )

    target_manifest_path = (
        LABELS_DIR
        / f"{args.target}_epoch_manifest.csv"
    )

    required_paths = [
        source_path,
        target_path,
        source_manifest_path,
        target_manifest_path
    ]

    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run preprocessing first."
            )

    source = np.load(
        source_path,
        allow_pickle=False
    )

    target = np.load(
        target_path,
        allow_pickle=False
    )

    X_source = source["X"]
    y_source = source["y"]

    X_target = target["X"]
    y_target = target["y"]

    source_manifest = pd.read_csv(
        source_manifest_path
    )

    target_manifest = pd.read_csv(
        target_manifest_path
    )

    if (
        X_source.shape[1:] != X_target.shape[1:]
    ):
        raise ValueError(
            "Source and target input shapes differ. "
            "Harmonize channels and epoch duration."
        )

    if (
        source["channels"].tolist()
        != target["channels"].tolist()
    ):
        raise ValueError(
            "Channel names or order differ."
        )

    validate_binary_labels(y_source, args.source, "Source")
    validate_binary_labels(y_target, args.target, "Target")

    # Group source epochs by subject.
    # Target data are never used for model selection.
    if "subject_id" not in source_manifest:
        raise SystemExit(
            f"ERROR: {source_manifest_path} has no subject_id column. "
            "Add verified participant IDs to the recordings metadata and rerun preprocessing."
        )
    source_subjects = source_manifest["subject_id"]
    missing_subjects = source_subjects.isna() | source_subjects.astype(str).str.strip().eq("")
    if missing_subjects.any():
        metadata_path = DATA_DIR / args.source / "metadata" / "recordings.csv"
        raise SystemExit(
            f"ERROR: {source_manifest_path} has missing participant IDs. "
            f"Add verified subject_id values to {metadata_path} and rerun preprocessing."
        )
    groups = source_subjects.astype(str).to_numpy()

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.2,
        random_state=RANDOM_SEED
    )

    train_idx, val_idx = next(
        splitter.split(
            X_source,
            y_source,
            groups=groups
        )
    )

    if len(np.unique(y_source[train_idx])) < 2:
        raise ValueError(
            "Training subjects contain only one class. "
            "Review subject-level label distribution."
        )

    # Classical models: handcrafted features.
    F_source = extract_features(X_source)
    F_target = extract_features(X_target)

    results = {
        "source": args.source,
        "target": args.target,
        "source_epochs": int(len(X_source)),
        "target_epochs": int(len(X_target)),
        "models": {}
    }

    # ---------------- SVM ----------------
    svm = make_pipeline(
        StandardScaler(),
        SVC(
            C=1.0,
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=RANDOM_SEED
        )
    )

    svm.fit(
        F_source[train_idx],
        y_source[train_idx]
    )

    svm_predictions = svm.predict(F_target)

    svm_probabilities = svm.predict_proba(
        F_target
    )[:, 1]

    results["models"]["SVM"] = calculate_metrics(
        y_target,
        svm_predictions,
        svm_probabilities
    )

    # ------------- Random Forest -------------
    rf = RandomForestClassifier(
        n_estimators=400,
        class_weight="balanced",
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=RANDOM_SEED
    )

    rf.fit(
        F_source[train_idx],
        y_source[train_idx]
    )

    rf_predictions = rf.predict(F_target)

    rf_probabilities = rf.predict_proba(
        F_target
    )[:, 1]

    results["models"]["RandomForest"] = (
        calculate_metrics(
            y_target,
            rf_predictions,
            rf_probabilities
        )
    )

    # ---------------- EEGNet ----------------
    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "cpu"
    )

    model = EEGNetBaseline(
        n_channels=X_source.shape[1],
        n_times=X_source.shape[2]
    ).to(device)

    # Calculate normalization using source training
    # subjects only, not target test recordings.
    mean = X_source[train_idx].mean(
        axis=(0, 2),
        keepdims=True
    )

    std = X_source[train_idx].std(
        axis=(0, 2),
        keepdims=True
    ) + 1e-6

    Xs_norm = (X_source - mean) / std
    Xt_norm = (X_target - mean) / std

    train_data = TensorDataset(
        torch.tensor(
            Xs_norm[train_idx],
            dtype=torch.float32
        ),
        torch.tensor(
            y_source[train_idx],
            dtype=torch.long
        )
    )

    val_data = TensorDataset(
        torch.tensor(
            Xs_norm[val_idx],
            dtype=torch.float32
        ),
        torch.tensor(
            y_source[val_idx],
            dtype=torch.long
        )
    )

    train_loader = DataLoader(
        train_data,
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    val_loader = DataLoader(
        val_data,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    criterion = nn.CrossEntropyLoss()

    best_loss = float("inf")
    best_state = None
    patience = 8
    stale_epochs = 0

    for epoch in range(EPOCHS):

        model.train()

        for xb, yb in train_loader:

            xb = xb.to(device)
            yb = yb.to(device)

            optimizer.zero_grad()

            logits = model(xb)
            loss = criterion(logits, yb)

            loss.backward()
            optimizer.step()

        model.eval()
        validation_losses = []

        with torch.no_grad():

            for xb, yb in val_loader:

                xb = xb.to(device)
                yb = yb.to(device)

                logits = model(xb)

                loss = criterion(
                    logits, yb
                )

                validation_losses.append(
                    loss.item()
                )

        val_loss = float(
            np.mean(validation_losses)
        )

        if val_loss < best_loss:

            best_loss = val_loss
            stale_epochs = 0

            best_state = {
                key: value.detach().cpu().clone()
                for key, value
                in model.state_dict().items()
            }

        else:
            stale_epochs += 1

        print(
            f"Epoch {epoch + 1}: "
            f"validation loss = {val_loss:.4f}"
        )

        if stale_epochs >= patience:
            break

    if best_state is None:
        raise RuntimeError(
            "No model checkpoint selected."
        )

    model.load_state_dict(best_state)
    model.eval()

    with torch.no_grad():

        X_tensor = torch.tensor(
            Xt_norm,
            dtype=torch.float32
        ).to(device)

        logits = model(X_tensor)

        probabilities = torch.softmax(
            logits,
            dim=1
        )[:, 1].cpu().numpy()

        predictions = logits.argmax(
            dim=1
        ).cpu().numpy()

    results["models"]["EEGNet_baseline"] = (
        calculate_metrics(
            y_target,
            predictions,
            probabilities
        )
    )

    # Save metrics and trained model.
    output_dir = RESULTS_DIR / "cross_dataset"
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    model_dir = MODELS_DIR
    model_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    experiment_name = (
        f"{args.source}_to_{args.target}"
    )

    with open(
        output_dir / f"{experiment_name}_metrics.json",
        "w"
    ) as file:
        json.dump(
            results,
            file,
            indent=2
        )

    pd.DataFrame([
        {"model": name, **values}
        for name, values
        in results["models"].items()
    ]).to_csv(
        output_dir / f"{experiment_name}_metrics.csv",
        index=False
    )

    torch.save(
        {
            "state_dict": best_state,
            "channels": source["channels"].tolist(),
            "sampling_rate": int(source["sfreq"]),
            "mean": mean,
            "std": std,
            "source": args.source,
            "target": args.target
        },
        model_dir / f"{experiment_name}_eegnet.pt"
    )

    print(json.dumps(results, indent=2))
    print(f"Results saved in {output_dir}")


if __name__ == "__main__":
    main()