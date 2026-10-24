import json
import numpy as np
import pytest
from src.data.pants_errata_v1 import EXPECTED, VERSION
from src.data.pants_errata_cache_v1 import load_target
from src.training.experiment_config import sha256


@pytest.fixture
def cache(tmp_path):
    name = sorted(EXPECTED)[0]
    target = np.zeros((4, 5, 6), dtype=np.uint8)
    target[1:3, 2:4, 2:4] = 1
    np.savez_compressed(tmp_path / (name + '.npz'), target=target)
    meta = dict(name=name, positive=False, lesion_voxels=0, label_revision_sha256='a'*64,
                geometry=dict(shape=list(target.shape)), pancreas_source_voxels=int(target.sum()))
    (tmp_path / (name + '.json')).write_text(json.dumps(meta))
    member = dict(target_sha256=sha256(tmp_path/(name+'.npz')), metadata_sha256=sha256(tmp_path/(name+'.json')))
    manifest = dict(version=VERSION, overlay_sha256='a'*64, members={n: member for n in EXPECTED})
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    args = dict(role='train', manifest_sha256=sha256(tmp_path/'manifest.json'), overlay_sha256='a'*64)
    return tmp_path, name, target, args


def test_exact_roundtrip(cache):
    root, name, target, args = cache
    loaded, meta = load_target(root, name, **args)
    assert np.array_equal(loaded, target) and not meta['positive']


@pytest.mark.parametrize('override', [dict(role='development'), dict(role='test'),
    dict(manifest_sha256='b'*64), dict(overlay_sha256='b'*64)])
def test_scope_and_binding_rejected(cache, override):
    root, name, _, args = cache
    with pytest.raises(ValueError): load_target(root, name, **(args | override))


def test_unlisted_rejected(cache):
    root, _, _, args = cache
    with pytest.raises(ValueError): load_target(root, 'PanTS_00000999', **args)


@pytest.mark.parametrize('extension', ['.npz', '.json'])
def test_tampered_member_rejected(cache, extension):
    root, name, _, args = cache
    with (root/(name+extension)).open('ab') as f: f.write(b'changed')
    with pytest.raises(ValueError): load_target(root, name, **args)


def test_old_lesion_target_rejected_even_with_updated_file_hash(cache):
    root, name, target, args = cache
    target[0,0,0] = 2
    np.savez_compressed(root/(name+'.npz'), target=target)
    path = root/'manifest.json'
    manifest = json.loads(path.read_text())
    manifest['members'][name]['target_sha256'] = sha256(root/(name+'.npz'))
    path.write_text(json.dumps(manifest))
    args['manifest_sha256'] = sha256(path)
    with pytest.raises(ValueError): load_target(root, name, **args)
