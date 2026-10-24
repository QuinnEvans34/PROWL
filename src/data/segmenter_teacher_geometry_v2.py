"""Additive centre-covering teacher preprocessing; v1 remains frozen.

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

from src.data.segmenter_teacher_geometry_v1 import predict, reconstruct, plan

POLICY=dict(version='medformer-single-pass-native-target-candidate-2',
    orientation='RAI_permutation_flip_preserve_obliquity',spacing_mm=[1.,1.,1.],
    interpolation='upstream_XY_bspline_then_XYZ_nearest',hu_clip=[-991.,500.],
    normalization='full_CT_mean_sample_std_before_padding_float32_CPU',
    padding='symmetric_zero_correct_zyx_axes',window=128,stride=64,
    inference='single_pass_no_TTA_no_gate_edge_anchored_gaussian_sigma_quarter_window',
    accumulation='lesion_only_float32_CPU',reconstruction='native_region_RAS_world_linear',
    resampling_size='max_legacy_round_and_ceil_source_centres_plus_one',
    status='candidate_requires_real_CT_quality_and_resource_qualification')


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


def covering_size(size, spacing, target):
    if len(size)!=3 or len(spacing)!=3 or len(target)!=3:
        raise ValueError('Three axes required')
    if any(n<1 or int(n)!=n for n in size) or any(not math.isfinite(s) or s<=0 for s in (*spacing,*target)):
        raise ValueError('Invalid resampling geometry')
    return tuple(max(int(round(n*s/t)), int(math.ceil((n-1)*s/t))+1)
                 for n,s,t in zip(size,spacing,target))


def _resample(image,spacing,interpolator,max_voxels):
    shape=covering_size(image.GetSize(),image.GetSpacing(),spacing)
    checked_shape(shape,max_voxels)
    ref=sitk.Image(shape,image.GetPixelIDValue());ref.SetSpacing(spacing)
    ref.SetOrigin(image.GetOrigin());ref.SetDirection(image.GetDirection())
    return sitk.Resample(image,ref,sitk.Transform(3,sitk.sitkIdentity),interpolator)


def preprocess(image,*,max_voxels):
    """Retain orientation/interpolation, extend grid to cover source centres.

    Grid extension changes normalization; this is not upstream-equivalent.

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


def metadata_grid(parent):
    """Predict preprocessing geometry without decoding a CT."""
    import nibabel as nib
    affine=np.asarray(parent['source_affine'],float);shape=np.asarray(parent['source_shape'])
    transform=nib.orientations.ornt_transform(nib.orientations.io_orientation(affine),nib.orientations.axcodes2ornt(('R','A','I')))
    oriented=affine@nib.orientations.inv_ornt_aff(transform,shape)
    size=shape[np.argsort(transform[:,0])];spacing=np.linalg.norm(oriented[:3,:3],axis=0)
    direction=oriented[:3,:3]/spacing
    for target in (np.array([1.,1.,spacing[2]]),np.ones(3)):
        size=np.array(covering_size(size,spacing,target));spacing=target
    result=oriented.copy();result[:3,:3]=direction*spacing
    return dict(shape=size[::-1].tolist(),affine=(result@np.eye(4)[:,[2,1,0,3]]).tolist())
