"""CPU candidate/provenance primitives, not a scientific training launcher.

Candidates come ONLY from a frozen segmenter's hard native lesion prediction.
Ground truth supplies training labels, never candidate geometry or inference.
"""
import math
import numpy as np
from scipy import ndimage


def validate_provenance(records, train_ids, development_ids):
    """Fail closed on generator exposure, partition leakage or missing identities.

    generator_exposed_ids must include optimization, checkpoint-selection and
    calibration exposure. Caller must bind these declarations to real receipts.
    A declared list alone is not evidence that an external checkpoint is clean.
    """
    train, dev = set(train_ids), set(development_ids)
    if not train or not dev or train & dev:
        raise ValueError('Disjoint nonempty source roles required')
    seen = set(); partitions = {'fit': set(), 'calibration': set()}
    for r in records:
        name, role = r['case_id'], r['role']
        if name in seen or name not in train or role not in partitions:
            raise ValueError('Duplicate, protected or invalid patient role')
        seen.add(name); partitions[role].add(name)
        for key in ('checkpoint_sha256', 'source_sha256', 'prediction_sha256', 'generator_receipt_sha256'):
            value = r.get(key, '')
            if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('Missing bound identity')
        exposed = set(r['generator_exposed_ids'])
        if name in exposed or exposed & dev:
            raise ValueError('Generator leakage into held-out or protected cases')
    if not all(partitions.values()):
        raise ValueError('Separate fit and calibration patients required')
    # A checkpoint generating fit candidates must not have learned calibration
    # labels either: otherwise the fitted verifier has indirect calibration exposure.
    if any(set(r['generator_exposed_ids']) & partitions['calibration'] for r in records):
        raise ValueError('Indirect calibration leakage')
    return {key: sorted(value) for key, value in partitions.items()}


def candidates(prediction):
    a = np.asarray(prediction)
    if a.ndim != 3 or a.dtype != np.bool_ or min(a.shape) < 1:
        raise ValueError('Nonempty native 3D boolean prediction required')
    labels, count = ndimage.label(a, np.ones((3, 3, 3), dtype=np.uint8))
    boxes = ndimage.find_objects(labels)
    return labels, [dict(component_id=i, low=[s.start for s in box],
                        high=[s.stop for s in box], voxels=int((labels[box] == i).sum()))
                    for i, box in enumerate(boxes, 1)]


def training_labels(component_map, truth):
    labels = np.asarray(component_map); target = np.asarray(truth)
    if labels.ndim != 3 or target.shape != labels.shape or target.dtype != np.bool_:
        raise ValueError('Aligned native boolean truth required')
    if not np.issubdtype(labels.dtype, np.integer) or (labels < 0).any():
        raise ValueError('Nonnegative integer components required')
    return {int(i): bool(target[labels == i].any()) for i in np.unique(labels) if i}


def retain_candidates(component_map, scores, threshold):
    """Whole-component gate; threshold zero is exactly the frozen baseline.

    This is a candidate policy for qualification, not a calibrated model.
    No voxel-level probability reinterpretation or GT-dependent fallback.
    """
    labels = np.asarray(component_map)
    if labels.ndim != 3 or not np.issubdtype(labels.dtype, np.integer) or (labels < 0).any():
        raise ValueError('Invalid component map')
    ids = {int(i) for i in np.unique(labels) if i}
    if set(scores) != ids:
        raise ValueError('Every candidate must be scored exactly once')
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('Invalid threshold')
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in scores.values()):
        raise ValueError('Invalid score')
    kept = [i for i, score in scores.items() if score >= threshold]
    return np.isin(labels, kept)
