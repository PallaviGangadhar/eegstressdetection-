#!/usr/bin/env python3
"""Prepare XDF EEG windows for baseline-vs-horror phase classification.

Labels: 0 = marker 100->110 (baseline phase); 1 = marker 120->130 (horror phase).
These are phase labels, not independently verified stress labels.
"""
import argparse, json, re
from pathlib import Path
from fractions import Fraction
import numpy as np
import pyxdf
from scipy.signal import butter, sosfiltfilt, iirnotch, filtfilt, resample_poly

def info(s, key):
    try:
        v=s["info"][key]
        return str(v[0] if isinstance(v,list) else v)
    except Exception:
        return ""

def sfreq(s):
    try:
        v=float(s["info"]["nominal_srate"][0])
        if v>0: return v
    except Exception: pass
    ts=np.asarray(s.get("time_stamps",[]),float)
    d=np.diff(ts); d=d[d>0]
    if len(d): return float(1/np.median(d))
    raise ValueError("Could not determine sampling rate")

def ch_names(s,n):
    try:
        cs=s["info"]["desc"][0]["channels"][0]["channel"]
        names=[str(c.get("label",[f"ch{i+1}"])[0]) for i,c in enumerate(cs)]
        if len(names)>=n: return names[:n]
    except Exception: pass
    return [f"ch{i+1}" for i in range(n)]

def get_markers(streams):
    events=[]; stream_info=[]
    for s in streams:
        name=info(s,"name").lower(); typ=info(s,"type").lower()
        a=np.asarray(s.get("time_series",[])); ts=np.asarray(s.get("time_stamps",[]),float)
        marker=("marker" in name or "marker" in typ or a.dtype.kind in "USO")
        if marker: stream_info.append({"name":name,"type":typ,"samples":len(a)})
        if not marker or len(a)!=len(ts): continue
        vals=a if a.ndim==1 else (a[:,0] if a.ndim==2 and a.shape[1] else [])
        for t,v in zip(ts,vals):
            try: c=int(float(str(v).strip()))
            except Exception: continue
            if c in (100,110,120,130): events.append((float(t),c))
    return sorted(events),stream_info

def make_intervals(events):
    out=[]
    for i,(t,c) in enumerate(events):
        if c not in (100,120): continue
        close=110 if c==100 else 130
        end=next((tt for tt,cc in events[i+1:] if cc==close),None)
        if end is not None and end>t: out.append((t,end,0 if c==100 else 1))
    return out

def select_eeg(streams):
    candidates=[]
    for i,s in enumerate(streams):
        x=np.asarray(s.get("time_series",[]))
        if x.ndim!=2 or x.shape[0]<100 or x.dtype.kind not in "iuf": continue
        nm=info(s,"name").lower(); ty=info(s,"type").lower()
        if "marker" in nm or "marker" in ty: continue
        score=(100000 if ("eeg" in nm or "eeg" in ty) else 0)+min(x.shape[1],128)
        candidates.append((score,i,s,x))
    if not candidates: raise ValueError("No numeric multi-channel EEG stream found")
    return max(candidates,key=lambda q:q[0])

def process(path,args,outdir):
    streams,_=pyxdf.load_xdf(str(path),synchronize_clocks=True,dejitter_timestamps=True)
    _,stream_idx,s,x=select_eeg(streams)
    x=np.asarray(x,dtype=np.float64)
    ts=np.asarray(s.get("time_stamps",[]),float)
    if len(ts)!=len(x) or len(ts)<2: raise ValueError(f"EEG timestamps={len(ts)} samples={len(x)}")
    if not np.isfinite(x).all(): raise ValueError("EEG contains NaN/Inf")
    fs=sfreq(s); original_ch=x.shape[1]; names=ch_names(s,original_ch)
    if original_ch<20: raise ValueError(f"Found {original_ch} channels; need at least 20")
    if original_ch>20: print(f"  NOTE: {original_ch} channels; using first 20. Verify channel order across subjects.")
    x=x[:,:20]; names=names[:20]

    events,marker_streams=get_markers(streams)
    intervals=make_intervals(events)
    if not intervals:
        raise ValueError(f"No valid 100->110 or 120->130 intervals. Marker codes={[c for _,c in events]}; streams={marker_streams}")

    eeg_start=float(ts[0]); eeg_duration=float(ts[-1]-ts[0])
    rel=[(st-eeg_start,en-eeg_start,lab) for st,en,lab in intervals]
    alignment="synchronized XDF timestamps"
    if not any(en>0 and st<eeg_duration for st,en,_ in rel):
        first=min(st for st,_,_ in intervals)
        rel=[(st-first,en-first,lab) for st,en,lab in intervals]
        alignment="WARNING: fallback relative alignment used; verify marker/EEG clocks"

    target=float(args.sfreq)
    frac=Fraction(target/fs).limit_denominator(1000)
    x=resample_poly(x,frac.numerator,frac.denominator,axis=0)
    hi=min(40.0,target/2-1.0)
    if hi<=1: raise ValueError(f"Target sample rate {target} too low for 1-40 Hz filtering")
    x=sosfiltfilt(butter(4,[1,hi],btype="bandpass",fs=target,output="sos"),x,axis=0)
    if args.notch>0 and args.notch<target/2-1:
        b,a=iirnotch(args.notch,30,fs=target); x=filtfilt(b,a,x,axis=0)
    x=x.astype(np.float32)
    duration=len(x)/target; wn=int(round(args.window_sec*target))
    step=max(1,int(round(wn*(1-args.overlap))))
    windows=[]; labels=[]; starts=[]
    for st,en,label in rel:
        st=max(0.0,float(st)); en=min(duration,float(en))
        if en<=st: continue
        lo=max(0,int(np.ceil(st*target-1e-8)))
        stop=min(len(x),int(np.floor(en*target+1e-8)))
        for pos in range(lo,stop-wn+1,step):
            w=x[pos:pos+wn,:].T
            if w.shape==(20,wn) and np.isfinite(w).all():
                windows.append(w); labels.append(label); starts.append(pos/target)
    if not windows:
        raise ValueError(f"Markers found but no windows fit. EEG duration={duration:.2f}s; intervals relative to EEG={rel}; window={args.window_sec}s; alignment={alignment}")
    X=np.stack(windows).astype(np.float32); y=np.asarray(labels,np.int64)
    m=re.search(r"(subject[_ -]?\d+|sub[_ -]?\d+|p\d+)",path.stem,re.I)
    subject=re.sub(r"[\s-]+","",m.group(1)) if m else path.stem
    dest=outdir/f"{subject}.npz"
    np.savez_compressed(dest,X=X,y=y,subject=np.array(subject),channels=np.array(names),
                        sfreq=np.array(target),window_sec=np.array(args.window_sec),
                        starts_sec=np.asarray(starts,dtype=np.float32))
    counts={str(int(k)):int((y==k).sum()) for k in np.unique(y)}
    print(f"  Saved {dest}: X={X.shape}, classes={counts}; {alignment}")
    return {"subject":subject,"xdf":str(path),"output":str(dest),"eeg_stream_index":int(stream_idx),
            "source_sfreq":fs,"target_sfreq":target,"original_channels":int(original_ch),
            "channels_used":names,"windows":len(y),"class_counts":counts,
            "labels":{"0":"baseline phase","1":"horror stimulus phase"},
            "marker_events_found":len(events),"marker_streams":marker_streams,"alignment":alignment}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--xdf-dir",default="Data/raw"); p.add_argument("--logs-dir",default="Data/logs")
    p.add_argument("--out-dir",default="processed"); p.add_argument("--sfreq",type=float,default=128)
    p.add_argument("--window-sec",type=float,default=4.0); p.add_argument("--overlap",type=float,default=.5)
    p.add_argument("--notch",type=float,default=50.0); args=p.parse_args()
    if args.sfreq<=2 or args.window_sec<=0 or not 0<=args.overlap<1:
        raise SystemExit("Invalid sfreq/window/overlap arguments")
    root=Path(args.xdf_dir); out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    files=sorted(q for q in root.rglob("*") if q.is_file() and q.suffix.lower()==".xdf")
    if not files: raise SystemExit(f"No XDF files found under {root.resolve()}")
    print(f"Found {len(files)} XDF files under {root.resolve()}")
    manifest=[]; errors=[]
    for f in files:
        print(f"\nLoading {f}")
        try: manifest.append(process(f,args,out))
        except Exception as e:
            msg=f"{f.name}: {type(e).__name__}: {e}"; errors.append(msg); print("  SKIP:",msg)
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    (out/"preprocessing_errors.txt").write_text("\n".join(errors)+("\n" if errors else ""))
    print(f"\nProcessed {len(manifest)} of {len(files)} XDF files.")
    print(f"Manifest: {out/'manifest.json'}")
    print(f"Errors: {out/'preprocessing_errors.txt'}")
    print("Labels are baseline-vs-horror phase labels, not independently verified stress labels.")

if __name__=="__main__": main()
