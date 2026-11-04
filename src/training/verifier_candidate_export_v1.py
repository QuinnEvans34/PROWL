"""Additive probability export, preserving original tiling/blending/argmax."""
import numpy as np
import torch
from src.data.segmenter_native_windows_v1 import tiles, orient
from src.data.segmenter_physical_windows_v1 import physical_geometry, sample_window, PhysicalReconstructor

def hard_codes(probabilities):
    if probabilities.ndim != 4 or probabilities.shape[0] != 3 or not np.isfinite(probabilities).all() or probabilities.min()<0 or probabilities.max()>1:
        raise ValueError('Invalid class probabilities')
    codes=np.zeros(probabilities.shape[1:],np.uint8);best=probabilities[0].copy()
    for k in (1,2):
        take=probabilities[k]>best;codes[take]=k;best[take]=probabilities[k][take]
    return codes

def native_embed(local, case):
    shape=tuple(case['parent_geometry']['shape'])
    low,high=case['region_low'],case['region_high']
    if len(low)!=3 or any(l<0 or h<=l or h>n for l,h,n in zip(low,high,shape)) or local.shape!=tuple(h-l for l,h in zip(low,high)):
        raise ValueError('Region bounds mismatch')
    result=np.zeros(shape,local.dtype)
    result[tuple(slice(l,h) for l,h in zip(low,high))]=local
    return orient(result,case['parent_geometry'],inverse=True)

@torch.no_grad()
def predict(session, image, native_geometry, *, progress=lambda completed,total:None):
    if image.shape!=tuple(native_geometry['shape']) or image.dtype!=np.float32 or not np.isfinite(image).all():
        raise ValueError('Invalid CT')
    record=physical_geometry(native_geometry);ts=tiles(record['shape']);recon=PhysicalReconstructor(record)
    session._clean()
    with session.rng_scope():
        session.model.eval()
        for i,origin in enumerate(ts):
            patch,_=sample_window(image,record,origin,order=1)
            logits=session.model(torch.from_numpy(patch[None,None]).to(session.device))
            if not torch.isfinite(logits).all():raise ValueError('Nonfinite prediction')
            recon.add(origin,torch.softmax(logits,dim=1)[0].cpu().numpy());progress(i+1,len(ts))
    probabilities=recon.finish(ts)
    return hard_codes(probabilities), probabilities[2].copy(),dict(tiles=len(ts),
        minimum_blend_weight=float(recon.weight.min()),gap_voxels=int((recon.weight==0).sum()),spacing_mm=record['spacing_mm'])
