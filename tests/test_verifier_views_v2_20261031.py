import numpy as np
from scipy import ndimage
from src.data.verifier_views_v2_20261031 import make_views

def test_thick_slice_upsampling_preserves_solid_support():
    shape=(20,20,20);a=np.ones(shape,np.float32)*.5;p=a.copy();mask=np.zeros(shape,np.int32);mask[8:10,8:10,8:10]=1
    views,meta=make_views(a,p,mask,1,np.diag([5.,5.,5.,1.]))
    global_support=views[0,2].astype(bool)
    assert global_support.sum()>1000
    assert ndimage.label(global_support,np.ones((3,3,3),np.uint8))[1]==1
    assert meta['global_view']['represented_source_voxels']==8

def test_thin_tiny_candidate_survives_and_stays_binary():
    a=np.zeros((20,20,20),np.float32);p=a.copy();p[0,0,0]=.8;m=np.zeros(a.shape,int);m[0,0,0]=1
    v,r=make_views(a,p,m,1,np.diag([.1,.1,.1,1.]))
    assert v[0,2].sum()>=1 and v[1,2].sum()>=1
    assert set(np.unique(v[:,2:]))<={0.,1.} and r['complete_component_coverage']

def test_broad_component_global_coverage_and_partial_detail():
    a=np.ones((90,10,10),np.float32)*.5;m=np.zeros(a.shape,int);m[1:89,2:8,2:8]=1
    v,r=make_views(a,a,m,1,np.eye(4))
    assert r['global_view']['represented_source_voxels']==int((m==1).sum())
    assert r['detail_is_partial_context'] and r['detail_view']['represented_source_voxels']<int((m==1).sum())
