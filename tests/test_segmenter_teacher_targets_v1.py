from copy import deepcopy
import itertools

import numpy as np
import pytest

from src.data.manifest_records import canonical, digest
from src.data.segmenter_full_batch_v1 import array_hash
from src.data.segmenter_teacher_targets_v1 import (
    HASH_FIELDS, SCHEMA, AUGMENTATION, checked_target, apply_spatial_trace,
)


def fixture():
    q = np.arange(64, dtype=np.float32).reshape(4, 4, 4) / 63
    support = np.ones(q.shape, dtype=bool)
    identity = dict(case_id='synthetic-training-case', role='train', **{k: 'a' * 64 for k in HASH_FIELDS})
    record = dict(schema=SCHEMA, identity=deepcopy(identity), shape=list(q.shape),
                  probability_sha256=array_hash(q), support_sha256=array_hash(support))
    return q, support, identity, record


def admit(q, support, identity, record, **kwargs):
    return checked_target(q, support, record, expected_identity=identity,
                          record_sha256=kwargs.pop('pin', digest(canonical(record))), **kwargs)


def test_bound_identity_payload_and_copy_isolation():
    q, support, identity, record = fixture()
    accepted, valid, meta = admit(q, support, identity, record)
    q[:] = 0; support[:] = False; record['identity']['case_id'] = 'changed'
    assert accepted.max() == 1 and valid.all() and meta['case_id'] == identity['case_id']


@pytest.mark.parametrize('field', ['case_id', 'role', *HASH_FIELDS])
def test_wrong_case_grid_or_provenance_rejected(field):
    q, support, identity, record = fixture()
    record['identity'][field] = 'different' if field in ('case_id', 'role') else 'b' * 64
    with pytest.raises(ValueError, match='identity mismatch'): admit(q, support, identity, record)


@pytest.mark.parametrize('role', ['validation', 'development', 'test'])
def test_protected_roles_never_used_for_optimizer(role):
    q, support, identity, record = fixture()
    identity['role'] = role; record['identity']['role'] = role
    with pytest.raises(ValueError, match='training-optimizer'): admit(q, support, identity, record)


def test_pin_or_payload_changes_rejected():
    q, support, identity, record = fixture()
    with pytest.raises(ValueError, match='pin'): admit(q, support, identity, record, pin='0' * 64)
    q[0, 0, 0] = .7
    with pytest.raises(ValueError, match='bytes'): admit(q, support, identity, record)
    with pytest.raises(ValueError, match='training-optimizer'): admit(q, support, identity, record, operation='evaluator')


@pytest.mark.parametrize('bad', ['nan', 'negative', 'large', 'dtype', 'support_dtype', 'empty'])
def test_invalid_fields_rejected(bad):
    q, support, identity, record = fixture()
    if bad == 'nan': q[0, 0, 0] = np.nan
    if bad == 'negative': q[0, 0, 0] = -.1
    if bad == 'large': q[0, 0, 0] = 1.1
    if bad == 'dtype': q = q.astype(np.float64)
    if bad == 'support_dtype': support = support.astype(np.uint8)
    if bad == 'empty': support[:] = False
    with pytest.raises(ValueError): admit(q, support, identity, record)


@pytest.mark.parametrize('flips,k', list(itertools.product(itertools.product([False, True], repeat=3), range(4))))
def test_every_spatial_combination_preserves_exact_alignment(flips, k):
    q, support, _, _ = fixture()
    support[0, :, :] = False
    expected, expected_support = q.copy(), support.copy()
    for axis, take in enumerate(flips):
        if take: expected, expected_support = np.flip(expected, axis), np.flip(expected_support, axis)
    expected, expected_support = (np.rot90(a, k, axes=(0, 1)) for a in (expected, expected_support))
    expected = expected.copy(); expected[~expected_support] = 0
    trace = dict(policy=AUGMENTATION, flips=list(flips), rotation_k=k, rotation_axes=[0, 1],
        valid_voxels=int(expected_support.sum()), support_sha256=array_hash(np.ascontiguousarray(expected_support)),
        intensity_scale=1.1, intensity_shift=.1, gaussian_noise=True)
    actual, valid = apply_spatial_trace(q, support, trace)
    assert np.array_equal(actual, expected) and np.array_equal(valid, expected_support)
    assert actual.flags.c_contiguous and valid.flags.c_contiguous


def test_replay_matches_actual_existing_augmentation_labels():
    from src.training.segmenter_augmentation_v1 import augment
    y = np.zeros((8, 8, 8), dtype=np.uint8); y[1:4, 2:6, 3:7] = 2
    x = np.full((1, 8, 8, 8), .4, dtype=np.float32)
    transform = dict(pad_low=[0, 0, 0], normalized_shape=[8, 8, 8])
    for step in range(1, 13):
        _, augmented_y, trace = augment(x, y, transform, seed=42, update=step, case_id='synthetic')
        q, support = apply_spatial_trace(y.astype(np.float32) / 2, np.ones_like(y, dtype=bool), trace)
        assert np.array_equal(q, augmented_y.astype(np.float32) / 2) and support.all()


def test_wrong_support_trace_and_axes_rejected():
    q, support, _, _ = fixture()
    trace = dict(policy=AUGMENTATION, flips=[False]*3, rotation_k=0, rotation_axes=[0, 1],
                 valid_voxels=64, support_sha256='0'*64)
    with pytest.raises(ValueError, match='support mismatch'): apply_spatial_trace(q, support, trace)
    trace['rotation_axes'] = [1, 2]
    with pytest.raises(ValueError, match='Unsupported'): apply_spatial_trace(q, support, trace)
