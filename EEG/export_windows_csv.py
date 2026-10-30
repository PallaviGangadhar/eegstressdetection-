#!/usr/bin/env python3
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
p=argparse.ArgumentParser()
p.add_argument("--processed-dir",default="processed"); p.add_argument("--out",default="windows.csv")
a=p.parse_args(); rows=[]
for f in sorted(Path(a.processed_dir).glob("*.npz")):
 z=np.load(f,allow_pickle=False); sid=str(z["subject"].item()) if "subject" in z.files else f.stem
 starts=z["starts_sec"] if "starts_sec" in z.files else np.full(len(z["y"]),np.nan)
 for i,(lab,st) in enumerate(zip(z["y"],starts)):
  rows.append({"subject":sid,"window_index":i,"start_sec_in_xdf":float(st),"label":int(lab),"label_name":"baseline" if int(lab)==0 else "horror"})
pd.DataFrame(rows).to_csv(a.out,index=False)
print(f"Saved {len(rows)} window metadata rows to {a.out}")
if not rows: print("No NPZ windows found; run prepare_xdf_dataset.py first.")
