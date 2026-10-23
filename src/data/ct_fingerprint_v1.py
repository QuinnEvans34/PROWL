"""CT-only duplicate candidate spike; similarity never establishes identity."""
import hashlib
import json
import math
import numpy as np
import nibabel as nib
from nibabel.processing import resample_to_output
from scipy import ndimage

CONFIG=dict(version='ct-fingerprint-spike-1',window=[-1000,1000],spacing_mm=3.,
            grid=32,foreground_hu=-500,metric='cosine_distance',threshold=.08,
            retrieval_depth=5,max_source_voxels=256000000,max_coarse_voxels=16000000)


def canonical(image):
    if len(image.shape)!=3 or math.prod(image.shape)>CONFIG['max_source_voxels']:
        raise ValueError('Fingerprint source size envelope')
    if not np.isfinite(image.affine).all() or abs(np.linalg.det(image.affine[:3,:3]))<1e-12:
        raise ValueError('Fingerprint affine invalid')
    result=nib.as_closest_canonical(image)
    data=result.get_fdata(dtype=np.float32)
    if not np.isfinite(data).all():raise ValueError('Nonfinite CT')
    return nib.Nifti1Image(data,result.affine)


def decoded_hash(image):
    data=np.asanyarray(image.dataobj)
    h=hashlib.sha256(json.dumps(list(data.shape),separators=(',',':')).encode())
    for slab in data:
        rounded=np.rint(slab)
        if not np.isfinite(rounded).all() or np.any(np.abs(rounded)>2147483000):
            raise ValueError('HU normalization range')
        h.update(rounded.astype('<i4').tobytes(order='C'))
    return h.hexdigest()


def fingerprint(image):
    from itertools import product
    corners=nib.affines.apply_affine(image.affine,np.array(list(product(*[(0,n-1) for n in image.shape]))))
    projected=np.ceil(np.ptp(corners,axis=0)/CONFIG['spacing_mm']).astype(int)+1
    if math.prod(projected)>CONFIG['max_coarse_voxels']:raise ValueError('Fingerprint coarse allocation')
    coarse=resample_to_output(image,voxel_sizes=(3.,)*3,order=1,cval=-1000).get_fdata(dtype=np.float32)
    labels,count=ndimage.label(coarse>CONFIG['foreground_hu'])
    if not count:raise ValueError('No CT foreground')
    sizes=np.bincount(labels.ravel());sizes[0]=0
    selected=labels==int(sizes.argmax())
    bounds=[]
    for axis in range(3):
        indices=np.flatnonzero(selected.any(axis=tuple(i for i in range(3) if i!=axis)))
        bounds.append(slice(int(indices[0]),int(indices[-1])+1))
    crop=np.clip(coarse[tuple(bounds)],-1000,1000)
    vector=ndimage.zoom(crop,np.array([32]*3)/crop.shape,order=1,prefilter=False).ravel()
    vector=np.rint(vector/8)*8
    vector=vector.astype(np.float32);vector-=vector.mean()
    norm=np.linalg.norm(vector)
    if not np.isfinite(norm) or norm<=0:raise ValueError('Degenerate fingerprint')
    return vector/norm


def variants(image):
    """Five deterministic threats; source is never modified."""
    from nibabel.processing import resample_from_to
    data=np.asanyarray(image.dataobj)
    yield 'header_copy',nib.Nifti1Image(data,image.affine)
    affine=image.affine.copy();affine[:3,3]+=affine[:3,0]*(data.shape[0]-1);affine[:3,0]*=-1
    yield 'axis_flip',nib.Nifti1Image(data[::-1],affine)
    yield 'round_2HU',nib.Nifti1Image(np.rint(data/2)*2,image.affine)
    affine=image.affine.copy();affine[:3,:3]*=1.02
    shape=tuple(max(2,int(np.ceil(n/1.02))) for n in data.shape)
    yield 'resample_1p02',resample_from_to(image,(shape,affine),order=1,cval=-1000)
    if min(data.shape)<5:raise ValueError('Calibration crop source too small')
    affine=image.affine.copy();affine[:3,3]=nib.affines.apply_affine(image.affine,[1,1,1])
    yield 'crop_one_voxel',nib.Nifti1Image(data[1:-1,1:-1,1:-1],affine)


def candidates(query,bank):
    query=np.asarray(query,dtype=np.float64);bank=np.asarray(bank,dtype=np.float64)
    norms=np.linalg.norm(bank,axis=1)*np.linalg.norm(query)
    if not np.isfinite(norms).all() or np.any(norms<=0):raise ValueError('Invalid retrieval vectors')
    scores=np.clip(1-(bank@query)/norms,0,2)
    order=np.argsort(scores,kind='stable')[:CONFIG['retrieval_depth']]
    return [(int(i),float(scores[i])) for i in order if scores[i]<=CONFIG['threshold']]
