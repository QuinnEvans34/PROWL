"""Opt-in candidate only: reference-free distance filtering, never auto-enabled."""
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree


def filter_prediction(prediction, affine, *, maximum_distance_mm=10.):
    affine=np.asarray(affine,dtype=float)
    if prediction.dtype!=np.uint8 or prediction.ndim!=3 or not np.isin(prediction,[0,1,2]).all():
        raise ValueError('Native uint8 three-class prediction required')
    if affine.shape!=(4,4) or not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3,:3]))<=0:
        raise ValueError('Finite nonsingular affine required')
    if not np.isfinite(maximum_distance_mm) or maximum_distance_mm<0:
        raise ValueError('Nonnegative finite world distance required')
    result=prediction.copy();pancreas=np.argwhere(prediction==1);guess=prediction==2
    if not len(pancreas) or not guess.any():
        return result,dict(removed_components=[],context_available=bool(len(pancreas)))
    labels,count=ndimage.label(guess,structure=np.ones((3,3,3)))
    def world(x):return x@affine[:3,:3].T+affine[:3,3]
    distances=cKDTree(world(pancreas)).query(world(np.argwhere(guess)),workers=1)[0]
    minima=np.full(count+1,np.inf);np.minimum.at(minima,labels[guess],distances)
    remove=minima>maximum_distance_mm;remove[0]=False
    result[remove[labels]]=0
    return result,dict(removed_components=np.flatnonzero(remove).tolist(),context_available=True,
                      maximum_distance_mm=float(maximum_distance_mm))
