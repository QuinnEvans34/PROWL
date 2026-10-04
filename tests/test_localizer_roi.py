import numpy as np
import pytest
from src.training.localizer_roi import select_region, evaluate_region


def test_physical_margin_half_open_clipping_and_coverage():
    p=np.zeros((20,20,20),np.uint8);p[1:3,8:10,10:12]=1
    s,r=select_region(p,np.diag([2,3,4,1]),margin_mm=5)
    assert r['box']==[[0,6,8],[6,12,14]]
    assert r['dimensions_mm']==[12,18,24]
    assert r['realized_margin_mm']==[[2,6,8],[6,6,8]]
    assert r['boundary_contact'][0]==[True,False,False]
    m=evaluate_region(s,p,r)
    assert m['dice']==m['box_reference_coverage']==1
    assert m['fit_diagnostic_pass'] and m['pre_mapping_roi_diagnostic_pass']


def test_largest_tie_does_not_use_reference_and_can_discard_anatomy():
    p=np.zeros((20,20,20),np.uint8);p[1:3,1:3,1:3]=1;p[17:19,17:19,17:19]=1
    s,r=select_region(p,np.eye(4),strategy='largest',margin_mm=0)
    assert s[1,1,1] and not s[17,17,17]
    assert r['component_count']==2 and r['component_volumes_mm3']==[8,8]
    target=np.zeros_like(p);target[17:19,17:19,17:19]=1
    m=evaluate_region(s,target,r)
    assert m['recall']==m['box_reference_coverage']==0
    assert not m['fit_diagnostic_pass'] and not m['pre_mapping_roi_diagnostic_pass']


def test_empty_prediction_is_failure_not_fallback():
    p=np.zeros((8,8,8));target=p.copy();target[4,4,4]=1
    s,r=select_region(p,np.eye(4));m=evaluate_region(s,target,r)
    assert r['box'] is None and r['state']=='failed_empty_localization'
    assert m['recall']==0 and m['box_reference_coverage'] is None
    assert not m['pre_mapping_roi_diagnostic_pass']
    assert evaluate_region(s,p,r)['fit_diagnostic_pass'] is None


def test_high_recall_excess_foreground_fails_fit():
    p=np.ones((8,8,8));target=np.zeros_like(p);target[2:6,2:6,2:6]=1
    s,r=select_region(p,np.eye(4),margin_mm=0);m=evaluate_region(s,target,r)
    assert m['recall']==1 and m['volume_ratio']==8
    assert not m['fit_diagnostic_pass'] and not m['pre_mapping_roi_diagnostic_pass']


@pytest.mark.parametrize('bad',[np.ones((4,4)),np.full((4,4,4),.5),np.full((4,4,4),np.nan)])
def test_invalid_masks(bad):
    with pytest.raises(ValueError):select_region(bad,np.eye(4))


def test_noncanonical_affine_and_grid_rejected():
    p=np.zeros((4,4,4));a=np.eye(4);a[0,1]=.2
    with pytest.raises(ValueError):select_region(p,a)
    s,r=select_region(p,np.eye(4))
    with pytest.raises(ValueError):evaluate_region(s,np.zeros((3,3,3)),r)
    with pytest.raises(ValueError):select_region(p,np.eye(4),margin_mm=float('inf'))


@pytest.mark.parametrize('changed',['receipt','member','source'])
def test_diagnostic_refuses_changed_training_evidence(tmp_path,monkeypatch,changed):
    import json
    from scripts.diagnostics import localizer_roi_check as cli
    run=tmp_path/'run';run.mkdir();source=tmp_path/'example.py';source.write_text('original')
    raw=json.dumps({'files':{'example.py':'original'}}).encode();(run/'source.json').write_bytes(raw)
    receipt=json.dumps({'files':{'source.json':{'sha256':cli.sha(raw)}}}).encode();(run/'receipt.json').write_bytes(receipt)
    monkeypatch.setattr(cli,'RUN',run);monkeypatch.setattr(cli,'REPO',tmp_path);monkeypatch.setattr(cli,'PIN',cli.sha(receipt))
    cli.verify_original()
    if changed=='receipt':(run/'receipt.json').write_bytes(b'{}')
    elif changed=='member':(run/'source.json').write_bytes(b'{}')
    else:source.write_text('changed')
    with pytest.raises(ValueError):cli.verify_original()
