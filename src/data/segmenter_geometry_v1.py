"""Shared physical ROI mapper, independent of paths/models and lesion box selection.

XYZ arrays; integer indices name voxel centers. Boxes are half-open native RAS
index bounds; their physical edges are lo-.5/hi-.5. Only signed-permutation
axis-aligned affines are supported in v1. No hidden oblique approximation.
"""
from copy import deepcopy
import math
import nibabel as nib
import numpy as np
from scipy import ndimage
from src.data.source_inventory_records import content_hash,require

RAS=nib.orientations.axcodes2ornt(('R','A','S'))
MAX_SOURCE=46_219_264


def recipe(*,tensor_shape=(144,144,144),sampling_mm=1.,margin_mm=10.):
    return dict(schema_version='1.0.0',component='segmenter-geometry-v1',
        tensor_shape=list(tensor_shape),sampling_mm=float(sampling_mm),margin_mm=float(margin_mm),
        hu_window=[-100.,250.],max_source_voxels=MAX_SOURCE,max_sampling_voxels=16_000_000,
        max_tensor_voxels=8_000_000,orientation='RAS',roi_selection='pancreas_only_all_support',
        jitter='none_diagnostic',image_interpolation='linear',target_interpolation='nearest',
        edge_mode='grid-constant',padding='symmetric_zero',rounding='ceil_cover',
        affine_support='signed_permutation_axis_aligned',affine_tolerance_mm=1e-8,
        outside_roi_probability=[1.,0.,0.])


def validate_recipe(r):
    fixed=recipe();variable={'tensor_shape','sampling_mm','margin_mm'}
    require(set(r)==set(fixed) and all(r[k]==v for k,v in fixed.items() if k not in variable),'Unsupported geometry recipe')
    require(len(r['tensor_shape'])==3 and all(type(n)==int and 0<n<=192 for n in r['tensor_shape']) and
        math.prod(r['tensor_shape'])<=r['max_tensor_voxels'],'Tensor shape envelope')
    require(type(r['sampling_mm']) in (float,int) and math.isfinite(r['sampling_mm']) and .5<=r['sampling_mm']<=4.,'Sampling spacing envelope')
    require(type(r['margin_mm']) in (float,int) and math.isfinite(r['margin_mm']) and 0<=r['margin_mm']<=50,'Margin envelope')


def canonical_geometry(shape,affine,r):
    validate_recipe(r);a=np.asarray(affine,dtype=np.float64)
    require(len(shape)==3 and all(type(n)==int and n>0 for n in shape) and math.prod(shape)<=r['max_source_voxels'],'Source shape envelope')
    require(a.shape==(4,4) and np.isfinite(a).all() and np.array_equal(a[3],[0,0,0,1]) and
        abs(np.linalg.det(a[:3,:3]))>1e-12,'Invalid physical affine')
    orientation=nib.orientations.io_orientation(a)
    forward=nib.orientations.ornt_transform(orientation,RAS)
    inverse=nib.orientations.ornt_transform(RAS,orientation)
    ca=a@nib.orientations.inv_ornt_aff(forward,shape)
    spacing=np.diag(ca)[:3];off=ca[:3,:3]-np.diag(spacing)
    require(np.all(spacing>0) and np.max(np.abs(off))<=r['affine_tolerance_mm'],'Unsupported oblique/sheared physical grid')
    return a,ca,np.asarray(shape)[np.argsort(forward[:,0])].astype(int),forward,inverse,spacing


def select_pancreas_box(pancreas,affine,r):
    p=np.asarray(pancreas);_,ca,shape,f,_,spacing=canonical_geometry(list(p.shape),affine,r)
    require(np.isin(p,[0,1]).all() and p.any(),'Nonempty binary pancreas localization required')
    p=nib.orientations.apply_orientation(p,f);bounds=[]
    for axis in range(3):
        indices=np.flatnonzero(p.any(axis=tuple(a for a in range(3) if a!=axis)))
        bounds.append([int(indices[0]),int(indices[-1])+1])
    lo=np.array([b[0] for b in bounds]);hi=np.array([b[1] for b in bounds]);pad=np.ceil(r['margin_mm']/spacing).astype(int)
    box=[np.maximum(0,lo-pad).tolist(),np.minimum(shape,hi+pad).tolist()]
    return box,dict(pancreas_bounds_ras=bounds,requested_margin_mm=r['margin_mm'],
        realized_margin_mm=[((lo-np.array(box[0]))*spacing).tolist(),((np.array(box[1])-hi)*spacing).tolist()],
        source_face_contact=[(np.array(box[0])==0).tolist(),(np.array(box[1])==shape).tolist()])


def plan_geometry(shape,affine,box,r,*,source_identity,roi_origin):
    a,ca,cs,f,inv,spacing=canonical_geometry(shape,affine,r)
    require(roi_origin in ('provided_pancreas_reference','predicted_region'),'Explicit ROI origin required')
    require(isinstance(source_identity,dict) and set(source_identity)=={'study_id','ct_sha256'} and
        isinstance(source_identity['study_id'],str) and bool(source_identity['study_id']) and
        isinstance(source_identity['ct_sha256'],str) and len(source_identity['ct_sha256'])==64 and
        all(c in '0123456789abcdef' for c in source_identity['ct_sha256']),'Source identity required')
    require(isinstance(box,list) and len(box)==2 and all(isinstance(b,list) and len(b)==3 and
        all(type(n)==int for n in b) for b in box),'Half-open integer RAS box required')
    lo,hi=np.asarray(box);require(np.all(lo>=0) and np.all(hi<=cs) and np.all(hi>lo),'Empty/unsafe localization box')
    crop_affine=ca.copy();crop_affine[:3,3]=(ca@np.r_[lo,1])[:3]
    edge=(ca@np.r_[lo-.5,1])[:3];extent=(hi-lo)*spacing;s=float(r['sampling_mm'])
    sampled=np.ceil(extent/s-1e-10).astype(int)
    require(np.all(sampled>0) and math.prod(sampled)<=r['max_sampling_voxels'],'Physical sampling grid envelope')
    scale=float(np.min(np.asarray(r['tensor_shape'])/sampled));step=s/scale
    normalized=np.ceil(sampled*scale-1e-10).astype(int)
    require(np.all(normalized>0) and np.all(normalized<=r['tensor_shape']),'Letterbox envelope')
    pad_lo=(np.asarray(r['tensor_shape'])-normalized)//2;pad_hi=np.asarray(r['tensor_shape'])-normalized-pad_lo
    def grid(step,origin):
        result=np.diag([step,step,step,1.]);result[:3,3]=origin;return result.tolist()
    record=dict(schema_version='1.0.0',component='segmenter-transform-v1',recipe=deepcopy(r),recipe_sha256=content_hash(r),
        source_identity=deepcopy(source_identity),roi_origin=roi_origin,source_shape=shape,source_affine=a.tolist(),
        orientation_forward=f.tolist(),orientation_inverse=inv.tolist(),canonical_shape=cs.tolist(),canonical_affine=ca.tolist(),
        box_ras_half_open=deepcopy(box),roi_native_shape=(hi-lo).tolist(),roi_native_affine=crop_affine.tolist(),
        roi_world_low_edge_mm=edge.tolist(),roi_physical_extent_mm=extent.tolist(),scan_fraction=float(math.prod(hi-lo)/math.prod(cs)),
        sampling_shape=sampled.tolist(),sampling_affine=grid(s,edge+s/2),sampling_extent_mm=(sampled*s).tolist(),
        uniform_scale=scale,normalized_shape=normalized.tolist(),normalized_affine=grid(step,edge+step/2),
        pad_low=pad_lo.tolist(),pad_high=pad_hi.tolist(),tensor_shape=deepcopy(r['tensor_shape']),
        tensor_affine=grid(step,edge+step/2-pad_lo*step),effective_spacing_mm=[step]*3,
        normalized_extent_mm=(normalized*step).tolist(),
        operations=['orientation_RAS','pancreas_only_roi','physical_isotropic_sampling','uniform_letterbox','symmetric_pad'],
        probability_inverse=['remove_pad','inverse_uniform_scale','roi_native_grid','embed_background','inverse_orientation'],
        coordinate_convention='integer_voxel_centers_half_open_index_boxes_physical_edges_minus_half',
        probability_sum_tolerance=1e-4)
    record['record_sha256']=content_hash(record);return record


def validate_record(record,trusted_record_sha256):
    require(content_hash(record)==trusted_record_sha256,'Independent transform pin differs')
    expected=plan_geometry(record['source_shape'],record['source_affine'],record['box_ras_half_open'],record['recipe'],
        source_identity=record['source_identity'],roi_origin=record['roi_origin'])
    require(record==expected,'Transform fields disagree with physical derivation')


def _sample(array,src_affine,dst_affine,shape,order,cval=0,tick=lambda:None):
    mapping=np.linalg.inv(np.asarray(src_affine))@np.asarray(dst_affine)
    # Bound work/output coordinates by slabs; scipy evaluates the affine without a dense coordinate mesh.
    result=np.empty(shape,dtype=array.dtype if order==0 else np.float32)
    for start in range(0,shape[2],16):
        tick();stop=min(shape[2],start+16);offset=mapping[:3,3]+mapping[:3,2]*start
        ndimage.affine_transform(array,mapping[:3,:3],offset=offset,output_shape=(shape[0],shape[1],stop-start),
            output=result[:,:,start:stop],order=order,mode='grid-constant',cval=cval,prefilter=False)
    return result


def _crop(array,record):
    oriented=nib.orientations.apply_orientation(array,np.asarray(record['orientation_forward']))
    lo,hi=record['box_ras_half_open'];return oriented[tuple(slice(l,h) for l,h in zip(lo,hi))]


def forward_field(array,record,*,order,tick=lambda:None):
    require(array.shape==tuple(record['source_shape']) and np.isfinite(array).all(),'Forward source grid/value mismatch')
    crop=_crop(array,record)
    sampled=_sample(crop,record['roi_native_affine'],record['sampling_affine'],record['sampling_shape'],order,tick=tick)
    mapped=_sample(sampled,record['sampling_affine'],record['normalized_affine'],record['normalized_shape'],order,tick=tick)
    return np.pad(mapped,list(zip(record['pad_low'],record['pad_high'])),constant_values=0)


def prepare_image(image,record,*,trusted_record_sha256,tick=lambda:None):
    validate_record(record,trusted_record_sha256)
    require(np.asarray(image).dtype.kind in 'fiu' and np.isfinite(image).all(),'Finite CT required')
    low,high=record['recipe']['hu_window'];scaled=np.clip((np.asarray(image,dtype=np.float32)-low)/(high-low),0,1)
    return forward_field(scaled,record,order=1,tick=tick)


def _restore_one(field,record,*,order,cval,tick):
    require(field.shape==tuple(record['tensor_shape']),'Restoration tensor shape mismatch')
    lo=record['pad_low'];shape=record['normalized_shape']
    field=field[tuple(slice(l,l+n) for l,n in zip(lo,shape))]
    sampled=_sample(field,record['normalized_affine'],record['sampling_affine'],record['sampling_shape'],order,cval,tick)
    crop=_sample(sampled,record['sampling_affine'],record['roi_native_affine'],record['roi_native_shape'],order,cval,tick)
    canonical=np.full(record['canonical_shape'],cval,dtype=crop.dtype);low,high=record['box_ras_half_open']
    canonical[tuple(slice(l,h) for l,h in zip(low,high))]=crop
    return nib.orientations.apply_orientation(canonical,np.asarray(record['orientation_inverse']))


def restore_codes(codes,record,*,trusted_record_sha256,tick=lambda:None):
    validate_record(record,trusted_record_sha256)
    require(np.issubdtype(codes.dtype,np.integer) and np.all((codes>=0)&(codes<=4096)),'Integer reference/component codes required')
    return _restore_one(codes,record,order=0,cval=0,tick=tick)


def restore_probabilities(probabilities,record,*,trusted_record_sha256,tick=lambda:None):
    validate_record(record,trusted_record_sha256);p=np.asarray(probabilities)
    require(p.shape==(3,*record['tensor_shape']) and np.isfinite(p).all() and np.all((p>=0)&(p<=1)) and
        np.allclose(p.sum(axis=0),1,rtol=0,atol=record['probability_sum_tolerance']),'Three finite normalized probabilities required')
    result=np.empty((3,*record['source_shape']),np.float32)
    for c in range(3):result[c]=_restore_one(p[c],record,order=1,cval=1 if c==0 else 0,tick=tick)
    require(np.isfinite(result).all() and np.allclose(result.sum(axis=0),1,rtol=0,atol=1e-4),'Invalid restored probabilities')
    return result


def preprocess(image,pancreas,lesion,affine,r,*,source_identity,lesion_target_state,tick=lambda:None):
    require(lesion_target_state in ('positive','verified_negative'),'Unknown/held target cannot be preprocessed')
    p=np.asarray(pancreas);l=np.asarray(lesion)
    require(p.shape==l.shape==image.shape and np.isin(p,[0,1]).all() and np.isin(l,[0,1]).all(),'Matched binary source targets required')
    require(bool(l.any())==(lesion_target_state=='positive'),'Target semantics disagree with native reference')
    box,margin=select_pancreas_box(p,affine,r)
    record=plan_geometry(list(image.shape),affine,box,r,source_identity=source_identity,roi_origin='provided_pancreas_reference')
    identity=content_hash(record);input_image=prepare_image(image,record,trusted_record_sha256=identity,tick=tick)
    native=np.where(l==1,2,p).astype(np.uint8);target=forward_field(native,record,order=0,tick=tick)
    restored=restore_codes(target,record,trusted_record_sha256=identity,tick=tick)
    labels,count=ndimage.label(l,structure=np.ones((3,3,3),np.uint8));require(count<=4096,'All component records exceed envelope; no truncation')
    normalized_ids=forward_field(labels,record,order=0,tick=tick)
    restored_ids=restore_codes(normalized_ids,record,trusted_record_sha256=identity,tick=tick)
    totals=np.bincount(labels.ravel(),minlength=count+1);inside=np.bincount(_crop(labels,record).ravel(),minlength=count+1)
    normalized_counts=np.bincount(normalized_ids.ravel(),minlength=count+1);roundtrip=np.bincount(restored_ids.ravel(),minlength=count+1)
    truepositives=np.bincount(labels[restored_ids==labels],minlength=count+1)
    components=[dict(component_id=i,native_voxels=int(totals[i]),inside_roi_voxels=int(inside[i]),
        tensor_voxels=int(normalized_counts[i]),restored_voxels=int(roundtrip[i]),
        roundtrip_true_positive=int(truepositives[i]),roundtrip_recall=float(truepositives[i]/totals[i])) for i in range(1,count+1)]
    metrics={}
    for name,original,back in [('pancreas_parenchyma',native==1,restored==1),('pancreas_lesion_union',native>0,restored>0),('lesion',native==2,restored==2)]:
        n=int(original.sum());b=int(back.sum());tp=int((original&back).sum())
        metrics[name]=dict(native_voxels=n,inside_roi_voxels=int(_crop(original,record).sum()),
            tensor_voxels=int((target==2).sum() if name=='lesion' else (target==1).sum() if name=='pancreas_parenchyma' else (target>0).sum()),
            restored_voxels=b,true_positive=tp,recall=tp/n if n else None,dice=2*tp/(n+b) if n else None)
    failed=[c['component_id'] for c in components if not c['tensor_voxels'] or not c['roundtrip_true_positive']]
    fidelity=dict(lesion_target_state=lesion_target_state,source_component_count=count,components=components,
        lost_or_displaced_component_ids=failed,all_components_survive=not failed,metrics=metrics,margin=margin,
        outside_pancreas_voxels=int(np.count_nonzero(l & (p==0))),source_arrays_changed=False,
        tensor_positive=bool((target==2).any()),mechanical_survival_pass=not failed and bool((target>0).any()),
        recipe_accepted=False,
        scope='provided_pancreas_roi_reference_fidelity_no_model_or_performance_claim')
    return dict(image=input_image,target=target,reference_roundtrip=restored,transform=record,
        transform_sha256=identity,fidelity=fidelity)
