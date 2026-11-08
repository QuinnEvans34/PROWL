"""Strict ancestry import and full-state continuation; original restore remains unchanged."""
from src.training.stunet_session_20261106 import *
from src.training.stunet_session_20261106 import Session as ParentSession
from src.data.stunet_errata_20261108 import continuation_lr
PARENT_SHA='ed000e1ce25829c29f1efea7bf7a5f3684cddf43b0dbcdc5d9f47e8afc8bfa55'


def loss_diagnostics(outputs,target):
    from torch.nn import functional as F
    result=[]
    with torch.no_grad():
        for out in outputs:
            small=F.interpolate(target[:,None].float(),size=out.shape[2:],mode='nearest')[:,0].long()
            ce=F.cross_entropy(out.detach().float(),small,reduction='none');prob=out.detach().float().softmax(1)
            classes=[]
            for k in range(3):
                mask=small==k; count=int(mask.sum());p=prob[:,k]
                dice=(2*(p*mask).sum()+1e-5)/(p.sum()+mask.sum()+1e-5)
                classes.append(dict(class_id=k,target_voxels=count,ce_mean=float(ce[mask].mean()) if count else None,soft_dice=float(dice)))
            result.append(dict(shape=list(out.shape[2:]),classes=classes))
    return dict(scales=result)


class Session(ParentSession):
    def __init__(self,model,identity,*,device='cuda'):
        if identity.get('parent_checkpoint_sha256')!=PARENT_SHA or identity.get('phase')!='corrected-12k-20261108':raise ValueError('Continuation ancestry required')
        super().__init__(model,identity,device=device)
        self.imported=False

    def import_parent(self,state,expected_identity,checkpoint_sha256):
        if self.imported or self.step!=0:raise ValueError('Duplicate parent import')
        if checkpoint_sha256!=PARENT_SHA or state['step']!=12000:raise ValueError('Wrong parent checkpoint/step')
        if expected_identity.get('nonpromotable') is not False or expected_identity.get('precision')!='fp32' or expected_identity['train']!=self.identity['train']:raise ValueError('Wrong parent roles/precision')
        expected_hash=hashlib.sha256(json.dumps(expected_identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if state['version']!='stunet-session-1' or state['identity']!=expected_identity or state['identity_sha256']!=expected_hash:raise ValueError('Parent identity mismatch')
        if state['scaler'] is not None or set(state['exposure'])!=set(self.exposure) or sum(state['exposure'].values())!=12000 or any(type(v)!=int or v<0 for v in state['exposure'].values()):raise ValueError('Parent exposure/scaler')
        self.model.load_state_dict(state['model'],strict=True);self.optimizer.load_state_dict(state['optimizer'])
        self.step=12000;self.exposure=dict(state['exposure']);restore_rng(state['rng'],self.device);self.imported=True
        loaded=self.state()
        return {k:compare(state[k],loaded[k]) for k in ('model','optimizer','rng','exposure')}

    def state(self):
        value=super().state();value['version']='stunet-continuation-session-1';return value

    def restore(self,state):
        if state['version']!='stunet-continuation-session-1' or not 12000<=state['step']<=24000:raise ValueError('Continuation checkpoint version/step')
        adapted=dict(state,version='stunet-session-1');super().restore(adapted);self.imported=True

    def update(self,provider):
        if not self.imported:raise ValueError("Parent must be imported")
        address=self.step
        image,target,trace=provider.training(address)
        if trace['case_id'] not in self.exposure or trace['step']!=address:raise ValueError('Optimizer role/address')
        if provider.identity!=self.identity['input_sha256']:raise ValueError('Input configuration changed')
        self.model.train();self.model.decoder.deep_supervision=True
        self.optimizer.zero_grad(set_to_none=True)
        lr=continuation_lr(self.step)
        for g in self.optimizer.param_groups:g['lr']=lr
        x=torch.from_numpy(image[None]).to(self.device);y=torch.from_numpy(target[None].astype(np.int64)).to(self.device)
        outputs=self.model(x);loss=deep_supervision_loss(outputs,y);loss.backward()
        diagnostics={}
        if self.identity['nonpromotable'] or (self.step-12000)%500==0:
            diagnostics=loss_diagnostics(outputs,y)
            diagnostics['gradient_l2']={group:float(torch.sqrt(sum(p.grad.detach().double().square().sum() for n,p in self.model.named_parameters() if n.startswith('seg_outputs.')==(group=='heads')))) for group in ('body','heads')}
        if any(p.grad is None or not torch.isfinite(p.grad).all() for p in self.model.parameters()):raise ValueError('Missing/nonfinite gradients')
        self.optimizer.step()
        if self.device.type=='cuda':
            torch.cuda.synchronize()
            if max(torch.cuda.max_memory_allocated(),torch.cuda.max_memory_reserved())>6*1024**3:raise RuntimeError('CUDA cap')
        self.step+=1;self.exposure[trace['case_id']]+=1
        result=dict(step=self.step,phase_step=self.step-12000,loss=float(loss.detach()),lr=lr,input=trace,diagnostics=diagnostics)
        self.optimizer.zero_grad(set_to_none=True)
        return result

