import gzip
import json

import nibabel as nib
import numpy as np
import pytest

from scripts.prepare_local_ct_intake import prepare, sha


def scan(path, *, units='mm', pixels=None):
    if pixels is None:
        pixels = np.arange(60, dtype=np.int16).reshape(3, 4, 5) - 1000
    affine = np.array([[-0.8, 0, 0, 15], [0, 0, 2.5, 30], [0, 0.9, 0, 60], [0, 0, 0, 1]])
    image = nib.Nifti1Image(pixels, affine)
    image.header.set_xyzt_units(units)
    nib.save(image, path)
    return nib.load(path)


@pytest.mark.parametrize('suffix', ['.nii', '.nii.gz'])
def test_retains_native_bytes_geometry_and_intensities(tmp_path, suffix):
    source = tmp_path / f'ct{suffix}'
    original = scan(source)
    out = tmp_path / 'intake'
    package = prepare(source, out, study_id='SYNTHETIC_CT', deidentified=True)
    assert package['status'] == 'ct_ready'
    assert package['ct_intensity_units'] == 'unverified'
    assert package['source']['sha256'] == sha(source)
    assert package['ct']['content_sha256'] == sha(out / 'ct.nii.gz')
    assert package['ct']['bytes'] == (out / 'ct.nii.gz').stat().st_size
    if suffix == '.nii.gz':
        assert (out / 'ct.nii.gz').read_bytes() == source.read_bytes()
    else:
        assert gzip.decompress((out / 'ct.nii.gz').read_bytes()) == source.read_bytes()
    np.testing.assert_array_equal(nib.load(out / 'ct.nii.gz').get_fdata(), original.get_fdata())
    np.testing.assert_array_equal(nib.load(out / 'ct.nii.gz').affine, original.affine)
    assert json.loads((out / 'manifest.json').read_text())['geometry']['shape'] == [3, 4, 5]


def test_refuses_nonfinite_unknown_units_and_unconfirmed_input(tmp_path):
    source = tmp_path / 'scan.nii.gz'
    out = tmp_path / 'intake'
    scan(source, units='unknown')
    with pytest.raises(ValueError, match='de-identified'):
        prepare(source, out, study_id='SYNTHETIC_CT', deidentified=False)
    with pytest.raises(ValueError, match='millimeter'):
        prepare(source, out, study_id='SYNTHETIC_CT', deidentified=True)
    scan(source, pixels=np.full((3, 3, 3), np.nan, dtype=np.float32))
    with pytest.raises(ValueError, match='nonfinite'):
        prepare(source, out, study_id='SYNTHETIC_CT', deidentified=True)
    assert not out.exists()


def test_refuses_truncated_compressed_or_existing_destination(tmp_path):
    source = tmp_path / 'scan.nii.gz'
    scan(source)
    source.write_bytes(source.read_bytes()[:-5])
    out = tmp_path / 'intake'
    with pytest.raises(EOFError):
        prepare(source, out, study_id='SYNTHETIC_CT', deidentified=True)
    assert not out.exists()
    out.mkdir()
    sentinel = out / 'previous.txt'
    sentinel.write_text('patient-independent test')
    with pytest.raises(FileExistsError):
        prepare(source, out, study_id='SYNTHETIC_CT', deidentified=True)
    assert sentinel.read_text() == 'patient-independent test'
