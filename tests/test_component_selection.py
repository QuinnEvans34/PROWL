import hashlib
import json

import nibabel as nib
import numpy as np
import pytest

from src.inference.component_selection import select_largest_union, compare_selection, binary_metrics


def fixture():
    raw = np.zeros((10, 10, 10), np.uint8)
    raw[3:6, 3:6, 3:6] = 1
    raw[4, 4, 4] = 2
    pancreas = (raw > 0).astype(np.uint8)
    lesion = (raw == 2).astype(np.uint8)
    return raw, pancreas, lesion, np.diag([2., 3., 4., 1.]), [[1, 1, 1], [9, 9, 9]]


def compare(raw, pancreas, lesion, affine, roi):
    candidate, _ = select_largest_union(raw)
    return compare_selection(raw, candidate, pancreas, lesion, affine, roi)


def test_false_fragment_removal_preserves_input_and_passes_only_exploratory_screen():
    raw, p, l, a, box = fixture()
    raw[1, 1, 1] = 1; raw[8, 8, 8] = 2
    original = raw.copy()
    candidate, info = select_largest_union(raw)
    assert info['removed_voxels'] == 2
    assert set(np.unique(candidate)) == {0, 1, 2}
    np.testing.assert_array_equal(raw, original)
    r = compare_selection(raw, candidate, p, l, a, box)
    assert r['screen_pass'] and not r['release_qualified']
    assert r['coverage']['raw']['crop_contact'] and not r['coverage']['candidate']['crop_contact']
    assert r['targets']['pancreas_extent']['candidate']['prediction_ml'] == pytest.approx(27 * .024)
    assert r['targets']['lesion']['candidate']['dice'] == 1


def test_true_disconnected_lesion_cannot_be_hidden_by_better_aggregate_dice():
    raw, p, l, a, box = fixture()
    raw[8, 8, 8] = 2; l[8, 8, 8] = 1
    raw[1:3, 1:3, 7:9] = 2  # Eight false positives; removal improves aggregate Dice.
    r = compare(raw, p, l, a, box)
    assert r['targets']['lesion']['candidate']['dice'] > r['targets']['lesion']['raw']['dice']
    assert not r['screen_pass']
    assert not r['rules']['no_correct_voxels_removed']
    assert not r['rules']['no_lesion_component_overlap_lost']
    assert r['reference_lesion_components'][1]['became_undetected']
    assert r['reference_lesion_outside_pancreas_voxels'] == 1
    assert sum(x['correct_lesion_voxels_removed'] for x in r['removed_components']) == 1


def test_diagonal_connections_and_no_reference_in_selector():
    raw, p, l, a, box = fixture()
    raw[2, 2, 2] = 2
    candidate, info = select_largest_union(raw)
    assert candidate[2, 2, 2] == 2 and info['removed_voxels'] == 0
    assert list(__import__('inspect').signature(select_largest_union).parameters) == ['prediction']


@pytest.mark.parametrize('fault', ['empty', 'tie', 'lesion_only', 'bad_label'])
def test_ambiguous_or_invalid_selection_refuses(fault):
    raw = np.zeros((5, 5, 5), np.uint8)
    if fault == 'tie': raw[1, 1, 1] = raw[3, 3, 3] = 1
    if fault == 'lesion_only': raw[1, 1, 1] = 2
    if fault == 'bad_label': raw[1, 1, 1] = 3
    with pytest.raises(ValueError): select_largest_union(raw)


def test_empty_reference_is_not_reported_as_healthy_or_perfect_dice():
    empty = np.zeros((2, 2, 2), bool)
    r = binary_metrics(empty, empty, .001)
    assert all(r[k] is None for k in ['dice', 'precision', 'recall', 'relative_volume_error'])
    assert r['reference_state'] == 'empty_annotation_not_verified_healthy'
    raw, p, l, a, box = fixture(); l[:] = 0; raw[raw == 2] = 1; raw[8, 8, 8] = 2
    r = compare(raw, p, l, a, box)
    assert r['screen_pass'] and r['reference_lesion_components'] == []


def test_volume_uses_sheared_affine_determinant_and_lesion_priority():
    raw, p, l, a, box = fixture(); a[0, 1] = 2; a[0, 0] = -2
    r = compare(raw, p, l, a, box)
    assert r['voxel_ml'] == pytest.approx(.024)
    assert r['targets']['pancreas_extent']['raw']['reference_voxels'] == 27
    assert r['targets']['pancreas_parenchyma']['raw']['reference_voxels'] == 26
    assert r['reference_overlap_voxels'] == 1
    assert not r['screen_pass']  # No false-positive reduction.


@pytest.mark.parametrize('fault', ['reference', 'geometry', 'roi', 'relabel'])
def test_invalid_comparison_inputs(fault):
    raw, p, l, a, box = fixture(); candidate = raw.copy()
    if fault == 'reference': l[1, 1, 1] = 2
    if fault == 'geometry': a[0, 0] = 0
    if fault == 'roi': box[0][0] = -1
    if fault == 'relabel': candidate[4, 4, 4] = 1
    with pytest.raises(ValueError): compare_selection(raw, candidate, p, l, a, box)


def package(tmp_path):
    raw, p, l, a, box = fixture(); raw[1, 1, 1] = 1
    for name, data in [('ct', raw), ('prediction', raw), ('pancreas', p), ('lesion', l)]:
        img = nib.Nifti1Image(data, a); img.header.set_xyzt_units('mm'); nib.save(img, tmp_path/f'{name}.nii.gz')
    sha = lambda n: hashlib.sha256((tmp_path/n).read_bytes()).hexdigest()
    e = {'assistance': {'sha256': sha('pancreas.nii.gz')}, 'prediction_id': 'synthetic',
         'model_sha256': {'segmenter': 'a'*64}, 'source_identity': {'ct_sha256': sha('ct.nii.gz')},
         'reconstruction': {'native_box': box}}
    (tmp_path/'evidence.json').write_text(json.dumps(e)); (tmp_path/'result.json').write_text('{}')
    files = {k: {'uri': n, 'bytes': (tmp_path/n).stat().st_size, 'content_sha256': sha(n)}
             for k, n in [('ct', 'ct.nii.gz'), ('pred', 'prediction.nii.gz'), ('evidence', 'evidence.json'), ('result', 'result.json')]}
    m = {'schema_version': 'assisted-prediction-view-v1', 'files': files, 'request_identity': 'test',
         'prediction_id': 'synthetic', 'model_sha256': e['model_sha256'], 'case_id': 'synthetic',
         'assistance_sha256': sha('pancreas.nii.gz'), 'geometry': {'shape': list(raw.shape), 'affine': a.tolist()}}
    (tmp_path/'manifest.json').write_text(json.dumps(m))
    return raw, a


def test_real_file_export_is_distinct_and_cannot_overwrite(tmp_path):
    from scripts.compare_prediction_components import run
    raw, a = package(tmp_path)
    r = run(tmp_path, tmp_path/'pancreas.nii.gz', tmp_path/'lesion.nii.gz', tmp_path/'result')
    assert r['screen_pass'] and r['candidate_sha256'] != r['identity']['package_files']['pred']['content_sha256']
    np.testing.assert_array_equal(np.asanyarray(nib.load(tmp_path/'prediction.nii.gz').dataobj), raw)
    np.testing.assert_array_equal(nib.load(tmp_path/'result/candidate.nii.gz').affine, a)
    assert (tmp_path/'result/input-pins.json').exists()
    with pytest.raises(FileExistsError): run(tmp_path, tmp_path/'pancreas.nii.gz', tmp_path/'lesion.nii.gz', tmp_path/'result')


def test_reference_mismatch_retains_pins_and_failure_without_candidate(tmp_path):
    from scripts.compare_prediction_components import run
    package(tmp_path)
    img = nib.Nifti1Image(np.zeros((3, 3, 3), np.uint8), np.eye(4)); nib.save(img, tmp_path/'lesion.nii.gz')
    with pytest.raises(ValueError, match='geometry'):
        run(tmp_path, tmp_path/'pancreas.nii.gz', tmp_path/'lesion.nii.gz', tmp_path/'result')
    assert (tmp_path/'result/input-pins.json').exists() and (tmp_path/'result/failure.json').exists()
    assert not (tmp_path/'result/candidate.nii.gz').exists()
