import numpy as np
import torch

from src.training.stunet_candidate_locator_v1 import Locator,center_target,nonmaximum,translated


def test_tiny_target_preserved_and_shifted_with_image():
    x=np.zeros((16,)*3,np.float32)
    y=np.zeros(x.shape,bool); y[5,6,7]=True;x[y]=1
    valid=np.ones(x.shape,bool)
    a,b,c=translated(x,y,valid,(4,-2,1))
    assert np.array_equal(a>0,b)
    h,s=center_target(b,c)
    assert h[2,1,8]==1 and s[2,1,8]
    assert center_target(np.zeros_like(b),c)[0].sum()==0


def test_locator_is_ct_only_and_nms_respects_physical_distance():
    torch.set_num_threads(2)
    model=Locator()
    assert model(torch.zeros(1,1,17,15,16)).shape==(1,1,5,4,16)
    a=np.diag([2.,1.,1.,1.])
    r=nonmaximum([[0,0,0],[3,0,0],[4,0,0],[0,8,0]],[.9,.8,.7,.6],a)
    assert [p for p,s in r]==[[0,0,0],[4,0,0],[0,8,0]]


def test_proposal_matching_counts_duplicates_as_false():
    from scripts.diagnostics.run_mac_candidate_locator_20261111 import matching,totals
    p=[{'edges':[[1,1.0],[2,2.0]]},{'edges':[[1,1.0]]},{'edges':[[1,1.0]]}]
    assert matching(p,2)=={1,2}
    rows=[dict(n=2,small=[1],incumbent_hits=[2],arms={'locator':p})]
    assert totals(rows,'locator')==dict(matched=2,small_hits=1,newly_located_small=1,
        false_proposals=1,empty_scans_with_proposals=0)
