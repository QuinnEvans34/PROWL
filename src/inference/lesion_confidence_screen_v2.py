"""Lossless four-policy replay and confidence counts, without model execution.

The original v1 policy remains the decision definition. A four-bit code retains
all four masks exactly, including the nonlesion fallback, without saving float
probability volumes. This changes storage only, not the inference policy.
"""
import numpy as np

from src.inference.lesion_confidence_policy_v1 import THRESHOLDS, apply_policy


def encode(probabilities):
    raw = apply_policy(probabilities, lesion_threshold=0.0)
    code = raw.copy()
    lesion = raw == 2
    level = sum((probabilities[2] >= t).astype(np.uint8) for t in THRESHOLDS[1:])
    fallback = probabilities[:2].argmax(0).astype(np.uint8)
    code[lesion] = 2 + 2*level[lesion] + fallback[lesion]
    return code


def decode(code, threshold):
    if threshold not in THRESHOLDS or code.dtype != np.uint8 or code.ndim != 3 or np.any(code > 9):
        raise ValueError('Invalid policy replay')
    raw_lesion = code >= 2
    out = code.copy()
    level = (code.astype(np.int16)-2)//2
    keep = raw_lesion & (level >= THRESHOLDS.index(threshold)) if threshold else raw_lesion
    out[raw_lesion] = code[raw_lesion] % 2
    out[keep] = 2
    return out


def pack(code):
    if code.dtype != np.uint8 or code.ndim != 3 or np.any(code > 9):
        raise ValueError('Invalid four-bit codes')
    flat = code.reshape(-1)
    out = flat[::2].copy()
    out[:len(flat)//2] |= flat[1::2] << 4
    return out


def unpack(packed, shape):
    if (packed.dtype != np.uint8 or packed.ndim != 1 or len(shape) != 3
            or any(type(n) is not int or n <= 0 for n in shape)):
        raise ValueError('Invalid packed metadata')
    size = int(np.prod(shape))
    if len(packed) != (size+1)//2 or (size % 2 and packed[-1] >> 4):
        raise ValueError('Packed length/padding mismatch')
    flat = np.empty(size, np.uint8)
    flat[::2] = packed & 15
    flat[1::2] = packed[:size//2] >> 4
    code = flat.reshape(shape)
    if np.any(code > 9):
        raise ValueError('Invalid packed class code')
    return code


def confidence_histogram(probabilities, lesion):
    """100 bins among raw lesion winners, split by reference overlap.

    Counts are voxel-weighted descriptive scores, not independent patients or
    calibrated disease probability. Bin i=[i/100,(i+1)/100), last includes 1.
    """
    raw = apply_policy(probabilities, lesion_threshold=0.0)
    if lesion.shape != raw.shape or not np.isin(lesion, [0, 1]).all():
        raise ValueError('Reference geometry/labels')
    scores = probabilities[2][raw == 2]
    truth = lesion[raw == 2].astype(bool)
    bins = np.minimum((scores*100).astype(np.int64), 99)
    return dict(true_positive=np.bincount(bins[truth], minlength=100).tolist(),
                false_positive=np.bincount(bins[~truth], minlength=100).tolist())
