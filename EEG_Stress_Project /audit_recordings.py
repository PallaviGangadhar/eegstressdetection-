#!/usr/bin/env python3
"""
Audit EDF recordings and build a metadata review table.
This does NOT guess stress labels or participant IDs.
"""
from pathlib import Path
import argparse, re
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--dataset-root", default="An EEG Recordings Dataset for Mental Stress Detection")
    ap.add_argument("--out", default="data/EEG_Recordings/metadata/recording_metadata_review.csv")
    args=ap.parse_args()
    root=Path(args.root).expanduser().resolve()
    ds=(root/args.dataset_root).resolve()
    if not ds.exists():
        # Search under project root for the folder name
        candidates=[p for p in root.rglob("*") if p.is_dir() and p.name=="An EEG Recordings Dataset for Mental Stress Detection"]
        if candidates: ds=candidates[0]
    if not ds.exists():
        raise SystemExit(f"Dataset folder not found: {ds}\nPass --dataset-root with the actual path relative to --root.")
    files=sorted(p for p in ds.rglob("*") if p.is_file() and p.suffix.lower() in {".edf",".bdf",".set",".fif",".vhdr"})
    if not files: raise SystemExit(f"No supported EEG files found under {ds}")
    rows=[]
    for p in files:
        rel=p.relative_to(ds)
        parts=rel.parts
        task=parts[0] if len(parts)>1 else ""
        # A candidate is for manual review only, never automatically accepted as truth.
        m=re.search(r"(?i)(?:subject|sub|participant|person|p)[ _-]*0*(\d+)",p.stem)
        candidate=m.group(1) if m else ""
        rows.append({
            "dataset":"EEG_Recordings",
            "absolute_file_path":str(p),
            "relative_file_path":str(rel),
            "task_folder_candidate":task,
            "filename":p.name,
            "subject_id_candidate_for_manual_review":candidate,
            "subject_id_verified":"",
            "label_from_documentation":"",
            "label_status":"needs_documentation_review",
            "notes":"Do not infer stress label from task-folder name without dataset protocol."
        })
    out=Path(args.out)
    if not out.is_absolute(): out=root/out
    out.parent.mkdir(parents=True,exist_ok=True)
    df=pd.DataFrame(rows)
    df.to_csv(out,index=False)
    print(f"Found {len(df)} EEG recordings.")
    print(f"Task folders: {df.task_folder_candidate.value_counts(dropna=False).to_dict()}")
    print(f"Review CSV: {out}")
    print("\nFirst rows:")
    print(df[["relative_file_path","task_folder_candidate","subject_id_candidate_for_manual_review","label_status"]].head(12).to_string(index=False))
    print("\nNext: fill subject_id_verified and label_from_documentation using the dataset's documented protocol.")
if __name__=="__main__": main()
