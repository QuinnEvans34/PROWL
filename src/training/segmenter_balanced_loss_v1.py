"""Provisional pancreas64/lesion256 weighted-mean CE with unchanged present-foreground Dice."""
import torch
import torch.nn.functional as F
from src.data.source_inventory_records import require
LOSS='voxel_ce_pancreas64_lesion256_present_foreground_dice_v4'


def objective(logits,target,loss_id=LOSS):
    require(loss_id==LOSS,'Wrong balanced-loss identity')
    require(logits.ndim==5 and logits.shape[1]==3 and logits.numel()>0 and
        logits.dtype in (torch.float32,torch.float64) and target.device==logits.device and
        target.shape==(logits.shape[0],*logits.shape[2:]) and target.dtype==torch.long and
        ((target>=0)&(target<=2)).all().item() and torch.isfinite(logits).all().item(),
        'Invalid balanced logits/target')
    ce=F.cross_entropy(logits,target,weight=logits.new_tensor([1.,64.,256.]),reduction='mean')
    p=logits.softmax(1);terms=[]
    for i in range(len(target)):
        present=[]
        for k in (1,2):
            truth=(target[i]==k).to(p.dtype)
            if truth.any():present.append(1-(2*(p[i,k]*truth).sum()+1e-5)/(p[i,k].sum()+truth.sum()+1e-5))
        terms.append(torch.stack(present).mean() if present else p[i].sum()*0)
    return ce+torch.stack(terms).mean()
