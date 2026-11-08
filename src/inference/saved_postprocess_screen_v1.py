"""Finite opt-in saved-mask policies. No reference, model or training inputs."""
import numpy as np
from scipy import ndimage
from src.inference.lesion_confidence_screen_v2 import decode

POLICIES=('raw','near5','near10','near20','near10_conf04','near10_conf05',
          'near10_conf06','near10_fill100mm3','near10_close1mm')


def physical_ball(affine,radius=1.):
    a=np.asarray(affine,dtype=float)[:3,:3]
    singular=np.linalg.svd(a,compute_uv=False)
    if not np.isfinite(a).all() or singular[-1]<=0 or not 0<radius<=1:
        raise ValueError('Finite nonsingular physical geometry required')
    extent=int(np.ceil(radius/singular[-1]))
    if extent>12:raise ValueError('Structuring element exceeds frozen engineering bound')
    coords=np.stack(np.meshgrid(*([np.arange(-extent,extent+1)]*3),indexing='ij'),-1)
    return np.linalg.norm(coords@a.T,axis=-1)<=radius+1e-12


def recover(prediction,affine,*,kind):
    if prediction.dtype!=np.uint8 or prediction.ndim!=3 or not np.isin(prediction,[0,1,2]).all():
        raise ValueError('Native three-class prediction required')
    a=np.asarray(affine,dtype=float)
    if a.shape!=(4,4) or not np.isfinite(a).all() or abs(np.linalg.det(a[:3,:3]))<=0:
        raise ValueError('Invalid affine')
    if kind not in ('holes','closing'):raise ValueError('Unsupported recovery policy')
    out=prediction.copy();coords=np.argwhere(prediction==2)
    if not len(coords):return out
    footprint=physical_ball(a) if kind=='closing' else ndimage.generate_binary_structure(3,1)
    pad=max(footprint.shape)//2+1
    low=np.maximum(coords.min(0)-pad,0);high=np.minimum(coords.max(0)+pad+1,prediction.shape)
    slices=tuple(slice(int(l),int(h)) for l,h in zip(low,high));local=prediction[slices];fg=local==2
    if kind=='closing':
        additions=ndimage.binary_closing(fg,structure=footprint)&~fg&(local==0)
    else:
        holes=ndimage.binary_fill_holes(fg,structure=ndimage.generate_binary_structure(3,1))&~fg
        labels,count=ndimage.label(holes,structure=ndimage.generate_binary_structure(3,1))
        size=np.bincount(labels.ravel(),minlength=count+1)
        pancreas=np.bincount(labels[local==1],minlength=count+1)>0
        fill=(size*abs(np.linalg.det(a[:3,:3]))<=100.)&~pancreas;fill[0]=False
        additions=fill[labels]&(local==0)
    view=out[slices];view[additions]=2
    return out


def predictions(code,affine,components):
    raw=decode(code,0.);labels,count=ndimage.label(raw==2,structure=np.ones((3,3,3)))
    if count!=len(components) or {r['component_id'] for r in components}!=set(range(1,count+1)):
        raise ValueError('Component identity drift')
    yield 'raw',raw
    incumbent=None
    for radius in (5,10,20):
        retained=np.ones(count+1,dtype=bool)
        for c in components:
            d=c['min_predicted_pancreas_center_distance_mm']
            retained[c['component_id']]=d is None or d<=radius
        retained[0]=True;out=raw.copy();out[~retained[labels]]=0
        if radius==10:incumbent=out
        yield 'near'+str(radius),out
    near=incumbent==2
    for threshold,suffix in ((.4,'04'),(.5,'05'),(.6,'06')):
        out=incumbent.copy();suppressed=decode(code,threshold);out[near]=suppressed[near]
        yield 'near10_conf'+suffix,out
    yield 'near10_fill100mm3',recover(incumbent,affine,kind='holes')
    yield 'near10_close1mm',recover(incumbent,affine,kind='closing')
