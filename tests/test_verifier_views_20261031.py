import numpy as np
import pytest
from src.data.verifier_views_20261031 import make_views

@pytest.mark.parametrize('bounds',[((0,0,0),(1,1,1)),((2,3,1),(25,24,12)),((28,28,13),(30,30,15))])
def test_complete_coverage_padding_and_tiny_candidates(bounds):
    a=np.full((30,30,15),.4,np.float32);p=np.full_like(a,.6);labels=np.zeros(a.shape,np.int32)
    lo,hi=bounds;labels[tuple(slice(l,h) for l,h in zip(lo,hi))]=1
    v,m=make_views(a,p,labels,1,np.diag([.7,.9,5.,1.]))
    assert v.shape==(2,4,64,64,64) and v.dtype==np.float16
    assert m['global_view']['represented_source_voxels']==int((labels==1).sum())
    assert v[0,2].sum()>0 and v[1,2].sum()>0 and v.min()>=0 and v.max()<=1
    assert m['global_view']['valid_fraction']<1

def test_truth_independent_repeatability():
    a=np.ones((5,6,7),np.float32);p=a*.5;l=np.zeros(a.shape,int);l[2,3,4]=1
    v,m=make_views(a,p,l,1,np.eye(4));w,n=make_views(a,p,l,1,np.eye(4))
    assert np.array_equal(v,w) and m==n

def test_invalid_input_refusal():
    a=np.zeros((4,4,4),np.float32)
    with pytest.raises(ValueError):make_views(a,a,a.astype(int),1,np.eye(4))
