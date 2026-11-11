import numpy as np
from scripts.diagnostics import replay_mac_candidate_locator_bounded_20261111 as replay


def test_split_covers_all_pancreas_support_with_unchanged_cap(monkeypatch):
    monkeypatch.setattr(replay,'ROI_CAP',36_000)
    points=np.array([[6,6,6],[7,7,7],[17,10,10],[90,80,60],[90,82,62],[91,84,63]])
    shape=np.array([100,90,70])
    basis=np.array([[1.,.2,0],[0,1.,0],[0,0,2.]])
    r=replay.regions(points,shape,basis)
    assert len(r)>1
    assert all(np.prod(hi-lo)<=36_000 and np.all(lo>=0) and np.all(hi<=shape) for lo,hi in r)
    assert all(any(np.all(lo<=p) and np.all(p<hi) for lo,hi in r) for p in points)
