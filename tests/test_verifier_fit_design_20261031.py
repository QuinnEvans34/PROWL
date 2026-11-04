import numpy as np
import pytest
from scripts.diagnostics.review_verifier_fit_20261031 import summarize

def test_merged_hits_and_missed_small_component():
    labels=np.zeros((8,8,8),int);labels[1:6,1,1]=1;labels[6,6,6]=2
    truth=np.zeros(labels.shape,bool);truth[1,1,1]=True;truth[5,1,1]=True;truth[7,0,0]=True
    r=summarize(labels,truth,np.diag([1.,1.,2.,1.]),np.ones(labels.shape)*.6)
    assert r['candidates'][0]['positive'] and len(r['candidates'][0]['gt_hits'])==2
    assert not r['candidates'][1]['positive']
    assert sum(x['detected'] for x in r['gt_components'])==2
    assert r['candidates'][0]['extent_mm']==[5.,1.,2.]

def test_empty_predictions_preserve_misses():
    a=np.zeros((3,3,3),int);t=a.astype(bool);t[1,1,1]=True
    r=summarize(a,t,np.eye(4),a.astype(float))
    assert r['candidates']==[] and not r['gt_components'][0]['detected']

def test_alignment_refused():
    with pytest.raises(ValueError):summarize(np.zeros((2,2,2)),np.zeros((3,3,3)),np.eye(4),np.zeros((2,2,2)))
