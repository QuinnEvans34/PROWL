"""Synthetic-only candidate checks; not a real device or inference qualification."""
import numpy as np
import pytest

from src.inference.lesion_confidence_policy_v1 import THRESHOLDS, apply_policy


def sample():
    # Four raw lesion winners: two weak, one boundary, one strong; two nonlesion winners.
    return np.array([[.30, .25, .20, .10, .70, .10],
                     [.31, .35, .30, .15, .10, .80],
                     [.39, .40, .50, .75, .20, .10]], dtype=np.float32).reshape(3, 1, 2, 3)


def test_raw_policy_exact_and_input_unchanged():
    p = sample()
    before = p.tobytes()
    result = apply_policy(p, lesion_threshold=0)
    np.testing.assert_array_equal(result, p.argmax(0))
    assert result.dtype == np.uint8 and result.shape == (1, 2, 3)
    assert p.tobytes() == before


def test_boundary_and_suppressed_fallback_preserve_nonlesion_winners():
    p = sample()
    result = apply_policy(p, lesion_threshold=.4).reshape(-1)
    np.testing.assert_array_equal(result, [1, 2, 2, 2, 0, 1])
    strict = apply_policy(p, lesion_threshold=.5).reshape(-1)
    np.testing.assert_array_equal(strict, [1, 1, 2, 2, 0, 1])


def test_ties_use_original_argmax_and_do_not_invent_lesion():
    p = np.array([.5, 0, .5], dtype=np.float32).reshape(3, 1, 1, 1)
    assert apply_policy(p, lesion_threshold=.4).item() == 0
    p = np.array([.25, .25, .5], dtype=np.float32).reshape(3, 1, 1, 1)
    assert apply_policy(p, lesion_threshold=.6).item() == 0


def test_probability_rank_suppression_cannot_recover_misses_or_add_lesions():
    rng = np.random.default_rng(73)
    p = rng.random((3, 4, 5, 6), dtype=np.float32)
    p /= p.sum(0)
    raw = p.argmax(0)
    last = raw == 2
    for threshold in THRESHOLDS:
        result = apply_policy(p, lesion_threshold=threshold)
        assert not np.any((result == 2) & (raw != 2))
        np.testing.assert_array_equal(result[raw != 2], raw[raw != 2])
        assert not np.any((result == 2) & ~last)
        last = result == 2


@pytest.mark.parametrize("threshold", [True, -.1, .45, .9, float("nan")])
def test_unregistered_threshold_refused(threshold):
    with pytest.raises(ValueError):
        apply_policy(sample(), lesion_threshold=threshold)


@pytest.mark.parametrize("value", [
    np.zeros((3, 1, 2, 3), dtype=np.float32),
    np.ones((3, 1, 2, 3), dtype=np.float32),
    np.full((3, 1, 2, 3), np.nan, dtype=np.float32),
    np.ones((2, 1, 2, 3), dtype=np.float32) / 2,
    np.zeros((3, 0, 2, 3), dtype=np.float32),
    sample().astype(np.float64),
])
def test_invalid_probability_volume_refused(value):
    with pytest.raises(ValueError):
        apply_policy(value, lesion_threshold=.4)
