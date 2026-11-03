import numpy as np
import pytest
from src.inference.native_review_overlays_20261103 import canonical,plane_choices,selected_component,sheet

def test_lossless_ras_and_physical_coordinates():
    a=np.arange(24).reshape(2,3,4);aff=np.diag([-2,-3,4,1]);aff[:3,3]=[10,20,30]
    out,new,t=canonical(a,aff)
    assert np.array_equal(out,a[::-1,::-1,:]);assert np.allclose(new@np.array([0,0,0,1]),[8,14,30,1])

def test_unsupported_shear_rejected():
    aff=np.eye(4);aff[0,1]=.2
    with pytest.raises(ValueError,match='Unsupported'):canonical(np.ones((3,3,3)),aff)

def test_component_reconciliation_and_deterministic_slice():
    a=np.zeros((5,6,7),bool);a[1:3,2:4,3:5]=1
    row=dict(component_id=1,voxels=8,bounds_xyz_half_open=[[1,3],[2,4],[3,5]])
    assert np.array_equal(selected_component(a,row),a)
    choices=plane_choices(a,np.eye(4));assert [x['index'] for x in choices]==[3,2,1]
    row['voxels']=9
    with pytest.raises(ValueError):selected_component(a,row)

def test_same_conventions_both_arms():
    a=np.zeros((12,14,16),bool);a[3:5,5:8,7:9]=1;pred=a.astype(np.uint8)*2
    image,rows=sheet(np.zeros(a.shape),a,a,dict(autonomous=pred,provided_region=pred),a,np.eye(4),'Synthetic')
    assert image.size==(1560,1020) and len(rows)==3
