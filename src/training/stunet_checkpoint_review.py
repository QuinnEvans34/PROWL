"""Compare saved native STU-Net metrics on matched development cases."""

from collections import Counter
from math import isfinite
import re

import numpy as np

from src.training.native_error_review_v1 import (
    case_error, check_pair, close, group_summary, integer, mean, require, validate_report,
)


SCOPE = 'native_development_provided_pancreas'
RAW = 'raw'
FIXED_5MM = 'predicted-pancreas-proximity-5mm-v1'
SOURCE_SCOPE = 'provided_pancreas_region_exploratory'
SOURCES = {'ct', 'pancreas', 'lesion'}


def case_index(rows):
    index = {row['case_id']: row for row in rows}
    require(len(rows) == len(index) and all(isinstance(key, str) and key for key in index),
            'Duplicate or invalid case IDs')
    return index


def case_identity(row):
    shape, affine = row['native_shape'], np.asarray(row['native_affine'], dtype=float)
    require(len(shape) == 3 and all(integer(n) and n > 0 for n in shape), 'Invalid native shape')
    require(affine.shape == (4, 4) and np.isfinite(affine).all()
            and np.array_equal(affine[3], [0, 0, 0, 1]), 'Invalid native affine')
    volume = abs(float(np.linalg.det(affine[:3, :3])))
    require(isfinite(volume) and volume > 0, 'Invalid native affine volume')
    sources = row['source_sha256']
    require(set(sources) == SOURCES and all(isinstance(v, str) and re.fullmatch('[0-9a-f]{64}', v)
                                           for v in sources.values()), 'Invalid native source hashes')
    tiles = row['tiles'] if 'tiles' in row else row['profile']['tiles']
    require(integer(tiles) and tiles > 0, 'Invalid native tile count')
    return dict(shape=shape, affine=affine.tolist(), sources=sources, volume=volume, tiles=tiles)


def validate_ids(ids, count, kind):
    require(isinstance(ids, list) and all(integer(i) and 1 <= i <= count for i in ids)
            and len(set(ids)) == len(ids), f'Invalid {kind} component IDs')
    return set(ids)


def validate_saved(report, identities, policy):
    require(policy in (RAW, FIXED_5MM), 'Unsupported scoring policy')
    require(report.get('policy', policy) == policy, 'Report scoring policy mismatch')
    require(report.get('scope', SOURCE_SCOPE) in (SOURCE_SCOPE, SCOPE), 'Unexpected native inference scope')
    identity = {key: case_identity(row) for key, row in case_index(identities).items()}
    require(len(identity) == 70, 'The 70-case frozen development cohort is required')
    rows = []
    for key, row in case_index(report['cases']).items():
        require(key in identity and row['tiles'] == identity[key]['tiles'] and row['gaps'] == 0,
                'Case identity, tiles or reconstruction gaps differ')
        require(row.get('scope', SOURCE_SCOPE) in (SOURCE_SCOPE, SCOPE)
                and row.get('step', report['step']) == report['step'], 'Case scope or step mismatch')
        m = row['metrics']
        require(close(m['voxel_mm3'], identity[key]['volume']), 'Metric voxel volume differs from native affine')
        if 'policy_applied' in m:
            require(m['policy_applied'] is None if policy == RAW else type(m['policy_applied']) is bool,
                    'Case scoring policy mismatch')
        if policy == FIXED_5MM:
            require(type(m.get('policy_applied')) is bool, 'Fixed 5 mm application status is required')
        if 'hit_ids' in m:
            hits = validate_ids(m['hit_ids'], m['reference_components'], 'hit')
            require(len(hits) == m['detected_components'], 'Hit IDs and component count differ')
        if 'small_ids' in row:
            validate_ids(row['small_ids'], m['reference_components'], 'small')
        rows.append(dict(row, scope=SCOPE, step=report['step']))
    normalized = dict(report, cases=rows, scope=SCOPE)
    if 'summary' in report:
        summary = report['summary']
        normalized['lesion_positive_macro_dice'] = summary['lesion_dice']
        require(summary['positive'] == 36 and summary['empty'] == 34, 'Report cohort totals differ')
        for key, metric in [('detected', 'case_detected'), ('alarms', 'false_alarm_any')]:
            if key in summary:
                require(summary[key] == sum(row['metrics'][metric] for row in rows),
                        'Report case totals differ')
    index = validate_report(normalized, identity)
    require(sum(row['metrics']['reference_components'] for row in rows) == 45,
            'The 45-component frozen reference cohort is required')
    return index, identity


def arm_summary(rows):
    metrics = [row['metrics'] for row in rows]
    errors = [case_error(row) for row in rows]
    small = [error for error in errors if error['size_band'] == 'small']
    result = group_summary(errors)
    result.update(
        reference_components=sum(error['components'] for error in errors),
        detected_components=sum(error['components_detected'] for error in errors),
        total_false_positive_mL=sum(error['false_positive_mL'] for error in errors),
        pancreas_macro_dice=mean([m['pancreas']['dice'] for m in metrics if m['pancreas']['dice'] is not None]),
        small_volume_cases=group_summary(small),
        small_volume_case_components=sum(error['components'] for error in small),
        small_volume_case_components_detected=sum(error['components_detected'] for error in small),
        fixed_5mm_unapplied_cases=sum(m.get('policy_applied') is False for m in metrics),
    )
    return result


def component_changes(baseline, candidate):
    if not all('hit_ids' in row['metrics'] for arm in (baseline, candidate) for row in arm.values()):
        return dict(status='unavailable_missing_reference_hit_ids')
    size_available = all('small_ids' in row for arm in (baseline, candidate) for row in arm.values())
    gained, lost = [], []
    small_total = small_before = small_after = 0
    for key, old in baseline.items():
        new = candidate[key]
        before, after = (set(row['metrics']['hit_ids']) for row in (old, new))
        if 'small_ids' in old and 'small_ids' in new:
            require(set(old['small_ids']) == set(new['small_ids']), 'Small reference component identity mismatch')
        small = set(old['small_ids']) if size_available else None
        for results, changes in ((gained, after - before), (lost, before - after)):
            results.extend(dict(case_id=key, component_id=i, under_1mL=None if small is None else i in small)
                           for i in sorted(changes))
        if size_available:
            small_total += len(small)
            small_before += len(small & before)
            small_after += len(small & after)
    small_result = (dict(status='available', reference_components=small_total, baseline_hits=small_before,
                         candidate_hits=small_after) if size_available else dict(status='unavailable_missing_sizes'))
    return dict(status='available', gained=gained, lost=lost, small_components=small_result)


def compare_checkpoints(baseline, candidate, baseline_identities, candidate_identities, *, policy):
    a, ai = validate_saved(baseline, baseline_identities, policy)
    b, bi = validate_saved(candidate, candidate_identities, policy)
    require(ai == bi, 'Cohort, native geometry, tiles or source hashes differ')
    require(candidate['step'] >= baseline['step'], 'Checkpoint order must be chronological')
    check_pair(a, b)
    groups = {(False, True): 'new_overlap', (True, False): 'lost_overlap',
              (True, True): 'overlap_both', (False, False): 'zero_overlap_both'}
    transitions = Counter({name: 0 for name in groups.values()})
    pairs = []
    for key in sorted(a):
        old, new = case_error(a[key]), case_error(b[key])
        positive = old['target_voxels'] > 0
        group = groups[old['case_detected'], new['case_detected']] if positive else 'reference_empty'
        if positive:
            transitions[group] += 1
        pairs.append(dict(case_id=key, group=group, size_band=old['size_band'],
                          baseline_dice=old['dice'], candidate_dice=new['dice'],
                          dice_delta=new['dice'] - old['dice'] if positive else None,
                          true_positive_voxels_delta=new['true_positive'] - old['true_positive'],
                          false_positive_voxels_delta=new['false_positive'] - old['false_positive'],
                          false_positive_mL_delta=new['false_positive_mL'] - old['false_positive_mL']))
    return dict(scope='exploratory_exposed_development', policy=policy, baseline_step=baseline['step'],
                candidate_step=candidate['step'], baseline=arm_summary(list(a.values())),
                candidate=arm_summary(list(b.values())), overlap_transitions=dict(transitions),
                cases_with_more_fp=sum(row['false_positive_voxels_delta'] > 0 for row in pairs),
                component_changes=component_changes(a, b), cases=pairs)
