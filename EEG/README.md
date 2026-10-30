# XDF EEG pipeline
Your files are XDF, not EDF. Put Subject1.xdf ... Subject15.xdf in `Data/raw`.
The XDF must contain both the EEG stream and `StressMarkers` marker stream from the recording.
The script labels 100→110 as baseline (0) and 120→130 as horror stimulus (1). These are phase labels, not proof of physiological stress.
Install: `python3 -m pip install -r requirements.txt`
Preprocess: `python3 prepare_xdf_dataset.py --xdf-dir Data/raw --logs-dir Data/logs --out-dir processed`
Export window metadata: `python3 export_windows_csv.py --processed-dir processed --out windows.csv`
Train: `python3 train_loso.py --data-dir processed --out-dir results --max-folds 15 --epochs 5 --batch-size 32`
If XDF has no marker stream, preprocessing stops rather than guessing event timing. Full LOSO may exceed 2–3 hours on a CPU Mac.
