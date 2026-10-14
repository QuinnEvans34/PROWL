"""Development-only native metrics for the preregistered PanTS course-reference run."""
import numpy as np
from scipy import ndimage
from src.data.source_inventory_records import require


def native_metrics(prediction, pancreas, lesion, affine):
    require(prediction.shape == pancreas.shape == lesion.shape and prediction.ndim == 3,
            'Native grids differ')
    require(np.isin(prediction, [0, 1, 2]).all() and np.isin(pancreas, [0, 1]).all()
            and np.isin(lesion, [0, 1]).all(), 'Invalid native labels')
    voxel_mm3 = abs(float(np.linalg.det(np.asarray(affine)[:3, :3])))
    require(np.isfinite(voxel_mm3) and voxel_mm3 > 0, 'Invalid voxel volume')
    target = np.where(lesion, 2, pancreas).astype(np.uint8)
    result = {}
    for label, code in [('pancreas', 1), ('lesion', 2)]:
        truth, guess = target == code, prediction == code
        n, p, tp = int(truth.sum()), int(guess.sum()), int((truth & guess).sum())
        result[label] = dict(target_voxels=n, predicted_voxels=p, true_positive=tp,
            dice=2*tp/(n+p) if n+p else None)
    guess = prediction == 2
    components, count = ndimage.label(lesion, structure=np.ones((3, 3, 3)))
    hits = np.unique(components[guess]); hits = hits[hits != 0]
    _, predicted_components = ndimage.label(guess, structure=np.ones((3, 3, 3)))
    volume = result['lesion']['target_voxels'] * voxel_mm3
    predicted_volume = result['lesion']['predicted_voxels'] * voxel_mm3
    result.update(reference_positive=bool(volume), case_detected=bool(len(hits)),
        reference_components=int(count), detected_components=int(len(hits)),
        predicted_components=int(predicted_components), voxel_mm3=voxel_mm3,
        target_volume_mm3=volume, predicted_volume_mm3=predicted_volume,
        false_alarm_any=bool(not volume and predicted_volume),
        case_alert_50mm3=bool(predicted_volume >= 50),
        size_band='empty' if not volume else ('small' if volume < 1000 else 'medium' if volume <= 10000 else 'large'))
    return result


def paired_decision(early, final):
    """Patient bootstrap; fail closed on mismatched cohort/reference definitions."""
    require(len(early) == len(final) and len({r['case_id'] for r in early}) == len(early)
            and len({r['case_id'] for r in final}) == len(final), 'Duplicate/missing cases')
    a = {r['case_id']: r['metrics'] for r in early}
    b = {r['case_id']: r['metrics'] for r in final}
    require(a.keys() == b.keys(), 'Different comparison cohorts')
    for name in a:
        require(a[name]['target_volume_mm3'] == b[name]['target_volume_mm3']
                and a[name]['reference_components'] == b[name]['reference_components'], 'Different references')
    positive = sorted(n for n in a if a[n]['reference_positive'])
    empty = sorted(n for n in a if not a[n]['reference_positive'])
    require(positive and empty, 'Both target groups required')
    dice = np.array([b[n]['lesion']['dice']-a[n]['lesion']['dice'] for n in positive])
    detection = np.array([int(b[n]['case_detected'])-int(a[n]['case_detected']) for n in positive])
    alarms = np.array([int(b[n]['false_alarm_any'])-int(a[n]['false_alarm_any']) for n in empty])
    rng = np.random.default_rng(20261011)
    stats = {}
    for key, values in [('dice', dice), ('detection', detection), ('false_alarm', alarms)]:
        draws = values[rng.integers(len(values), size=(10000, len(values)))].mean(axis=1)
        stats[key] = dict(difference=float(values.mean()), ci95=np.quantile(draws, [.025,.975]).tolist())
    accepted = dice.mean() >= .02 and stats['dice']['ci95'][0] > 0 and detection.mean() >= -.03 and alarms.mean() <= .03
    rejected = detection.mean() < -.03 or alarms.mean() > .03 or stats['dice']['ci95'][1] < .02
    return dict(status='accepted' if accepted else 'rejected' if rejected else 'inconclusive',
        positive_cases=len(positive), reference_empty_cases=len(empty), metrics=stats,
        guardrail_claim='point_estimate_guardrails_not_statistical_noninferiority')
