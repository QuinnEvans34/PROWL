import numpy as np
import pytest
from copy import deepcopy

from src.inference.stunet_margin_screen_20261110 import encode
from src.inference.stunet_voxel_clip_20261110 import clip_prediction
from src.inference.stunet_voxel_clip_20261110 import summarize
from src.inference.component_proximity_filter_v1 import filter_prediction


def test_clips_attached_overextension_that_component_filter_retains():
    raw = np.zeros((10, 2, 2), np.uint8)
    raw[0, 0, 0] = 1
    raw[1:9, 0, 0] = 2
    code = encode(np.eye(3, dtype=np.float32)[raw].transpose(3, 0, 1, 2))
    whole, _ = filter_prediction(raw, np.eye(4), maximum_distance_mm=5.)
    clipped, proof = clip_prediction(code, np.eye(4), bias=0., radius_mm=5.)
    assert (whole == 2).sum() == 8
    assert (clipped == 2).sum() == 5
    assert proof['removed_voxels'] == 3
    assert clipped[0, 0, 0] == 1


def test_sheared_affine_and_no_pancreas_fallback():
    raw = np.zeros((3, 4, 2), np.uint8); raw[0, 0, 0] = 1; raw[0, 2, 0] = 2
    code = encode(np.eye(3, dtype=np.float32)[raw].transpose(3, 0, 1, 2))
    affine = np.eye(4); affine[0, 1] = 3.
    clipped, _ = clip_prediction(code, affine, bias=0., radius_mm=5.)
    assert clipped[0, 2, 0] == 0  # world distance sqrt(6²+2²), not index distance2.
    raw[0, 0, 0] = 0
    code = encode(np.eye(3, dtype=np.float32)[raw].transpose(3, 0, 1, 2))
    clipped, proof = clip_prediction(code, affine, bias=0., radius_mm=5.)
    np.testing.assert_array_equal(clipped, raw)
    assert proof['context_available'] is False
    with pytest.raises(ValueError):
        clip_prediction(code, affine, bias=0., radius_mm=float('nan'))


def test_secondary_selection_keeps_full_denominators_and_component_id_guards():
    rows = []
    for i in range(70):
        positive = i < 36
        n, p, tp = (100, 100, 50) if positive else (0, 10, 0)
        raw = dict(lesion=dict(target_voxels=n, predicted_voxels=p, true_positive=tp,
                               dice=2*tp/(n+p) if n+p else None),
            pancreas=dict(dice=.8), reference_positive=positive,
            target_volume_mm3=n*(1 if i < 5 else 100), voxel_mm3=1. if i < 5 else 100.,
            reference_components=2 if i < 9 else 1 if positive else 0,
            detected_components=1 if positive else 0, hit_component_ids=[1] if positive else [],
            case_detected=positive, false_alarm_any=not positive)
        arms = {'raw':raw}
        for bias in (0., .5):
            for radius in (5., 10., 20.):
                candidate = deepcopy(raw)
                if positive:
                    candidate['lesion'].update(predicted_voxels=60, dice=100/160)
                arms[f'clip_bias{bias:g}_near{radius:g}'] = candidate
        rows.append(dict(case_id=str(i), policies=arms))
    result = summarize(rows)
    assert result['guards']['clip_bias0_near5']['passes']
    rows[0]['policies']['clip_bias0_near5'].update(hit_component_ids=[], detected_components=0, case_detected=False)
    result = summarize(rows)
    assert not result['guards']['clip_bias0_near5']['passes']
    assert result['guards']['clip_bias0_near5']['lost_cases'] == ['0']
    with pytest.raises(ValueError, match='census'):
        summarize(rows[:-1])
