from copy import deepcopy
import hashlib
import json

import numpy as np
import pytest
from scipy.ndimage import label
import torch

from test_segmenter_full import Invented, config
from src.data.manifest_records import canonical, digest
from src.data.segmenter_full_batch_v1 import array_hash
from src.training.experiment_config import sha256
from src.training.segmenter_full_session_v1 import Session
from src.training.segmenter_augmentation_v1 import POLICY, augment, support_mask, OptimizerViews, AugmentedSession
from src.training.segmenter_augmented_executor_v1 import execute
from scripts.diagnostics.profile_lenovo_real_segmenter import compare


def fixture():
    y = np.zeros((16, 16, 16), np.uint8)
    y[3:9, 4:8, 4:12] = 1
    y[4:6, 5:7, 5:7] = 2; y[7:9, 5:7, 8:10] = 2
    x = y[None].astype(np.float32)/2
    return x, y, dict(pad_low=[2, 3, 1], normalized_shape=[10, 9, 14])


class PreparedInvented(Invented):
    def __init__(self, root):
        super().__init__(); self.root = root; self.members = {}
        for name in self.control['train']+self.control['validation']:
            path = root/(name+'.json')
            path.write_bytes(canonical(dict(transform=dict(pad_low=[0]*3, normalized_shape=[16]*3))))
            self.members[name] = dict(metadata_sha256=sha256(path))
        self.control['members'] = self.members; self.pin = digest(canonical(self.control))


def make(root, steps=4):
    torch.set_num_threads(2); p = PreparedInvented(root)
    return p, AugmentedSession(Session(config(steps), p.control, device='cpu', initialization={'kind':'scratch'}))


def test_exact_stateless_seed_and_no_source_mutation():
    x, y, t = fixture(); old = x.copy(), y.copy()
    a = augment(x, y, t, seed=42, update=1, case_id='case')
    b = augment(x, y, t, seed=42, update=1, case_id='case')
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and a[2] == b[2]
    assert a[2]['seed'] == int.from_bytes(hashlib.sha256(f'{POLICY}:42:1:case'.encode()).digest()[:8], 'little')
    assert np.array_equal(x, old[0]) and np.array_equal(y, old[1])


def test_alignment_topology_padding_and_all_branches():
    x, y, t = fixture(); seen = set(); distinct = set()
    for update in range(1, 161):
        ax, ay, trace = augment(x, y, t, seed=42, update=update, case_id='case')
        expected, support = y.copy(), support_mask(y.shape, t)
        for axis, flip in enumerate(trace['flips']):
            if flip: expected, support = np.flip(expected, axis), np.flip(support, axis); seen.add('flip'+str(axis))
        if trace['rotation_k']:
            expected, support = (np.rot90(a, trace['rotation_k'], axes=(0, 1)) for a in (expected, support))
            seen.add('rotate'+str(trace['rotation_k']))
        assert np.array_equal(ay, expected)
        assert not ax[0, ~support].any() and not ay[~support].any()
        assert np.array_equal(np.bincount(y.ravel()), np.bincount(ay.ravel()))
        assert label(ay == 2)[1] == label(y == 2)[1] == 2
        assert ax.dtype == np.float32 and ay.dtype == np.uint8
        assert np.isfinite(ax).all() and ax.min() >= 0 and ax.max() <= 1
        if trace['intensity_scale'] is not None: seen.add('scale')
        if trace['intensity_shift'] is not None: seen.add('shift')
        if trace['gaussian_noise']: seen.add('noise')
        distinct.add(array_hash(ax))
    assert seen == {'flip0', 'flip1', 'flip2', 'rotate1', 'rotate2', 'rotate3', 'scale', 'shift', 'noise'}
    assert len(distinct) > 60


def test_valid_zero_intensities_are_not_padding():
    x, y, t = fixture(); x[:] = 0
    for update in range(1, 100):
        ax, _, trace = augment(x, y, t, seed=42, update=update, case_id='case')
        if (trace['intensity_shift'] or 0) > 0:
            assert np.count_nonzero(ax) == trace['valid_voxels']; break
    else: pytest.fail('No positive shift exercised')


@pytest.mark.parametrize('bad', ['padding', 'support', 'label', 'nan', 'update'])
def test_invalid_inputs_refused(bad):
    x, y, t = fixture(); update = 1
    if bad == 'padding': x[0, 0, 0, 0] = .3
    if bad == 'support': t['normalized_shape'] = [30]*3
    if bad == 'label': y[4, 4, 4] = 3
    if bad == 'nan': x[0, 5, 5, 5] = np.nan
    if bad == 'update': update = 0
    with pytest.raises(ValueError): augment(x, y, t, seed=42, update=update, case_id='case')


def test_rng_isolation():
    x, y, t = fixture(); np.random.seed(123); expected = np.random.random(8)
    np.random.seed(123); before = torch.get_rng_state().clone()
    augment(x, y, t, seed=42, update=1, case_id='case')
    assert np.array_equal(np.random.random(8), expected) and torch.equal(before, torch.get_rng_state())


def test_provider_guard_metadata_and_trace(tmp_path):
    p, s = make(tmp_path)
    a = OptimizerViews(p, seed=42, update=1)
    with pytest.raises(ValueError, match='optimizer-only'): a.get('v0', role='validation', operation='evaluator')
    result = s.update(p)
    assert result['batch_sha256'] == result['augmentation']['transformed_batch_sha256']
    name = s.next_member(); (tmp_path/(name+'.json')).write_text('{}')
    with pytest.raises(ValueError, match='metadata changed'): s.update(p)


@pytest.mark.parametrize('step', [0, 1, 3])
def test_exact_restore_next_update_and_unchanged_evaluation(tmp_path, step):
    p, s = make(tmp_path)
    for _ in range(step): s.update(p)
    saved = deepcopy(s.state()); other = AugmentedSession.restore(saved, s.identity)
    compare(saved, other.state(), exact=True)
    # Native and tensor evaluation call the unaugmented raw batch path.
    b = s._batch(p, 'v0', 'validation', 'evaluator')[0]
    assert b.hashes() == p.get('v0', role='validation', operation='evaluator').hashes()
    assert s.evaluate_case(p, 'v0') == s.raw.evaluate_case(p, 'v0')
    compare(saved, s.state(), exact=True)
    assert s.update(p) == other.update(p); compare(s.state(), other.state(), exact=True)


@pytest.mark.parametrize('bad', ['identity', 'numpy', 'raw', 'mutate'])
def test_corrupt_or_changed_identity_refused(tmp_path, bad):
    p, s = make(tmp_path); s.update(p); state = s.state(); identity = deepcopy(s.identity)
    if bad == 'identity': state['identity']['augmentation']['policy'] = 'other'
    if bad == 'numpy': identity['augmentation']['numpy_version'] = 'other'
    if bad == 'raw': state['raw']['identity']['config']['seed'] = 7
    if bad == 'mutate':
        s.identity['augmentation']['policy'] = 'other'
        with pytest.raises(ValueError): s.update(p)
        return
    with pytest.raises(ValueError): AugmentedSession.restore(state, identity)


def test_case_order_matches_unaugmented_sampler(tmp_path):
    p, s = make(tmp_path, 20)
    raw = Session(config(20), p.control, device='cpu', initialization={'kind':'scratch'})
    for step in range(20):
        s.raw.step = raw.step = step
        assert s.next_member() == raw.next_member()


def test_executor_checkpoints_native_endpoints_and_ties(tmp_path):
    cache = tmp_path/'cache'; cache.mkdir(); p, s = make(cache); seen = []
    original = s.raw.evaluate_case
    def fixed(provider, name):
        row = original(provider, name); row['metrics']['lesion']['dice'] = .5; return row
    s.raw.evaluate_case = fixed
    result = execute(s, p, tmp_path/'run', validate_every=2, checkpoint_every=2, retain_steps=[2, 4],
                     track=seen.append, native=lambda raw, provider, name: raw.evaluate_case(provider, name))
    assert result['completed_updates'] == 4 and result['selected_step'] == 2
    assert len([r for r in seen if r['event'] == 'update' and 'augmentation' in r]) == 4
    assert {r['variant'] for r in seen if r['event'] == 'validation'} == {'raw'}
    assert len([r for r in seen if r['event'] == 'native_case']) == 4
    assert seen[-1]['event'] == 'completed'
    assert json.loads((tmp_path/'run/native-selected.json').read_text())['step'] == 2
    assert json.loads((tmp_path/'run/native-terminal.json').read_text())['step'] == 4
    for name in ('initial.pt', 'last.pt', 'best.pt', 'step-000002.pt', 'step-000004.pt'):
        AugmentedSession.restore(torch.load(tmp_path/'run'/name, weights_only=True)['session'], s.identity)
    with pytest.raises(FileExistsError): execute(s, p, tmp_path/'run')


def test_native_failure_cannot_claim_completed(tmp_path):
    cache = tmp_path/'cache'; cache.mkdir(); p, s = make(cache, 1)
    def failed(*args): raise RuntimeError('native failure')
    with pytest.raises(RuntimeError, match='native failure'):
        execute(s, p, tmp_path/'run', native=failed)
    rows = [json.loads(l) for l in (tmp_path/'run/history.jsonl').read_text().splitlines()]
    assert rows[-1]['event'] == 'failed' and not any(r['event'] == 'completed' for r in rows)
