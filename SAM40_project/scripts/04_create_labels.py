
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted"
RATING_FILE = DATA / "Data" / "scales.xls"
OUT = ROOT / "outputs" / "reports" / "labels.csv"

OUT.parent.mkdir(parents=True, exist_ok=True)

if not RATING_FILE.exists():
    # Support layouts where scales.xls is directly under extracted.
    matches = list(DATA.rglob("scales.xls"))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected one scales.xls; found {len(matches)}"
        )
    RATING_FILE = matches[0]

# The first two spreadsheet rows contain trial and task headers.
df = pd.read_excel(RATING_FILE, header=None)

# From the inspected spreadsheet:
# row 0: Subject No., Trial_1, ..., Trial_2, ..., Trial_3
# row 1:             Maths, Symmetry, Stroop, ...
records = []

for r in range(2, len(df)):
    subject_value = pd.to_numeric(df.iloc[r, 0], errors="coerce")

    if pd.isna(subject_value):
        continue

    subject_id = int(subject_value)

    for trial_num, start_col in [(1, 1), (2, 4), (3, 7)]:
        for offset, task in enumerate(
            ["Arithmetic", "Symmetry", "Stroop"]
        ):
            rating = pd.to_numeric(
                df.iloc[r, start_col + offset],
                errors="coerce"
            )

            # Missing ratings remain missing; do not invent labels.
            records.append({
                "subject_id": subject_id,
                "task": task,
                "trial": trial_num,
                "rating": rating
            })

ratings = pd.DataFrame(records)

# Match to actual extracted task-trial filenames.
mat_files = list(DATA.rglob("*.mat"))
filename_pattern = re.compile(
    r"^(Arithmetic|Maths|Symmetry|Mirror_image|Stroop|Relax)_sub_(\d+)_trial(\d+)\.mat$",
    re.IGNORECASE
)

actual_files = []

for path in mat_files:
    match = filename_pattern.match(path.name)
    if not match:
        continue

    task_name, subject, trial = match.groups()
    task_name = task_name.lower()

    if task_name in {"maths", "arithmetic"}:
        task_key = "Arithmetic"
    elif task_name in {"symmetry", "mirror_image"}:
        task_key = "Symmetry"
    else:
        task_key = task_name.capitalize()

    actual_files.append({
        "filename": path.relative_to(DATA).as_posix(),
        "subject_id": int(subject),
        "task": task_key,
        "trial": int(trial)
    })

files_df = pd.DataFrame(actual_files)

if files_df.empty:
    raise RuntimeError(
        "No matching task-trial files found. "
        "Check the actual filenames before changing the pattern."
    )

labels = files_df.merge(
    ratings,
    on=["subject_id", "task", "trial"],
    how="left",
    validate="many_to_one"
)

# Preserve all recordings so missing ratings can be investigated.
labels["rating"] = pd.to_numeric(labels["rating"], errors="coerce")

labels.to_csv(OUT, index=False)

print("Saved:", OUT)
print("Matched recording files:", len(labels))
print("Unique participants:", labels["subject_id"].nunique())
print("Missing ratings:", int(labels["rating"].isna().sum()))
print("\nTask counts:")
print(labels["task"].value_counts().to_string())
print("\nFirst rows:")
print(labels.head(10).to_string(index=False))
