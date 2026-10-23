"""Provided-pancreas regions; lesion masks never select region boundaries."""
from copy import deepcopy
from itertools import product
import numpy as np
import nibabel as nib
from src.data.segmenter_geometry_v2 import select_pancreas_box, recipe
from src.data.segmenter_native_windows_v1 import geometry, orient, tiles
from src.data.segmenter_physical_windows_v1 import physical_geometry, coverage_bank, sample_window
from src.data.segmenter_native_inputs_v1 import NativeInputs
from src.data.manifest_records import canonical, digest

# Rounded-up training-only maximum extension beyond the original 10mm box,
# plus 1mm safety. Source-index plane distances, not assumed world-axis lengths.
POLICY = dict(version='provided-pancreas-region-1', extra_margin_mm=[81.,43.,71.],
    base_margin_mm=10., window=144, stride=72, spacing='physical-detail-windows-1',
    sampling='three_focused_one_context_global_updates', inference='provided_pancreas_only',
    focused='round_robin_union_pancreas_lesion_cover_bank', context='uniform_region')


def source_box(pancreas, affine):
    lo,hi=np.asarray(select_pancreas_box(pancreas,affine,recipe()))
    plane=1/np.linalg.norm(np.linalg.inv(np.asarray(affine)[:3,:3]),axis=1)
    pad=np.ceil(np.asarray(POLICY['extra_margin_mm'])/plane).astype(int)
    return np.maximum(0,lo-pad),np.minimum(pancreas.shape,hi+pad)


def oriented_box(pancreas, native):
    lo,hi=source_box(pancreas,np.asarray(native['source_affine']))
    inverse=nib.orientations.inv_ornt_aff(np.asarray(native['forward']),pancreas.shape)
    points=np.asarray([list(p)+[1] for p in product(*zip(lo,hi-1))])
    points=(np.linalg.inv(inverse)@points.T).T[:,:3]
    if not np.allclose(points,np.rint(points)):raise ValueError('Nonintegral orientation')
    points=np.rint(points).astype(int)
    return points.min(0),points.max(0)+1


def crop_case(case):
    # This function must remain independent of lesion contents for its box.
    low,high=oriented_box(case['original_pancreas'],case['geometry'])
    slices=tuple(slice(int(l),int(h)) for l,h in zip(low,high))
    affine=np.asarray(case['geometry']['affine']).copy()
    affine[:3,3]=(affine@[*low,1])[:3]
    native=geometry((high-low).tolist(),affine)
    # The parent is already closest-RAS; the local orientation must be identity.
    if native['forward']!=[[0.,1.],[1.,1.],[2.,1.]]:raise ValueError('Unexpected local orientation')
    result=dict(case,geometry=native,target=np.ascontiguousarray(case['target'][slices]),
        region_low=low.tolist(),region_high=high.tolist(),parent_geometry=case['geometry'])
    if 'image' in case:result['image']=np.ascontiguousarray(case['image'][slices])
    return result


def bank(case):
    record=physical_geometry(case['geometry'])
    return record,coverage_bank(case['target']>0,record)


def window_origin(record,cover,*,step,focused_visit,seed,name):
    if step<0 or focused_visit<0:raise ValueError('Invalid schedule')
    if step%4!=3:return tuple(cover[focused_visit%len(cover)]),'focused_cover'
    key=digest(canonical(dict(seed=seed,step=step,name=name,policy=POLICY['version'])))
    rng=np.random.Generator(np.random.PCG64(int(key[:16],16)))
    return tuple(int(rng.integers(max(0,n-144)+1)) for n in record['shape']),'region_context'


class RegionInputs(NativeInputs):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.control=deepcopy(self.control)
        self.control.update(version=POLICY['version'],region_policy=deepcopy(POLICY))
        self.pin=digest(canonical(self.control))

    def load(self,name,*,role,operation='audit'):
        return crop_case(super().load(name,role=role,operation=operation))

    def training_window(self,name,*,step,focused_visit,seed):
        case=self.load(name,role='train',operation='optimizer')
        record,cover=bank(case)
        origin,kind=window_origin(record,cover,step=step,focused_visit=focused_visit,seed=seed,name=name)
        image,transform=sample_window(case['image'],record,origin,order=1)
        target,_=sample_window(case['target'],record,origin,order=0)
        return image[None],target,transform,dict(kind=kind,origin=list(origin),focused_visit=focused_visit,
            coverage_windows=len(cover),region_low=case['region_low'],region_high=case['region_high'])
