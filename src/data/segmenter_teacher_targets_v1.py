"""Training-only teacher target admission and exact spatial trace replay.

In-memory contracts only. Native teacher inference/resampling and cache I/O are
deliberately not implemented here; matching shapes alone never proves alignment.
"""
from copy import deepcopy
import re

import numpy as np

from src.data.manifest_records import canonical, digest
from src.data.segmenter_full_batch_v1 import array_hash

SCHEMA = 'lesion_teacher_target_v1'
AUGMENTATION = 'pants_cached_view_augmentation_v1'
HASH_FIELDS = ('source_image_sha256', 'source_geometry_sha256', 'teacher_sha256',
               'teacher_config_sha256', 'teacher_mapping_sha256',
               'preprocessing_sha256', 'control_sha256', 'grid_sha256')
IDENTITY_FIELDS = ('case_id', 'role', *HASH_FIELDS)


def checked_target(probability, support, record, *, expected_identity, record_sha256,
                   operation='optimizer'):
    """Require caller-pinned provenance and bytes before any training target use."""
    if operation != 'optimizer' or expected_identity.get('role') != 'train':
        raise ValueError('Teacher targets are training-optimizer only')
    if set(expected_identity) != set(IDENTITY_FIELDS) or not isinstance(expected_identity['case_id'], str) or not expected_identity['case_id']:
        raise ValueError('Complete target identity required')
    if any(not isinstance(expected_identity[k], str) or not re.fullmatch('[0-9a-f]{64}', expected_identity[k])
           for k in HASH_FIELDS):
        raise ValueError('Expected SHA256 provenance required')
    if digest(canonical(record)) != record_sha256:
        raise ValueError('Teacher record pin mismatch')
    if set(record) != {'schema', 'identity', 'shape', 'probability_sha256', 'support_sha256'} or record['schema'] != SCHEMA:
        raise ValueError('Unsupported teacher record')
    if record['identity'] != expected_identity:
        raise ValueError('Teacher case/role/source/grid/model identity mismatch')
    if not isinstance(probability, np.ndarray) or probability.dtype != np.float32 or probability.ndim != 3 or min(probability.shape) < 1:
        raise ValueError('Nonempty float32 teacher field required')
    if not isinstance(support, np.ndarray) or support.dtype != np.bool_ or support.shape != probability.shape or not support.any():
        raise ValueError('Boolean real support required')
    if not np.isfinite(probability).all() or probability.min() < 0 or probability.max() > 1:
        raise ValueError('Invalid teacher probabilities')
    if list(probability.shape) != record['shape'] or array_hash(probability) != record['probability_sha256'] or array_hash(support) != record['support_sha256']:
        raise ValueError('Teacher field bytes/shape mismatch')
    # Copy to prevent caller mutation of an admitted field through a shared view.
    return probability.copy(), support.copy(), deepcopy(record['identity'])


def apply_spatial_trace(probability, support, trace):
    """Replay existing flips then R/A quarter-turn; never intensity-jitter a label.

Input must already describe the very same pre-augmentation physical window.
The trace binds transformed valid support. Teacher confidence is NOT support.
"""
    if not isinstance(probability, np.ndarray) or probability.dtype != np.float32 or probability.ndim != 3 or len(set(probability.shape)) != 1 or min(probability.shape) < 1:
        raise ValueError('Expected a nonempty float32 cubic probability window')
    if not np.isfinite(probability).all() or probability.min() < 0 or probability.max() > 1:
        raise ValueError('Invalid probability window')
    if not isinstance(support, np.ndarray) or support.dtype != np.bool_ or support.shape != probability.shape or not support.any():
        raise ValueError('Window support mismatch')
    flips = trace.get('flips')
    if (trace.get('policy') != AUGMENTATION or not isinstance(flips, list) or len(flips) != 3
            or any(type(v) is not bool for v in flips) or trace.get('rotation_axes') != [0, 1]
            or type(trace.get('rotation_k')) is not int or trace['rotation_k'] not in range(4)):
        raise ValueError('Unsupported spatial augmentation trace')
    q, valid = probability.copy(), support.copy()
    for axis, flip in enumerate(flips):
        if flip:
            q, valid = np.flip(q, axis), np.flip(valid, axis)
    if trace['rotation_k']:
        q, valid = (np.rot90(a, k=trace['rotation_k'], axes=(0, 1)) for a in (q, valid))
    q, valid = np.ascontiguousarray(q), np.ascontiguousarray(valid)
    if trace.get('valid_voxels') != int(valid.sum()) or trace.get('support_sha256') != array_hash(valid):
        raise ValueError('Teacher/image transformed support mismatch')
    q[~valid] = 0.
    return q, valid
