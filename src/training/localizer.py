"""Bounded CPU localizer mechanics. No source paths or legacy checkpoint discovery."""
from copy import deepcopy
import hashlib
import math
import torch
import torch.nn.functional as F
from monai.inferers import sliding_window_inference
from src.models.segresnet import build_model
from src.data.source_inventory_records import require


def validate_config(c):
    fields={'patch_size','seed','learning_rate','weight_decay','max_steps'}
    require(set(c) in (fields,fields|{'loss_id'},fields|{'loss_id','budget_id'}), 'Unknown localizer configuration')
    sustained='budget_id' in c
    if sustained:require(c['budget_id']=='sustained_localizer_v1' and c.get('loss_id')=='balanced_ce_dice_v1','Unknown sustained budget')
    require(c.get('loss_id','voxel_ce_dice_v1') in ('voxel_ce_dice_v1','balanced_ce_dice_v1'),'Unknown localizer loss')
    require(len(c['patch_size'])==3 and all(type(x)==int and 16<=x<=96 and x%8==0 for x in c['patch_size']), 'Patch must be a bounded multiple of eight')
    require(type(c['seed'])==int and 0<=c['seed']<2**32, 'Invalid seed')
    require(type(c['max_steps'])==int and 1<=c['max_steps']<=(2400 if sustained else 300 if c.get('loss_id')=='balanced_ce_dice_v1' else 100), 'Invalid step budget')
    require(type(c['learning_rate']) in (float,int) and math.isfinite(c['learning_rate']) and 0<c['learning_rate']<=.01, 'Invalid learning rate')
    require(type(c['weight_decay']) in (float,int) and math.isfinite(c['weight_decay']) and 0<=c['weight_decay']<=.1, 'Invalid weight decay')


def image_tensor(x):
    x=x.as_tensor() if hasattr(x,'as_tensor') else torch.as_tensor(x)
    require(x.device.type=='cpu' and x.dtype==torch.float32 and x.ndim==4 and x.shape[0]==1 and
            0<math.prod(x.shape[1:])<=8_000_000 and torch.isfinite(x).all().item(), 'Finite bounded CPU single-channel float32 image required')
    require(x.min().item()>=0 and x.max().item()<=1, 'Expected normalized CT')
    return x


def patch_batch(image,target,config,*,step,member_id):
    """Stateless sampling; retrying a completed-step boundary repeats its next crop."""
    validate_config(config);image=image_tensor(image)
    target=target.as_tensor() if hasattr(target,'as_tensor') else torch.as_tensor(target)
    require(target.device.type=='cpu' and target.shape==image.shape and torch.all((target==0)|(target==1)).item(), 'Binary same-grid CPU target required')
    require(type(step)==int and 0<=step<config['max_steps'] and isinstance(member_id,str) and member_id, 'Invalid sampler position')
    seed=int.from_bytes(hashlib.sha256(f"{config['seed']}:{step}:{member_id}".encode()).digest()[:8],'little')
    rng=torch.Generator().manual_seed(seed)
    roi=config['patch_size'];shape=image.shape[1:]
    pads=[max(0,r-s) for r,s in zip(roi,shape)]
    pad=tuple(v for n in reversed(pads) for v in (n//2,n-n//2))
    image=F.pad(image,pad);target=F.pad(target,pad)
    positive=bool(torch.rand((),generator=rng)<.5)
    coords=torch.nonzero(target[0]==int(positive),as_tuple=False)
    if not len(coords):
        positive=not positive;coords=torch.nonzero(target[0]==int(positive),as_tuple=False)
    center=coords[torch.randint(len(coords),(1,),generator=rng).item()].tolist()
    origin=[max(0,min(c-r//2,s-r)) for c,r,s in zip(center,roi,image.shape[1:])]
    slices=tuple(slice(a,a+r) for a,r in zip(origin,roi))
    x=image[(slice(None),)+slices].clone()[None]
    y=target[(slice(None),)+slices].clone().long()[None]
    return x,y,dict(member_id=member_id,step=step,origin_in_padded_grid=origin,padding=list(pad),
                   center=center,center_class=int(positive),policy='pancreas_background_equal_v1')


def foreground_dice(prediction,target):
    require(prediction.shape==target.shape and all(torch.all((v==0)|(v==1)).item() for v in (prediction,target)), 'Binary matching metrics required')
    n=int(target.sum());p=int(prediction.sum())
    return dict(dice=None if n==0 else 2*int((prediction.bool()&target.bool()).sum())/(n+p),
                target_foreground=n,predicted_foreground=p)


def loss_value(logits,target):
    require(logits.ndim==5 and logits.shape[1]==2 and target.shape==(logits.shape[0],1,*logits.shape[2:]) and
            torch.isfinite(logits).all().item() and torch.all((target==0)|(target==1)).item(), 'Invalid binary logits/target')
    truth=target[:,0].float();prob=logits.softmax(1)[:,1]
    # Empty references contribute CE only, avoiding an invented foreground Dice score.
    dims=(1,2,3);nonempty=truth.sum(dims)>0
    dice=1-(2*(prob*truth).sum(dims)+1e-5)/(prob.sum(dims)+truth.sum(dims)+1e-5)
    return F.cross_entropy(logits,target[:,0].long())+(dice[nonempty].mean() if nonempty.any() else prob.sum()*0)


def balanced_cross_entropy(logits,y):
    per=F.cross_entropy(logits,y,reduction='none');cases=[]
    for i in range(len(y)):
        terms=[(per[i]*(y[i]==k)).sum()/(y[i]==k).sum() for k in (0,1) if (y[i]==k).any()]
        cases.append(torch.stack(terms).mean())
    return torch.stack(cases).mean()


def configured_loss(logits,target,config):
    if config.get('loss_id','voxel_ce_dice_v1')=='voxel_ce_dice_v1':return loss_value(logits,target)
    require(config['loss_id']=='balanced_ce_dice_v1','Unknown objective')
    require(logits.ndim==5 and logits.shape[1]==2 and target.shape==(logits.shape[0],1,*logits.shape[2:]) and
        torch.isfinite(logits).all().item() and torch.all((target==0)|(target==1)).item(),'Invalid balanced logits/target')
    y=target[:,0].long();ce=balanced_cross_entropy(logits,y)
    truth=y.float();p=logits.softmax(1)[:,1];dims=(1,2,3);positive=truth.sum(dims)>0
    dice=1-(2*(p*truth).sum(dims)+1e-5)/(p.sum(dims)+truth.sum(dims)+1e-5)
    return ce+(dice[positive].mean() if positive.any() else p.sum()*0)


class LocalizerSession:
    """CPU reference session; dedicated RNG policy and explicit completed-step boundary."""
    def __init__(self,config):
        validate_config(config);self.config=deepcopy(config);self.step=0
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(config['seed'])
            self.model=build_model({'model':dict(in_channels=1,out_channels=2,init_filters=16,
                norm='group',num_groups=8,blocks_down=(1,2,2,4),blocks_up=(1,1,1),dropout_prob=0)})
        self.optimizer=torch.optim.AdamW(self.model.parameters(),lr=config['learning_rate'],weight_decay=config['weight_decay'])
        self.scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(self.optimizer,T_max=config['max_steps'],eta_min=0)

    def update(self,image,target,member_id):
        require(self.step<self.config['max_steps'], 'Step budget exhausted')
        x,y,trace=patch_batch(image,target,self.config,step=self.step,member_id=member_id)
        self.model.train();self.optimizer.zero_grad(set_to_none=True)
        loss=configured_loss(self.model(x),y,self.config);require(torch.isfinite(loss).item(),'Nonfinite loss')
        loss.backward()
        require(all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in self.model.parameters()),'Missing/nonfinite gradient')
        self.optimizer.step();self.scheduler.step();self.step+=1
        require(all(torch.isfinite(p).all().item() for p in self.model.parameters()),'Nonfinite updated parameter')
        return dict(completed_step=self.step,loss=float(loss.detach()),sampling=trace,**(dict(target_fraction=float(y.float().mean())) if 'loss_id' in self.config else {}))

    @torch.no_grad()
    def predict(self,image):
        image=image_tensor(image);self.model.eval()
        result=sliding_window_inference(image[None],self.config['patch_size'],1,self.model,
            overlap=.25,mode='constant',padding_mode='constant',sw_device='cpu',device='cpu')
        require(result.shape==(1,2,*image.shape[1:]) and torch.isfinite(result).all().item(),'Invalid full-volume output')
        return result[0].softmax(0)
