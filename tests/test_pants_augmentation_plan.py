"""Portable consistency checks for the prospective plan; no private data or jobs."""
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'docs/capstone/operations/PANTS-AUGMENTED-VIEWS-24K-20261017.json'


def load():
    return json.loads(PLAN.read_text(encoding='utf-8'))


def test_plan_is_not_launch_authority_or_a_completed_experiment():
    p = load()
    assert p['experiment_id'] == 'CAP-EXP-019'
    assert p['status'] == 'specified_implementation_and_qualification_pending'
    assert p['launch_ready'] is False and p['training_started'] is False
    assert (ROOT / p['specification']).is_file()
    assert len(p['launch_requirements']) == 8


def test_fixed_cohort_and_budget():
    p = load(); c = p['cohort']; r = p['fixed_recipe']
    assert c['train'] == c['positive_train'] + c['reference_empty_train'] == 1333
    assert c['development'] == c['positive_development'] + c['reference_empty_development'] == 70
    assert len(set(c['excluded_development'])) == 5
    assert all(c[k] is False for k in ('panorama', 'test_evaluation', 'duplicate_audit_repeated', 'cache_rebuild'))
    assert r['max_updates'] == r['lr_horizon_steps'] == 24000
    assert r['warmup_steps'] == 500 and r['tensor_shape'] == [144]*3
    assert all(r[k] is False for k in ('ema', 'encoder_freeze', 'postprocessing', 'tta'))
    assert p['evaluation']['selection_opportunities'] == r['max_updates']//2000


def test_augmentation_is_train_only_and_preserves_cached_source():
    a = load()['augmentation']
    assert a['roles'] == ['train_optimizer_only']
    assert a['source_cache_mutation'] is False
    assert a['rotation_spatial_axes'] == [0, 1] and a['rotation_k_uniform'] == [1, 2, 3]
    assert a['clip'] == [0, 1]
    assert a['flip_probability_per_axis'] == [.2]*3
    for k in ('rotation_probability', 'intensity_scale_probability', 'intensity_shift_probability', 'noise_probability'):
        assert 0 < a[k] < 1
    assert a['noise_standard_deviation'] == .01
    assert a['order'][-1] == 'clip_and_zero_padding'


def test_primary_and_guardrails_are_distinct_from_the_record():
    p = load(); h = p['hypotheses']; e = p['evaluation']; c = p['control']
    assert h['H0'] == 'delta <= 0' and h['H1'] == 'delta > 0'
    assert h['minimum_practical_gain'] == .02
    assert c['selected_native_dice'] + h['minimum_practical_gain'] > h['current_descriptive_record']
    assert e['guardrails'] == dict(case_detection_delta_min=-.03, empty_alarm_delta_max=.03,
                                   pancreas_dice_delta_min=-.02, empty_predicted_voxel_total_delta_max=0)
    assert c['selected_empty_predicted_voxels'] == 205564
    assert e['bootstrap_samples'] == 10000 and e['bootstrap_seed'] == 20261017


@pytest.mark.parametrize('section,key', [
    ('control', 'configuration_sha256'), ('control', 'matched_native_reports_sha256'),
    ('control', 'selected_checkpoint_sha256'), ('cohort', 'matched_development_sha256'),
    ('fixed_recipe', 'initialization_sha256'),
])
def test_parent_pins_are_explicit(section, key):
    assert re.fullmatch('[0-9a-f]{64}', load()[section][key])


def test_no_automatic_retry_or_unbounded_compute():
    r = load()['resources']
    assert r['max_seconds'] == 30*60*60 and r['ac_required'] is True
    assert r['automatic_retry_or_resume'] is False and r['scheduled_AI_checks'] is False
    assert r['maximum_qualification_producer_updates'] == 4
    assert r['maximum_qualification_cold_updates'] == 1
