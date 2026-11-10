"""Finite, replayable inference-policy study; never an enabled clinical default.

Inputs are reconstructed probabilities. References enter scoring only, never the
decision functions. Positive margin bias can recover non-winning lesion voxels;
negative bias suppresses them. These scores are not calibrated probabilities.
"""
from copy import deepcopy
from statistics import mean

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

BIASES = (-1., -.5, 0., .5, 1.)
RADII = (5., 10., 20.)
VOLUMES = (0., 10., 25.)
STRUCTURE = np.ones((3, 3, 3), dtype=bool)


def policies():
    result = {'raw': dict(bias=0., radius=None, volume=0., seed=None)}
    for b in BIASES:
        if b:
            result[f'bias{b:g}_unfiltered'] = dict(bias=b, radius=None, volume=0., seed=None)
        for r in RADII:
            for v in VOLUMES:
                result[f'bias{b:g}_near{r:g}_min{v:g}'] = dict(bias=b, radius=r, volume=v, seed=None)
    for b in (.5, 1.):
        for r in (5., 10.):
            result[f'grow{b:g}_seed-0.5_near{r:g}'] = dict(bias=b, radius=r, volume=0., seed=-.5)
    return result


def encode(probabilities):
    """Four bits retain every finite bias decision, including exact tie order."""
    p = np.asarray(probabilities)
    if (p.dtype != np.float32 or p.ndim != 4 or p.shape[0] != 3
            or not np.isfinite(p).all() or (p < 0).any() or (p > 1).any()
            or not np.allclose(p.sum(0), 1., rtol=0, atol=1e-4)):
        raise ValueError('Finite normalized float32 three-class field required')
    fallback = p[:2].argmax(0).astype(np.uint8)
    nonlesion = p[:2].max(0)
    count = np.zeros(p.shape[1:], dtype=np.uint8)
    # Float64 comparison freezes the arithmetic of this post-blend decision.
    for b in BIASES:
        count += p[2].astype(np.float64) * np.exp(b) > nonlesion
    code = 2*count + fallback
    if not np.array_equal(decode(code, 0.), p.argmax(0).astype(np.uint8)):
        raise ValueError('Zero-bias argmax parity failed')
    return code


def decode(code, bias):
    if bias not in BIASES or code.dtype != np.uint8 or code.ndim != 3 or (code > 11).any():
        raise ValueError('Invalid finite margin replay')
    out = code % 2
    out[code//2 >= len(BIASES)-BIASES.index(bias)] = 2
    return out


def pack(code):
    decode(code, 0.)
    flat = code.reshape(-1)
    out = flat[::2].copy()
    out[:len(flat)//2] |= flat[1::2] << 4
    return out


def unpack(packed, shape):
    if (packed.dtype != np.uint8 or packed.ndim != 1 or len(shape) != 3
            or any(type(n) is not int or n <= 0 for n in shape)):
        raise ValueError('Invalid packed metadata')
    size = int(np.prod(shape))
    if len(packed) != (size+1)//2 or (size % 2 and packed[-1] >> 4):
        raise ValueError('Packed length/padding mismatch')
    flat = np.empty(size, dtype=np.uint8)
    flat[::2] = packed & 15
    flat[1::2] = packed[:size//2] >> 4
    code = flat.reshape(shape)
    decode(code, 0.)
    return code


def components(code, bias, affine):
    """Reference-free candidate components and fixed *raw* pancreas context."""
    affine = np.asarray(affine, dtype=float)
    if affine.shape != (4, 4) or not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3, :3])) <= 0:
        raise ValueError('Finite nonsingular full affine required')
    pred = decode(code, bias)
    labels, count = ndimage.label(pred == 2, structure=STRUCTURE)
    ids = labels[pred == 2]
    sizes = np.bincount(ids, minlength=count+1)
    raw_pancreas = np.argwhere(decode(code, 0.) == 1)
    distances = np.full(count+1, np.inf)
    if len(raw_pancreas) and len(ids):
        def world(x):
            return x @ affine[:3, :3].T + affine[:3, 3]
        nearest = cKDTree(world(raw_pancreas)).query(world(np.argwhere(pred == 2)), workers=1)[0]
        np.minimum.at(distances, ids, nearest)
    seeds = np.bincount(labels[decode(code, -.5) == 2], minlength=count+1) > 0
    return pred, labels, dict(sizes=sizes, distance=distances, seed=seeds,
        context=bool(len(raw_pancreas)), voxel_mm3=abs(float(np.linalg.det(affine[:3, :3]))))


def retained(info, policy):
    keep = np.ones(len(info['sizes']), dtype=bool)
    if policy['radius'] is not None and info['context']:
        keep &= info['distance'] <= policy['radius']
    keep &= info['sizes'] * info['voxel_mm3'] >= policy['volume']
    if policy['seed'] is not None:
        keep &= info['seed']
    keep[0] = False
    return keep


def apply(code, affine, policy):
    """Suppressed candidate lesions become background; no reference accepted."""
    pred, labels, info = components(code, policy['bias'], affine)
    keep = retained(info, policy)
    pred[(labels != 0) & ~keep[labels]] = 0
    return pred


def score_case(code, pancreas, lesion, affine, *, progress=lambda x: None):
    """Score all54 policies by exact additive component counts, not54 forwards."""
    from src.training.pants_native_evaluation import native_metrics
    if code.shape != pancreas.shape or code.shape != lesion.shape or not np.isin(lesion, [0, 1]).all():
        raise ValueError('Reference shape/labels')
    reference, count = ndimage.label(lesion, structure=STRUCTURE)
    results = {}
    settings = policies()
    for bias in BIASES:
        pred, labels, info = components(code, bias, affine)
        baseline = native_metrics(pred, pancreas, lesion, affine)
        positive = labels != 0
        tp = np.bincount(labels[positive & (lesion != 0)], minlength=len(info['sizes']))
        pairs = np.unique(np.column_stack((labels[positive & (lesion != 0)],
                                          reference[positive & (lesion != 0)])), axis=0)
        for name, policy in settings.items():
            if policy['bias'] != bias:
                continue
            keep = retained(info, policy)
            n = baseline['lesion']['target_voxels']
            p, t = int(info['sizes'][keep].sum()), int(tp[keep].sum())
            hits = sorted({int(r) for c, r in pairs if keep[c]})
            metric = deepcopy(baseline)
            metric['lesion'] = dict(target_voxels=n, predicted_voxels=p, true_positive=t,
                                    dice=2*t/(n+p) if n+p else None)
            metric.update(case_detected=bool(hits), detected_components=len(hits),
                hit_component_ids=hits, reference_components=int(count),
                predicted_components=int(keep.sum()), predicted_volume_mm3=p*info['voxel_mm3'],
                false_alarm_any=bool(not n and p), case_alert_50mm3=bool(p*info['voxel_mm3'] >= 50))
            results[name] = metric
        progress(dict(event='bias_scored', bias=bias, policies=len(results)))
    if set(results) != set(settings):
        raise ValueError('Finite policy census mismatch')
    return results


def summarize(rows, *, require_full=True):
    if len({r['case_id'] for r in rows}) != len(rows) or not rows:
        raise ValueError('Unique nonempty cases required')
    settings = policies()
    result = {}
    for name in settings:
        metrics = [r['policies'][name] for r in rows]
        pos = [m for m in metrics if m['reference_positive']]
        empty = [m for m in metrics if not m['reference_positive']]
        small = [m for m in pos if m['target_volume_mm3'] < 1000]
        if require_full and (len(rows), len(pos), len(empty), sum(m['reference_components'] for m in metrics), len(small)) != (70, 36, 34, 45, 5):
            raise ValueError('Fixed development denominators changed')
        for m in metrics:
            n, p, t = (m['lesion'][k] for k in ('target_voxels', 'predicted_voxels', 'true_positive'))
            if not all(type(x) is int and x >= 0 for x in (n, p, t)) or t > min(n, p):
                raise ValueError('Invalid confusion counts')
            if n+p and not np.isclose(m['lesion']['dice'], 2*t/(n+p), rtol=0, atol=1e-12):
                raise ValueError('Dice arithmetic mismatch')
            if (len(m['hit_component_ids']) != m['detected_components'] or
                    len(set(m['hit_component_ids'])) != len(m['hit_component_ids']) or
                    any(type(c) is not int or not 1 <= c <= m['reference_components'] for c in m['hit_component_ids']) or
                    bool(m['hit_component_ids']) != m['case_detected']):
                raise ValueError('Component identity census mismatch')
        for row in rows:
            raw, candidate = row['policies']['raw'], row['policies'][name]
            if (raw['lesion']['target_voxels'] != candidate['lesion']['target_voxels'] or
                    any(raw[k] != candidate[k] for k in ('voxel_mm3', 'target_volume_mm3', 'reference_positive', 'reference_components'))):
                raise ValueError('Matched reference changed between policies')
        def recall(group):
            return mean(m['lesion']['true_positive']/m['lesion']['target_voxels'] for m in group) if group else None
        result[name] = dict(positive_macro_dice=mean(m['lesion']['dice'] for m in pos) if pos else None,
            positive_macro_recall=recall(pos), small_case_macro_recall=recall(small),
            pancreas_macro_dice=mean(m['pancreas']['dice'] for m in metrics),
            detected_cases=sum(m['case_detected'] for m in pos),
            detected_components=sum(m['detected_components'] for m in pos),
            empty_alarm_cases=sum(m['false_alarm_any'] for m in empty),
            empty_case_specificity=1-sum(m['false_alarm_any'] for m in empty)/len(empty) if empty else None,
            false_positive_mL=sum((m['lesion']['predicted_voxels']-m['lesion']['true_positive'])*m['voxel_mm3']/1000 for m in metrics),
            false_negative_voxels=sum(m['lesion']['target_voxels']-m['lesion']['true_positive'] for m in pos))
    raw = result['raw']
    guards = {}
    for name, now in result.items():
        if name == 'raw':
            continue
        lost_cases = [r['case_id'] for r in rows if r['policies']['raw']['case_detected'] and not r['policies'][name]['case_detected']]
        lost = [dict(case_id=r['case_id'], component_id=int(c)) for r in rows for c in sorted(
            set(r['policies']['raw']['hit_component_ids'])-set(r['policies'][name]['hit_component_ids']))]
        checks = dict(dice_gain_at_least_02=now['positive_macro_dice'] is not None and now['positive_macro_dice']-raw['positive_macro_dice'] >= .02-1e-12,
            no_lost_cases=not lost_cases, no_lost_components=not lost,
            small_recall_unchanged=now['small_case_macro_recall'] is not None and now['small_case_macro_recall'] >= raw['small_case_macro_recall']-1e-12,
            overall_recall_within_01=now['positive_macro_recall'] is not None and now['positive_macro_recall'] >= raw['positive_macro_recall']-.01-1e-12,
            pancreas_dice_within_01=now['pancreas_macro_dice'] >= raw['pancreas_macro_dice']-.01-1e-12,
            empty_alarms_nonincrease=now['empty_alarm_cases'] <= raw['empty_alarm_cases'],
            fp_volume_nonincrease=now['false_positive_mL'] <= raw['false_positive_mL']+1e-12)
        guards[name] = dict(passes=all(checks.values()), checks=checks, lost_cases=lost_cases, lost_components=lost)
    eligible = [k for k, g in guards.items() if g['passes']]
    # Prospective deterministic tie-break; no checkpoint reselection.
    chosen = sorted(eligible, key=lambda k: (-result[k]['positive_macro_dice'], k))[0] if eligible else 'raw'
    return dict(policies=result, guards=guards, selected_exploratory_policy=chosen,
        selection='54 fixed policies on already exposed development; no independent efficacy or deployment claim',
        optimizer_updates=0)
