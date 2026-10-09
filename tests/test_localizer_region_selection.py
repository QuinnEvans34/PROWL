import numpy as np
import pytest
from src.inference.localizer_region_selection import select_region


def test_largest_removes_distant_island_without_reference():
    a=np.zeros((12,12,12),np.uint8);a[1:4,1:4,1:4]=1;a[10,10,10]=1
    b,r=select_region(a,'largest_component_26')
    assert b.sum()==27 and b[10,10,10]==0 and a.sum()==28
    assert r['component_count']==2 and r['input_voxels']==28
    original,_=select_region(a);assert np.array_equal(original,a)


def test_diagonal_connectivity_and_deterministic_tie():
    a=np.zeros((8,8,8),np.uint8);a[0,0,0]=a[1,1,1]=1;a[6,6,6]=a[7,7,7]=1
    b,r=select_region(a,'largest_component_26')
    assert b.sum()==2 and b[0,0,0]==1 and b[7,7,7]==0
    assert r['component_count']==2 and r['selected_component']==1


def test_empty_never_becomes_full_volume_and_invalid_policy_refused():
    a=np.zeros((4,4,4),np.uint8)
    b,r=select_region(a,'largest_component_26');assert not b.any() and r['selected_component']==0
    with pytest.raises(ValueError):select_region(a,'reference')
    with pytest.raises(ValueError):select_region(a+2,'largest_component_26')
