import numpy as np
from scripts.diagnostics.review_training_input_fidelity import overlap, plane


def test_overlap_counts_partial_and_exact():
    a=np.array([True,True,False,False]);b=np.array([True,False,True,False])
    assert overlap(a,b)['dice']==.5
    assert overlap(a,b)['recall']==.5
    assert overlap(a,a)['dice']==1


def test_physical_plane_honors_translation_and_axis():
    a=np.arange(24).reshape(2,3,4).astype(float)
    affine=np.diag([2.,3.,4.,1.]);affine[:3,3]=[10,20,30]
    grid=np.ones((4,3,4))
    grid[0]=12
    grid[1]=20+np.arange(3)[:,None]*3
    grid[2]=30+np.arange(4)[None,:]*4
    np.testing.assert_array_equal(plane(a,affine,grid,0),a[1])
