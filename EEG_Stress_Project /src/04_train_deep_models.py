"""Train EEGNet, 1D CNN, and CNN-LSTM with subject-grouped validation or cross-dataset testing."""
import argparse, json, random, copy
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, precision_score,
    recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report)
from config import EPOCHS_DIR, LABELS_DIR, MODELS_DIR, RESULTS_DIR, COMMON_CHANNELS, RANDOM_SEED, BATCH_SIZE, EPOCHS, LEARNING_RATE, WEIGHT_DECAY

def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)

class EEGNet(nn.Module):
    def __init__(self, n_channels, n_times, n_classes=2, dropout=.5, F1=8, D=2, F2=16, kernel_length=64):
        super().__init__()
        self.temporal=nn.Sequential(nn.Conv2d(1,F1,(1,kernel_length),padding=(0,kernel_length//2),bias=False),nn.BatchNorm2d(F1))
        self.spatial=nn.Sequential(nn.Conv2d(F1,F1*D,(n_channels,1),groups=F1,bias=False),nn.BatchNorm2d(F1*D),nn.ELU(),nn.AvgPool2d((1,4)),nn.Dropout(dropout))
        self.temporal_depthwise=nn.Sequential(nn.Conv2d(F1*D,F1*D,(1,16),padding=(0,8),groups=F1*D,bias=False),nn.Conv2d(F1*D,F2,(1,1),bias=False),nn.BatchNorm2d(F2),nn.ELU(),nn.AvgPool2d((1,8)),nn.Dropout(dropout))
        with torch.no_grad():
            dummy=torch.zeros(1,1,n_channels,n_times)
            count=self._features(dummy).flatten(1).shape[1]
        self.classifier=nn.Linear(count,n_classes)
    def _features(self,x):
        return self.temporal_depthwise(self.spatial(self.temporal(x)))
    def forward(self,x):
        return self.classifier(self._features(x.unsqueeze(1)).flatten(1))

class CNN1D(nn.Module):
    def __init__(self, channels, n_classes=2, dropout=.4):
        super().__init__()
        self.features=nn.Sequential(
            nn.Conv1d(channels,32,7,padding=3,bias=False),nn.BatchNorm1d(32),nn.GELU(),
            nn.Conv1d(32,64,7,padding=3,stride=2,bias=False),nn.BatchNorm1d(64),nn.GELU(),nn.Dropout(dropout),
            nn.Conv1d(64,96,5,padding=2,stride=2,bias=False),nn.BatchNorm1d(96),nn.GELU(),nn.AdaptiveAvgPool1d(1))
        self.head=nn.Sequential(nn.Flatten(),nn.Dropout(dropout),nn.Linear(96,n_classes))
    def forward(self,x): return self.head(self.features(x))

class CNNLSTM(nn.Module):
    def __init__(self, channels, n_classes=2, dropout=.4):
        super().__init__()
        self.cnn=nn.Sequential(
            nn.Conv1d(channels,32,7,padding=3,bias=False),nn.BatchNorm1d(32),nn.GELU(),
            nn.Conv1d(32,64,5,padding=2,stride=2,bias=False),nn.BatchNorm1d(64),nn.GELU(),
            nn.Dropout(dropout),nn.Conv1d(64,64,5,padding=2,stride=2,bias=False),nn.BatchNorm1d(64),nn.GELU())
        self.lstm=nn.LSTM(64,64,batch_first=True,bidirectional=True)
        self.head=nn.Sequential(nn.Dropout(dropout),nn.Linear(128,n_classes))
    def forward(self,x):
        seq=self.cnn(x).transpose(1,2)
        out,_=self.lstm(seq)
        return self.head(out[:,-1,:])

def load_data(name):
    ep=EPOCHS_DIR/f"{name}_epochs.npz"; mp=LABELS_DIR/f"{name}_epoch_manifest.csv"
    if not ep.exists() or not mp.exists():
        raise FileNotFoundError(f"Missing {ep} or {mp}. Run inventory/preprocessing first.")
    d=np.load(ep,allow_pickle=False); X=d["X"].astype(np.float32); y=d["y"].astype(int)
    channels=[str(c).strip() for c in d["channels"].tolist()]
    manifest=pd.read_csv(mp)
    if X.ndim!=3 or len(X)!=len(y) or len(y)!=len(manifest):
        raise ValueError(f"{name}: inconsistent X/y/manifest dimensions.")
    for col in ["label","subject_id"]:
        if col not in manifest: raise ValueError(f"{name} manifest missing {col}.")
    labels=pd.to_numeric(manifest["label"],errors="coerce").to_numpy()
    if np.any(~np.isfinite(labels)) or not np.array_equal(labels.astype(int),y):
        raise ValueError(f"{name}: manifest labels do not match NPZ labels.")
    if not np.isin(y,[0,1]).all() or set(np.unique(y))!={0,1}:
        vals,counts=np.unique(y,return_counts=True)
        raise ValueError(f"{name}: need documented labels 0=non-stress, 1=stress and both classes. Found {dict(zip(vals.tolist(),counts.tolist()))}. Do not guess labels.")
    if manifest.subject_id.isna().any() or (manifest.subject_id.astype(str).str.strip()=="").any():
        raise ValueError(f"{name}: missing subject IDs; grouped evaluation is not valid until fixed.")
    if len(channels)!=X.shape[1]: raise ValueError(f"{name}: channel metadata doesn't match tensor.")
    missing=[c for c in COMMON_CHANNELS if c not in channels]
    if missing: raise ValueError(f"{name}: common channels missing {missing}; available={channels}.")
    ix=[channels.index(c) for c in COMMON_CHANNELS]
    X=X[:,ix,:]
    if not np.isfinite(X).all(): raise ValueError(f"{name}: X contains NaN/inf.")
    return X,y,manifest.subject_id.astype(str).to_numpy(),list(COMMON_CHANNELS),float(d["sfreq"])

def standardize(train, others):
    # Fit channel-wise scaler on source/training data only.
    n,c,t=train.shape
    scaler=StandardScaler().fit(train.transpose(0,2,1).reshape(-1,c))
    def trans(x):
        return scaler.transform(x.transpose(0,2,1).reshape(-1,c)).reshape(len(x),t,c).transpose(0,2,1).astype(np.float32)
    return trans(train),[trans(x) for x in others],scaler

def build_model(name,channels,times):
    if name=="eegnet": return EEGNet(channels,times)
    if name=="cnn": return CNN1D(channels)
    if name=="cnn_lstm": return CNNLSTM(channels)
    raise ValueError(name)

def evaluate(model,X,y,device):
    model.eval(); all_y=[]; pred=[]; probs=[]
    loader=DataLoader(TensorDataset(torch.tensor(X),torch.tensor(y,dtype=torch.long)),batch_size=BATCH_SIZE)
    with torch.no_grad():
        for xb,yb in loader:
            logits=model(xb.to(device)); p=torch.softmax(logits,1).cpu().numpy()
            probs.append(p); all_y.extend(yb.numpy().tolist()); pred.extend(p.argmax(1).tolist())
    return np.asarray(all_y),np.asarray(pred),np.concatenate(probs)

def metrics(y,pred,prob):
    try: auc=float(roc_auc_score(y,prob[:,1]))
    except ValueError: auc=None
    cm=confusion_matrix(y,pred,labels=[0,1])
    # labels: rows true non-stress/stress, cols predicted non-stress/stress
    tn,fp,fn,tp=cm.ravel()
    return {"n_epochs":int(len(y)),"accuracy":float(accuracy_score(y,pred)),
      "balanced_accuracy":float(balanced_accuracy_score(y,pred)),
      "precision_macro":float(precision_score(y,pred,average="macro",zero_division=0)),
      "recall_macro":float(recall_score(y,pred,average="macro",zero_division=0)),
      "f1_macro":float(f1_score(y,pred,average="macro",zero_division=0)),
      "sensitivity_stress":float(tp/(tp+fn)) if tp+fn else None,
      "specificity_non_stress":float(tn/(tn+fp)) if tn+fp else None,
      "roc_auc":auc,"confusion_matrix_labels_0_1":cm.tolist()}

def fit_model(name,Xtr,ytr,Xv,yv,device,epochs=EPOCHS,patience=8):
    model=build_model(name,Xtr.shape[1],Xtr.shape[2]).to(device)
    train_dl=DataLoader(TensorDataset(torch.tensor(Xtr),torch.tensor(ytr,dtype=torch.long)),batch_size=BATCH_SIZE,shuffle=True)
    val_dl=DataLoader(TensorDataset(torch.tensor(Xv),torch.tensor(yv,dtype=torch.long)),batch_size=BATCH_SIZE)
    opt=torch.optim.AdamW(model.parameters(),lr=LEARNING_RATE,weight_decay=WEIGHT_DECAY)
    criterion=nn.CrossEntropyLoss()
    best=float("inf"); best_state=None; stale=0; history=[]
    for ep in range(epochs):
        model.train(); losses=[]
        for xb,yb in train_dl:
            xb,yb=xb.to(device),yb.to(device); opt.zero_grad(set_to_none=True)
            loss=criterion(model(xb),yb); loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); losses.append(loss.item())
        model.eval(); vl=[]
        with torch.no_grad():
            for xb,yb in val_dl: vl.append(criterion(model(xb.to(device)),yb.to(device)).item())
        vloss=float(np.mean(vl)); history.append({"epoch":ep+1,"train_loss":float(np.mean(losses)),"val_loss":vloss})
        print(f"  epoch {ep+1:02d}: train_loss={np.mean(losses):.4f} val_loss={vloss:.4f}")
        if vloss<best-1e-5:
            best=vloss; stale=0; best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        else: stale+=1
        if stale>=patience: break
    if best_state is None: raise RuntimeError("No best checkpoint selected.")
    model.load_state_dict(best_state)
    return model,pd.DataFrame(history),best_state

def run(args):
    seed_all(RANDOM_SEED); device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    RESULTS_DIR.mkdir(parents=True,exist_ok=True); MODELS_DIR.mkdir(parents=True,exist_ok=True)
    if args.mode=="cv":
        X,y,g,ch,sf=load_data(args.dataset)
        train_i,val_i=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=RANDOM_SEED).split(X,y,g))
        if set(np.unique(y[train_i]))!={0,1} or set(np.unique(y[val_i]))!={0,1}:
            raise ValueError("Grouped split does not contain both classes in train and validation. Inspect label distribution by subject; do not use random epoch split.")
        Xtr,rest,_=standardize(X[train_i],[X[val_i]])
        Xv=rest[0]
        model,hist,state=fit_model(args.model,Xtr,y[train_i],Xv,y[val_i],device)
        yt,p,pr=evaluate(model,Xv,y[val_i],device); tag=f"cv_{args.dataset}_{args.model}"
        source=args.dataset; target=args.dataset; sf_out=sf
    else:
        Xs,ys,gs,ch,sf=load_data(args.source); Xt,yt,gt,tch,tsf=load_data(args.target)
        if len(ch)!=len(tch) or ch!=tch: raise ValueError("Channel harmonization failed.")
        if not np.isclose(sf,tsf): print(f"WARNING: sampling rates differ ({sf} vs {tsf}); ensure epochs are harmonized to a common rate and duration.")
        tr,va=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=RANDOM_SEED).split(Xs,ys,gs))
        if set(np.unique(ys[tr]))!={0,1} or set(np.unique(ys[va]))!={0,1}:
            raise ValueError("Source grouped split missing a class; inspect subjects and labels.")
        Xtr,scaled,_=standardize(Xs[tr],[Xs[va],Xt])
        Xv,Xtest=scaled
        model,hist,state=fit_model(args.model,Xtr,ys[tr],Xv,ys[va],device)
        yt,p,pr=evaluate(model,Xtest,yt,device); tag=f"cross_{args.source}_to_{args.target}_{args.model}"
        source=args.source; target=args.target; sf_out=sf
    result=metrics(yt,p,pr)
    result.update({"mode":args.mode,"model":args.model,"source_dataset":source,"target_dataset":target,
      "channels":ch,"source_sampling_rate_hz":sf_out,"seed":RANDOM_SEED,"device":str(device),
      "evaluation_note":"One grouped holdout / external dataset run; report as measured, not guaranteed population performance."})
    od=RESULTS_DIR/("cross_dataset" if args.mode=="cross" else "cross_validation"); od.mkdir(parents=True,exist_ok=True)
    with open(od/f"{tag}_metrics.json","w") as f: json.dump(result,f,indent=2)
    hist.to_csv(od/f"{tag}_history.csv",index=False)
    pd.DataFrame(result["confusion_matrix_labels_0_1"],index=["true_non_stress","true_stress"],columns=["pred_non_stress","pred_stress"]).to_csv(od/f"{tag}_confusion.csv")
    with open(od/f"{tag}_report.txt","w") as f: f.write(classification_report(yt,p,labels=[0,1],target_names=["non-stress","stress"],zero_division=0))
    torch.save({"state_dict":state,"model":args.model,"channels":ch,"sampling_rate":sf_out,"class_map":{"0":"non-stress","1":"stress"},"source":source,"target":target},MODELS_DIR/f"{tag}.pt")
    print("\nFINAL METRICS\n"+json.dumps(result,indent=2)); print(f"Saved metrics/model outputs: {od}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["cv","cross"],required=True)
    ap.add_argument("--dataset",choices=["SAM40","EEG_Recordings","Own_Dataset"])
    ap.add_argument("--source",choices=["SAM40","EEG_Recordings","Own_Dataset"])
    ap.add_argument("--target",choices=["SAM40","EEG_Recordings","Own_Dataset"])
    ap.add_argument("--model",choices=["eegnet","cnn","cnn_lstm"],required=True)
    a=ap.parse_args()
    if a.mode=="cv" and not a.dataset: ap.error("--dataset required in cv mode")
    if a.mode=="cross" and (not a.source or not a.target): ap.error("--source and --target required in cross mode")
    if a.mode=="cross" and a.source==a.target: ap.error("source and target must differ")
    run(a)
if __name__=="__main__": main()
