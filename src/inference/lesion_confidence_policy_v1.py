"""Synthetic-qualified candidate only; not wired into any producing inference path."""
import numpy as np

THRESHOLDS = (0.0, 0.4, 0.5, 0.6)


def apply_policy(probabilities, *, lesion_threshold):
    """Keep raw class winners unless lesion confidence is below the fixed threshold.

    Channels are background, pancreas, lesion. Suppressed lesion winners use the
    highest nonlesion probability. This cannot recover a raw missed lesion and
    does not remove components by size or rank. Array geometry is unchanged.
    """
    if (type(lesion_threshold) not in (int, float) or lesion_threshold not in THRESHOLDS
            or not isinstance(probabilities, np.ndarray) or probabilities.dtype != np.float32
            or probabilities.ndim != 4 or probabilities.shape[0] != 3
            or any(n == 0 for n in probabilities.shape[1:])
            or not np.isfinite(probabilities).all()
            or probabilities.min() < 0 or probabilities.max() > 1
            or not np.allclose(probabilities.sum(axis=0), 1, atol=1e-4, rtol=0)):
        raise ValueError("Expected fixed threshold and finite normalized three-channel float32 volume")
    raw = probabilities.argmax(axis=0).astype(np.uint8)
    if lesion_threshold == 0:
        return raw
    suppressed = (raw == 2) & (probabilities[2] < lesion_threshold)
    raw[suppressed] = probabilities[:2].argmax(axis=0)[suppressed]
    return raw
