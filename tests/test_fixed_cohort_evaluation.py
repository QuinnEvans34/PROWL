"""Boundary/reuse/accounting checks using synthetic saved native predictions."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import nibabel as nib
import numpy as np
import pytest
from src.inference.fixed_cohort_evaluation import (
    file_hash, write_new, validate_plan, prediction_request, run_predictions,
    score_predictions, compare_reports, ROOT,
)

PIN = 'a' * 64


def fixture(tmp_path):
    def save(name, codes):
        path = tmp_path / (name + '.nii.gz')
        image = nib.Nifti1Image(codes, np.eye(4)); image.header.set_xyzt_units('mm')
        nib.save(image, path)
        return dict(path=str(path), sha256=file_hash(path))
    z = np.zeros((2, 2, 2), np.uint8)
    lesion = z.copy(); lesion.flat[0] = 1
    refs = dict(pancreas=save('pancreas', z + 1), lesion=save('lesion', lesion), allow_unknown_units=False)
    settings = dict(models={r: dict(path=str(tmp_path / (r + '.pt')), sha256=PIN)
                            for r in ('localizer', 'segmenter')}, localizer_recipe={'fixture': True},
                    patch_size=[16]*3, tensor_shape=[16]*3, device='cpu')
    plan = dict(version=1, cohort_id='frozen-development', inference=settings,
                limits=dict(seconds_per_case=10, total_seconds=30, rss_bytes=1000000, free_floor_bytes=1),
                cases=[dict(case_id='a', ct=save('ct', z), references=refs, reference_state='positive',
                            flags=['annotation concern'])], limitations=['Development only'])
    return plan, lesion


def runner(codes):
    def run(request_path, log, seconds, rss):
        request = json.loads(request_path.read_text())
        assert set(request) == {'models', 'localizer_recipe', 'patch_size', 'tensor_shape', 'device',
                                'max_sampling_voxels', 'region_policy', 'ct_path', 'ct_sha256', 'case_id', 'output_dir'}
        assert 'references' not in request and 'reference_state' not in request
        directory = Path(request['output_dir']); directory.mkdir()
        image = nib.Nifti1Image(codes, np.eye(4)); image.header.set_xyzt_units('mm')
        nib.save(image, directory / 'prediction.nii.gz')
        write_new(directory / 'result.json', dict(case_id=request['case_id'], status='complete', reference_inputs_used=False,
             prediction_sha256=file_hash(directory / 'prediction.nii.gz'), spatial_units=dict(interpreted_units='mm'),
             evidence=dict(component='autonomous-cascade-v1', reference_inputs_used=False,
                 source_identity=dict(study_id=request['case_id'], ct_sha256=request['ct_sha256']),
                 model_sha256={r: PIN for r in ('localizer', 'segmenter')},
                 region_plan=dict(transform=dict(tensor_shape=request['tensor_shape'])), localizer_recipe=request['localizer_recipe'], patch_size=request['patch_size'], device=request['device'],
                 localizer_decision='argmax_then_' + request['region_policy'])))
        return dict(seconds=.01, workers_reaped=True)
    return run


def test_separate_scoring_and_reference_free_request(tmp_path):
    plan, lesion = fixture(tmp_path)
    # No label reads in prediction: remove both label paths until scoring.
    refs = [Path(plan['cases'][0]['references'][r]['path']) for r in ('pancreas', 'lesion')]
    raw = [p.read_bytes() for p in refs]
    for path in refs: path.unlink()
    journal = run_predictions(validate_plan(plan), PIN, tmp_path / 'out', runner(lesion * 2))
    for path, data in zip(refs, raw): path.write_bytes(data)
    report = score_predictions(plan, PIN, journal)
    assert report['summary']['positive_lesion_macro_dice'] == dict(value=1, n=1)
    assert report['rows'][0]['flags'] == ['annotation concern']
    with pytest.raises(FileExistsError): run_predictions(plan, PIN, tmp_path / 'out', runner(lesion * 2))


def reusable(tmp_path):
    plan, lesion = fixture(tmp_path)
    run_predictions(plan, PIN, tmp_path / 'original', runner(lesion * 2))
    directory = tmp_path / 'original/a/prediction'
    request = directory.parent / 'request.json'
    plan['cases'][0]['reuse'] = dict(directory=str(directory), result_sha256=file_hash(directory / 'result.json'),
                                   request=dict(path=str(request), sha256=file_hash(request)))
    return plan


def test_reuse_on_different_drive_roots_without_ct_or_models(tmp_path):
    plan = reusable(tmp_path)
    plan['cases'][0]['ct']['path'] = '/absent/new-root/ct.nii.gz'
    for model in plan['inference']['models'].values(): model['path'] = '/absent/weights.pt'
    def forbidden(*args): raise AssertionError('Compatible reuse must not execute models')
    journal = run_predictions(plan, PIN, tmp_path / 'reuse', forbidden)
    assert json.loads(journal.read_text())['status'] == 'reused'
    assert score_predictions(plan, PIN, journal)['summary']['scored_cases'] == 1


@pytest.mark.parametrize('change', ['ct', 'model', 'policy', 'tensor', 'capacity', 'units', 'receipt', 'prediction', 'request'])
def test_incompatible_or_tampered_reuse_is_visible_failure(tmp_path, change):
    plan = reusable(tmp_path); case = plan['cases'][0]
    if change == 'ct': case['ct']['sha256'] = 'b'*64
    elif change == 'model': plan['inference']['models']['segmenter']['sha256'] = 'b'*64
    elif change == 'policy': plan['inference']['region_policy'] = 'largest_component_26'
    elif change == 'tensor': plan['inference']['tensor_shape'] = [24]*3
    elif change == 'capacity': plan['inference']['max_sampling_voxels'] = 64_000_000
    elif change == 'units': case['spatial_units_review'] = {'fabricated': True}
    else:
        target = (Path(case['reuse']['request']['path']) if change == 'request' else
                  Path(case['reuse']['directory']) / ('result.json' if change == 'receipt' else 'prediction.nii.gz'))
        target.write_bytes(target.read_bytes() + b' ')
    journal = run_predictions(plan, PIN, tmp_path / 'reuse', lambda *args: pytest.fail('No automatic retry'))
    report = score_predictions(plan, PIN, journal)
    assert report['summary']['failed_or_unscored_cases'] == 1
    assert report['summary']['positive_lesion_macro_dice']['value'] is None


def test_full_accounting_resource_failure_and_continue(tmp_path):
    plan, lesion = fixture(tmp_path)
    second = deepcopy(plan['cases'][0]); second['case_id'] = 'b'; plan['cases'].append(second)
    calls = []
    def fail_first(*args):
        calls.append(args)
        if len(calls) == 1: raise ValueError('unknown CT units')
        return runner(lesion * 2)(*args)
    journal = run_predictions(plan, PIN, tmp_path / 'out', fail_first)
    report = score_predictions(plan, PIN, journal)
    assert report['summary']['fixed_cases'] == 2 and report['summary']['scored_cases'] == 1
    assert report['summary']['unscored_reference_states'] == {'positive': 1}
    assert report['rows'][0]['inference_error'] == 'unknown CT units'
    plan['limits']['free_floor_bytes'] = 10**30
    journal = run_predictions(plan, PIN, tmp_path / 'limited', lambda *a: pytest.fail('resource ceiling'))
    assert all(json.loads(s)['status'] == 'not_run_resource_limit' for s in journal.read_text().splitlines())


def test_journal_missing_reordered_changed_plan_refused(tmp_path):
    plan, lesion = fixture(tmp_path)
    journal = run_predictions(plan, PIN, tmp_path / 'out', runner(lesion * 2))
    with pytest.raises(ValueError, match='pinned plan'): score_predictions(plan, 'b'*64, journal)
    journal.write_text('')
    with pytest.raises(ValueError, match='pinned plan'): score_predictions(plan, PIN, journal)
    plan['cases'].append(deepcopy(plan['cases'][0]))
    with pytest.raises(ValueError, match='Duplicate'): validate_plan(plan)


def test_matched_comparison_accounts_for_failures_and_rejects_different_refs(tmp_path):
    plan, lesion = fixture(tmp_path)
    journal = run_predictions(plan, PIN, tmp_path / 'out', runner(lesion * 2))
    baseline = score_predictions(plan, PIN, journal); candidate = deepcopy(baseline)
    candidate['rows'][0]['score']['metrics']['lesion']['dice'] = .5
    result = compare_reports(baseline, candidate)
    assert result['worsened_positive_cases'] == 1
    assert result['rows'][0]['deltas']['lesion.dice'] == -.5
    candidate['rows'][0]['scoring_status'] = 'failed'
    assert compare_reports(baseline, candidate)['unpaired_cases'] == 1
    candidate['rows'][0]['reference_sha256']['lesion'] = 'b'*64
    with pytest.raises(ValueError, match='identity'): compare_reports(baseline, candidate)
    candidate['rows'] = []
    with pytest.raises(ValueError, match='cohort'): compare_reports(baseline, candidate)


def test_cli_reuse_then_score_in_separate_processes(tmp_path):
    plan = reusable(tmp_path)
    path = tmp_path / 'plan.json'; write_new(path, plan); pin = file_hash(path)
    prefix = [sys.executable, str(ROOT / 'scripts/evaluate_autonomous_cohort.py')]
    subprocess.run(prefix + ['predict', '--plan', str(path), '--plan-sha256', pin,
                            '--output-dir', str(tmp_path / 'cli')], check=True, capture_output=True)
    subprocess.run(prefix + ['score', '--plan', str(path), '--plan-sha256', pin,
                            '--journal', str(tmp_path / 'cli/journal.jsonl'), '--report', str(tmp_path / 'report.json')],
                   check=True, capture_output=True)
    report = tmp_path / 'report.json'
    assert json.loads(report.read_text())['summary']['scored_cases'] == 1
    subprocess.run(prefix + ['compare', '--baseline', str(report), '--baseline-sha256', file_hash(report),
                            '--candidate', str(report), '--candidate-sha256', file_hash(report),
                            '--report', str(tmp_path / 'comparison.json')], check=True, capture_output=True)
    assert json.loads((tmp_path / 'comparison.json').read_text())['tied_positive_cases'] == 1


def test_real_synthetic_cascade_through_evaluator(tmp_path):
    import torch
    from src.inference.autonomous_cascade_v1 import run_case

    class Localizer(torch.nn.Module):
        def forward(self, x): return torch.cat((.4-x, x-.4), dim=1)

    class Segmenter(torch.nn.Module):
        def forward(self, x): return torch.cat((.2-x, torch.zeros_like(x), x-.2), dim=1)

    plan, _ = fixture(tmp_path)
    image = np.full((32, 32, 32), -100, np.float32); image[10:22, 10:22, 10:22] = 150
    for role, array in [('ct', image), ('pancreas', (image > 0).astype(np.uint8)),
                        ('lesion', (image > 0).astype(np.uint8))]:
        path = tmp_path / (role + '.nii.gz')
        im = nib.Nifti1Image(array, np.eye(4)); im.header.set_xyzt_units('mm'); nib.save(im, path)
        if role == 'ct': plan['cases'][0]['ct']['sha256'] = file_hash(path)
        else: plan['cases'][0]['references'][role]['sha256'] = file_hash(path)
    plan['inference']['localizer_recipe'] = dict(schema_version='4.0.0', component='pancreas-localizer-preprocessing-v4',
        orientation='RAS', image_interpolation='bilinear', target_interpolation='nearest', padding_mode='constant_zero',
        crop='none', augmentation='none', cache='none', workers=0, spacing_mm=[2., 2., 2.],
        hu_window=[-100., 300.], minimum_shape=[16]*3, max_source_voxels=96_000_000, max_output_voxels=16_000_000)
    plan['inference']['tensor_shape'] = [24]*3
    def real_runner(request_path, *args):
        request = json.loads(request_path.read_text()); models = request.pop('models')
        ct = request.pop('ct_path'); out = request.pop('output_dir'); pin = request.pop('ct_sha256')
        run_case(ct, out, expected_ct_sha256=pin, localizer=Localizer(), segmenter=Segmenter(),
                 localizer_sha256=models['localizer']['sha256'], segmenter_sha256=models['segmenter']['sha256'], **request)
        return {'seconds': 0, 'workers_reaped': True}
    journal = run_predictions(plan, PIN, tmp_path / 'actual', real_runner)
    report = score_predictions(plan, PIN, journal)
    assert report['summary']['scored_cases'] == 1
    assert report['rows'][0]['score']['metrics']['lesion']['dice'] > 0
    assert nib.load(tmp_path / 'actual/a/prediction/prediction.nii.gz').shape == image.shape


def test_mps_lock_refuses_duplicate_before_creating_output(tmp_path):
    fcntl = pytest.importorskip('fcntl')
    plan, _ = fixture(tmp_path); plan['inference']['device'] = 'mps'
    with (ROOT / 'outputs/prowl/.mps-profile.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            run_predictions(plan, PIN, tmp_path / 'duplicate', lambda *a: pytest.fail('No competing GPU job'))
    assert not (tmp_path / 'duplicate').exists()
