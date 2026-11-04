import numpy as np
import pytest
from src.data.verifier_generator_geometry_v1 import apply_margin,fit_margin,contains


def row():return dict(native_box=[[3,3,3],[7,7,7]],shape=[10,10,10],affine=np.eye(4).tolist(),lesion_box=[[1,3,3],[8,8,7]])


def test_fit_and_coverage():
    r=row();m=fit_margin({'a':r},['a']);assert m==[3,2,1]
    assert contains(apply_margin(r['native_box'],r['shape'],r['affine'],m),r['lesion_box'])


def test_oblique_plane_distance():
    r=row();r['affine'][0][1]=.7
    m=fit_margin({'a':r},['a'])
    assert contains(apply_margin(r['native_box'],r['shape'],r['affine'],m),r['lesion_box'])


def test_protected_members_rejected():
    with pytest.raises(ValueError):fit_margin({'a':row(),'heldout':row()},['a'])


def test_inference_does_not_take_lesion():
    r=row();box=apply_margin(r['native_box'],r['shape'],r['affine'],[1,1,1])
    assert not contains(box,[[0,0,0],[10,10,10]])
    assert contains(box,None)


@pytest.mark.parametrize('m', [[-1,1,1],[float('nan'),1,1],[1,1]])
def test_bad_margin(m):
    r=row()
    with pytest.raises(ValueError):apply_margin(r['native_box'],r['shape'],r['affine'],m)
