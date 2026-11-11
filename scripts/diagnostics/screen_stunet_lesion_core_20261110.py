"""Bounded, reference-blind candidate rules on saved native margin decisions."""
import argparse
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.diagnostics.audit_stunet_selected_dice_20261110 import (
    RESULT_SHA, REQUEST_SHA, SELECTED, STUDY, admitted_cases, read, sha,
)

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from src.inference.stunet_margin_screen_20261110 import STRUCTURE, components, policies, retained, unpack

PROTOCOL = ROOT/'docs/capstone/evaluation/STUNET-24K-CONFIDENT-CORE-PROTOCOL-20261110.json'
TOL = 1e-12


def flat_coordinates(indices, shape):
    return np.column_stack(np.unravel_index(indices, shape))


def core_support(code, affine, *, trim_levels, grow_radii):
    """Only prediction data enter this function. All changes are lesion ↔ background."""
    pred, labels, info = components(code, .5, affine)
    del pred
    keep = retained(info, policies()[SELECTED])
    baseline = np.flatnonzero(keep[labels])
    flat = code.reshape(-1)
    tiers = flat[baseline]//2
    if (tiers < 2).any():
        raise ValueError('Incumbent candidate tier mismatch')
    coords = flat_coordinates(baseline, code.shape)
    core = tiers >= 4  # lesion wins at -.5, the incumbent's exact seed decision
    basis = np.asarray(affine)[:3,:3]
    distances = np.full(len(baseline), np.inf)
    weak = tiers <= max(trim_levels)
    ids = labels.reshape(-1)[baseline]
    del labels
    for component in np.unique(ids[weak]):
        in_component = ids == component
        seeds = in_component & core
        queried = in_component & weak
        if not seeds.any():
            raise ValueError('Retained component has no confident core')
        distances[queried] = cKDTree(coords[seeds] @ basis.T).query(coords[queried] @ basis.T, workers=1)[0]

    # Direct 26-neighbors of a retained core, only if lesion wins at +1 but
    # not +.5 and the fallback label is background (packed value exactly 2).
    # Translation cancels in affine distances. No shared or reference mask.
    shell = {r:[] for r in grow_radii}
    core_coords = coords[core]
    shape = np.array(code.shape)
    for shift in product((-1,0,1), repeat=3):
        if shift == (0,0,0) or not len(core_coords):
            continue
        d = float(np.linalg.norm(basis @ shift))
        radii = [r for r in grow_radii if d <= r]
        if not radii:
            continue
        points = core_coords + shift
        points = points[((points >= 0) & (points < shape)).all(axis=1)]
        indices = np.ravel_multi_index(points.T, code.shape)
        indices = indices[flat[indices] == 2]
        for r in radii:
            shell[r].append(indices)
    shells = {r:np.unique(np.concatenate(chunks)) if chunks else np.empty(0,dtype=np.intp)
              for r,chunks in shell.items()}
    return baseline, tiers, distances, shells


def candidate_name(tier, trim_mm, grow_mm):
    return f'tier{tier}_trim{trim_mm:g}mm_grow{grow_mm:g}mm'


def score(indices, truth_ids):
    labels = truth_ids[indices]
    return dict(p=int(len(indices)), t=int(np.count_nonzero(labels)),
                hits=[int(x) for x in np.unique(labels) if x])


def evaluate(case, receipt, protocol):
    import nibabel as nib
    from src.data.segmenter_content_v1 import target_content
    affine = np.asarray(case['native_affine'])
    source = case['sources']['lesion']
    if sha(source['path']) != source['sha256']:
        raise ValueError('Admitted reference hash changed')
    image = nib.load(source['path'])
    if list(image.shape) != case['native_shape'] or not np.allclose(image.affine, affine, rtol=0, atol=1e-5):
        raise ValueError('Admitted reference geometry changed')
    lesion, _ = target_content(image.dataobj.get_unscaled(),
        dict(slope=float(image.dataobj.slope),intercept=float(image.dataobj.inter)))
    truth, reference_count = ndimage.label(lesion, structure=STRUCTURE)
    truth = truth.reshape(-1)
    n = int(np.count_nonzero(lesion))
    del lesion
    artifact = receipt['artifact']
    if sha(artifact['backup']) != artifact['sha256']:
        raise ValueError('Independent prediction archive hash changed')
    with np.load(artifact['backup'], allow_pickle=False) as saved:
        code = unpack(saved['packed'], [int(x) for x in saved['shape']])
    if list(code.shape) != case['native_shape']:
        raise ValueError('Native prediction shape changed')
    levels, trim, grow = (protocol[k] for k in ('trim_max_tier','trim_radius_mm','growth_radius_mm'))
    indices, tiers, dist, shells = core_support(code, affine, trim_levels=levels, grow_radii=grow)
    baseline = score(indices, truth)
    old = receipt['policies'][SELECTED]
    voxel_mm3 = abs(float(np.linalg.det(affine[:3,:3])))
    if (old['lesion']['target_voxels'] != n or old['reference_components'] != reference_count or
            voxel_mm3 != old['voxel_mm3'] or
            baseline != dict(p=old['lesion']['predicted_voxels'],t=old['lesion']['true_positive'],
                             hits=old['hit_component_ids'])):
        raise ValueError('Incumbent replay did not exactly match the verified receipt')

    result = {'incumbent':baseline}
    added = {r:score(shells[r], truth) for r in grow}
    for level,radius in product(levels,trim):
        surviving = score(indices[(tiers > level) | (dist <= radius)], truth)
        for grow_mm in grow:
            extra = added[grow_mm]
            result[candidate_name(level,radius,grow_mm)] = dict(
                p=surviving['p']+extra['p'], t=surviving['t']+extra['t'],
                hits=sorted(set(surviving['hits']) | set(extra['hits'])),
                dropped_voxels=baseline['p']-surviving['p'], dropped_tp=baseline['t']-surviving['t'],
                added_voxels=extra['p'], added_tp=extra['t'])
    return dict(case_id=case['case_id'], n=n, reference_count=reference_count, voxel_mm3=voxel_mm3,
                small=bool(n and n*voxel_mm3 < 1000), arms=result)


def summarize(rows):
    positive = [r for r in rows if r['n']]
    empty = [r for r in rows if not r['n']]
    small = [r for r in positive if r['small']]
    if (len(rows),len({r['case_id'] for r in rows}),len(positive),len(empty),len(small),
            sum(r['reference_count'] for r in rows)) != (70,70,36,34,5,45):
        raise ValueError('Fixed development denominators changed')
    names = set(rows[0]['arms'])
    if len(names) != 19 or any(set(r['arms']) != names for r in rows):
        raise ValueError('Expected exactly 18 candidate policies plus incumbent')
    def metrics(name):
        def recall(rs):
            return mean(r['arms'][name]['t']/r['n'] for r in rs)
        def fp(rs):
            return sum((r['arms'][name]['p']-r['arms'][name]['t'])*r['voxel_mm3']/1000 for r in rs)
        return dict(dice=mean(2*r['arms'][name]['t']/(r['n']+r['arms'][name]['p']) for r in positive),
                    recall=recall(positive), small_recall=recall(small),
                    tp=sum(r['arms'][name]['t'] for r in positive),
                    detected_cases=sum(bool(r['arms'][name]['hits']) for r in positive),
                    detected_components=sum(len(r['arms'][name]['hits']) for r in positive),
                    empty_alarms=sum(r['arms'][name]['p']>0 for r in empty),
                    fp_ml=fp(rows), positive_fp_ml=fp(positive), empty_fp_ml=fp(empty))
    base = metrics('incumbent')
    arms = {}
    for name in sorted(names-{'incumbent'}):
        m = metrics(name)
        changes = [r['arms'][name] for r in rows]
        lost = sum(len(set(r['arms']['incumbent']['hits'])-set(r['arms'][name]['hits'])) for r in positive)
        lost_cases = sum(bool(r['arms']['incumbent']['hits']) and not r['arms'][name]['hits'] for r in positive)
        checks = dict(dice_improved=m['dice']>base['dice']+TOL,
            recall_non_decrease=m['recall']>=base['recall']-TOL,
            small_recall_non_decrease=m['small_recall']>=base['small_recall']-TOL,
            total_tp_non_decrease=m['tp']>=base['tp'], no_lost_case_or_component=not (lost or lost_cases),
            empty_alarm_nonincrease=m['empty_alarms']<=base['empty_alarms'],
            fp_nonincrease=m['fp_ml']<=base['fp_ml']+TOL,
            positive_fp_nonincrease=m['positive_fp_ml']<=base['positive_fp_ml']+TOL,
            empty_fp_nonincrease=m['empty_fp_ml']<=base['empty_fp_ml']+TOL,
            pancreas_labels_unchanged=True)
        arms[name] = dict(metrics=m, checks=checks, passes=all(checks.values()),
            lost_components=lost,lost_cases=lost_cases,
            positive_cases_with_lower_recall=sum(r['arms'][name]['t']<r['arms']['incumbent']['t'] for r in positive),
            **{k:sum(c[k] for c in changes) for k in ('dropped_voxels','dropped_tp','added_voxels','added_tp')})
    ranked = sorted(arms, key=lambda name:(-arms[name]['metrics']['dice'],name))
    selected = next((name for name in ranked if arms[name]['passes']),'incumbent')
    return dict(incumbent=base, candidates=arms, highest_new_dice=ranked[0],
                selected=selected, qualified_count=sum(x['passes'] for x in arms.values()),
                distinct_new_metric_vectors=len({tuple(x['metrics'].values()) for x in arms.values()}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--producer-sha256',required=True)
    parser.add_argument('--protocol-sha256',required=True)
    args = parser.parse_args()
    script = Path(__file__).resolve()
    def verify():
        if sha(script) != args.producer_sha256 or sha(PROTOCOL) != args.protocol_sha256:
            raise ValueError('Frozen producer or protocol changed')
    verify()
    protocol = read(PROTOCOL)
    if (protocol['trim_max_tier'],protocol['trim_radius_mm'],protocol['growth_radius_mm']) != ([2,3],[4,8,16],[0,1.5,3]):
        raise ValueError('Frozen 18-candidate grid changed')
    cases, receipts = admitted_cases()
    rows = []
    for case in cases:
        rows.append(evaluate(case,receipts[case['case_id']],protocol))
        print(json.dumps(dict(event='case_verified',completed=len(rows))),flush=True)
    result = summarize(rows)
    saved = read(STUDY/'result.json')['policies'][SELECTED]
    base = result['incumbent']
    for key, old in (('dice','positive_macro_dice'),('recall','positive_macro_recall'),
                     ('small_recall','small_case_macro_recall'),('fp_ml','false_positive_mL'),
                     ('empty_alarms','empty_alarm_cases')):
        if abs(base[key]-saved[old]) > TOL:
            raise ValueError('Cohort incumbent mismatch: '+key)
    verify()
    with args.output.open('x') as f:
        json.dump(dict(result, rows=rows, primary_request_sha256=REQUEST_SHA,
            primary_result_sha256=RESULT_SHA, producer_sha256=args.producer_sha256,
            protocol_sha256=args.protocol_sha256, gpu_calls=0, ct_voxel_reads=0, training_updates=0),
            f, indent=2,allow_nan=False)
        f.write('\n')


if __name__ == '__main__':
    main()
