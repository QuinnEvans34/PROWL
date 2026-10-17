"""Offline native-grid scoring. Never imports models or modifies predictions."""
from hashlib import sha256
from pathlib import Path
import math
import nibabel as nib
import numpy as np


def score_saved(prediction_path, pancreas_path, lesion_path, *, expected_prediction_sha256,
                expected_pancreas_sha256, expected_lesion_sha256,
                allow_unknown_reference_units=False):
    paths = [Path(p) for p in (prediction_path, pancreas_path, lesion_path)]
    pins = [expected_prediction_sha256, expected_pancreas_sha256, expected_lesion_sha256]
    images, arrays = [], []
    for index, (path, pin) in enumerate(zip(paths, pins)):
        if sha256(path.read_bytes()).hexdigest() != pin:
            raise ValueError('File checksum differs')
        image = nib.load(path)
        if len(image.shape) != 3 or math.prod(image.shape) > 96_000_000:
            raise ValueError('Unsupported native allocation')
        units = image.header.get_xyzt_units()[0]
        if units != 'mm' and not (index > 0 and units == 'unknown' and allow_unknown_reference_units):
            raise ValueError('Physical units must be mm')
        affine = image.affine
        if not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3, :3])) < 1e-12:
            raise ValueError('Invalid affine')
        if images and (image.shape != images[0].shape or
                       not np.allclose(affine, images[0].affine, rtol=0, atol=1e-5)):
            raise ValueError('Reference and prediction grids differ')
        values = np.asarray(image.dataobj, dtype=np.float32)
        rounded = np.rint(values)
        if not np.allclose(values, rounded, rtol=0, atol=1e-6) or not np.isin(
                rounded, [0, 1, 2] if index == 0 else [0, 1]).all():
            raise ValueError('Invalid label codes')
        images.append(image)
        arrays.append(rounded.astype(np.uint8))
    prediction, pancreas, lesion = arrays
    volume_ml = abs(np.linalg.det(images[0].affine[:3, :3])) / 1000
    metrics = {}
    for name, reference, predicted in (
        ('pancreas_parenchyma', (pancreas == 1) & (lesion == 0), prediction == 1),
        ('pancreas_lesion_union', (pancreas == 1) | (lesion == 1), prediction > 0),
        ('lesion', lesion == 1, prediction == 2),
    ):
        n, p = int(reference.sum()), int(predicted.sum())
        tp = int(np.count_nonzero(reference & predicted))
        metrics[name] = dict(reference_voxels=n, predicted_voxels=p, true_positive=tp,
            dice=2 * tp / (n + p) if n else None, recall=tp / n if n else None,
            false_positive_ml=(p - tp) * volume_ml)
    for path, pin in zip(paths, pins):
        if sha256(path.read_bytes()).hexdigest() != pin:
            raise ValueError('Input changed during scoring')
    return dict(component='saved-native-prediction-scoring-v1',
        file_sha256=dict(zip(('prediction', 'pancreas', 'lesion'), pins)), metrics=metrics,
        lesion_reference_state='positive' if lesion.any() else 'reference_empty',
        empty_reference_policy='Dice/recall undefined; report prediction volume, not verified health',
        reference_units=[im.header.get_xyzt_units()[0] for im in images[1:]],
        unknown_reference_units_assumed_mm=allow_unknown_reference_units and any(
            im.header.get_xyzt_units()[0] == 'unknown' for im in images[1:]),
        prediction_modified=False)
