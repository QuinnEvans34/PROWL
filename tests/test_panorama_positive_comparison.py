from copy import deepcopy
import pytest
from scripts.diagnostics.compare_panorama_positive import compare


def rows():
    return [dict(case_id=str(i),metrics=dict(reference_positive=i<4,target_volume_mm3=100 if i<4 else 0,
        reference_components=1 if i<4 else 0,lesion={'dice':.3 if i<4 else None},pancreas={'dice':.8},
        case_detected=i<4,false_alarm_any=False)) for i in range(8)]


def test_positive_gain_passes():
    a=rows();b=deepcopy(a)
    for r in b[:4]:r['metrics']['lesion']['dice']+=.05
    result=compare(a,b)
    assert result['status']=='accepted' and result['seed']==20261012


def test_pancreas_guardrail_rejects_despite_dice_gain():
    a=rows();b=deepcopy(a)
    for r in b[:4]:r['metrics']['lesion']['dice']+=.05
    for r in b:r['metrics']['pancreas']['dice']-=.1
    assert compare(a,b)['status']=='rejected'


def test_missing_case_rejected():
    with pytest.raises(ValueError):compare(rows(),rows()[:-1])


def test_reference_change_rejected():
    a=rows();b=deepcopy(a);b[0]['metrics']['reference_components']=2
    with pytest.raises(ValueError):compare(a,b)
