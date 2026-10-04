"""Read-only binary probability and local logit-loss diagnostics (no optimizer)."""
import torch
import torch.nn.functional as F
from src.data.source_inventory_records import require


def checked(p,target):
    p=torch.as_tensor(p).detach().cpu().float();y=torch.as_tensor(target).detach().cpu()
    require(p.shape==y.shape and 0<p.numel()<=8_000_000 and torch.isfinite(p).all().item() and
        p.min().item()>=0 and p.max().item()<=1 and torch.all((y==0)|(y==1)).item(),'Invalid probability/target')
    return p,y.bool()


def distribution(values):
    if not values.numel():return None
    q=torch.quantile(values.flatten(),torch.tensor([.01,.5,.99]))
    return dict(count=values.numel(),mean=values.mean().item(),minimum=values.min().item(),
        maximum=values.max().item(),q01=q[0].item(),median=q[1].item(),q99=q[2].item())


def probability_summary(p,target):
    p,y=checked(p,target);n=y.sum().item();total=p.numel()
    per=-torch.where(y,p.clamp_min(1e-7).log(),(1-p).clamp_min(1e-7).log())
    fg=per[y].sum().item()/total;bg=per[~y].sum().item()/total
    soft=1-(2*p[y].sum().item()+1e-5)/(p.sum().item()+n+1e-5) if n else 0.
    thresholds=[]
    for t in (.01,.05,.1,.25,.5):
        pred=p>t;intersection=(pred&y).sum().item();count=pred.sum().item()
        thresholds.append(dict(threshold=t,predicted_foreground=count,dice=2*intersection/(count+n) if n else None,
            reference_recall=intersection/n if n else None))
    constants=[]
    for value in (.001,.003,.01,.05,.5):
        z=torch.tensor(value,dtype=torch.float64)
        ce=(-(n/total)*z.log()-(1-n/total)*(1-z).log()).item()
        dice=1-(2*value*n+1e-5)/(value*total+n+1e-5) if n else 0.
        constants.append(dict(probability=value,ce=ce,soft_dice_loss=dice,total=ce+dice))
    return dict(target_foreground=n,voxels=total,target_fraction=n/total,
        foreground_probability=distribution(p[y]),background_probability=distribution(p[~y]),
        ce_foreground_contribution=fg,ce_background_contribution=bg,ce=fg+bg,
        mean_ce_foreground=per[y].mean().item() if n else None,
        mean_ce_background=per[~y].mean().item() if n<total else None,
        soft_dice_loss=soft,total=fg+bg+soft,threshold_diagnostics=thresholds,constant_baselines=constants)


def logit_diagnostics(logits,target,*,include_balanced=False):
    """Gradient with respect to foreground-minus-background logit, not model parameters."""
    z=torch.as_tensor(logits).detach().cpu().float();t=torch.as_tensor(target).detach().cpu()
    require(z.ndim==5 and z.shape[0]==1 and z.shape[1]==2 and t.shape==(1,1,*z.shape[2:]) and
        torch.isfinite(z).all().item() and torch.all((t==0)|(t==1)).item(),'Invalid logits/target')
    delta=(z[:,1]-z[:,0]).clone().requires_grad_(True);y=t[:,0].float();p=delta.sigmoid()
    ce=F.binary_cross_entropy_with_logits(delta,y)
    dice=1-(2*(p*y).sum()+1e-5)/(p.sum()+y.sum()+1e-5) if y.any() else p.sum()*0
    objectives=[('ce',ce),('soft_dice',dice)]
    if include_balanced:
        per=F.binary_cross_entropy_with_logits(delta,y,reduction='none')
        objectives.append(('balanced_ce',torch.stack([per[y==k].mean() for k in (0,1) if (y==k).any()]).mean()))
    out={}
    for name,loss in objectives:
        g=torch.autograd.grad(loss,delta,retain_graph=True)[0];groups={}
        for key,mask in [('foreground',y.bool()),('background',~y.bool())]:
            v=g[mask];groups[key]=dict(signed_sum=v.sum().item(),absolute_sum=v.abs().sum().item(),
                mean=v.mean().item() if v.numel() else None)
        out[name]=dict(value=loss.item(),uniform_logit_shift_derivative=g.sum().item(),groups=groups)
    return dict(terms=out,meaning='dLoss/d(foreground_logit-background_logit); negative derivative favors increasing that logit under gradient descent; not a parameter/AdamW update prediction')
