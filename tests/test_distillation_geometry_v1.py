from copy import deepcopy
import numpy as np
import pytest
import SimpleITK as sitk
import torch

from src.data.segmenter_teacher_geometry_v1 import grid,preprocess,plan,predict,reconstruct


def image(shape=(17,19,23),spacing=(1.,1.,1.)):
    z,y,x=np.indices(shape,dtype=np.float32)
    obj=sitk.GetImageFromArray(x*2+y*3-z*4-100)
    obj.SetSpacing(spacing);obj.SetOrigin((31.,-27.,17.))
    return obj


@pytest.mark.parametrize('angle',[0.,.3])
def test_sitk_zyx_to_ras_world_points_with_obliquity(angle):
    obj=image(spacing=(.7,1.2,2.5));c,s=np.cos(angle),np.sin(angle)
    obj.SetDirection((c,-s,0.,s,c,0.,0.,0.,1.))
    record=grid(obj);a=np.asarray(record['affine'])
    for point in ((0,0,0),(5,7,11),(16,18,22)):
        expected=np.array(obj.TransformIndexToPhysicalPoint(tuple(reversed(point))))*[-1,-1,1]
        np.testing.assert_allclose((a@[*point,1])[:3],expected,rtol=0,atol=1e-10)


def test_preprocessing_matches_declared_upstream_sequence_and_normalization():
    obj=image(spacing=(.8,1.3,2.));actual,record,info=preprocess(obj,max_voxels=100000)
    expected=sitk.DICOMOrient(obj,'RAI')
    for spacing,method in (((1.,1.,2.),sitk.sitkBSpline),((1.,1.,1.),sitk.sitkNearestNeighbor)):
        size=[int(round(n*s/t)) for n,s,t in zip(expected.GetSize(),expected.GetSpacing(),spacing)]
        expected=sitk.Resample(expected,size,sitk.Transform(3,sitk.sitkIdentity),method,
            expected.GetOrigin(),spacing,expected.GetDirection(),0.,expected.GetPixelIDValue())
    t=torch.from_numpy(sitk.GetArrayFromImage(expected).astype(np.float32)).clamp(-991,500)
    t=(t-t.mean())/t.std(correction=1)
    np.testing.assert_array_equal(actual,t.numpy());assert record==grid(expected)
    assert info['normalization_voxels']==actual.size
    assert actual.mean()==pytest.approx(0,abs=1e-6) and actual.std(ddof=1)==pytest.approx(1,abs=1e-6)


def test_preprocess_memory_degenerate_and_shear_rejected():
    with pytest.raises(ValueError,match='resource'):preprocess(image(spacing=(1.,1.,10.)),max_voxels=10000)
    constant=sitk.GetImageFromArray(np.ones((5,6,7),np.float32))
    with pytest.raises(ValueError,match='Degenerate'):preprocess(constant,max_voxels=10000)
    obj=image();obj.SetDirection((1.,.2,0.,0.,1.,0.,0.,0.,1.))
    with pytest.raises(ValueError,match='Nonorthogonal'):preprocess(obj,max_voxels=10000)


@pytest.mark.parametrize('shape',[(17,29,33),(33,35,37),(32,32,32)])
def test_tiling_padding_unpadding_blending_exact_pointwise_predictor(shape):
    values=np.linspace(-2,2,np.prod(shape),dtype=np.float32).reshape(shape);events=[]
    result,info=predict(values,lambda t:t[:,0].sigmoid(),max_voxels=100000,max_tiles=30,
        window=32,stride=16,tick=events.append)
    expected=torch.from_numpy(values).sigmoid().numpy()
    np.testing.assert_allclose(result,expected,rtol=0,atol=2e-7)
    assert info['reconstruction_gaps']==0 and info['minimum_blend_weight']>0
    assert len(events)==info['tiles'] and events[-1]['tile']==info['tiles']


def test_tiling_fails_before_forward_when_over_budget_or_bad_prediction():
    with pytest.raises(ValueError,match='tile budget'):plan((100,100,100),window=32,stride=16,max_voxels=1000000,max_tiles=1)
    with pytest.raises(ValueError,match='shape'):
        predict(np.zeros((32,)*3,np.float32),lambda t:t,max_voxels=100000,max_tiles=1,window=32,stride=16)
    with pytest.raises(ValueError,match='probabilities'):
        predict(np.zeros((32,)*3,np.float32),lambda t:t[:,0]+float('nan'),max_voxels=100000,max_tiles=1,window=32,stride=16)


@pytest.mark.parametrize('oblique',[False,True])
def test_native_probability_world_mapping_flip_permutation_spacing_and_translation(oblique):
    shape=(12,13,14);z,y,x=np.indices(shape,dtype=np.float32)
    probability=(.1+.01*z+.02*y+.015*x).astype(np.float32)
    affine=np.eye(4);affine[:3,3]=[31,-25,17]
    if oblique:
        affine[:3,:3]=[[.8,-.6,0],[.6,.8,0],[0,0,2]]
    relative=np.array([[0,0,.7,1.],[0,.8,0,2.],[-.6,0,0,9.],[0,0,0,1]])
    native=dict(shape=[7,8,9],affine=(affine@relative).tolist())
    teacher=dict(shape=list(shape),affine=affine.tolist())
    actual,report=reconstruct(probability,teacher,native,max_voxels=10000,slab=2)
    points=np.indices(native['shape'],dtype=float).reshape(3,-1)
    coords=relative[:3,:3]@points+relative[:3,3,None]
    expected=(.1+.01*coords[0]+.02*coords[1]+.015*coords[2]).reshape(native['shape'])
    np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-7)
    assert report['out_of_field_voxels']==0 and report['boundary_extended_voxels']==0
    shifted=deepcopy(native);shifted['affine'][0][3]+=100
    with pytest.raises(ValueError,match='outside teacher coverage'):reconstruct(probability,teacher,shifted,max_voxels=10000)


def test_boundary_cell_extension_is_measured_not_silent_zero():
    a=np.eye(4);a[0,3]=-.25;teacher=dict(shape=[4]*3,affine=np.eye(4).tolist())
    q,report=reconstruct(np.full((4,)*3,.75,np.float32),teacher,dict(shape=[4]*3,affine=a.tolist()),max_voxels=64)
    assert np.all(q==.75) and report['boundary_extended_voxels']==16
    a[0,3]=-.6
    with pytest.raises(ValueError):reconstruct(q,teacher,dict(shape=[4]*3,affine=a.tolist()),max_voxels=64)


def test_no_cuda_context():assert not torch.cuda.is_initialized()
