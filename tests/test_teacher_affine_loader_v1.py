import itertools
import numpy as np
import nibabel as nib
import pytest
import SimpleITK as sitk
from scipy.ndimage import affine_transform
from src.data.teacher_affine_loader_v1 import orthogonal_grid,load
from src.data.segmenter_teacher_geometry_v2 import grid,preprocess


@pytest.mark.parametrize('shear',[.000137,.07,-.12])
@pytest.mark.parametrize('flip',[1,-1])
def test_world_ramp_and_full_coverage(shear,flip):
    shape=(19,15,13);a=np.eye(4);a[:3,:3]=[[flip*1.5,shear,0],[0,1.2,0],[0,0,2.]];a[:3,3]=[30,-12,50]
    size,b=orthogonal_grid(shape,a)
    assert np.allclose((b[:3,:3]/np.linalg.norm(b[:3,:3],axis=0)).T@(b[:3,:3]/np.linalg.norm(b[:3,:3],axis=0)),np.eye(3))
    corners=np.array([(*c,1) for c in itertools.product(*[(0,n-1) for n in shape])]).T
    q=np.linalg.solve(b,a@corners)[:3];assert np.all(q>=-1e-10) and np.all(q<=np.array(size)[:,None]-1+1e-10)
    xyz=np.indices(shape).reshape(3,-1);world=a[:3,:3]@xyz+a[:3,3,None];values=(world[0]+2*world[1]-world[2]).reshape(shape)
    m=np.linalg.solve(a,b);out=affine_transform(values,m[:3,:3],offset=m[:3,3],output_shape=size,order=1,prefilter=False)
    ix=np.indices(size).reshape(3,-1);source=m[:3,:3]@ix+m[:3,3,None];valid=np.all((source>=1)&(source<np.array(shape)[:,None]-2),axis=0)
    target=b[:3,:3]@ix+b[:3,3,None];expected=target[0]+2*target[1]-target[2]
    np.testing.assert_allclose(out.ravel()[valid],expected[valid],atol=1e-10)


def test_ordinary_path_exact(tmp_path):
    p=tmp_path/'ct.nii.gz';a=np.diag([1.5,1.5,1.5,1.]);nib.save(nib.Nifti1Image(np.random.default_rng(2).normal(size=(17,13,11)).astype('float32'),a),p)
    before=sitk.ReadImage(str(p));meta={'parent_geometry':{'source_shape':[17,13,11],'source_affine':a.tolist()},'geometry':grid(before)}
    after,_,record=load(p,meta,'ordinary')
    assert record['path']=='unchanged-SimpleITK';assert grid(before)==grid(after)
    np.testing.assert_array_equal(sitk.GetArrayFromImage(before),sitk.GetArrayFromImage(after))
    x,g,_=preprocess(before,max_voxels=100000);y,h,_=preprocess(after,max_voxels=100000)
    assert g==h;np.testing.assert_array_equal(x,y)


def test_exception_rejects_geometry_mismatch(tmp_path):
    p=tmp_path/'ct.nii.gz';nib.save(nib.Nifti1Image(np.ones((5,6,7),dtype='float32'),np.eye(4)),p)
    with pytest.raises(ValueError,match='frozen geometry'):load(p,{'parent_geometry':{'source_shape':[5,6,8],'source_affine':np.eye(4).tolist()}},'PanTS_00004348')


def test_degenerate_affine_rejected():
    with pytest.raises(ValueError):orthogonal_grid([5,6,7],np.zeros((4,4)))
