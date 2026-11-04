"""Fit margins from generator patients only; apply without lesion information."""
import numpy as np


def apply_margin(native_box, source_shape, affine, margins):
    box=np.asarray(native_box,dtype=float);shape=np.asarray(source_shape)
    a=np.asarray(affine,dtype=float);m=np.asarray(margins,dtype=float)
    if box.shape!=(2,3) or shape.shape!=(3,) or a.shape!=(4,4) or m.shape!=(3,):
        raise ValueError('Geometry shape')
    if not np.isfinite(a).all() or not np.isfinite(box).all() or not np.isfinite(m).all() or (m<0).any():
        raise ValueError('Nonfinite geometry or negative margin')
    if (box!=np.rint(box)).any() or (shape<1).any() or (box[0]<0).any() or (box[1]>shape).any() or (box[1]<=box[0]).any():
        raise ValueError('Invalid half-open box')
    plane=1/np.linalg.norm(np.linalg.inv(a[:3,:3]),axis=1)
    pad=np.ceil(m/plane).astype(int)
    return np.maximum(0,box[0].astype(int)-pad),np.minimum(shape,box[1].astype(int)+pad)


def fit_margin(records, allowed):
    allowed=set(allowed)
    if not allowed or set(records)!=allowed:raise ValueError('Exact generator membership required')
    maximum=np.zeros(3)
    for name in sorted(allowed):
        r=records[name];box=np.asarray(r['native_box']);a=np.asarray(r['affine'])
        apply_margin(box,r['shape'],a,[0,0,0])
        lesion=r['lesion_box']
        if lesion is None:continue
        lesion=np.asarray(lesion)
        if lesion.shape!=(2,3) or (lesion[0]<0).any() or (lesion[1]>r['shape']).any() or (lesion[1]<=lesion[0]).any():
            raise ValueError('Invalid lesion box')
        plane=1/np.linalg.norm(np.linalg.inv(a[:3,:3]),axis=1)
        needed=np.maximum.reduce([box[0]-lesion[0],lesion[1]-box[1],np.zeros(3)])*plane
        maximum=np.maximum(maximum,needed)
    return (np.ceil(maximum)+1).tolist()


def contains(box, lesion):
    if lesion is None:return True
    return bool(np.all(np.asarray(box[0])<=lesion[0]) and np.all(np.asarray(box[1])>=lesion[1]))
