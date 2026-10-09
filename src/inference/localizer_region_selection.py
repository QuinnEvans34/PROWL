"""Explicit, reference-free candidate policies for a native binary localizer mask."""
from hashlib import sha256
import numpy as np
from scipy import ndimage


def select_region(mask, policy='all_support'):
    a=np.asarray(mask)
    if policy not in ('all_support','largest_component_26'):
        raise ValueError('Unknown localizer region policy')
    if a.ndim!=3 or a.size>96_000_000 or not np.isin(a,[0,1]).all():
        raise ValueError('Native binary localizer mask required')
    a=a.astype(np.uint8,copy=False);total=int(a.sum())
    trace=dict(policy=policy,input_mask_sha256=sha256(a.tobytes()).hexdigest(),input_voxels=total)
    if policy=='all_support':
        selected=a.copy()
    else:
        labels,count=ndimage.label(a,structure=np.ones((3,3,3),np.uint8))
        sizes=np.bincount(labels.ravel(),minlength=count+1)
        winner=int(np.argmax(sizes[1:]))+1 if count else 0
        selected=(labels==winner).astype(np.uint8) if winner else np.zeros_like(a)
        trace.update(connectivity=26,component_count=count,selected_component=winner,
                     tie_rule='first component in native C-order labeling')
    trace.update(selected_voxels=int(selected.sum()),selected_mask_sha256=sha256(selected.tobytes()).hexdigest())
    return selected,trace
