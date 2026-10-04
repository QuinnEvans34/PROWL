"""Per-case equal means over present true classes; preserved present-foreground Dice."""
import torch
from src.data.source_inventory_records import require
LOSS='per_case_present_class_mean_ce_present_foreground_dice_v5'


def objective(logits,target,loss_id=LOSS):
    require(loss_id==LOSS,'Wrong normalized-loss identity')
    require(logits.ndim==5 and logits.shape[1]==3 and logits.numel()>0 and logits.dtype in (torch.float32,torch.float64)
        and target.device==logits.device and target.shape==(logits.shape[0],*logits.shape[2:]) and target.dtype==torch.long
        and ((target>=0)&(target<=2)).all().item() and torch.isfinite(logits).all().item(),'Invalid normalized logits/target')
    logp=logits.log_softmax(1);p=logits.softmax(1);ce=[];dice=[]
    for i in range(len(target)):
        classes=[];foreground=[]
        for k in range(3):
            mask=target[i]==k
            if mask.any():
                classes.append(-logp[i,k][mask].mean())
                if k:
                    t=mask.to(p.dtype)
                    foreground.append(1-(2*(p[i,k]*t).sum()+1e-5)/(p[i,k].sum()+t.sum()+1e-5))
        ce.append(torch.stack(classes).mean())
        dice.append(torch.stack(foreground).mean() if foreground else p[i].sum()*0)
    return torch.stack(ce).mean()+torch.stack(dice).mean()
