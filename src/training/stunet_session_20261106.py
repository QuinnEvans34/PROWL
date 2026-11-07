"""Explicit FP32 full-state session for one STU-Net arm; no automatic launch."""
import copy,hashlib,json,math,random
import numpy as np
import torch
from src.training.stunet_transfer_20261106 import deep_supervision_loss


def lr_at(step):
    if type(step)!=int or not 0<=step<12000:raise ValueError('Step outside12k')
    if step<500:return 1e-4*(step+1)/500
    return 1e-4*.5*(1+math.cos(math.pi*(step+1-500)/(12000-500)))


def cpu_tree(value):
    if torch.is_tensor(value):return value.detach().cpu().clone()
    if isinstance(value,dict):return {k:cpu_tree(v) for k,v in value.items()}
    if isinstance(value,list):return [cpu_tree(x) for x in value]
    if isinstance(value,tuple):return tuple(cpu_tree(x) for x in value)
    return copy.deepcopy(value)


def rng_state(device):
    state=np.random.get_state()
    return dict(python=random.getstate(),numpy=(state[0],state[1].tolist(),state[2],state[3],state[4]),
                torch=torch.get_rng_state(),cuda=torch.cuda.get_rng_state_all() if device.type=='cuda' else [])


def restore_rng(value,device):
    random.setstate(value['python']);n=value['numpy'];np.random.set_state((n[0],np.asarray(n[1],dtype=np.uint32),*n[2:]))
    torch.set_rng_state(value['torch'])
    if device.type=='cuda':torch.cuda.set_rng_state_all(value['cuda'])


def compare(a,b,*,atol=0,rtol=0):
    """Recursive full-state comparison, exact metadata; explicit numeric tolerance."""
    peak=0.;count=0
    def walk(x,y,path):
        nonlocal peak,count
        if torch.is_tensor(x):
            if not torch.is_tensor(y) or x.shape!=y.shape or x.dtype!=y.dtype:raise ValueError('Tensor metadata: '+path)
            if x.is_floating_point():
                if not torch.isfinite(x).all() or not torch.isfinite(y).all():raise ValueError('Nonfinite state: '+path)
                if x.numel():peak=max(peak,float((x-y).abs().max()))
                if not torch.allclose(x,y,atol=atol,rtol=rtol):raise ValueError('State numeric mismatch: '+path)
            elif not torch.equal(x,y):raise ValueError('Integer state mismatch: '+path)
            count+=1
        elif isinstance(x,dict):
            if not isinstance(y,dict) or set(x)!=set(y):raise ValueError('State keys: '+path)
            for k in x:walk(x[k],y[k],path+'/'+str(k))
        elif isinstance(x,(tuple,list)):
            if type(x)!=type(y) or len(x)!=len(y):raise ValueError('State sequence: '+path)
            for i,(u,v) in enumerate(zip(x,y)):walk(u,v,path+'/'+str(i))
        elif x!=y:raise ValueError('State metadata: '+path)
    walk(a,b,'state');return dict(tensors=count,max_abs_difference=peak,atol=atol,rtol=rtol)


class Session:
    def __init__(self,model,identity,*,device='cuda'):
        self.device=torch.device(device);self.model=model.to(self.device);self.identity=copy.deepcopy(identity)
        self.identity_sha256=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.optimizer=torch.optim.AdamW(self.model.parameters(),lr=1e-4,weight_decay=1e-5,foreach=False)
        self.step=0;self.exposure={n:0 for n in identity['train']}

    def update(self,provider):
        indices=self.identity.get('qualification_indices')
        address=indices[self.step] if indices is not None else self.step
        image,target,trace=provider.training(address)
        if trace['case_id'] not in self.exposure or trace['step']!=address:raise ValueError('Optimizer role/address')
        if provider.identity!=self.identity['input_sha256']:raise ValueError('Input configuration changed')
        self.model.train();self.model.decoder.deep_supervision=True
        self.optimizer.zero_grad(set_to_none=True)
        lr=lr_at(self.step)
        for g in self.optimizer.param_groups:g['lr']=lr
        x=torch.from_numpy(image[None]).to(self.device);y=torch.from_numpy(target[None].astype(np.int64)).to(self.device)
        loss=deep_supervision_loss(self.model(x),y);loss.backward()
        if any(p.grad is None or not torch.isfinite(p.grad).all() for p in self.model.parameters()):raise ValueError('Missing/nonfinite gradients')
        self.optimizer.step()
        if self.device.type=='cuda':
            torch.cuda.synchronize()
            if max(torch.cuda.max_memory_allocated(),torch.cuda.max_memory_reserved())>6*1024**3:raise RuntimeError('CUDA cap')
        self.step+=1;self.exposure[trace['case_id']]+=1
        result=dict(step=self.step,loss=float(loss.detach()),lr=lr,input=trace)
        self.optimizer.zero_grad(set_to_none=True)
        return result

    def state(self):
        return dict(version='stunet-session-1',identity=self.identity,identity_sha256=self.identity_sha256,
                    step=self.step,exposure=dict(self.exposure),model=cpu_tree(self.model.state_dict()),
                    optimizer=cpu_tree(self.optimizer.state_dict()),rng=rng_state(self.device),scaler=None)

    def restore(self,state):
        if state['version']!='stunet-session-1' or state['identity']!=self.identity or state['identity_sha256']!=self.identity_sha256:
            raise ValueError('Checkpoint identity mismatch')
        if set(state['exposure'])!=set(self.exposure) or sum(state['exposure'].values())!=state['step']:
            raise ValueError('Checkpoint sampler state mismatch')
        if state['scaler'] is not None:raise ValueError('Unexpected precision state')
        self.model.load_state_dict(state['model'],strict=True);self.optimizer.load_state_dict(state['optimizer'])
        self.step=state['step'];self.exposure=dict(state['exposure']);restore_rng(state['rng'],self.device)
