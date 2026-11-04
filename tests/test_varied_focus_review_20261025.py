from copy import deepcopy
from scripts.diagnostics.review_varied_focus_20261025 import compare
import pytest


def rows(dice=.3,recall=.5):
    result=[]
    for i in range(70):
        positive=i<36
        result.append(dict(case_id=str(i),metrics=dict(reference_positive=positive,
            reference_components=int(positive),size_band='small' if positive else 'empty',
            target_volume_mm3=100 if positive else 0,predicted_volume_mm3=100,
            case_detected=positive,false_alarm_any=not positive,
            detected_components=int(positive),pancreas=dict(dice=.8,target_voxels=100),
            lesion=dict(dice=dice if positive else 0,target_voxels=100 if positive else 0,
                predicted_voxels=100,true_positive=100*recall if positive else 0))))
    return result


def test_preregistered_seed_and_positive_gain():
    r=compare(rows(),rows(.35))
    assert r['seed']==20261022 and r['null']=='reject' and r['practical']=='accept'
    assert r['ci95']==pytest.approx([.05,.05])


def test_recall_guard_rejects_despite_dice_gain():
    r=compare(rows(),rows(.35,.45))
    assert r['null']=='reject' and r['practical']=='reject'
    assert not r['guards']['positive_macro_recall']


def test_zero_gain_not_proof_of_improvement():
    r=compare(rows(),rows())
    assert r['null']=='fail_to_reject' and r['practical']=='reject'


def test_mismatched_targets_rejected():
    b=deepcopy(rows());b[0]['metrics']['lesion']['target_voxels']=101
    with pytest.raises(ValueError):compare(rows(),b)
