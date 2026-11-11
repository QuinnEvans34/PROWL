"""A compact CT-only lesion center locator, independent of the contour refiner."""
from itertools import product
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

# Keep every acquired axial slice so a 5 mm slice is never quantized to a
# 20 mm center grid. The cached patches and inference region are native RAS.
STRIDE = (4,4,1)


class Locator(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv3d(1,12,3,padding=1),nn.GroupNorm(3,12),nn.SiLU(),
            nn.Conv3d(12,16,3,padding=2,dilation=2),nn.GroupNorm(4,16),nn.SiLU(),
            nn.Conv3d(16,16,3,padding=3,dilation=3),nn.GroupNorm(4,16),nn.SiLU(),
            nn.Conv3d(16,1,1),
        )

    def forward(self, x):
        if x.ndim!=5 or x.shape[1]!=1 or any(n<s for n,s in zip(x.shape[2:],STRIDE)):
            raise ValueError('One normalized CT channel required')
        padding=tuple(p for n,s in reversed(list(zip(x.shape[2:],STRIDE))) for p in (0,(-n)%s))
        return self.layers(F.avg_pool3d(F.pad(x,padding),STRIDE))


def center_target(mask, support):
    """Preserve a one-voxel target at the lower-resolution center grid."""
    if mask.ndim!=3 or mask.shape!=support.shape or any(n%s for n,s in zip(mask.shape,STRIDE)):
        raise ValueError('Aligned divisible training patch required')
    if np.any(mask&~support):
        raise ValueError('Target outside supported input')
    shape=tuple(n//s for n,s in zip(mask.shape,STRIDE))
    valid=support.reshape(*(a for pair in zip(shape,STRIDE) for a in pair)).any(axis=(1,3,5))
    heat=np.zeros(shape,dtype=np.float32)
    points=np.argwhere(mask)
    if len(points):
        lo,hi=points.min(axis=0),points.max(axis=0)
        center=(lo+hi)//(2*np.array(STRIDE))
        if not valid[tuple(center)]:
            raise ValueError('Unsupported center')
        grid=np.indices(shape,dtype=np.float32)
        heat=np.exp(-np.square(grid-center[:,None,None,None]).sum(0)/2).astype(np.float32)
        heat[heat<.05]=0
    return heat,valid


def translated(image, mask, support, shift):
    if max(abs(x) for x in shift)>8 or any(a.shape!=image.shape for a in (mask,support)):
        raise ValueError('Bounded joint shift required')
    n=image.shape
    src=tuple(slice(max(0,-d),min(s,s-d)) for s,d in zip(n,shift))
    dst=tuple(slice(max(0,d),min(s,s+d)) for s,d in zip(n,shift))
    out=[np.zeros_like(a) for a in (image,mask,support)]
    for v,a in zip(out,(image,mask,support)):v[dst]=a[src]
    return (image,mask,support) if out[1].sum()!=mask.sum() else tuple(out)


def focal_heatmap(logits, targets, support):
    x,y=logits[support],targets[support]
    if not x.numel():raise ValueError('Empty supported cells')
    p=x.sigmoid()
    pos=y==1
    # CenterNet-style positive focal term and reduced penalties around centers.
    pos_loss=F.softplus(-x[pos])*(1-p[pos]).square()
    neg_loss=F.softplus(x[~pos])*p[~pos].square()*(1-y[~pos]).pow(4)
    return (pos_loss.sum()+neg_loss.sum())/max(1,int(pos.sum()))


def nonmaximum(coords, scores, affine, *, radius_mm=8., limit=3):
    coords=np.asarray(coords,dtype=int).reshape(-1,3)
    scores=np.asarray(scores,dtype=float)
    a=np.asarray(affine,dtype=float)
    if scores.shape!=(len(coords),) or not np.isfinite(scores).all() or a.shape!=(4,4):
        raise ValueError('Invalid proposal coordinates or scores')
    order=np.lexsort((coords[:,2],coords[:,1],coords[:,0],-scores))
    world=coords@a[:3,:3].T
    keep=[]
    for i in order:
        if not keep or np.min(np.linalg.norm(world[keep]-world[i],axis=1))>=radius_mm:
            keep.append(int(i))
        if len(keep)==limit:break
    return [(coords[i].tolist(),float(scores[i])) for i in keep]
