from copy import deepcopy
import pytest
from scripts.diagnostics.review_pants_ema_72k import compare

def cases(dice=.3):
    return [dict(case_id=str(i),metrics=dict(reference_positive=i<4,reference_components=int(i<4),
        target_volume_mm3=100 if i<4 else 0,size_band='small' if i<4 else 'empty',
        lesion=dict(dice=dice if i<4 else None,target_voxels=10 if i<4 else 0),
        pancreas=dict(dice=.8,target_voxels=100),case_detected=i<4,false_alarm_any=False)) for i in range(6)]

def test_fixed_rules():
    a=cases();same=compare(a,a,.01)
    assert same['decision']=='rejected' and same['null_hypothesis']=='not_rejected'
    better=compare(a,cases(.35),.02)
    assert better['decision']=='accepted' and better['null_hypothesis']=='rejected'
    b=cases(.35);b[0]['metrics']['case_detected']=False
    assert compare(a,b,.02)['decision']=='rejected'

@pytest.mark.parametrize('bad',['duplicate','reference','cohort'])
def test_mismatch_rejected(bad):
    a=cases();b=deepcopy(a)
    if bad=='duplicate':b.append(b[0])
    if bad=='reference':b[0]['metrics']['lesion']['target_voxels']=12
    if bad=='cohort':b[0]['case_id']='other'
    with pytest.raises(ValueError):compare(a,b,.02)

def test_pair_order_deterministic():
    a=cases();b=cases(.31)
    assert compare(a,b,.02)==compare(a[::-1],b[::-1],.02)
