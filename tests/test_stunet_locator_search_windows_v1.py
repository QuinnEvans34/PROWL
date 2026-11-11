import numpy as np
from src.training.stunet_locator_search_windows_v1 import (
    complete_components,offcenter_order,search_grid,
)


def test_partial_lesion_never_becomes_a_negative():
    a=np.zeros((8,)*3,dtype=np.uint16)
    a[0,0,0]=1
    a[5,5,5]=2
    assert complete_components(a,[0,1,2]) is None
    a[5,5,6]=2
    assert complete_components(a,[0,1,2])==(1,2)
    assert complete_components(a[1:4,1:4,1:4],[0,1,2])==()


def test_offcenter_search_windows_are_grid_points_and_cover_target():
    grid=search_grid(np.array([[10,10,10],[110,110,110]]),(128,128,128))
    box=(slice(48,51),slice(54,56),slice(45,52))
    windows=offcenter_order(grid,box,np.random.default_rng(42))
    assert windows and all(c in grid for c in windows)
    assert all(max(abs(x-y) for x,y in zip(c,(49,54,48)))>=10 for c in windows)
    assert all(all(x-32<=s.start and x+32>=s.stop for x,s in zip(c,box)) for c in windows)
