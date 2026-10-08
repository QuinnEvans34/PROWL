import csv
import json
from copy import deepcopy

import pytest
import yaml

from src.training import experiment_config as E


@pytest.fixture
def experiment(tmp_path, monkeypatch):
    monkeypatch.setattr(E, 'REPO_ROOT', tmp_path)
    spec = yaml.safe_load((E.resolve('configs/experiments/full_suprem.yaml')).read_text())
    spec['base_config'] = str(E.resolve('configs/level45.yaml'))
    spec['initialization'] = dict(kind='scratch', checkpoint=None, sha256=None, source_review=None)
    spec['run'].update(max_seconds=60, min_free_bytes=1)
    cohort = spec['cohort']
    names = {'train_ids': [f't{i}' for i in range(9)], 'development_ids': ['v1', 'v2'],
             'original_train_ids': [f't{i}' for i in range(9)], 'original_development_ids': ['v1', 'v2'], 'test_ids': ['test']}
    for key, values in names.items():
        path = tmp_path / f'{key}.txt'; path.write_text('\n'.join(values)); cohort[key] = str(path)
    path = tmp_path / 'manifest.csv'; cohort['manifest'] = str(path)
    payload = tmp_path / 'invented-placeholder'; payload.write_text('metadata fixture, never decoded')
    with path.open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=['case_id', 'ct_path', 'pancreas_path', 'lesion_path']); writer.writeheader()
        for name in names['train_ids'] + names['development_ids']:
            writer.writerow(dict(case_id=name, ct_path=str(payload), pancreas_path=str(payload), lesion_path=str(payload)))
    review = tmp_path / 'review.json'; cohort['review'] = str(review)
    review.write_text(json.dumps(dict(decision='accepted', input_sha256={k: E.sha256(cohort[k]) for k in (*names, 'manifest')}, evidence=['invented unit fixture'])))
    config = tmp_path / 'experiment.yaml'; config.write_text(yaml.safe_dump(spec))
    return spec, config, tmp_path


def load(experiment):
    spec, path, _ = experiment; path.write_text(yaml.safe_dump(spec)); return E.load_experiment(path)


@pytest.mark.parametrize('steps', [24000, 72000, 100000])
def test_arbitrary_full_horizon_and_cohort(experiment, steps):
    experiment[0]['run']['max_updates'] = steps
    cfg = load(experiment); result = E.preflight(cfg, inspect_payload_paths=True)
    assert result['ready'], result
    assert (result['train_cases'], result['development_cases'], result['max_updates']) == (9, 2, steps)
    assert not (experiment[2] / 'outputs').exists()


def test_duplicate_and_cross_role_members_refused(experiment):
    spec, _, _ = experiment
    path = E.resolve(spec['cohort']['train_ids']); path.write_text('t0 t0')
    assert any('duplicate' in s for s in E.preflight(load(experiment))['errors'])
    path.write_text('t0 v1 test')
    errors = E.preflight(load(experiment))['errors']
    assert any('overlap' in s for s in errors)
    assert any('original training' in s for s in errors)


def test_manifest_missing_member_and_stale_review(experiment):
    path = E.resolve(experiment[0]['cohort']['manifest'])
    path.write_text('\n'.join(path.read_text().splitlines()[:-1]) + '\n')
    errors = E.preflight(load(experiment))['errors']
    assert any('Missing manifest member' in s for s in errors)
    assert any('exact files' in s for s in errors)


def test_review_does_not_make_missing_sources_ready(experiment):
    (experiment[2] / 'invented-placeholder').unlink()
    assert E.preflight(load(experiment))['ready']  # metadata-only is explicitly labelled
    assert not E.preflight(load(experiment), inspect_payload_paths=True)['ready']


def test_isolated_outputs_and_no_reuse(experiment):
    cfg = load(experiment)
    with pytest.raises(ValueError, match='source path'):
        E.prepare_run(cfg, E.preflight(cfg))
    E.prepare_run(cfg, E.preflight(cfg, inspect_payload_paths=True))
    output = E.resolve(cfg['paths']['output_dir'])
    assert (output / 'resolved.yaml').exists()
    assert (output / 'splits' / 'test.txt').read_text() == 'test'
    assert not E.preflight(cfg)['ready']
    with pytest.raises(FileExistsError): E.prepare_run(cfg, {'ready': True, 'payload_paths_checked': True})


def test_suprem_never_implicitly_switches_to_scratch(experiment):
    experiment[0]['initialization'] = dict(kind='suprem', checkpoint='missing.pth', sha256='a'*64, source_review=None)
    cfg = load(experiment)
    result = E.preflight(cfg)
    assert not result['ready'] and any('SuPreM source' in s for s in result['errors'])
    assert cfg['transfer']['use_pretrained'] is True


@pytest.mark.parametrize('value', [0, -1, True, 2.5])
def test_invalid_horizon(experiment, value):
    experiment[0]['run']['max_updates'] = value
    with pytest.raises(ValueError): load(experiment)


def test_runtime_limit_retains_outputs(experiment):
    cfg = load(experiment); E.prepare_run(cfg, E.preflight(cfg, inspect_payload_paths=True))
    with pytest.raises(RuntimeError, match='runtime limit'): E.check_resources(cfg, elapsed=60)
    assert E.resolve(cfg['paths']['output_dir']).is_dir()


def test_suprem_strict_backbone_and_fresh_head(tmp_path):
    import torch
    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__(); self.backbone = torch.nn.Linear(2, 2)
            self.conv_final = torch.nn.Sequential(torch.nn.Identity(), torch.nn.Identity(), torch.nn.Module())
            self.conv_final[2].conv = torch.nn.Linear(2, 3)
    model = Model(); original = deepcopy(model.state_dict()); state = deepcopy(original)
    state['backbone.weight'].fill_(0.5)
    state['conv_final.2.conv.weight'] = torch.zeros(32, 2)
    state['conv_final.2.conv.bias'] = torch.zeros(32)
    path = tmp_path / 'invented.pth'; torch.save({'net': state}, path)
    init = dict(checkpoint=str(path), sha256=E.sha256(path))
    E.load_suprem_checked(model, init)
    assert torch.equal(model.state_dict()['conv_final.2.conv.weight'], original['conv_final.2.conv.weight'])
    assert torch.all(model.backbone.weight == 0.5)
    state['extra'] = torch.ones(1); torch.save({'net': state}, path); init['sha256'] = E.sha256(path)
    with pytest.raises(ValueError, match='tensor names'): E.load_suprem_checked(model, init)
    init['sha256'] = '0'*64
    with pytest.raises(ValueError, match='hash'): E.load_suprem_checked(model, init)


def test_actual_cpu_training_validation_and_checkpoints(experiment):
    """Exercise the real entry point on invented volumes, beyond the old six/one cohort."""
    import os
    import subprocess
    import sys
    import nibabel as nib
    import numpy as np
    import torch
    spec, config, directory = experiment
    shape = (16, 16, 16)
    pancreas = np.zeros(shape, dtype=np.uint8); pancreas[3:13, 3:13, 3:13] = 1
    lesion = np.zeros(shape, dtype=np.uint8); lesion[7:10, 7:10, 7:10] = 1
    arrays = {'ct_path': pancreas.astype(np.float32) * 100, 'pancreas_path': pancreas, 'lesion_path': lesion}
    paths = {}
    for key, array in arrays.items():
        path = directory / f'{key}.nii.gz'; nib.save(nib.Nifti1Image(array, np.eye(4)), path); paths[key] = str(path)
    manifest = E.resolve(spec['cohort']['manifest'])
    with manifest.open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=['case_id', *paths]); writer.writeheader()
        for name in [f't{i}' for i in range(9)] + ['v1', 'v2']: writer.writerow(dict(case_id=name, **paths))
    review = E.resolve(spec['cohort']['review']); record = json.loads(review.read_text())
    record['input_sha256']['manifest'] = E.sha256(manifest); review.write_text(json.dumps(record))
    spec['recipe'] = {'device': 'cpu', 'model': {'init_filters': 8, 'blocks_down': [1, 1], 'blocks_up': [1]},
                      'preprocessing': {'whole_box': True, 'roi_source': 'pancreas', 'crop_native_margin_vox': 2},
                      'sampling': {'patch_size': [16]*3, 'num_samples': 1},
                      'inference': {'sw_roi_size': [16]*3}, 'training': {'num_workers': 0}}
    # Non-divisible final interval exercises terminal validation as well as the periodic checkpoint.
    spec['run'].update(max_updates=3, validate_every=2, checkpoint_every=2, log_every=1, cache='none')
    load(experiment)
    program = ('import sys,torch; from pathlib import Path; torch.set_num_threads(1); '
               'from src.training import experiment_config as E; E.REPO_ROOT=Path(sys.argv[1]); '
               'from scripts.train import main; sys.argv=["train.py","--experiment",sys.argv[2]]; main()')
    result = subprocess.run([sys.executable, '-c', program, str(directory), str(config)],
                            cwd=E.resolve('.'), env={**os.environ, 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'},
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '[val @ 2]' in result.stdout and '[val @ 3]' in result.stdout
    output = directory / 'outputs' / 'experiments' / spec['name']
    last = list(output.glob('checkpoints/*/last.pt'))
    assert len(last) == 1
    checkpoint = torch.load(last[0], map_location='cpu', weights_only=False)
    assert checkpoint['step'] == 3 and checkpoint['extra']['total_iters'] == 3
    assert checkpoint['extra']['cohort_sha256']['train'] == record['input_sha256']['train_ids']
    assert list(output.glob('checkpoints/*/best.pt'))
    events = [json.loads(line) for line in (output / 'metrics.jsonl').read_text().splitlines()]
    assert [e['step'] for e in events if e['event'] == 'update'] == [1, 2, 3]
    assert [e['step'] for e in events if e['event'] == 'validation'] == [2, 3]
    assert events[-1] == dict(event='finished', state='complete', completed_updates=3)
