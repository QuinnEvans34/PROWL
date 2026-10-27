import json
from pathlib import Path
from unittest.mock import patch
import pytest
from test_generated_target_admission_v1 import inputs
from src.data.manifest_records import canonical
from src.data.segmenter_teacher_cache_v1 import sha, TeacherTargetStore
from src.data.teacher_target_publication_v1 import publish
from scripts.diagnostics.admit_rsuper_full_targets import main


def fixture(tmp_path):
    root = tmp_path / 'producer'; root.mkdir()
    provider, request, result, resources = inputs(root)
    pins = {'provider_sha256': provider.pin}
    for name, value in [('request', request), ('result', result), ('resources', resources)]:
        path = root / (name + '.json'); path.write_bytes(canonical(value))
        pins[name + '_sha256'] = sha(path)
    return root, provider, pins


def test_publication_consumed_by_existing_store_preserves_producer(tmp_path):
    root, provider, pins = fixture(tmp_path)
    before = {p.name: sha(p) for p in root.iterdir()}
    output = tmp_path / 'admitted'
    result = publish(root, output, provider, **pins)
    common = json.loads((output / 'common-identity.json').read_text())
    store = TeacherTargetStore(output, result['manifest_sha256'], control=provider.control,
                               common_identity=common)
    assert store.manifest['complete'] and not store.manifest['qualification_only']
    assert result['scientific_ready'] is False
    assert (output / 'A.npz').is_symlink()
    assert {p.name: sha(p) for p in root.iterdir()} == before
    with pytest.raises(FileExistsError): publish(root, output, provider, **pins)


@pytest.mark.parametrize('fault', ['request', 'result', 'resources', 'provider', 'payload', 'incomplete'])
def test_rejected_inputs_do_not_publish(tmp_path, fault):
    root, provider, pins = fixture(tmp_path)
    if fault in ('request', 'result', 'resources', 'provider'):
        pins[fault + '_sha256'] = '0' * 64
    elif fault == 'payload':
        (root / 'A.npz').write_bytes(b'bad')
    else:
        path = root / 'result.json'; value = json.loads(path.read_text())
        value['complete'] = False; path.write_bytes(canonical(value)); pins['result_sha256'] = sha(path)
    with pytest.raises(ValueError): publish(root, tmp_path / 'admitted', provider, **pins)
    assert not (tmp_path / 'admitted').exists()


def test_failed_publication_preserved_and_not_consumable(tmp_path):
    root, provider, pins = fixture(tmp_path)
    output = tmp_path / 'admitted'
    with patch('src.data.teacher_target_publication_v1.os.link', side_effect=OSError('disk full')):
        with pytest.raises(OSError): publish(root, output, provider, **pins)
    assert output.exists() and (output / 'manifest.pending').exists()
    assert not (output / 'manifest.json').exists()
    with pytest.raises(FileExistsError): publish(root, output, provider, **pins)


def test_no_publication_inside_producer(tmp_path):
    root, provider, pins = fixture(tmp_path)
    with pytest.raises(ValueError): publish(root, root / 'admitted', provider, **pins)


def argv(root, out, pins):
    args = ['--targets', str(root), '--output', str(out)]
    for key, value in pins.items(): args += ['--' + key.replace('_', '-'), value]
    return args


def test_cli_rejects_unreaped_before_provider_or_preflight(tmp_path):
    root, provider, pins = fixture(tmp_path)
    path = root / 'resources.json'; value = json.loads(path.read_text())
    value['workers_reaped'] = False; path.write_bytes(canonical(value)); pins['resources_sha256'] = sha(path)
    def forbidden(): raise AssertionError('must not run')
    with pytest.raises(ValueError, match='reaped'):
        main(argv(root, tmp_path/'out', pins), provider_factory=forbidden, preflight=forbidden)


def test_cli_rejects_small_provider(tmp_path):
    root, provider, pins = fixture(tmp_path)
    with pytest.raises(ValueError, match='1333/70'):
        main(argv(root, tmp_path/'out', pins), provider_factory=lambda: provider, preflight=lambda: None)


def test_full_count_cli_publishes_synthetic_cohort(tmp_path, capsys):
    from copy import deepcopy
    from src.data.manifest_records import digest
    import os
    root, provider, pins = fixture(tmp_path)
    request = json.loads((root/'request.json').read_text())
    result = json.loads((root/'result.json').read_text())
    template = result['members']['A']
    names = [f'Train_{i:04d}' for i in range(1333)]
    provider.control = dict(train=names, validation=[f'Dev_{i:03d}' for i in range(70)])
    provider.pin = digest(canonical(provider.control)); pins['provider_sha256'] = provider.pin
    request['train'] = names; result['members'] = {}
    for name in names:
        os.link(root/'A.npz', root/(name+'.npz'))
        row = deepcopy(template); row['case_id'] = name; result['members'][name] = row
    for name, value in [('request', request), ('result', result)]:
        path = root/(name+'.json'); path.write_bytes(canonical(value)); pins[name+'_sha256'] = sha(path)
    output = tmp_path/'published'
    answer = main(argv(root, output, pins), provider_factory=lambda: provider, preflight=lambda: None)
    assert answer['members'] == 1333
    assert json.loads(capsys.readouterr().out)['scientific_ready'] is False
    store = TeacherTargetStore(output, answer['manifest_sha256'], control=provider.control,
                               common_identity=json.loads((output/'common-identity.json').read_text()))
    assert set(store.manifest['members']) == set(names)
    # References are checked again at consumption, not trusted forever.
    (root/(names[0]+'.npz')).write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='payload changed'):
        store.window(names[0], provider.small, {'native': provider.small['geometry']}, [0,0,0])


def test_real_cli_process_rejects_incomplete_generation(tmp_path):
    import os
    import subprocess
    import sys
    root, provider, pins = fixture(tmp_path)
    path = root/'result.json'; value = json.loads(path.read_text())
    value['complete'] = False; path.write_bytes(canonical(value)); pins['result_sha256'] = sha(path)
    output = tmp_path/'out'
    completed = subprocess.run([sys.executable, 'scripts/diagnostics/admit_rsuper_full_targets.py',
                               *argv(root, output, pins)], capture_output=True, text=True,
                              timeout=30, env=dict(os.environ, CUDA_VISIBLE_DEVICES='-1'))
    assert completed.returncode != 0
    assert 'Successful complete, reaped generation required' in completed.stderr
    assert not output.exists()
