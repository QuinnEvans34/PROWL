"""CPU saved-mask component audit; reference overlap is for scoring only."""
from statistics import mean

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

RULES = ('raw', 'near_predicted_pancreas_10mm', 'at_least_100mm3', 'both')


def world(indices, affine):
    return np.asarray(indices) @ affine[:3, :3].T + affine[:3, 3]


def inspect(prediction, lesion, affine, raw):
    if prediction.shape != lesion.shape or prediction.ndim != 3:
        raise ValueError('Native shape mismatch')
    if not np.isin(prediction, [0, 1, 2]).all() or not np.isin(lesion, [0, 1]).all():
        raise ValueError('Invalid labels')
    affine = np.asarray(affine, dtype=float)
    volume = abs(float(np.linalg.det(affine[:3, :3])))
    if not np.isfinite(affine).all() or volume <= 0:
        raise ValueError('Invalid affine')
    guess = prediction == 2
    labels, count = ndimage.label(guess, structure=np.ones((3, 3, 3)))
    reference, nref = ndimage.label(lesion, structure=np.ones((3, 3, 3)))
    coords = np.argwhere(guess)
    ids = labels[guess]
    truth_ids = reference[guess]
    sizes = np.bincount(ids, minlength=count+1)
    tp = np.bincount(ids[truth_ids > 0], minlength=count+1)
    hits = {i: set() for i in range(1, count+1)}
    for a, b in np.unique(np.column_stack((ids[truth_ids > 0], truth_ids[truth_ids > 0])), axis=0):
        hits[int(a)].add(int(b))
    pancreas = np.argwhere(prediction == 1)
    distances = np.full(count+1, np.inf)
    if len(pancreas) and len(coords):
        tree = cKDTree(world(pancreas, affine))
        nearest = tree.query(world(coords, affine), workers=1)[0]
        np.minimum.at(distances, ids, nearest)
    records = [dict(component_id=i, voxels=int(sizes[i]), volume_mm3=float(sizes[i]*volume),
        true_positive_voxels=int(tp[i]), false_positive_voxels=int(sizes[i]-tp[i]),
        min_predicted_pancreas_center_distance_mm=float(distances[i]) if np.isfinite(distances[i]) else None,
        reference_hit_ids=sorted(hits[i])) for i in range(1, count+1)]
    n = int(lesion.sum())
    policies = {}
    for rule in RULES + ('oracle_remove_reference_disjoint_components',):
        def retain(r):
            # No pancreas prediction: fail open, never delete solely for absent context.
            near = r['min_predicted_pancreas_center_distance_mm'] is None or r['min_predicted_pancreas_center_distance_mm'] <= 10.
            large = r['volume_mm3'] >= 100.
            return {'raw': True, 'near_predicted_pancreas_10mm': near,
                    'at_least_100mm3': large, 'both': near and large,
                    'oracle_remove_reference_disjoint_components': r['true_positive_voxels'] > 0}[rule]
        retained = [r for r in records if retain(r)]
        p = sum(r['voxels'] for r in retained)
        t = sum(r['true_positive_voxels'] for r in retained)
        hit_ids = sorted({i for r in retained for i in r['reference_hit_ids']})
        policies[rule] = dict(lesion=dict(target_voxels=n, predicted_voxels=p, true_positive=t,
            dice=2*t/(n+p) if n+p else None), pancreas=raw['pancreas'], reference_positive=bool(n),
            case_detected=bool(hit_ids), reference_components=int(nref), detected_components=len(hit_ids),
            hit_component_ids=hit_ids, predicted_components=len(retained), voxel_mm3=volume,
            target_volume_mm3=n*volume, false_alarm_any=not n and p > 0)
    if policies['raw']['lesion'] != raw['lesion'] or policies['raw']['reference_components'] != raw['reference_components']:
        raise ValueError('Saved raw reference/count drift')
    return dict(components=records, policies=policies, predicted_pancreas_present=bool(len(pancreas)))


def summarize(rows, *, require_full=True):
    if len({r['case_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate cases')
    if require_full and (len(rows) != 70 or sum(r['policies']['raw']['reference_positive'] for r in rows) != 36
                         or sum(r['policies']['raw']['reference_components'] for r in rows) != 45):
        raise ValueError('Incomplete fixed development cohort')
    result = {}
    for rule in RULES + ('oracle_remove_reference_disjoint_components',):
        metrics = [r['policies'][rule] for r in rows]
        pos = [m for m in metrics if m['reference_positive']]
        small = [m for m in pos if m['target_volume_mm3'] < 1000]
        result[rule] = dict(positive_macro_dice=mean(m['lesion']['dice'] for m in pos),
            positive_macro_recall=mean(m['lesion']['true_positive']/m['lesion']['target_voxels'] for m in pos),
            small_case_macro_recall=mean(m['lesion']['true_positive']/m['lesion']['target_voxels'] for m in small) if small else None,
            pancreas_macro_dice=mean(m['pancreas']['dice'] for m in metrics),
            detected_cases=sum(m['case_detected'] for m in pos),
            detected_components=sum(m['detected_components'] for m in pos),
            empty_alarm_cases=sum(m['false_alarm_any'] for m in metrics),
            false_positive_voxels=sum(m['lesion']['predicted_voxels']-m['lesion']['true_positive'] for m in metrics),
            false_positive_mL=sum((m['lesion']['predicted_voxels']-m['lesion']['true_positive'])*m['voxel_mm3']/1000 for m in metrics))
    guards = {}
    a = result['raw']
    for rule in RULES[1:]:
        b = result[rule]
        lost_cases = [r['case_id'] for r in rows if r['policies']['raw']['case_detected'] and not r['policies'][rule]['case_detected']]
        lost_components = [dict(case_id=r['case_id'], component_id=i) for r in rows
            for i in sorted(set(r['policies']['raw']['hit_component_ids'])-set(r['policies'][rule]['hit_component_ids']))]
        checks = dict(dice_gain_at_least_02=b['positive_macro_dice']-a['positive_macro_dice'] >= .02-1e-12,
            no_lost_cases=not lost_cases, no_lost_components=not lost_components,
            small_recall_unchanged=b['small_case_macro_recall'] is not None and b['small_case_macro_recall'] >= a['small_case_macro_recall']-1e-12,
            overall_recall_within_01=b['positive_macro_recall'] >= a['positive_macro_recall']-.01-1e-12,
            pancreas_dice_within_01=b['pancreas_macro_dice'] >= a['pancreas_macro_dice']-.01-1e-12,
            empty_alarms_nonincrease=b['empty_alarm_cases'] <= a['empty_alarm_cases'],
            fp_volume_nonincrease=b['false_positive_mL'] <= a['false_positive_mL']+1e-12)
        guards[rule] = dict(checks=checks, passes=all(checks.values()), lost_cases=lost_cases, lost_components=lost_components)
    groups = {}
    for row in rows:
        for c in row['components']:
            near = c['min_predicted_pancreas_center_distance_mm']
            kind = 'overlaps_reference' if c['true_positive_voxels'] else 'reference_disjoint'
            band = 'unknown' if near is None else 'near_le10mm' if near <= 10 else 'far_gt10mm'
            g = groups.setdefault(kind+'/'+band, dict(components=0, true_positive_voxels=0, false_positive_voxels=0, false_positive_mL=0.))
            g['components'] += 1
            for key in ('true_positive_voxels', 'false_positive_voxels'):
                g[key] += c[key]
            g['false_positive_mL'] += c['false_positive_voxels']*row['policies']['raw']['voxel_mm3']/1000
    return dict(policies=result, guards=guards, component_groups=groups,
                policy_deployment='None; exploratory exposed-development analysis only')
