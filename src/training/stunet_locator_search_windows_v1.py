"""Prediction-only mining and complete-label search windows for locator training."""
from itertools import product
import numpy as np

SIZE=64


def search_grid(points,shape,step=24):
    points=np.asarray(points)
    shape=np.asarray(shape)
    if points.ndim!=2 or points.shape[1]!=3 or not len(points):
        raise ValueError('Nonempty pancreas support required')
    low,high=points.min(0),points.max(0)
    axes=[sorted(set([*range(int(a),int(b)+1,step),int(b)])) for a,b in zip(low,high)]
    return [tuple(int(x) for x in c) for c in product(*axes)
            if np.all(np.asarray(c)>=0) and np.all(np.asarray(c)<shape)]


def complete_components(patch,sizes):
    """None denotes a clipped lesion; an empty tuple is an actual negative."""
    present,counts=np.unique(patch[patch!=0],return_counts=True)
    if any(i>=len(sizes) or n!=sizes[i] for i,n in zip(present,counts)):
        return None
    return tuple(int(i) for i in present)


def offcenter_order(grid,box,rng):
    """Use existing search-grid windows, not a box supplied at inference."""
    lo,hi=(np.array([getattr(s,name) for s in box]) for name in ('start','stop'))
    middle=(lo+hi-1)//2
    eligible=[c for c in grid if np.all(np.asarray(c)-SIZE//2<=lo)
              and np.all(np.asarray(c)+SIZE//2>=hi)
              and np.max(np.abs(np.asarray(c)-middle))>=10]
    return [eligible[i] for i in rng.permutation(len(eligible))]


def extent_window_count(roi_windows):
    return sum(int(np.prod(hi-lo)) for lo,hi in roi_windows)
