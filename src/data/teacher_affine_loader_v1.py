"""Explicit full-affine CT resampling for the two qualified sheared-source cases.

Ordinary cases use the original SimpleITK reader byte-for-byte. Exceptional cases
are resampled in world coordinates, never repaired by dropping the shear terms.
"""
import itertools
import numpy as np
import nibabel as nib
import SimpleITK as sitk
from scipy.ndimage import affine_transform
from src.data.segmenter_teacher_geometry_v2 import checked_shape, grid
from src.data.teacher_header_geometry_v1 import checked_header_grid

EXCEPTIONS=frozenset({'PanTS_00003067','PanTS_00004348'})
POLICY=dict(version='qualified-two-case-full-affine-v1',basis='polar-orthogonal',
    spacing='source-affine-column-norm',extent='enclose-all-source-voxel-centres',
    interpolation='linear-full-affine',outside_hu=-1024.,ordinary='unchanged-SimpleITK')


def orthogonal_grid(shape, affine, *, max_voxels=256000000):
    checked_shape(list(shape),max_voxels)
    a=np.asarray(affine,dtype=float)
    if a.shape!=(4,4) or not np.isfinite(a).all() or not np.array_equal(a[3],[0,0,0,1]):
        raise ValueError('Invalid source affine')
    spacing=np.linalg.norm(a[:3,:3],axis=0)
    if np.any(spacing<=0) or np.linalg.cond(a[:3,:3])>100:raise ValueError('Degenerate source affine')
    u,_,vt=np.linalg.svd(a[:3,:3]/spacing);direction=u@vt
    basis=direction*spacing
    corners=np.array(list(itertools.product(*[(0,n-1) for n in shape]))).T
    projected=np.linalg.solve(basis,a[:3,:3]@corners)
    lo=projected.min(axis=1);hi=projected.max(axis=1)
    size=np.ceil(hi-lo).astype(int)+1
    checked_shape(size.tolist(),max_voxels)
    target=np.eye(4);target[:3,:3]=basis;target[:3,3]=a[:3,3]+basis@lo
    return size.tolist(),target


def itk_image(values, affine):
    image=sitk.GetImageFromArray(np.asarray(values,dtype=np.float32).transpose(2,1,0).copy())
    lps=np.diag([-1.,-1.,1.,1.])@affine
    spacing=np.linalg.norm(lps[:3,:3],axis=0)
    image.SetSpacing(tuple(spacing));image.SetDirection(tuple((lps[:3,:3]/spacing).flat));image.SetOrigin(tuple(lps[:3,3]))
    return image


def load(path, meta, case_id, *, max_voxels=256000000):
    if case_id not in EXCEPTIONS:
        image=sitk.ReadImage(str(path))
        return image,checked_header_grid(image,meta,max_voxels=max_voxels),{'path':'unchanged-SimpleITK'}
    source=nib.load(str(path));parent=meta['parent_geometry']
    if list(source.shape)!=parent['source_shape'] or not np.array_equal(source.affine,np.asarray(parent['source_affine'])):
        raise ValueError('Exceptional source differs from frozen geometry')
    shape,affine=orthogonal_grid(source.shape,source.affine,max_voxels=max_voxels)
    mapping=np.linalg.solve(source.affine,affine)
    values=source.get_fdata(dtype=np.float32)
    if not np.isfinite(values).all():raise ValueError('Nonfinite source CT')
    resampled=affine_transform(values,mapping[:3,:3],offset=mapping[:3,3],output_shape=tuple(shape),order=1,mode='constant',cval=-1024.,prefilter=False)
    image=itk_image(resampled,affine)
    derived=dict(meta,parent_geometry=dict(source_shape=shape,source_affine=affine.tolist()))
    expected=checked_header_grid(image,derived,max_voxels=max_voxels)
    return image,expected,dict(path=POLICY['version'],policy=POLICY,source_affine=source.affine.tolist(),source_shape=list(source.shape),orthogonal_affine=affine.tolist(),orthogonal_shape=shape,output_to_source=mapping.tolist())
