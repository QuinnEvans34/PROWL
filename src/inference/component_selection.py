"""Exploratory CP01 selection/evaluation. Not imported by the live measurement path."""
from __future__ import annotations

import numpy as np
from scipy import ndimage

POLICY = 'largest-union-26-v1'
STRUCTURE = np.ones((3, 3, 3), dtype=np.uint8)


def _labels(a):
    a = np.asarray(a)
    if a.ndim != 3 or not all(a.shape) or a.size > 32_000_000 or not np.isin(a, [0, 1, 2]).all():
        raise ValueError('Invalid prediction grid or labels')
    return a


def _components(mask):
    ids, count = ndimage.label(mask, STRUCTURE)
    if count > 10_000:
        raise ValueError('Component budget exceeded')
    return ids, count


def select_largest_union(prediction):
    """Prediction-only selection. Equal maxima refuse; never consult annotations."""
    raw = _labels(prediction)
    ids, count = _components(raw > 0)
    sizes = np.bincount(ids.ravel(), minlength=count + 1)
    if count == 0:
        raise ValueError('Empty foreground')
    largest = np.flatnonzero(sizes[1:] == sizes[1:].max()) + 1
    if len(largest) != 1:
        raise ValueError('Ambiguous equal-largest components')
    keep = ids == largest[0]
    if not np.any(keep & (raw == 1)):
        raise ValueError('Largest component has no pancreas label')
    candidate = np.where(keep, raw, 0).astype(np.uint8)
    return candidate, {'policy': POLICY, 'connectivity': 26, 'selected_component': int(largest[0]),
                       'original_components': count, 'removed_voxels': int(np.count_nonzero(raw) - keep.sum())}


def binary_metrics(prediction, reference, voxel_ml):
    p, r = np.asarray(prediction, dtype=bool), np.asarray(reference, dtype=bool)
    if p.shape != r.shape or not np.isfinite(voxel_ml) or voxel_ml <= 0:
        raise ValueError('Invalid metric grid or voxel volume')
    n, m = int(p.sum()), int(r.sum())
    tp = int(np.count_nonzero(p & r)); fp = n - tp; fn = m - tp
    signed = (n - m) * voxel_ml
    return {'prediction_voxels': n, 'reference_voxels': m, 'tp': tp, 'fp': fp, 'fn': fn,
            'dice': 2 * tp / (n + m) if n + m else None,
            'precision': tp / n if n else None, 'recall': tp / m if m else None,
            'prediction_ml': n * voxel_ml, 'reference_ml': m * voxel_ml,
            'signed_volume_error_ml': signed, 'absolute_volume_error_ml': abs(signed),
            'relative_volume_error': (n - m) / m if m else None,
            'reference_state': 'positive' if m else 'empty_annotation_not_verified_healthy'}


def lesion_component_matches(prediction, lesion):
    """Describe residual lesion regions; never select them using the reference."""
    prediction = _labels(prediction)
    lesion = np.asarray(lesion)
    if lesion.shape != prediction.shape or not np.isin(lesion, [0, 1]).all():
        raise ValueError('Lesion reference must be aligned and binary')
    ids, n = _components(prediction == 2)
    sizes = np.bincount(ids.ravel(), minlength=n + 1)
    overlap = np.bincount(ids[lesion == 1], minlength=n + 1)
    objects = ndimage.find_objects(ids)
    return [{'id': i, 'voxels': int(sizes[i]), 'reference_overlap_voxels': int(overlap[i]),
             'false_positive_voxels': int(sizes[i] - overlap[i]),
             'box': [[s.start for s in objects[i - 1]], [s.stop for s in objects[i - 1]]]}
            for i in range(1, n + 1)]


def _coverage(prediction, roi):
    shape = np.array(prediction.shape); box = np.asarray(roi)
    if (box.shape != (2, 3) or not np.issubdtype(box.dtype, np.integer)
            or (box[0] < 0).any() or (box[1] > shape).any() or (box[1] <= box[0]).any()):
        raise ValueError('Invalid inference region')
    # Check planes/slices without materializing an N-by-3 list of foreground coordinates.
    p = prediction > 0
    outside = int(p.sum() - p[tuple(slice(a, b) for a, b in zip(*box))].sum())
    crop = image = False
    for axis in range(3):
        crop |= bool(np.take(p, [box[0, axis], box[1, axis] - 1], axis=axis).any())
        image |= bool(np.take(p, [0, shape[axis] - 1], axis=axis).any())
    return {'crop_contact': crop, 'image_contact': image, 'outside_voxels': outside}


def compare_selection(raw, candidate, pancreas, lesion, affine, roi):
    raw, candidate = _labels(raw), _labels(candidate)
    if candidate.shape != raw.shape or not np.all((candidate == raw) | (candidate == 0)):
        raise ValueError('Candidate may only remove original labels')
    p, l = np.asarray(pancreas), np.asarray(lesion)
    if (p.shape != raw.shape or l.shape != raw.shape or not np.isin(p, [0, 1]).all()
            or not np.isin(l, [0, 1]).all() or not p.any()):
        raise ValueError('References must be aligned binary grids with nonempty pancreas')
    a = np.asarray(affine, dtype=float)
    if (a.shape != (4, 4) or not np.isfinite(a).all() or not np.allclose(a[3], [0, 0, 0, 1], atol=1e-8, rtol=0)
            or abs(np.linalg.det(a[:3, :3])) < 1e-9):
        raise ValueError('Invalid affine')
    voxel_ml = float(abs(np.linalg.det(a[:3, :3])) / 1000)
    p, l = p.astype(bool), l.astype(bool)
    targets = {}
    for name, truth, b, c in [('pancreas_extent', p | l, raw > 0, candidate > 0),
                             ('pancreas_parenchyma', p & ~l, raw == 1, candidate == 1),
                             ('lesion', l, raw == 2, candidate == 2)]:
        targets[name] = {'raw': binary_metrics(b, truth, voxel_ml),
                         'candidate': binary_metrics(c, truth, voxel_ml)}
    lesion_ids, n = _components(l)
    lesion_components = []
    sizes = np.bincount(lesion_ids.ravel(), minlength=n + 1)
    before = np.bincount(lesion_ids[raw == 2], minlength=n + 1)
    after = np.bincount(lesion_ids[candidate == 2], minlength=n + 1)
    for i in range(1, n + 1):
        lesion_components.append({'id': i, 'reference_voxels': int(sizes[i]),
            'raw_tp': int(before[i]), 'candidate_tp': int(after[i]),
            'raw_recall': float(before[i] / sizes[i]), 'candidate_recall': float(after[i] / sizes[i]),
            'lost_overlap_voxels': int(before[i] - after[i]),
            'became_undetected': bool(before[i] > 0 and after[i] == 0)})
    removed_ids, n = _components((raw > 0) & (candidate == 0))
    sizes = np.bincount(removed_ids.ravel(), minlength=n + 1)
    ref_p = np.bincount(removed_ids[p], minlength=n + 1)
    ref_l = np.bincount(removed_ids[l], minlength=n + 1)
    correct_l = np.bincount(removed_ids[l & (raw == 2)], minlength=n + 1)
    removed = [{'id': i, 'voxels': int(sizes[i]), 'reference_pancreas_overlap': int(ref_p[i]),
                'reference_lesion_overlap': int(ref_l[i]), 'correct_lesion_voxels_removed': int(correct_l[i])}
               for i in range(1, n + 1)]
    coverage = {'raw': _coverage(raw, roi), 'candidate': _coverage(candidate, roi)}
    rules = {'boundary_clear': not any(coverage['candidate'].values()),
             'no_correct_voxels_removed': all(t['candidate']['tp'] == t['raw']['tp'] for t in targets.values()),
             'no_lesion_component_overlap_lost': all(x['lost_overlap_voxels'] == 0 for x in lesion_components),
             'nonworsening_dice': all(t['candidate']['dice'] is None or t['candidate']['dice'] + 1e-12 >= t['raw']['dice']
                                     for t in targets.values()),
             'nonworsening_absolute_volume_error': all(t['candidate']['absolute_volume_error_ml'] <= t['raw']['absolute_volume_error_ml'] + 1e-12
                                                       for t in targets.values()),
             'strict_false_positive_reduction': any(t['candidate']['fp'] < t['raw']['fp'] for t in targets.values())}
    return {'schema': 'component-selection-comparison-v1', 'voxel_ml': voxel_ml, 'targets': targets,
            'reference_overlap_voxels': int((p & l).sum()), 'reference_lesion_outside_pancreas_voxels': int((l & ~p).sum()),
            'reference_lesion_components': lesion_components, 'removed_components': removed,
            'coverage': coverage, 'rules': rules, 'screen_pass': all(rules.values()), 'release_qualified': False}
