import numpy as np
import pytest
from src.inference.native_error_review_20261104 import crop_bounds,render,canonical

def test_zoom_includes_whole_target_and_respects_border():
    a=np.zeros((30,40),bool);a[0:4,36:40]=1
    assert crop_bounds(a,[2,4],8)==(32,0,40,6)
    with pytest.raises(ValueError):crop_bounds(np.zeros((5,5),bool),[1,1])

def test_plane_world_native_indices_and_no_source_mutation():
    shape=(16,18,20);ct=np.arange(np.prod(shape),dtype=float).reshape(shape);before=ct.copy()
    les=np.zeros(shape,bool);les[4:7,8:10,12:14]=1;pan=les.copy();pr=les.astype(np.uint8)*2
    aff=np.diag([2.,3.,4.,1.]);aff[:3,3]=[10,20,30]
    im,rows=render(ct,pan,les,pr,les,aff,aff,[0,0,0],list(shape),'Synthetic')
    assert im.size==(1560,1420) and np.array_equal(ct,before)
    assert [r['index'] for r in rows]==[12,8,4]
    for r in rows:
        v=np.array(r['original_native_voxel_at_target']);assert abs(v[r['axis']]-r['index'])<1e-9
        assert np.allclose((aff@np.r_[v,1])[:3],r['world_ras_mm'])

def test_oblique_rejected():
    aff=np.eye(4);aff[0,1]=.1
    with pytest.raises(ValueError):canonical(np.ones((4,4,4)),aff)
