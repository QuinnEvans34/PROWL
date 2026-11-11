"""Native-grid crops and a compact 3D refiner for a known-location pilot."""
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


def crop_record(shape, affine, center, size):
    shape, center = np.asarray(shape, dtype=int), np.asarray(center, dtype=int)
    a = np.asarray(affine, dtype=float)
    if (shape.shape != (3,) or center.shape != (3,) or np.any(shape < 1)
            or np.any(center < 0) or np.any(center >= shape) or not 4 <= size <= 128
            or size % 4 or a.shape != (4,4) or not np.isfinite(a).all()
            or abs(np.linalg.det(a[:3,:3])) < 1e-10):
        raise ValueError('Invalid native crop geometry')
    origin = center-size//2
    low, high = np.maximum(origin,0), np.minimum(origin+size,shape)
    patch = a.copy()
    patch[:3,3] = a[:3,:3]@origin+a[:3,3]
    return dict(size=int(size),source_shape=shape.tolist(),origin=origin.tolist(),
        source_low=low.tolist(),source_high=high.tolist(),dest_low=(low-origin).tolist(),
        dest_high=(high-origin).tolist(),patch_affine=patch.tolist())


def slices(low, high):
    return tuple(slice(l,h) for l,h in zip(low,high))


def crop(array, record, *, padding=0):
    if tuple(record['source_shape']) != array.shape:
        raise ValueError('Source shape differs from crop binding')
    out = np.full((record['size'],)*3,padding,dtype=array.dtype)
    out[slices(record['dest_low'],record['dest_high'])] = array[slices(record['source_low'],record['source_high'])]
    return out


def restore(array, record):
    if array.shape != (record['size'],)*3:
        raise ValueError('Patch shape differs from crop binding')
    out = np.zeros(record['source_shape'],dtype=array.dtype)
    out[slices(record['source_low'],record['source_high'])] = array[slices(record['dest_low'],record['dest_high'])]
    return out


def valid_support(record):
    mask = np.zeros((record['size'],)*3,dtype=bool)
    mask[slices(record['dest_low'],record['dest_high'])] = True
    return mask


def channels(image, support):
    """Fixed CT scaling plus the location hint; never use labels as inputs."""
    size = image.shape[0]
    a = (np.arange(size,dtype=np.float32)-size//2)/(size/5)
    h = np.exp(-.5*(a[:,None,None]**2+a[None,:,None]**2+a[None,None,:]**2))
    return np.stack([np.where(support,np.clip((image+100.)/350.,0.,1.),0.),
                     np.where(support,h,0.)]).astype(np.float32)


def block(a,b):
    return nn.Sequential(nn.Conv3d(a,b,3,padding=1),nn.GroupNorm(2,b),nn.SiLU(),
                         nn.Conv3d(b,b,3,padding=1),nn.GroupNorm(2,b),nn.SiLU())


class Refiner(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc1,self.enc2,self.center=block(2,8),block(8,16),block(16,24)
        self.dec2,self.dec1=block(40,16),block(24,8)
        self.head=nn.Conv3d(8,1,1)

    def forward(self,x):
        a=self.enc1(x)
        b=self.enc2(F.max_pool3d(a,2))
        c=self.center(F.max_pool3d(b,2))
        d=self.dec2(torch.cat((b,F.interpolate(c,size=b.shape[2:],mode='nearest')),1))
        e=self.dec1(torch.cat((a,F.interpolate(d,size=a.shape[2:],mode='nearest')),1))
        return self.head(e)


def objective(logits, target, support):
    if logits.shape != target.shape or support.shape != target.shape:
        raise ValueError('Loss shape mismatch')
    use=support.bool()
    x,y=logits[use],target[use]
    if not x.numel():
        raise ValueError('Empty crop support')
    # Keep the negative term active. Weight foreground errors without
    # manufacturing any foreground on negative training patches.
    ce=F.binary_cross_entropy_with_logits(x,y,weight=torch.where(y>0,4.,1.))
    if not y.any():
        return ce
    p=x.sigmoid()
    return ce+1-(2*(p*y).sum()+1e-5)/(p.sum()+y.sum()+1e-5)
