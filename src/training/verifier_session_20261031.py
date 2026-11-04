"""Small shared-encoder candidate verifier; patient-balanced, role-bound fitting."""
import hashlib,json
from pathlib import Path
import numpy as np
import torch
from torch import nn
from src.training.experiment_config import sha256

class Verifier(nn.Module):
    def __init__(self):
        super().__init__();layers=[];channels=4
        for out in (16,32,64):
            layers.extend([nn.Conv3d(channels,out,3,stride=2,padding=1),nn.GroupNorm(4,out),nn.SiLU()]);channels=out
        self.encoder=nn.Sequential(*layers,nn.AdaptiveAvgPool3d(1));self.head=nn.Sequential(nn.Linear(132,32),nn.SiLU(),nn.Linear(32,1))
    def forward(self,x,features):
        if x.ndim!=6 or tuple(x.shape[1:3])!=(2,4) or features.shape!=(len(x),4):raise ValueError('Verifier input contract')
        encoded=self.encoder(x.reshape(-1,4,*x.shape[-3:])).reshape(len(x),128)
        return self.head(torch.cat([encoded,features],dim=1))[:,0]

class Dataset:
    def __init__(self,manifest,expected_sha,*,qualification=False):
        self.path=Path(manifest)
        if sha256(self.path)!=expected_sha:raise ValueError('Dataset manifest changed')
        self.manifest=json.loads(self.path.read_text());self.pin=expected_sha
        if self.manifest['status']!=('PILOT_COMPLETE_PENDING_VISUAL_REVIEW' if qualification else 'QUALIFIED_FIT_TUNE_VIEWS'):raise ValueError('Unqualified inputs')
        self.rows=self.manifest['candidates'];self.checked=set()
        patients=self.manifest['patients']
        if set(patients)!={'verifier_fit','verifier_tune'} or set(patients['verifier_fit'])&set(patients['verifier_tune']):raise ValueError('Invalid roles')
        keys=[]
        for r in self.rows:
            if r['role'] not in patients or r['case_id'] not in patients[r['role']]:raise ValueError('Protected input')
            keys.append((r['case_id'],r['component_id']))
        if len(set(keys))!=len(keys):raise ValueError('Duplicate candidates')
        self.fit=[i for i,r in enumerate(self.rows) if r['role']=='verifier_fit']
        self.tune=[i for i,r in enumerate(self.rows) if r['role']=='verifier_tune']
        if not self.fit or (not self.tune and not qualification):raise ValueError('Empty candidate role')
        counts={}
        for i in self.fit:
            n=self.rows[i]['case_id'];counts[n]=counts.get(n,0)+1
        self.weights={i:len(self.fit)/(len(counts)*counts[self.rows[i]['case_id']]) for i in self.fit}

    def get(self,index,operation):
        r=self.rows[index]
        if operation not in ('optimizer','tune') or r['role']!=('verifier_fit' if operation=='optimizer' else 'verifier_tune'):raise ValueError('Protected data operation')
        path=Path(r['path'])
        # Hash on every read; immutable cache inputs are small and checks explicit.
        if sha256(path)!=r['sha256']:raise ValueError('Candidate cache changed')
        with np.load(path,allow_pickle=False) as a:
            x=a['views'].astype(np.float32);f=a['features'].astype(np.float32)
        if x.shape!=(2,4,64,64,64) or f.shape!=(4,) or not np.isfinite(x).all() or not np.isfinite(f).all():raise ValueError('Invalid cached views')
        return x,f,float(r['positive'])

class Session:
    def __init__(self,dataset,*,device='cuda',seed=20261031,batch_size=8,lr=.0003):
        self.dataset=dataset;self.device=torch.device(device);self.seed=seed;self.batch_size=batch_size;self.lr=lr
        torch.manual_seed(seed);self.model=Verifier().to(self.device)
        self.optimizer=torch.optim.AdamW(self.model.parameters(),lr=lr,weight_decay=.0001)
        self.step=0;self.epoch=0;self.position=0;self.trace=None
    def order(self):
        g=torch.Generator().manual_seed(self.seed+self.epoch)
        return [self.dataset.fit[i] for i in torch.randperm(len(self.dataset.fit),generator=g).tolist()]
    def update(self):
        order=self.order();ids=order[self.position:self.position+self.batch_size]
        if not ids:raise ValueError('Empty update')
        batch=[self.dataset.get(i,'optimizer') for i in ids]
        x=torch.from_numpy(np.stack([b[0] for b in batch])).to(self.device);f=torch.from_numpy(np.stack([b[1] for b in batch])).to(self.device)
        y=torch.tensor([b[2] for b in batch],device=self.device);w=torch.tensor([self.dataset.weights[i] for i in ids],device=self.device)
        self.model.train();self.optimizer.zero_grad(set_to_none=True)
        logits=self.model(x,f);loss=(nn.functional.binary_cross_entropy_with_logits(logits,y,reduction='none')*w).mean()
        if not torch.isfinite(loss):raise ValueError('Nonfinite loss')
        loss.backward()
        grads=[p.grad for p in self.model.parameters() if p.grad is not None]
        if not grads or any(not torch.isfinite(g).all() for g in grads):raise ValueError('Nonfinite/missing gradient')
        norm=nn.utils.clip_grad_norm_(self.model.parameters(),5.,error_if_nonfinite=True);self.optimizer.step()
        self.step+=1;self.position+=len(ids)
        self.trace=dict(indices=ids,input_sha256=hashlib.sha256(x.detach().cpu().numpy().tobytes()+f.detach().cpu().numpy().tobytes()).hexdigest(),loss=float(loss.detach()),gradient_norm=float(norm),step=self.step,epoch=self.epoch)
        if self.position==len(order):self.epoch+=1;self.position=0
        return self.trace
    @torch.no_grad()
    def evaluate(self):
        self.model.eval();losses={};scores=[]
        for i in self.dataset.tune:
            x,f,y=self.dataset.get(i,'tune');logit=self.model(torch.from_numpy(x[None]).to(self.device),torch.from_numpy(f[None]).to(self.device))[0]
            loss=float(nn.functional.binary_cross_entropy_with_logits(logit,torch.tensor(y,device=self.device)))
            if not np.isfinite(loss):raise ValueError('Nonfinite tune loss')
            r=self.dataset.rows[i];losses.setdefault(r['case_id'],[]).append(loss);scores.append(dict(case_id=r['case_id'],component_id=r['component_id'],score=float(logit.sigmoid())))
        return dict(patient_balanced_bce=float(np.mean([np.mean(v) for v in losses.values()])),candidate_patients=len(losses),scores=scores)
    def state(self):
        return dict(model=self.model.state_dict(),optimizer=self.optimizer.state_dict(),step=self.step,epoch=self.epoch,position=self.position,
            seed=self.seed,batch_size=self.batch_size,lr=self.lr,dataset_sha256=self.dataset.pin,torch_rng=torch.get_rng_state(),
            cuda_rng=torch.cuda.get_rng_state_all() if self.device.type=='cuda' else [])
    @classmethod
    def restore(cls,state,dataset,device='cuda'):
        if state['dataset_sha256']!=dataset.pin:raise ValueError('Restore input identity')
        obj=cls(dataset,device=device,seed=state['seed'],batch_size=state['batch_size'],lr=state['lr'])
        obj.model.load_state_dict(state['model'],strict=True);obj.optimizer.load_state_dict(state['optimizer'])
        obj.step=state['step'];obj.epoch=state['epoch'];obj.position=state['position'];torch.set_rng_state(state['torch_rng'])
        if obj.device.type=='cuda':torch.cuda.set_rng_state_all(state['cuda_rng'])
        return obj
