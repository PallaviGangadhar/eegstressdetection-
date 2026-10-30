
# EEG Stress Detection Project

## Objective
Evaluate EEG mental stress detection using SAM40,
An EEG Recordings Dataset for Mental Stress Detection,
and eventually our own EEG recordings.

## Installation
python -m pip install -r requirements.txt

## Dataset locations
SAM40 raw files:
data/SAM40/raw/

EEG Recordings raw files:
data/EEG_Recordings/raw/

Own EEG recordings:
data/Own_Dataset/raw/

## Step 1: Inspect datasets
python src/01_inventory.py --metadata data/SAM40/metadata/recordings.csv

python src/01_inventory.py --metadata data/EEG_Recordings/metadata/recordings.csv

## Step 2: Configure channels
Inspect the inventory reports.
Set the verified common channel names in src/config.py.

## Step 3: Preprocess and segment
python src/02_preprocess_segment.py --metadata data/SAM40/metadata/recordings.csv

python src/02_preprocess_segment.py --metadata data/EEG_Recordings/metadata/recordings.csv

## Step 4: Train and cross-test
python src/03_train_evaluate.py --source SAM40 --target EEG_Recordings

python src/03_train_evaluate.py --source EEG_Recordings --target SAM40

## WS-KAN-EEGNet subject-held-out run
For the already-preprocessed EEG_Recordings epochs, run:

```bash
python wskan_eegnet_pipeline.py --device auto
```

This trains the included wavelet/CNN/KAN model with separate subject-level
training, validation, and test splits. Metrics, predictions, and model weights
are saved under `results/WSKAN_EEGNet_subject_holdout/` and `models/`.
Training defaults to 3 epochs; pass `--epochs` to change this. The runner uses
prepared NPZ epochs and does not load SAM40 raw MATLAB files.

## Important
Use only documented labels.
Do not infer stress labels from stimulus names alone.
Use subject-independent splits. Results depend on the dataset labels and
protocol being correct.
