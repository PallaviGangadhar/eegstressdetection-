#!/usr/bin/env python3
"""Model A: CNN-LSTM + Leave-One-Subject-Out (LOSO).
Input NPZ files in processed/: X=(windows,channels,samples), y=0/1, optional subject.
Labels here mean baseline (0) vs horror phase (1), not independently verified stress.
"""
import argparse, csv, json
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, precision_recall_fscore_support

class CNNLSTM(nn.Module):
    def __init__(self, channels, classes=2):
        super().__init__()
        self.cnn = nn.Sequential(nn.Conv1d(channels,32,7,padding=3), nn.BatchNorm1d(32), nn.ReLU(), nn.MaxPool1d(2), nn.Conv1d(32,64,5,padding=2), nn.BatchNorm1d(64), nn.ReLU(), nn.MaxPool1d(2))
        self.lstm = nn.LSTM(64,32,batch_first=True,bidirectional=True)
        self.head = nn.Sequential(nn.Dropout(.3), nn.Linear(64,classes))
    def forward(self,x):
        x=self.cnn(x).transpose(1,2); _,(h,_)=self.lstm(x)
        return self.head(torch.cat((h[-2],h[-1]),dim=1))

def load_subjects(folder):
    files=sorted(Path(folder).glob('*.npz'))
    if not files: raise FileNotFoundError(f'No .npz files found in {folder}')
    out={}
    for f in files:
        with np.load(f,allow_pickle=False) as z:
            X=z['X'].astype(np.float32); y=z['y'].astype(np.int64).reshape(-1)
            sid=str(z['subject'].item()) if 'subject' in z.files else f.stem
        if X.ndim!=3 or len(X)!=len(y): raise ValueError(f'{f}: expected X=(windows,channels,samples) and matching y')
        if not set(np.unique(y)).issubset({0,1}): raise ValueError(f'{f}: expected labels 0/1, got {np.unique(y)}')
        out[sid]=(X,y)
    if len({x.shape[1] for x,y in out.values()})!=1 or len({x.shape[2] for x,y in out.values()})!=1:
        raise ValueError('All subjects must have the same channel and sample dimensions.')
    return out

def normalize(train,test):
    mean=train.mean(axis=(0,2),keepdims=True); std=train.std(axis=(0,2),keepdims=True); std=np.where(std<1e-6,1,std)
    return ((train-mean)/std).astype(np.float32),((test-mean)/std).astype(np.float32)

def score(y,p):
    pr,re,f1,_=precision_recall_fscore_support(y,p,labels=[0,1],average='macro',zero_division=0)
    return {'accuracy':float(accuracy_score(y,p)),'balanced_accuracy':float(balanced_accuracy_score(y,p)) if len(np.unique(y))==2 else None,'macro_precision':float(pr),'macro_recall':float(re),'macro_f1':float(f1),'confusion_matrix_labels_0_1':json.dumps(confusion_matrix(y,p,labels=[0,1]).tolist())}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',default='processed'); ap.add_argument('--out-dir',default='results_model_a'); ap.add_argument('--epochs',type=int,default=15); ap.add_argument('--batch-size',type=int,default=32); ap.add_argument('--lr',type=float,default=1e-3); ap.add_argument('--seed',type=int,default=42); a=ap.parse_args()
    np.random.seed(a.seed); torch.manual_seed(a.seed)
    device=torch.device('mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu'))
    outdir=Path(a.out_dir); outdir.mkdir(parents=True,exist_ok=True); subjects=load_subjects(a.data_dir); ids=list(subjects)
    print('Device:',device,'\nSubjects:',ids); rows=[]; truth=[]; preds=[]
    for fold,test_id in enumerate(ids,1):
        train_ids=[s for s in ids if s!=test_id]; Xtr=np.concatenate([subjects[s][0] for s in train_ids]); ytr=np.concatenate([subjects[s][1] for s in train_ids]); Xte,yte=subjects[test_id]
        if len(np.unique(ytr))<2: print('Skipping',test_id,'training data has one class'); continue
        Xtr,Xte=normalize(Xtr,Xte); counts=np.bincount(ytr,minlength=2).astype(np.float32); weights=counts.sum()/(2*np.maximum(counts,1))
        model=CNNLSTM(Xtr.shape[1]).to(device); opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=1e-4); lossfn=nn.CrossEntropyLoss(weight=torch.tensor(weights,dtype=torch.float32,device=device))
        loader=DataLoader(TensorDataset(torch.from_numpy(Xtr),torch.from_numpy(ytr)),batch_size=a.batch_size,shuffle=True)
        print(f'\nFold {fold}/{len(ids)} test={test_id}; train={len(ytr)} test={len(yte)}')
        for ep in range(1,a.epochs+1):
            model.train(); total=seen=0
            for xb,yb in loader:
                xb,yb=xb.to(device),yb.to(device); opt.zero_grad(set_to_none=True); loss=lossfn(model(xb),yb); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); total+=loss.item()*len(yb); seen+=len(yb)
            print(f' epoch {ep:02d}/{a.epochs} loss={total/max(seen,1):.4f}')
        model.eval()
        with torch.no_grad(): p=model(torch.from_numpy(Xte).to(device)).argmax(1).cpu().numpy()
        m=score(yte,p); rows.append({'fold':fold,'test_subject':test_id,'n_test_windows':len(yte),'test_baseline':int((yte==0).sum()),'test_horror':int((yte==1).sum()),**m}); truth.extend(yte.tolist()); preds.extend(p.tolist())
        print(' test metrics:',m); torch.save({'model_state_dict':model.state_dict(),'test_subject':test_id,'n_channels':Xtr.shape[1],'n_timepoints':Xtr.shape[2],'class_weights':weights.tolist()},outdir/f'cnn_lstm_loso_{test_id}.pt')
    if not rows: raise SystemExit('No folds completed; check NPZ data and labels.')
    with open(outdir/'fold_metrics.csv','w',newline='') as f: w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary={'model':'CNN-LSTM','completed_folds':len(rows),'subjects_total':len(ids),'window_weighted_accuracy':float(accuracy_score(truth,preds)),'window_weighted_balanced_accuracy':float(balanced_accuracy_score(truth,preds)) if len(set(truth))==2 else None,'window_weighted_macro_f1':float(precision_recall_fscore_support(truth,preds,labels=[0,1],average='macro',zero_division=0)[2]),'confusion_matrix_labels_0_1':confusion_matrix(truth,preds,labels=[0,1]).tolist(),'note':'Preliminary baseline-vs-horror phase classification, not independently verified stress detection. Single-class test subjects limit interpretation.'}
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2)); print('\nOVERALL HELD-OUT RESULTS\n'+json.dumps(summary,indent=2)); print('Saved results to',outdir.resolve())
if __name__=='__main__': main()
