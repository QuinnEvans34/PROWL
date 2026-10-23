"""Candidate teacher preprocessing, streaming one-pass inference and world mapping.

No patient file access, label-guided crops, test roles, CUDA dispatch or launch
authority lives here. Caller must supply bounded, qualified inputs. This is NOT
an assertion of equivalence to upstream's default two-pass/TTA inference.
"""
from itertools import product
import math

import numpy as np
from scipy import ndimage
import SimpleITK as sitk
import torch

from src.data.segmenter_native_windows_v1 import starts

POLICY=dict(version='medformer-single-pass-native-target-candidate-1',
    orientation='RAI_permutation_flip_preserve_obliquity',spacing_mm=[1.,1.,1.],
    interpolation='upstream_XY_bspline_then_XYZ_nearest',hu_clip=[-991.,500.],
    normalization='full_CT_mean_sample_std_before_padding_float32_CPU',
    padding='symmetric_zero_correct_zyx_axes',window=128,stride=64,
    inference='single_pass_no_TTA_no_gate_edge_anchored_gaussian_sigma_quarter_window',
    accumulation='lesion_only_float32_CPU',reconstruction='native_region_RAS_world_linear',
    status='candidate_requires_real_CT_CUDA_quality_and_resource_qualification')


def checked_shape(shape,max_voxels):
    if (len(shape)!=3 or any(type(n) not in (int,np.int64,np.int32) or n<1 for n in shape)
            or type(max_voxels) is not int or max_voxels<1 or math.prod(shape)>max_voxels):
        raise ValueError('Teacher shape/resource gate')
    return tuple(map(int,shape))


def grid(image):
    """RAS world affine for a SimpleITK array in z,y,x order."""
    a=np.eye(4);a[:3,:3]=np.asarray(image.GetDirection()).reshape(3,3)@np.diag(image.GetSpacing())
    a[:3,3]=image.GetOrigin()
    lps_to_ras=np.diag([-1.,-1.,1.,1.]);reverse=np.eye(4)[:,[2,1,0,3]]
    a=lps_to_ras@a@reverse
    return dict(shape=list(reversed(image.GetSize())),affine=a.tolist())


def _resample(image,spacing,interpolator,max_voxels):
    shape=tuple(int(round(n*s/t)) for n,s,t in zip(image.GetSize(),image.GetSpacing(),spacing))
    checked_shape(shape,max_voxels)
    ref=sitk.Image(shape,image.GetPixelIDValue());ref.SetSpacing(spacing)
    ref.SetOrigin(image.GetOrigin());ref.SetDirection(image.GetDirection())
    return sitk.Resample(image,ref,sitk.Transform(3,sitk.sitkIdentity),interpolator)


def preprocess(image,*,max_voxels):
    """Keep upstream spatial/normalization rules, with explicit memory preflight.

    CPU reduction is intentionally declared; exact GPU floating-point reduction
    equivalence is not claimed. No CT source is modified or permanently resampled.
    """
    if image.GetDimension()!=3 or image.GetNumberOfComponentsPerPixel()!=1:
        raise ValueError('Scalar 3D CT required')
    checked_shape(image.GetSize(),max_voxels)
    directions=np.asarray(image.GetDirection()).reshape(3,3)
    if not np.allclose(directions.T@directions,np.eye(3),rtol=0,atol=1e-5):
        raise ValueError('Nonorthogonal source direction requires investigation')
    if not np.isfinite(sitk.GetArrayViewFromImage(image)).all():raise ValueError('Nonfinite CT')
    oriented=sitk.DICOMOrient(image,'RAI');spacing=oriented.GetSpacing()
    if spacing!=(1.,1.,1.):
        oriented=_resample(oriented,(1.,1.,spacing[2]),sitk.sitkBSpline,max_voxels)
        oriented=_resample(oriented,(1.,1.,1.),sitk.sitkNearestNeighbor,max_voxels)
    values=torch.from_numpy(sitk.GetArrayFromImage(oriented).astype(np.float32))
    values.clamp_(-991.,500.);mean=float(values.mean());std=float(values.std(correction=1))
    if not math.isfinite(std) or std<=1e-8:raise ValueError('Degenerate CT normalization')
    values.sub_(mean).div_(std)
    if not torch.isfinite(values).all():raise ValueError('Nonfinite normalized CT')
    return values.numpy(),grid(oriented),dict(source_grid=grid(image),mean=mean,sample_std=std,
        normalization_voxels=values.numel(),policy=POLICY.copy())


def plan(shape,*,window=128,stride=64,max_voxels,max_tiles):
    shape=checked_shape(shape,max_voxels)
    if type(window) is not int or window<32 or window%16 or type(stride) is not int or not 1<=stride<=window:
        raise ValueError('Teacher window/stride')
    padded=tuple(max(n,window) for n in shape);checked_shape(padded,max_voxels)
    axes=[starts(n,window,stride) for n in padded];count=math.prod(map(len,axes))
    if type(max_tiles) is not int or not 1<=count<=max_tiles:raise ValueError('Teacher tile budget exceeded')
    return dict(shape=list(shape),padded=list(padded),low=[(b-a)//2 for a,b in zip(shape,padded)],
        window=window,stride=stride,tiles=count,origins=list(product(*axes)),
        dense_float32_bytes_lower_bound=4*(3*math.prod(padded)+math.prod(shape)))


def predict(values,predict_window,*,max_voxels,max_tiles,window=128,stride=64,tick=lambda row:None):
    """One GPU window at a time; all accumulation remains CPU and lesion-only.

    predict_window must be the frozen teacher's bounded forward. The caller must
    provide an external process watchdog: per-tile callbacks are not a hard cap.
    """
    if values.dtype!=np.float32 or not np.isfinite(values).all():raise ValueError('Finite teacher input required')
    p=plan(values.shape,window=window,stride=stride,max_voxels=max_voxels,max_tiles=max_tiles)
    padding=[(lo,b-a-lo) for a,b,lo in zip(p['shape'],p['padded'],p['low'])]
    padded=np.pad(values,padding);acc=np.zeros(padded.shape,np.float32);weight=np.zeros_like(acc)
    axis=np.exp(-.5*((np.arange(window,dtype=np.float32)-(window-1)/2)/(window*.25))**2)
    blend=axis[:,None,None]*axis[None,:,None]*axis[None,None,:]
    for index,origin in enumerate(p['origins']):
        slices=tuple(slice(o,o+window) for o in origin)
        x=torch.from_numpy(np.ascontiguousarray(padded[slices]))[None,None]
        probability=predict_window(x)
        if not isinstance(probability,torch.Tensor) or probability.shape!=(1,window,window,window):
            raise ValueError('Teacher prediction shape')
        q=probability.detach().cpu().numpy()
        if q.dtype!=np.float32 or not np.isfinite(q).all() or q.min()<0 or q.max()>1:
            raise ValueError('Teacher prediction probabilities')
        acc[slices]+=q[0]*blend;weight[slices]+=blend
        tick(dict(tile=index+1,total=p['tiles']))
    if np.any(weight<=0):raise ValueError('Teacher reconstruction gap')
    np.divide(acc,weight,out=acc);np.clip(acc,0,1,out=acc)
    unpad=tuple(slice(lo,lo+n) for lo,n in zip(p['low'],p['shape']))
    return acc[unpad].copy(),dict(tiles=p['tiles'],padded=p['padded'],pad_low=p['low'],
        reconstruction_gaps=0,minimum_blend_weight=float(weight.min()))


def reconstruct(probability,teacher_grid,native_grid,*,max_voxels,slab=4):
    """Map complete native-region voxel centres through RAS, not array shape.

    Nearest edge extension is allowed only inside a teacher boundary voxel cell.
    Out-of-field native centres fail; unavailable probability is never zero-filled.
    """
    shape=checked_shape(native_grid['shape'],max_voxels)
    if type(slab) is not int or slab<1:raise ValueError('Positive reconstruction slab')
    if probability.dtype!=np.float32 or probability.shape!=tuple(teacher_grid['shape']):
        raise ValueError('Teacher probability/grid mismatch')
    if not np.isfinite(probability).all() or probability.min()<0 or probability.max()>1:
        raise ValueError('Teacher probability invalid')
    affines=[np.asarray(g['affine'],float) for g in (teacher_grid,native_grid)]
    for a in affines:
        if a.shape!=(4,4) or not np.isfinite(a).all() or not np.allclose(a[3],[0,0,0,1]) or abs(np.linalg.det(a[:3,:3]))<1e-10:
            raise ValueError('Invalid world affine')
    transform=np.linalg.solve(affines[0],affines[1]);out=np.empty(shape,np.float32)
    boundary_extended=0
    for start in range(0,shape[0],slab):
        stop=min(shape[0],start+slab)
        points=np.indices((stop-start,shape[1],shape[2]),dtype=np.float64);points[0]+=start
        coords=(transform[:3,:3]@points.reshape(3,-1)+transform[:3,3,None]).reshape(points.shape)
        if any(c.min()<-.5-1e-5 or c.max()>n-.5+1e-5 for c,n in zip(coords,probability.shape)):
            raise ValueError('Native field outside teacher coverage; investigate, do not zero-fill')
        boundary_extended+=int(np.any((coords<0)|(coords>np.asarray(probability.shape)[:,None,None,None]-1),axis=0).sum())
        out[start:stop]=ndimage.map_coordinates(probability,coords,order=1,mode='nearest',prefilter=False)
    return out,dict(native_voxels=out.size,covered_voxels=out.size,boundary_extended_voxels=boundary_extended,
        out_of_field_voxels=0,method='RAS_world_linear_slabbed')
