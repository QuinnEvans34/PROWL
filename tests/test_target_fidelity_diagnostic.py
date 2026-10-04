import json
from pathlib import Path
import numpy as np
import pytest
from src.data.target_fidelity_diagnostic import center_splat,measure,compare


def test_native_grid_recovers_boundary_reference():
    recipe=json.loads(Path('configs/capstone/localizer-preprocessing-v3.json').read_text())
    a=np.diag([-1.5,1.5,-1.5,1.]);a[:3,3]=[12,-6,27]
    target=np.zeros((17,19,21),dtype=np.uint8);target[5:8,4:8,-1]=1
    rows=compare(target,a,recipe)['comparisons'];native=next(x for x in rows if x['spacing_mm']==1.5)
    assert native['recall']==native['precision']==native['dice']==1
    assert native['false_positive']==native['false_negative']==0


def test_splat_is_centers_not_volume_overlap():
    t=np.zeros((9,9,9),dtype=np.uint8);t[1,1,1]=1;t[2,2,2]=1
    m=center_splat(t,np.eye(4),np.diag([3,3,3,1]),(4,4,4))
    assert m.sum()==2 and m[0,0,0] and m[1,1,1]


def test_splat_oblique_affine_identity():
    a=np.array([[0,-2,0,30],[2,0,0,-10],[0,0,2,5],[0,0,0,1.]])
    t=np.zeros((7,8,9),dtype=np.uint8);t[1:3,2:4,0]=1
    assert np.array_equal(center_splat(t,a,a,t.shape),t)


def test_splat_rejects_outside_grid():
    t=np.ones((2,2,2),dtype=np.uint8)
    with pytest.raises(ValueError):center_splat(t,np.eye(4),np.eye(4),(1,1,1))


def test_metrics_separate_inflation_and_loss():
    a=np.zeros((3,3,3));a[0,0,0]=a[1,1,1]=1
    b=np.zeros_like(a);b[0,:,:]=1
    r=measure(a,b,np.diag([2,2,2,1]));assert r['recall']==.5 and r['false_positive']==8 and r['volume_ratio']==4.5
    assert r['source_volume_mm3']==pytest.approx(16)
