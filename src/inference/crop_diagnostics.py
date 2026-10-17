"""Reference-only diagnostics; never use these results to choose inference crops."""
import numpy as np
from scipy import ndimage
from src.data import segmenter_geometry_v2 as geometry


def target_roundtrip(pancreas, lesion, record, *, trusted_record_sha256):
    """Measure label representation, not a mathematical upper bound on model Dice."""
    geometry.validate_record(record, trusted_record_sha256)
    a, b = np.asarray(pancreas), np.asarray(lesion)
    if (list(a.shape) != record['source_shape'] or a.shape != b.shape
            or not np.isin(a, [0, 1]).all() or not np.isin(b, [0, 1]).all()):
        raise ValueError('Exact native binary reference grids required')
    truth = np.where(b, 2, a).astype(np.uint8)
    tensor = geometry.forward_field(truth, record, order=0)
    restored = geometry.restore_codes(tensor, record, trusted_record_sha256=trusted_record_sha256)
    lo, hi = record['native_box']; crop = tuple(slice(l, h) for l, h in zip(lo, hi))
    metrics = {}
    for name, native, mapped, roundtrip in (
        ('lesion', truth == 2, tensor == 2, restored == 2),
        ('pancreas_lesion_union', truth > 0, tensor > 0, restored > 0),
    ):
        n, p = int(native.sum()), int(roundtrip.sum())
        tp = int(np.count_nonzero(native & roundtrip))
        metrics[name] = dict(native_voxels=n, tensor_voxels=int(mapped.sum()),
            native_box_coverage=int(native[crop].sum())/n if n else None,
            roundtrip_dice=2*tp/(n+p) if n else None, roundtrip_recall=tp/n if n else None)
    del truth, tensor, restored
    labels, count = ndimage.label(b, structure=np.ones((3, 3, 3), np.uint8))
    if count:
        mapped = geometry.forward_field(labels, record, order=0)
        present = set(np.unique(mapped).tolist())
        lost = [i for i in range(1, count+1) if i not in present]
    else:
        lost = []
    return dict(purpose='reference-only resampling diagnostic; not autonomous prediction',
        effective_spacing_mm=record['effective_spacing_mm'], metrics=metrics,
        lesion_components=count, lost_component_ids=lost,
        interpretation='Nearest-label roundtrip fidelity is not a model performance ceiling')


def decode_binary_reference(values):
    """Match the saved scorer's 1e-6 tolerance for scaled NIfTI label values."""
    a = np.asarray(values)
    rounded = np.rint(a)
    if not np.allclose(a, rounded, rtol=0, atol=1e-6) or not np.isin(rounded, [0, 1]).all():
        raise ValueError('Reference is not a finite near-binary label array')
    return rounded.astype(np.uint8)
