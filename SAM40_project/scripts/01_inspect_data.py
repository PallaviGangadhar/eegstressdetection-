
from pathlib import Path
import rarfile
import shutil
import subprocess
import pandas as pd
import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "Data" / "Data.rar"
DATA = ROOT / "data" / "extracted"
EXTRACTION_MARKER = DATA / ".sam40_extracted"

DATA.mkdir(parents=True, exist_ok=True)

# Extract the RAR archive only if it has not already been extracted.
if not EXTRACTION_MARKER.exists():
    if not ARCHIVE.exists():
        raise FileNotFoundError(f"Archive not found: {ARCHIVE}")

    bsdtar = shutil.which("bsdtar")
    if bsdtar:
        subprocess.run(
            [bsdtar, "-xf", str(ARCHIVE), "-C", str(DATA)],
            check=True
        )
    else:
        with rarfile.RarFile(ARCHIVE) as archive:
            archive.extractall(DATA)

    EXTRACTION_MARKER.touch()

print("\nMATLAB files:")
mat_files = sorted(DATA.rglob("*.mat"))
for path in mat_files[:20]:
    print(path.relative_to(DATA))

print(f"\nTotal MAT files: {len(mat_files)}")

print("\nSpreadsheets:")
for path in DATA.rglob("*"):
    if path.suffix.lower() in {".xls", ".xlsx"}:
        print(path.relative_to(DATA))

        try:
            book = pd.ExcelFile(path)
            print("Sheets:", book.sheet_names)

            for sheet in book.sheet_names:
                frame = pd.read_excel(path, sheet_name=sheet)
                print(f"\nSheet: {sheet}")
                print(frame.head(10).to_string(index=False))
                print("Columns:", frame.columns.tolist())
        except Exception as exc:
            print("Spreadsheet inspection failed:", exc)

print("\nMAT variable inspection:")
for path in mat_files[:10]:
    print(f"\n{path.name}")

    try:
        variables = loadmat(path)
        for name, value in variables.items():
            if not name.startswith("__"):
                if isinstance(value, np.ndarray):
                    print(name, value.shape, value.dtype)
                else:
                    print(name, type(value))
    except Exception as exc:
        print("Could not read with scipy:", exc)



