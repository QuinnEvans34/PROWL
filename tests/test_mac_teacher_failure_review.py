import numpy as np
import SimpleITK as sitk
import pytest
from scripts.diagnostics.review_mac_teacher_failure import teacher_grid,coverage
from src.data.segmenter_teacher_geometry_v1 import grid


@pytest.mark.parametrize('direction',[(1.,0,0,0,1.,0,0,0,1.),(-1.,0,0,0,-1.,0,0,0,1.)])
def test_metadata_grid_matches_sitk_resampling_geometry(direction):
    image=sitk.Image((41,31,17),sitk.sitkFloat32)
    image.SetSpacing((.7421879768371582,.7421879768371582,1.25));image.SetDirection(direction)
    image.SetOrigin((31.,-27.,17.))
    reverse=np.eye(4)[:,[2,1,0,3]]
    parent=dict(source_shape=list(image.GetSize()),source_affine=(np.asarray(grid(image)['affine'])@reverse).tolist())
    expected=sitk.DICOMOrient(image,'RAI');spacing=expected.GetSpacing()
    for target in ((1.,1.,spacing[2]),(1.,1.,1.)):
        size=[round(n*s/t) for n,s,t in zip(expected.GetSize(),expected.GetSpacing(),target)]
        expected=sitk.Resample(expected,size,sitk.Transform(3,sitk.sitkIdentity),sitk.sitkLinear,expected.GetOrigin(),target,expected.GetDirection())
    actual=teacher_grid(parent)
    assert actual['shape']==grid(expected)['shape']
    np.testing.assert_allclose(actual['affine'],grid(expected)['affine'],rtol=0,atol=1e-10)


def test_rounded_grid_loses_edge_and_candidate_covers_centres():
    a=np.diag([.7421879768371582,.7421879768371582,1.25,1.])
    parent=dict(source_shape=[441,301,177],source_affine=a.tolist())
    native=dict(shape=parent['source_shape'],affine=a.tolist())
    old=coverage(teacher_grid(parent),native)
    assert not old['covered']
    assert coverage(teacher_grid(parent,preserve_centres=True),native)['covered']
