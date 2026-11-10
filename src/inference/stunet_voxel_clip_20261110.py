"""Secondary anatomy-support hypothesis, separate from the frozen54-policy study."""
import numpy as np
from scipy.spatial import cKDTree
from statistics import mean

from src.inference.stunet_margin_screen_20261110 import decode


def clip_prediction(code, affine, *, bias, radius_mm):
    """Clip individual lesion voxels, using only fixed raw predicted pancreas.

    Distances are native voxel-center distances under the entire source affine.
    Missing pancreas fails open. This may also remove true tumor tissue: never
    enable it without paired component, recall and pancreas guard evaluation.
    """
    a = np.asarray(affine, dtype=float)
    if (a.shape != (4, 4) or not np.isfinite(a).all() or
            abs(np.linalg.det(a[:3, :3])) <= 0 or not np.isfinite(radius_mm) or radius_mm < 0):
        raise ValueError('Valid full affine and nonnegative finite radius required')
    pred = decode(code, bias)
    context = np.argwhere(decode(code, 0.) == 1)
    positions = np.argwhere(pred == 2)
    if not len(context) or not len(positions):
        return pred, dict(context_available=bool(len(context)), removed_voxels=0)
    def world(x):
        return x @ a[:3, :3].T + a[:3, 3]
    distances = cKDTree(world(context)).query(world(positions), workers=1)[0]
    remove = positions[distances > radius_mm]
    pred[tuple(remove.T)] = 0
    return pred, dict(context_available=True, removed_voxels=int(len(remove)))


def summarize(rows):
    """Seven secondary arms (raw+six) with the unchanged eight utility gates."""
    keys = {'raw'} | {f'clip_bias{b:g}_near{r:g}' for b in (0., .5) for r in (5., 10., 20.)}
    if len(rows) != 70 or len({r['case_id'] for r in rows}) != 70 or any(set(r['policies']) != keys for r in rows):
        raise ValueError('Complete fixed70-case/seven-arm census required')
    metrics = {}
    for key in sorted(keys):
        arm = [r['policies'][key] for r in rows]
        positive = [m for m in arm if m['reference_positive']]
        small = [m for m in positive if m['target_volume_mm3'] < 1000]
        if (len(positive), sum(m['reference_components'] for m in arm), len(small)) != (36, 45, 5):
            raise ValueError('Reference denominators changed')
        for row in rows:
            a, b = row['policies']['raw'], row['policies'][key]
            if (a['lesion']['target_voxels'] != b['lesion']['target_voxels'] or
                    any(a[k] != b[k] for k in ('voxel_mm3', 'target_volume_mm3', 'reference_components', 'reference_positive'))):
                raise ValueError('Matched native references changed')
            n,p,t = (b['lesion'][k] for k in ('target_voxels','predicted_voxels','true_positive'))
            if not all(type(x) is int and x >= 0 for x in (n,p,t)) or t > min(n,p):
                raise ValueError('Invalid confusion counts')
            if n+p and not np.isclose(b['lesion']['dice'], 2*t/(n+p), rtol=0, atol=1e-12):
                raise ValueError('Dice arithmetic')
        metrics[key] = dict(positive_macro_dice=mean(m['lesion']['dice'] for m in positive),
            positive_macro_recall=mean(m['lesion']['true_positive']/m['lesion']['target_voxels'] for m in positive),
            small_case_macro_recall=mean(m['lesion']['true_positive']/m['lesion']['target_voxels'] for m in small),
            pancreas_macro_dice=mean(m['pancreas']['dice'] for m in arm),
            detected_cases=sum(m['case_detected'] for m in positive),
            detected_components=sum(m['detected_components'] for m in positive),
            empty_alarm_cases=sum(m['false_alarm_any'] for m in arm),
            false_positive_mL=sum((m['lesion']['predicted_voxels']-m['lesion']['true_positive'])*m['voxel_mm3']/1000 for m in arm))
    raw = metrics['raw']; guards = {}
    for key, m in metrics.items():
        if key == 'raw':
            continue
        lost_cases = [r['case_id'] for r in rows if r['policies']['raw']['case_detected'] and not r['policies'][key]['case_detected']]
        lost = [dict(case_id=r['case_id'], component_id=c) for r in rows for c in sorted(
            set(r['policies']['raw']['hit_component_ids'])-set(r['policies'][key]['hit_component_ids']))]
        checks = dict(dice_gain_at_least_02=m['positive_macro_dice']-raw['positive_macro_dice'] >= .02-1e-12,
            no_lost_cases=not lost_cases, no_lost_components=not lost,
            small_recall_unchanged=m['small_case_macro_recall'] >= raw['small_case_macro_recall']-1e-12,
            overall_recall_within_01=m['positive_macro_recall'] >= raw['positive_macro_recall']-.01-1e-12,
            pancreas_dice_within_01=m['pancreas_macro_dice'] >= raw['pancreas_macro_dice']-.01-1e-12,
            empty_alarms_nonincrease=m['empty_alarm_cases'] <= raw['empty_alarm_cases'],
            fp_volume_nonincrease=m['false_positive_mL'] <= raw['false_positive_mL']+1e-12)
        guards[key] = dict(passes=all(checks.values()), checks=checks, lost_cases=lost_cases, lost_components=lost)
    return dict(policies=metrics, guards=guards, cases=70, positive=36, empty=34, components=45,
                scope='secondary exposed-development screen; no deployment')
