
from pathlib import Path
import json
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

# ==================================================
# 1. CONFIGURATION
# ==================================================
ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = ROOT / "outputs" / "preprocessed" / "sam40_windows.npz"
REPORTS = ROOT / "outputs" / "reports"
MODELS = ROOT / "outputs" / "models"

REPORTS.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)

SEED = 42
EPOCHS = 50
BATCH_SIZE = 32

CLASS_NAMES = ["Low stress", "High stress"]

tf.keras.utils.set_random_seed(SEED)

# ==================================================
# 2. LOAD DATA
# ==================================================
if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_FILE}\n"
        "Run 02_prepare_dataset.py first."
    )

with np.load(DATA_FILE, allow_pickle=False) as data:
    X = data["X"].astype(np.float32)
    y_original = data["y"].astype(np.int64)
    subjects = data["subjects"].astype(str)

print("\n========== DATASET INFORMATION ==========")
print("EEG shape:", X.shape)
print("Original labels:", dict(zip(
    *np.unique(y_original, return_counts=True)
)))
print("Unique participants:", len(np.unique(subjects)))

if X.ndim != 3:
    raise ValueError(
        f"Expected (windows, time, channels); received {X.shape}"
    )

if len(X) != len(y_original) or len(X) != len(subjects):
    raise ValueError("X, y and subjects have inconsistent lengths.")

if not np.isfinite(X).all():
    raise ValueError("EEG data contains NaN or infinite values.")

# ==================================================
# 3. FIX THE LABEL ERROR
# ==================================================
# Existing labels from preprocessing:
# 1 = low stress
# 2 = high stress
#
# Convert them into the binary labels required by the model:
# 0 = low stress
# 1 = high stress

original_classes = set(np.unique(y_original).tolist())

if original_classes != {1, 2}:
    raise ValueError(
        f"Expected original labels {{1, 2}}, got {original_classes}. "
        "Inspect labels.csv and verify the class definitions."
    )

y = (y_original - 1).astype(np.int64)

print("\n========== BINARY LABELS ==========")
print("0 = Low stress")
print("1 = High stress")
print("Binary class counts:", dict(zip(
    *np.unique(y, return_counts=True)
)))

# Check that the groups contain both classes overall.
subject_class_counts = pd.crosstab(
    pd.Series(subjects, name="subject_id"),
    pd.Series(y, name="label")
)

subject_class_counts.to_csv(
    REPORTS / "participant_class_distribution.csv"
)

print("\nParticipant class distribution saved.")

if len(np.unique(subjects)) < 3:
    raise ValueError("Not enough participants for LOSO training.")

# ==================================================
# 4. MULTI-SCALE CNN + BiLSTM + ATTENTION
# ==================================================
def build_model(input_shape):
    inputs = tf.keras.Input(shape=input_shape)

    # Parallel temporal CNN branches.
    branches = []

    for kernel_size in (3, 7, 15):
        z = tf.keras.layers.Conv1D(
            filters=32,
            kernel_size=kernel_size,
            padding="same",
            use_bias=False,
        )(inputs)

        z = tf.keras.layers.BatchNormalization()(z)
        z = tf.keras.layers.Activation("gelu")(z)
        branches.append(z)

    z = tf.keras.layers.Concatenate()(branches)
    z = tf.keras.layers.SpatialDropout1D(0.20)(z)

    # Learn temporal dependencies.
    z = tf.keras.layers.Bidirectional(
        tf.keras.layers.LSTM(
            32,
            return_sequences=True,
        )
    )(z)

    # Temporal attention.
    attention_scores = tf.keras.layers.Dense(1)(z)
    attention_weights = tf.keras.layers.Softmax(axis=1)(
        attention_scores
    )

    z = tf.keras.layers.Multiply()([z, attention_weights])

    z = tf.keras.layers.Lambda(
        lambda t: tf.reduce_sum(t, axis=1)
    )(z)

    z = tf.keras.layers.Dense(64, activation="gelu")(z)
    z = tf.keras.layers.Dropout(0.35)(z)

    outputs = tf.keras.layers.Dense(
        2,
        activation="softmax",
        name="stress_probabilities",
    )(z)

    model = tf.keras.Model(inputs, outputs)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=1e-3
        ),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


# ==================================================
# 5. LEAVE-ONE-SUBJECT-OUT CROSS-VALIDATION
# ==================================================
logo = LeaveOneGroupOut()

fold_results = []
prediction_rows = []
all_true = []
all_pred = []

unique_subjects = np.unique(subjects)
total_folds = len(unique_subjects)

for fold, (trainval_idx, test_idx) in enumerate(
    logo.split(X, y, groups=subjects),
    start=1,
):
    test_subject = subjects[test_idx[0]]

    # Select a validation participant without using the test participant.
    candidate_subjects = np.unique(subjects[trainval_idx])
    train_idx = None
    val_idx = None
    val_subject = None

    # Find a validation participant whose removal leaves both classes
    # represented in the training set.
    for candidate in candidate_subjects:
        candidate_val_idx = trainval_idx[
            subjects[trainval_idx] == candidate
        ]
        candidate_train_idx = trainval_idx[
            subjects[trainval_idx] != candidate
        ]

        if set(np.unique(y[candidate_train_idx]).tolist()) == {0, 1}:
            train_idx = candidate_train_idx
            val_idx = candidate_val_idx
            val_subject = candidate
            break

    if train_idx is None:
        raise ValueError(
            f"Fold {fold}: cannot form a training set containing "
            "both classes after selecting a validation participant. "
            "Inspect participant_class_distribution.csv."
        )

    # Verify that the test subject has not leaked into training.
    assert test_subject not in set(subjects[train_idx])
    assert test_subject not in set(subjects[val_idx])

    print(
        f"\nFold {fold}/{total_folds}: "
        f"test subject={test_subject}, "
        f"validation subject={val_subject}"
    )

    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(SEED + fold)

    # Calculate class weights from training data only.
    weights = compute_class_weight(
        class_weight="balanced",
        classes=np.array([0, 1]),
        y=y[train_idx],
    )

    class_weights = {
        0: float(weights[0]),
        1: float(weights[1]),
    }

    model = build_model(X.shape[1:])

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=8,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-5,
        ),
    ]

    # Train using training participants only.
    model.fit(
        X[train_idx],
        y[train_idx],
        validation_data=(X[val_idx], y[val_idx]),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=0,
    )

    # Evaluate on the completely held-out participant.
    probabilities = model.predict(X[test_idx], verbose=0)
    predictions = np.argmax(probabilities, axis=1)
    truth = y[test_idx]

    accuracy = accuracy_score(truth, predictions)
    balanced_acc = balanced_accuracy_score(truth, predictions)

    precision = precision_score(
        truth, predictions,
        average="macro",
        zero_division=0,
    )

    recall = recall_score(
        truth, predictions,
        average="macro",
        zero_division=0,
    )

    macro_f1 = f1_score(
        truth, predictions,
        average="macro",
        zero_division=0,
    )

    fold_results.append({
        "fold": fold,
        "test_subject": test_subject,
        "validation_subject": val_subject,
        "test_windows": len(test_idx),
        "accuracy": accuracy,
        "balanced_accuracy": balanced_acc,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": macro_f1,
    })

    all_true.extend(truth.tolist())
    all_pred.extend(predictions.tolist())

    for idx, actual, predicted, probs in zip(
        test_idx, truth, predictions, probabilities
    ):
        prediction_rows.append({
            "subject_id": subjects[idx],
            "true_label": int(actual),
            "true_class": CLASS_NAMES[int(actual)],
            "predicted_label": int(predicted),
            "predicted_class": CLASS_NAMES[int(predicted)],
            "prob_low_stress": float(probs[0]),
            "prob_high_stress": float(probs[1]),
        })

    model.save(MODELS / f"loso_fold_{fold:02d}.keras")

    print(
        f"Accuracy={accuracy:.4f} | "
        f"Balanced accuracy={balanced_acc:.4f} | "
        f"Macro-F1={macro_f1:.4f}"
    )

# ==================================================
# 6. SAVE EVALUATION REPORTS
# ==================================================
results = pd.DataFrame(fold_results)

results.to_csv(
    REPORTS / "loso_per_subject.csv",
    index=False,
)

pd.DataFrame(prediction_rows).to_csv(
    REPORTS / "loso_predictions.csv",
    index=False,
)

cm = confusion_matrix(all_true, all_pred, labels=[0, 1])

pd.DataFrame(
    cm,
    index=["true_low_stress", "true_high_stress"],
    columns=["pred_low_stress", "pred_high_stress"],
).to_csv(REPORTS / "loso_confusion_matrix.csv")

report = classification_report(
    all_true,
    all_pred,
    labels=[0, 1],
    target_names=CLASS_NAMES,
    zero_division=0,
)

(REPORTS / "loso_classification_report.txt").write_text(report)

summary = {
    "participants": int(len(unique_subjects)),
    "folds": int(len(results)),
    "mean_subject_accuracy": float(results["accuracy"].mean()),
    "std_subject_accuracy": float(results["accuracy"].std()),
    "mean_subject_balanced_accuracy": float(
        results["balanced_accuracy"].mean()
    ),
    "mean_subject_macro_f1": float(results["macro_f1"].mean()),
    "pooled_window_accuracy": float(
        accuracy_score(all_true, all_pred)
    ),
    "pooled_window_macro_f1": float(
        f1_score(
            all_true,
            all_pred,
            average="macro",
            zero_division=0,
        )
    ),
}

pd.DataFrame([summary]).to_csv(
    REPORTS / "loso_summary.csv",
    index=False,
)

(REPORTS / "loso_summary.json").write_text(
    json.dumps(summary, indent=2)
)

print("\n========== CLASSIFICATION REPORT ==========")
print(report)

print("Confusion matrix:")
print(cm)

print("\n========== FINAL SUMMARY ==========")
for key, value in summary.items():
    print(f"{key}: {value}")

print("\nReports saved to:", REPORTS)
print("Models saved to:", MODELS)


# ==================================================
# FINAL ACCURACY REPORT: EACH PARTICIPANT + OVERALL
# ==================================================

results = pd.DataFrame(fold_results)

# Save accuracy for every held-out participant.
results["accuracy_percent"] = results["accuracy"] * 100
results["balanced_accuracy_percent"] = (
    results["balanced_accuracy"] * 100
)
results["macro_f1_percent"] = results["macro_f1"] * 100

results.to_csv(
    REPORTS / "loso_per_subject.csv",
    index=False
)

# Overall performance across all held-out windows.
overall_accuracy = accuracy_score(all_true, all_pred) * 100

overall_balanced_accuracy = (
    balanced_accuracy_score(all_true, all_pred) * 100
)

overall_macro_f1 = (
    f1_score(
        all_true,
        all_pred,
        average="macro",
        zero_division=0
    ) * 100
)

mean_subject_accuracy = results["accuracy"].mean() * 100
std_subject_accuracy = results["accuracy"].std() * 100

print("\n" + "=" * 60)
print("SAM-40 EEG STRESS DETECTION - LOSO RESULTS")
print("=" * 60)

print("\n1. EACH PARTICIPANT'S TEST ACCURACY")
print("-" * 60)

for row in results.itertuples():
    print(
        f"Participant {row.test_subject}: "
        f"{row.accuracy_percent:.2f}% "
        f"({row.test_windows} windows)"
    )

print("\n2. OVERALL DATASET PERFORMANCE")
print("-" * 60)

print(f"Participants tested: {len(results)}")
print(f"Mean participant accuracy: {mean_subject_accuracy:.2f}%")
print(f"Standard deviation: {std_subject_accuracy:.2f}%")
print(f"Overall pooled window accuracy: {overall_accuracy:.2f}%")
print(f"Overall balanced accuracy: {overall_balanced_accuracy:.2f}%")
print(f"Overall macro-F1: {overall_macro_f1:.2f}%")

# Save an overall summary.
summary = pd.DataFrame([{
    "participants_tested": len(results),
    "mean_subject_accuracy_percent": mean_subject_accuracy,
    "std_subject_accuracy_percent": std_subject_accuracy,
    "overall_pooled_accuracy_percent": overall_accuracy,
    "overall_balanced_accuracy_percent": overall_balanced_accuracy,
    "overall_macro_f1_percent": overall_macro_f1,
}])

summary.to_csv(
    REPORTS / "loso_summary.csv",
    index=False
)

print("\nSaved participant results:")
print(REPORTS / "loso_per_subject.csv")

print("\nSaved overall results:")
print(REPORTS / "loso_summary.csv")
print("=" * 60)
