"""Dedicated, deterministic single-channel pancreas preprocessing and grid restoration.

No paths, cohort bypass, lesion masks, supplied ROI or target-derived input crop.
Training and inference share the exact image transform. Source arrays remain untouched.
"""
from copy import deepcopy
import math
import numpy as np
import torch
from monai.data import MetaTensor
from monai.data.utils import zoom_affine,compute_shape_offset
from monai.transforms import Compose,Orientationd,Spacingd,ScaleIntensityRanged,SpatialPadd,SpatialResample
from src.data.source_inventory_records import require,content_hash


def validate_recipe(recipe):
    fixed=dict(schema_version='1.0.0',component='pancreas-localizer-preprocessing-v1',orientation='RAS',
        image_interpolation='bilinear',target_interpolation='nearest',padding_mode='constant_zero',
        crop='none',augmentation='none',cache='none',workers=0)
    require(set(recipe)==set(fixed)|{'spacing_mm','hu_window','minimum_shape','max_output_voxels'},'Unknown recipe field')
    require(all(recipe[k]==v for k,v in fixed.items()),'Unsupported preprocessing policy')
    require(len(recipe['spacing_mm'])==3 and all(np.isfinite(v) and v>0 for v in recipe['spacing_mm']), 'Invalid spacing')
    require(len(recipe['hu_window'])==2 and all(np.isfinite(v) for v in recipe['hu_window']) and
            recipe['hu_window'][0]<recipe['hu_window'][1], 'Invalid HU window')
    require(len(recipe['minimum_shape'])==3 and all(type(v)==int and v>0 for v in recipe['minimum_shape']), 'Invalid padding shape')
    require(type(recipe['max_output_voxels'])==int and 0<recipe['max_output_voxels']<=8_000_000,'Output voxel cap')


def geometry(affine,shape):
    a=np.asarray(affine,dtype=np.float64)
    require(a.shape==(4,4) and np.isfinite(a).all() and np.array_equal(a[3],[0,0,0,1]) and
            abs(np.linalg.det(a[:3,:3]))>1e-12,'Invalid physical affine')
    require(len(shape)==3 and all(int(v)>0 for v in shape),'Nonempty 3D grid required')
    return a


def preprocess(image,affine,recipe,*,target=None):
    validate_recipe(recipe);image=np.asarray(image);a=geometry(affine,image.shape)
    require(image.dtype.kind in 'fiu' and np.isfinite(image).all(),'Finite CT required')
    require(image.size<=20_000_000,'Source voxel cap')
    data={'image':MetaTensor(torch.from_numpy(np.array(image,dtype=np.float32,copy=True))[None],affine=a)}
    keys=['image'];modes=['bilinear']
    if target is not None:
        target=np.asarray(target)
        require(target.shape==image.shape and np.isin(target,[0,1]).all(),'Exact binary same-grid pancreas target required')
        data['label']=MetaTensor(torch.from_numpy(np.array(target,dtype=np.float32,copy=True))[None],affine=a)
        keys.append('label');modes.append('nearest')
    data=Orientationd(keys=keys,axcodes='RAS',labels=(('L','R'),('P','A'),('I','S')))(data)
    oriented=data['image'];new_affine=zoom_affine(oriented.affine.numpy(),recipe['spacing_mm'],diagonal=False)
    projected,_=compute_shape_offset(oriented.shape[1:],oriented.affine.numpy(),new_affine)
    require(math.prod(max(int(v)+2,m) for v,m in zip(projected,recipe['minimum_shape']))<=recipe['max_output_voxels'],
            'Projected resampling budget exceeded')
    chain=Compose([
        ScaleIntensityRanged(keys='image',a_min=recipe['hu_window'][0],a_max=recipe['hu_window'][1],b_min=0,b_max=1,clip=True),
        Spacingd(keys=keys,pixdim=recipe['spacing_mm'],mode=tuple(modes),padding_mode='zeros',align_corners=False),
        SpatialPadd(keys=keys,spatial_size=recipe['minimum_shape'],mode='constant')])
    result=chain(data)
    require(math.prod(result['image'].shape[1:])<=recipe['max_output_voxels'],'Transformed voxel cap')
    require(torch.isfinite(result['image']).all().item(),'Nonfinite transformed image')
    if target is not None:
        if np.any(target):require(torch.any(result['label']>0).item(),'Resampling lost the entire positive target; review recipe')
        require(set(torch.unique(result['label']).tolist())<={0.,1.},'Interpolation changed target classes')
        require(np.allclose(result['image'].affine,result['label'].affine,rtol=0,atol=1e-6),'Transformed grid disagreement')
    record=dict(schema_version='1.0.0',recipe=deepcopy(recipe),recipe_sha256=content_hash(recipe),
        source_shape=list(image.shape),source_affine=a.tolist(),processed_shape=list(result['image'].shape[1:]),
        processed_affine=result['image'].affine.tolist(),operations=['orientation_RAS','HU_scale','spacing','symmetric_zero_pad'],
        image_interpolation='trilinear',target_interpolation='nearest',align_corners=False,
        label_influences_image=False,crop='none')
    record['record_sha256']=content_hash(record)
    result['transform_record']=record
    return result


def restore_to_source(values,record,*,discrete):
    require(record['record_sha256']==content_hash({k:v for k,v in record.items() if k!='record_sha256'}),'Transform record changed')
    require(record['recipe_sha256']==content_hash(record['recipe']),'Transform recipe changed')
    validate_recipe(record['recipe'])
    a=geometry(record['processed_affine'],record['processed_shape'])
    source=geometry(record['source_affine'],record['source_shape'])
    x=torch.as_tensor(values.as_tensor() if isinstance(values,MetaTensor) else values,dtype=torch.float32)
    require(x.ndim==4 and list(x.shape[1:])==record['processed_shape'] and torch.isfinite(x).all().item(), 'Wrong output grid')
    if discrete:require(torch.all(x==x.round()).item(),'Discrete restoration requires class labels')
    image=MetaTensor(x.detach().clone(),affine=a)
    result=SpatialResample(mode='nearest' if discrete else 'bilinear',padding_mode='zeros',align_corners=False)(
        image,dst_affine=source,spatial_size=record['source_shape'])
    require(tuple(result.shape[1:])==tuple(record['source_shape']) and
            np.allclose(result.affine,source,rtol=0,atol=1e-6),'Source restoration grid mismatch')
    return result
