import argparse
from pathlib import Path

import pandas as pd
import mne

from config import CHANNEL_MAP_DIR


def read_raw(path):
    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".edf":
        return mne.io.read_raw_edf(
            path, preload=False, verbose="ERROR"
        )

    elif ext == ".bdf":
        return mne.io.read_raw_bdf(
            path, preload=False, verbose="ERROR"
        )

    elif ext == ".gdf":
        return mne.io.read_raw_gdf(
            path, preload=False, verbose="ERROR"
        )

    elif ext == ".set":
        return mne.io.read_raw_eeglab(
            path, preload=False, verbose="ERROR"
        )

    elif ext == ".fif":
        return mne.io.read_raw_fif(
            path, preload=False, verbose="ERROR"
        )

    elif ext == ".mat":
        raise ValueError(
            "MAT files require inspection of their variables "
            "and array dimensions before loading."
        )

    raise ValueError(f"Unsupported file format: {ext}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--metadata",
        required=True
    )

    args = parser.parse_args()

    metadata = pd.read_csv(args.metadata)

    required = {
        "dataset",
        "file_path",
        "subject_id",
        "label"
    }

    missing = required - set(metadata.columns)

    if missing:
        raise ValueError(
            f"Missing metadata columns: {sorted(missing)}"
        )

    results = []

    for _, row in metadata.iterrows():

        path = Path(str(row["file_path"]))

        if not path.is_absolute():
            path = Path.cwd() / path

        result = {
            "dataset": row["dataset"],
            "file_path": str(path),
            "subject_id": row["subject_id"],
            "label": row["label"]
        }

        try:
            if not path.exists():
                raise FileNotFoundError(path)

            raw = read_raw(path)

            result.update({
                "sampling_rate": raw.info["sfreq"],
                "number_of_channels": len(raw.ch_names),
                "duration_seconds":
                    raw.n_times / raw.info["sfreq"],
                "channel_names":
                    ";".join(raw.ch_names),
                "error": ""
            })

            raw.close()

        except Exception as error:
            result["error"] = str(error)

        results.append(result)

    report = pd.DataFrame(results)

    CHANNEL_MAP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    dataset_name = Path(
        args.metadata
    ).parent.parent.name

    output = (
        CHANNEL_MAP_DIR
        / f"inventory_{dataset_name}.csv"
    )

    report.to_csv(output, index=False)

    print(report.to_string(index=False))
    print(f"\nReport saved to: {output}")


if __name__ == "__main__":
    main()