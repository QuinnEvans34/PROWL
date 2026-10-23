import copy
import pytest
from scripts.diagnostics.review_augmented_views import compare


def rows():
    return [dict(case_id=str(i), metrics=dict(reference_positive=i < 4,
        reference_components=int(i < 4), target_volume_mm3=float(i < 4), size_band='small',
        lesion=dict(target_voxels=int(i < 4), predicted_voxels=2, dice=.3),
        pancreas=dict(target_voxels=10, dice=.8), case_detected=i < 4, false_alarm_any=i >= 4))
        for i in range(8)]


def test_identical_rejects_practical_not_null():
    a = rows()
    r = compare(a, a)
    assert r['decision'] == 'rejected'
    assert r['null_hypothesis'] == 'not_rejected'
    assert r['metrics']['dice']['ci95'] == [0., 0.]


def test_improvement_and_guard_failure_distinct_from_null():
    a = rows(); b = copy.deepcopy(a)
    for r in b[:4]: r['metrics']['lesion']['dice'] += .1
    assert compare(a, b)['decision'] == 'accepted'
    b[-1]['metrics']['lesion']['predicted_voxels'] += 1
    result = compare(a, b)
    assert result['decision'] == 'rejected'
    assert result['null_hypothesis'] == 'rejected'
    assert not result['guardrails']['empty_voxel_burden']


def test_order_invariant_and_invalid_references_refused():
    a = rows(); b = copy.deepcopy(a)
    assert compare(a, b) == compare(a[::-1], b[::-1])
    b[0]['metrics']['lesion']['target_voxels'] += 1
    with pytest.raises(AssertionError): compare(a, b)
    with pytest.raises(AssertionError): compare(a, a[:-1])
