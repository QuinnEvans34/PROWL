import pytest
from src.training.verifier_decisions_20261031 import metrics,calibrate

def patients():
    return [dict(case_id='p',role='verifier_calibration',annotated_voxels=10,gt_components=[dict(component_id=1,volume_ml=.01)],
        candidates=[dict(component_id=1,voxels=10,overlap_voxels=10,gt_hits=[1])]),
        dict(case_id='n',role='verifier_calibration',annotated_voxels=0,gt_components=[],candidates=[dict(component_id=1,voxels=5,overlap_voxels=0,gt_hits=[])])]

def test_threshold_preserves_small_lesion_and_removes_false_alarm():
    r=calibrate(patients(),{('p',1):.8,('n',1):.2})
    assert r['threshold']==.8 and r['selected']['small_hits']==1 and r['absolute_alarm_reduction']==1

def test_bad_rank_cannot_remove_true_lesion():
    r=calibrate(patients(),{('p',1):.2,('n',1):.8})
    assert r['selected']['small_hits']==1 and r['absolute_alarm_reduction']==0

def test_missing_group_is_not_pass():
    p=patients();p[0]['gt_components'][0]['volume_ml']=2
    assert calibrate(p,{('p',1):.8,('n',1):.2})['status']=='NONESTIMABLE_GUARDS_BASELINE_ONLY'

def test_roles_and_missing_scores_rejected():
    with pytest.raises(ValueError):metrics(patients(),{},0)
    p=patients();p[0]['role']='verifier_tune'
    with pytest.raises(ValueError):calibrate(p,{('p',1):.8,('n',1):.2})
