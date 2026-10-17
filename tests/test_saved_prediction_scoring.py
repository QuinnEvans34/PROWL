from hashlib import sha256
import nibabel as nib
import numpy as np
import pytest
from src.inference.saved_prediction_scoring import score_saved


def fixture(tmp_path, prediction, pancreas, lesion, shift=0):
    paths, pins = [], []
    for name, array in zip(('prediction', 'pancreas', 'lesion'), (prediction, pancreas, lesion)):
        affine = np.diag([2., 2., 2., 1.])
        if name == 'lesion': affine[0, 3] += shift
        im = nib.Nifti1Image(np.asarray(array, np.uint8), affine)
        im.header.set_xyzt_units('mm')
        path = tmp_path / (name + '.nii.gz'); nib.save(im, path)
        paths.append(path); pins.append(sha256(path.read_bytes()).hexdigest())
    kwargs = dict(zip(('expected_prediction_sha256', 'expected_pancreas_sha256',
                      'expected_lesion_sha256'), pins))
    return paths, kwargs


def test_known_counts_and_lesion_precedence(tmp_path):
    shape = (2, 2, 2)
    p = np.zeros(shape, np.uint8); a = p.copy(); b = p.copy()
    a.flat[:3] = 1; b.flat[0] = 1; p.flat[:2] = 2; p.flat[2] = 1
    paths, kwargs = fixture(tmp_path, p, a, b)
    r = score_saved(*paths, **kwargs)['metrics']
    assert r['lesion']['dice'] == pytest.approx(2/3)
    assert r['lesion']['false_positive_ml'] == pytest.approx(.008)
    assert r['pancreas_lesion_union']['dice'] == 1
    assert r['pancreas_parenchyma']['dice'] == pytest.approx(2/3)


def test_empty_is_not_verified_healthy(tmp_path):
    z = np.zeros((2, 2, 2), np.uint8)
    paths, kwargs = fixture(tmp_path, z + 2, z, z)
    r = score_saved(*paths, **kwargs)
    assert r['lesion_reference_state'] == 'reference_empty'
    assert r['metrics']['lesion']['dice'] is None
    assert r['metrics']['lesion']['false_positive_ml'] == pytest.approx(.064)


def test_shifted_grid_and_changed_bytes_refused(tmp_path):
    z = np.zeros((2, 2, 2), np.uint8)
    paths, kwargs = fixture(tmp_path, z, z, z, shift=2)
    with pytest.raises(ValueError, match='grids differ'): score_saved(*paths, **kwargs)
    kwargs['expected_prediction_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='checksum'): score_saved(*paths, **kwargs)


def test_unknown_reference_units_require_explicit_assumption(tmp_path):
    z = np.zeros((2, 2, 2), np.uint8)
    paths, kwargs = fixture(tmp_path, z, z, z)
    im = nib.load(paths[1]); im.header.set_xyzt_units('unknown'); nib.save(im, paths[1])
    kwargs['expected_pancreas_sha256'] = sha256(paths[1].read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='units'): score_saved(*paths, **kwargs)
    result = score_saved(*paths, **kwargs, allow_unknown_reference_units=True)
    assert result['unknown_reference_units_assumed_mm']
