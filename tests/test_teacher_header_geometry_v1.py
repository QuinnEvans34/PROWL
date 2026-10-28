import numpy as np
import pytest
import SimpleITK as sitk
from src.data.teacher_header_geometry_v1 import checked_header_grid
from src.data.segmenter_teacher_geometry_v2 import preprocess, grid


def fixture(spacing, oblique=False):
    values=np.random.default_rng(4).normal(size=(21, 18, 19)).astype('float32')
    im=sitk.GetImageFromArray(values); im.SetSpacing(spacing)
    if oblique:
        t=.08; im.SetDirection((np.cos(t),-np.sin(t),0,np.sin(t),np.cos(t),0,0,0,1))
    g=grid(im);a=np.array(g['affine'])@np.eye(4)[:,[2,1,0,3]]
    meta={'parent_geometry':{'source_shape':list(im.GetSize()),'source_affine':a.tolist()},'geometry':g}
    return im,meta


@pytest.mark.parametrize('spacing',[(1.,1.,1.),(1.5,1.5000001192092896,1.5),(.7,.8,2.5)])
@pytest.mark.parametrize('oblique',[False,True])
def test_matches_actual_preprocessing(spacing,oblique):
    im,meta=fixture(spacing,oblique)
    _,actual,_=preprocess(im,max_voxels=100000)
    expected=checked_header_grid(im,meta,max_voxels=100000)
    assert expected['shape']==actual['shape']
    np.testing.assert_allclose(expected['affine'],actual['affine'],atol=1e-4,rtol=0)


def test_rounding_from_affine_does_not_override_header_spacing():
    im,meta=fixture((1.5,1.5,1.5))
    a=np.array(meta['parent_geometry']['source_affine']);a[:3,:3]*=(1-1e-8)
    meta['parent_geometry']['source_affine']=a.tolist()
    _,actual,_=preprocess(im,max_voxels=100000)
    assert checked_header_grid(im,meta)['shape']==actual['shape']


@pytest.mark.parametrize('damage',['origin','shape','coverage'])
def test_rejects_real_geometry_errors(damage):
    im,meta=fixture((1.5,1.5,1.5))
    if damage=='origin':meta['parent_geometry']['source_affine'][0][3]+=1
    if damage=='shape':meta['parent_geometry']['source_shape'][0]+=1
    if damage=='coverage':meta['geometry']['affine'][0][3]+=1000
    with pytest.raises(ValueError):checked_header_grid(im,meta)
