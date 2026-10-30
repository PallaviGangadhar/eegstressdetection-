from pathlib import Path

# Project directories
ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
PROCESSED_DIR = ROOT / "processed"

EPOCHS_DIR = PROCESSED_DIR / "epochs"
LABELS_DIR = PROCESSED_DIR / "labels"
CHANNEL_MAP_DIR = PROCESSED_DIR / "channel_mapping"

MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"

# Verified in every EEG_Recordings EDF inventory entry.
# Recheck compatibility before applying this channel set to another dataset.
COMMON_CHANNELS = ["AF3", "T7", "Pz", "T8", "AF4"]

# Signal preprocessing
TARGET_SFREQ = 128
LOW_CUT_HZ = 0.5
HIGH_CUT_HZ = 40.0

# Segmentation
EPOCH_SECONDS = 4.0
OVERLAP_SECONDS = 0.0

# Model training
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
RANDOM_SEED = 42