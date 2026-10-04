"""Prediction-only region diagnostics; no production ROI policy selection."""
import math
import numpy as np
from scipy import ndimage


def _mask(value):
    a = np.asarray(value)
    if a.ndim != 3 or not 0 < a.size <= 8_000_000 or not all(a.shape):
        raise ValueError('Expected bounded nonempty 3D grid')
    if not np.isin(a, (0, 1)).all():
        raise ValueError('Binary mask required')
    return a.astype(bool, copy=False)


def select_region(prediction, affine, *, strategy='all', margin_mm=10.):
    """Select solely from prediction. Boxes use half-open voxel edge bounds."""
    mask = _mask(prediction)
    a = np.asarray(affine, dtype=float)
    if a.shape != (4, 4) or not np.isfinite(a).all() or not np.allclose(a[3], [0, 0, 0, 1]):
        raise ValueError('Invalid affine')
    spacing = np.diag(a)[:3]
    if (spacing <= 0).any() or not np.allclose(a[:3, :3], np.diag(spacing)):
        raise ValueError('Canonical positive axis-aligned grid required')
    if strategy not in ('all', 'largest') or not math.isfinite(margin_mm) or not 0 <= margin_mm <= 50:
        raise ValueError('Invalid fixed diagnostic policy')
    labels, count = ndimage.label(mask, structure=ndimage.generate_binary_structure(3, 1))
    if count > 4096:
        raise ValueError('Component diagnostic budget exceeded')
    sizes = np.bincount(labels.ravel())[1:]
    selected = mask if strategy == 'all' or count == 0 else labels == (int(sizes.argmax()) + 1)
    voxel_volume = float(np.prod(spacing))
    info = dict(strategy=strategy, connectivity=6, margin_mm=float(margin_mm),
                component_count=int(count), component_volumes_mm3=(sizes * voxel_volume).tolist(),
                selected_voxels=int(selected.sum()), shape=list(mask.shape), spacing_mm=spacing.tolist())
    if not selected.any():
        return selected, dict(info, state='failed_empty_localization', box=None,
                              scan_fraction=None, box_volume_mm3=None)
    coordinates = np.nonzero(selected)
    lower = np.array([c.min() for c in coordinates]); upper = np.array([c.max()+1 for c in coordinates])
    pad = np.ceil(margin_mm / spacing).astype(int)
    lo = np.maximum(0, lower-pad); hi = np.minimum(mask.shape, upper+pad)
    dimensions = hi-lo
    return selected, dict(info, state='region_available', box=[lo.tolist(), hi.tolist()],
                          dimensions_mm=(dimensions*spacing).tolist(),
                          realized_margin_mm=[((lower-lo)*spacing).tolist(), ((hi-upper)*spacing).tolist()],
                          boundary_contact=[(lo == 0).tolist(), (hi == mask.shape).tolist()],
                          box_volume_mm3=float(np.prod(dimensions)*voxel_volume),
                          scan_fraction=float(np.prod(dimensions)/mask.size))


def evaluate_region(selected_prediction, reference, region):
    """Reference is used only after selection, for descriptive processed-grid metrics."""
    pred, target = _mask(selected_prediction), _mask(reference)
    if pred.shape != target.shape or list(pred.shape) != region['shape']:
        raise ValueError('Evaluation grid mismatch')
    n, p = int(target.sum()), int(pred.sum())
    tp = int((pred & target).sum())
    box = region['box']
    coverage = None
    if box is not None:
        lo, hi = np.asarray(box[0]), np.asarray(box[1])
        if lo.shape != (3,) or hi.shape != (3,) or not np.issubdtype(lo.dtype, np.integer) or not np.issubdtype(hi.dtype, np.integer) or (lo < 0).any() or (hi > pred.shape).any() or (hi <= lo).any():
            raise ValueError('Invalid box')
        coverage = int(target[tuple(slice(int(l), int(h)) for l, h in zip(lo, hi))].sum()) / n if n else None
    dice = 2*tp/(n+p) if n else None
    recall = tp/n if n else None
    ratio = p/n if n else None
    fit = None if not n else bool(recall >= .98 and dice >= .65 and ratio <= 2.)
    roi = None if not n else bool(coverage is not None and coverage >= .995 and region['scan_fraction'] <= .25)
    return dict(reference_voxels=n, predicted_voxels=p, true_positive=tp, false_positive=p-tp,
                false_negative=n-tp, dice=dice, precision=tp/p if p else None, recall=recall,
                volume_ratio=ratio, box_reference_coverage=coverage,
                fit_diagnostic_pass=fit, pre_mapping_roi_diagnostic_pass=roi,
                evaluation_scope='processed-grid pancreas only; no Stage 2 mapping or lesion coverage')
