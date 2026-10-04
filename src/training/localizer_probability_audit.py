"""Fixed descriptive probability probes; no threshold selection or training API."""
import numpy as np
from src.data.source_inventory_records import require
from src.training.expanded_executor import metrics
from src.training.localizer_coverage import mapped_source_box

THRESHOLDS = (.01, .05, .10, .25, .50)
QUANTILES = (0, 1, 5, 25, 50, 75, 95, 99, 100)


def audit_probabilities(probabilities, target, transform):
    p = np.asarray(probabilities)
    y = np.asarray(target)
    require(p.shape == (2, *y.shape) and y.ndim == 3 and 0 < y.size <= 8_000_000, 'Probability grid differs')
    require(np.isfinite(p).all() and (p >= 0).all() and (p <= 1).all(), 'Invalid probability values')
    require(np.allclose(p.sum(axis=0), 1, rtol=0, atol=1e-5), 'Probabilities not normalized')
    require(np.isin(y, [0, 1]).all() and y.any(), 'Positive binary target required')
    baseline = p.argmax(axis=0).astype(np.uint8)
    reference = y.astype(bool)
    subsets = {'reference': reference, 'background': ~reference,
               'missed_reference': reference & (baseline == 0)}
    distributions = {}
    for name, mask in subsets.items():
        values = p[1][mask]
        distributions[name] = dict(count=int(values.size), quantiles=(
            dict(zip(map(str, QUANTILES), map(float, np.percentile(values, QUANTILES)))) if values.size else None))
    results = {}
    for name, threshold in [('argmax', None)] + [(str(t), t) for t in THRESHOLDS]:
        pred = baseline if threshold is None else (p[1] >= threshold).astype(np.uint8)
        m = metrics(pred, y, transform['processed_affine'])
        # Legacy padded-grid pass flags must not look like a policy recommendation.
        m.pop('pre_mapping_roi_diagnostic_pass');m.pop('fit_diagnostic_pass')
        m['source_crop_geometry'] = mapped_source_box(m['box'], **{k:transform[k] for k in (
            'processed_shape','processed_affine','source_shape','source_affine')})
        m['scan_fraction_scope'] = 'padded processed tensor; acquired size is source_crop_geometry.scan_fraction'
        results[name] = m
    return dict(distributions=distributions, operating_points=results,
                policy_selected=False, coverage_scope='processed reference; not native reference')


def require_baseline_parity(measured, original, *, role, study_id):
    require(original['role'] == role and original['study_id'] == study_id and original['step'] == 2400,
            'Export identity or role differs')
    fields = ('reference_voxels','predicted_voxels','true_positive','false_positive','false_negative','box')
    require(all(measured[k] == original['metrics'][k] for k in fields), 'Baseline hard-mask metrics differ')
