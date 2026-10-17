"""Full-cohort affine geometry: bounded native volumes, including tilted physical grids.

The pancreas-only native box is mapped to a RAS-aligned physical box. CT and labels use
the same physical transform. Sampling is slabbed; no full-volume coordinate mesh or
three-channel native probability volume is needed during training preparation.
"""
from copy import deepcopy
import itertools
import math

import numpy as np
from scipy import ndimage

from src.data.source_inventory_records import content_hash, require
from src.data.segmenter_geometry_v1 import _sample


def recipe(*, tensor_shape=(144,144,144), sampling_mm=1., margin_mm=10., max_source_voxels=256_000_000, max_sampling_voxels=16_000_000):
    return dict(component='segmenter-geometry-v2', tensor_shape=list(tensor_shape),
        sampling_mm=float(sampling_mm), margin_mm=float(margin_mm), max_source_voxels=max_source_voxels,
        max_sampling_voxels=max_sampling_voxels, hu_window=[-100.,250.], roi_selection='pancreas_only',
        image_interpolation='linear', target_interpolation='nearest', orientation='physical_RAS',
        affine_support='finite_invertible_affine', padding='symmetric_zero')


def validate_recipe(r):
    fixed=recipe();variable={'tensor_shape','sampling_mm','margin_mm','max_source_voxels','max_sampling_voxels'}
    require(set(r)==set(fixed) and all(r[k]==v for k,v in fixed.items() if k not in variable), 'Geometry v2 recipe')
    require(type(r['max_sampling_voxels']) is int and 0<r['max_sampling_voxels']<=64_000_000, 'Sampling volume allocation')
    require(len(r['tensor_shape'])==3 and all(type(v) is int and 0<v<=192 for v in r['tensor_shape']), 'Tensor shape')
    require(type(r['max_source_voxels']) is int and 0<r['max_source_voxels']<=256_000_000, 'Native volume allocation')
    require(all(type(r[k]) in (int,float) and math.isfinite(r[k]) for k in ('sampling_mm','margin_mm'))
        and .5<=r['sampling_mm']<=4 and 0<=r['margin_mm']<=50, 'Physical sampling/margin')


def canonical_geometry(shape, affine, r):
    validate_recipe(r);a=np.asarray(affine,dtype=np.float64)
    require(len(shape)==3 and all(type(v) is int and v>0 for v in shape)
        and math.prod(shape)<=r['max_source_voxels'], 'Source shape envelope')
    require(a.shape==(4,4) and np.isfinite(a).all() and np.array_equal(a[3],[0,0,0,1])
        and abs(np.linalg.det(a[:3,:3]))>1e-12 and np.linalg.cond(a[:3,:3])<1e6,
        'Invalid/ill-conditioned physical affine')
    return a


def select_pancreas_box(pancreas, affine, r):
    a=canonical_geometry(list(pancreas.shape),affine,r)
    require(np.isin(pancreas,[0,1]).all() and pancreas.any(), 'Nonempty binary pancreas required')
    low=[];high=[]
    # Distance between native index planes, including a sheared grid.
    plane_spacing=1/np.linalg.norm(np.linalg.inv(a[:3,:3]),axis=1)
    pad=np.ceil(r['margin_mm']/plane_spacing).astype(int)
    for axis in range(3):
        support=np.flatnonzero(pancreas.any(axis=tuple(k for k in range(3) if k!=axis)))
        low.append(max(0,int(support[0])-int(pad[axis])))
        high.append(min(pancreas.shape[axis],int(support[-1])+1+int(pad[axis])))
    return [low,high]


def plan_geometry(shape, affine, box, r, *, source_identity, roi_origin="provided_pancreas_reference"):
    require(roi_origin in ("provided_pancreas_reference", "predicted_region"), "Unsupported ROI origin")
    a=canonical_geometry(shape,affine,r)
    require(set(source_identity)=={'study_id','ct_sha256'} and isinstance(source_identity['study_id'],str)
        and len(source_identity['ct_sha256'])==64, 'Source identity required')
    lo,hi=np.asarray(box[0]),np.asarray(box[1])
    require(lo.shape==hi.shape==(3,) and lo.dtype.kind in 'iu' and hi.dtype.kind in 'iu'
        and np.all(lo>=0) and np.all(hi<=shape) and np.all(hi>lo), 'Native pancreas box bounds')
    corners=np.array([list(p)+[1.] for p in itertools.product(*zip(lo-.5,hi-.5))])
    world=(a@corners.T).T[:,:3];edge=world.min(0);extent=world.max(0)-edge
    spacing=r['sampling_mm'];sampled=np.ceil(extent/spacing-1e-10).astype(int)
    require(np.all(sampled>0) and math.prod(sampled)<=r['max_sampling_voxels'], 'ROI sampling allocation exceeded')
    scale=float(np.min(np.asarray(r['tensor_shape'])/sampled));step=spacing/scale
    normalized=np.ceil(sampled*scale-1e-10).astype(int)
    pad=(np.asarray(r['tensor_shape'])-normalized)//2
    def grid(sp, origin):
        g=np.diag([sp,sp,sp,1.]);g[:3,3]=origin;return g.tolist()
    crop=a.copy();crop[:3,3]=(a@np.r_[lo,1])[:3]
    return dict(component='segmenter-transform-v2',recipe=deepcopy(r),source_identity=deepcopy(source_identity),
        source_shape=shape,source_affine=a.tolist(),native_box=deepcopy(box),crop_affine=crop.tolist(),
        crop_shape=(hi-lo).tolist(),world_low_edge_mm=edge.tolist(),physical_extent_mm=extent.tolist(),
        sampling_shape=sampled.tolist(),sampling_affine=grid(spacing,edge+spacing/2),
        normalized_shape=normalized.tolist(),normalized_affine=grid(step,edge+step/2),
        tensor_shape=deepcopy(r['tensor_shape']),tensor_affine=grid(step,edge+step/2-pad*step),
        pad_low=pad.tolist(),pad_high=(np.asarray(r['tensor_shape'])-normalized-pad).tolist(),
        effective_spacing_mm=[step]*3,roi_origin=roi_origin)


def validate_record(record, trusted_record_sha256):
    require(content_hash(record)==trusted_record_sha256, 'Changed geometry record')
    require(record==plan_geometry(record['source_shape'],record['source_affine'],record['native_box'],
        record['recipe'],source_identity=record['source_identity'],roi_origin=record['roi_origin']), 'Geometry derivation mismatch')


def forward_field(array, record, *, order, tick=lambda:None):
    require(array.shape==tuple(record['source_shape']) and order in (0,1), 'Forward shape/interpolation')
    lo,hi=record['native_box'];crop=array[tuple(slice(l,h) for l,h in zip(lo,hi))]
    sampled=_sample(crop,record['crop_affine'],record['sampling_affine'],record['sampling_shape'],order,tick=tick)
    mapped=_sample(sampled,record['sampling_affine'],record['normalized_affine'],record['normalized_shape'],order,tick=tick)
    return np.pad(mapped,list(zip(record['pad_low'],record['pad_high'])),constant_values=0)


def prepare_image(image, record, *, trusted_record_sha256, tick=lambda:None):
    """Image-only preparation on an explicitly identified physical transform."""
    validate_record(record, trusted_record_sha256)
    image = np.asarray(image)
    require(image.shape == tuple(record['source_shape']) and image.dtype.kind in 'buif'
            and np.isfinite(image).all(), 'Finite matching source image required')
    low, high = record['recipe']['hu_window']
    scaled = np.clip((image.astype(np.float32)-low)/(high-low), 0, 1)
    return forward_field(scaled, record, order=1, tick=tick)


def restore_codes(codes, record, *, trusted_record_sha256, tick=lambda:None):
    validate_record(record,trusted_record_sha256)
    require(codes.shape==tuple(record['tensor_shape']) and codes.dtype.kind in 'iu', 'Integer tensor codes required')
    lo=record['pad_low'];shape=record['normalized_shape']
    cropped=codes[tuple(slice(l,l+n) for l,n in zip(lo,shape))]
    sampled=_sample(cropped,record['normalized_affine'],record['sampling_affine'],record['sampling_shape'],0,tick=tick)
    native=_sample(sampled,record['sampling_affine'],record['crop_affine'],record['crop_shape'],0,tick=tick)
    result=np.zeros(record['source_shape'],dtype=codes.dtype)
    low,high=record['native_box'];result[tuple(slice(l,h) for l,h in zip(low,high))]=native
    return result


def preprocess(image, pancreas, lesion, affine, r, *, source_identity, lesion_target_state, tick=lambda:None):
    require(lesion_target_state in ('positive','verified_negative','reference_empty'), 'Unknown/held target refused')
    canonical_geometry(list(image.shape),affine,r)
    require(pancreas.shape==lesion.shape==image.shape and np.isfinite(image).all()
        and np.isin(pancreas,[0,1]).all() and np.isin(lesion,[0,1]).all(), 'Invalid matched source arrays')
    require(bool(lesion.any())==(lesion_target_state=='positive'), 'Target semantics mismatch')
    box=select_pancreas_box(pancreas,affine,r)
    record=plan_geometry(list(image.shape),affine,box,r,source_identity=source_identity)
    low,high=r['hu_window'];scaled=np.clip((image.astype(np.float32)-low)/(high-low),0,1)
    x=forward_field(scaled,record,order=1,tick=tick);del scaled
    native=np.where(lesion,2,pancreas).astype(np.uint8)
    target=forward_field(native,record,order=0,tick=tick);del native
    labels,count=ndimage.label(lesion,structure=np.ones((3,3,3),np.uint8));tick()
    require(count<=4096, 'Component inventory exceeds allocation')
    totals=np.bincount(labels.ravel(),minlength=count+1)
    mapped=forward_field(labels,record,order=0,tick=tick)
    present=np.bincount(mapped.ravel(),minlength=count+1)
    components=[dict(component_id=i,native_voxels=int(totals[i]),tensor_voxels=int(present[i])) for i in range(1,count+1)]
    lost=[c['component_id'] for c in components if not c['tensor_voxels']]
    return dict(image=x,target=target,transform=record,transform_sha256=content_hash(record),
        fidelity=dict(lesion_target_state=lesion_target_state,components=components,
            lost_component_ids=lost,mechanical_survival_pass=not lost and bool((target>0).any()),
            scope='forward_component_survival_not_native_roundtrip_or_quality_acceptance'))
