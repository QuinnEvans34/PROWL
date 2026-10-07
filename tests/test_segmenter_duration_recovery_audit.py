"""Invented metadata/tiny tensor/fake cold-worker checks; no model computation."""
from copy import deepcopy
from collections import OrderedDict
from io import BytesIO
import json
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from src.training import segmenter_duration_recovery_audit_v1 as audit
from scripts.diagnostics import segmenter_duration_launch as launch


@pytest.fixture(autouse=True)
def no_model_calls(monkeypatch):
    def denied(*a, **k):
        raise AssertionError('Model computation outside DUR-05')
    monkeypatch.setattr(launch.core, 'Session', denied)
    monkeypatch.setattr(launch.core, 'scratch', denied)
    monkeypatch.setattr(torch.nn.Module, '_call_impl', denied)
    monkeypatch.setattr(torch.optim.AdamW, 'step', denied)


def states():
    return dict(model={'weight': torch.tensor([1., 2.])},
                optimizer={'state': {0: {'exp_avg': torch.tensor([0., 1.])}}},
                progress={'step': 49, 'history': [{'loss': 0.25}]},
                cpu_rng=torch.tensor([1, 2], dtype=torch.uint8),
                mps_rng=torch.tensor([3, 4], dtype=torch.uint8))


def compare(a, b):
    return audit.compare(a, b, tree_equal=launch.core.tree_exact)


def test_exact_predicates_and_no_state_values():
    a = states(); report = compare(a, deepcopy(a))
    assert report['all_exact'] and report['differences'] == []
    assert all(v['exact'] and v['differing_fields'] == 0 and v['max_absolute_difference'] == 0 for v in report['components'].values())
    assert b'exp_avg' not in audit.encode(report)


@pytest.mark.parametrize('component', audit.COMPONENTS)
def test_each_component_failure(component):
    a = states(); b = deepcopy(a)
    if component == 'model': b[component]['weight'][0] += 0.125
    elif component == 'optimizer': b[component]['state'][0]['exp_avg'][1] += 0.125
    elif component == 'progress': b[component]['history'][0]['loss'] += 0.125
    else: b[component][0] += 1
    report = compare(a, b)
    assert not report['all_exact']
    assert [k for k, v in report['components'].items() if not v['exact']] == [component]
    assert report['differences'][0]['path'].startswith(component)
    assert report['differences'][0]['max_absolute_difference'] == (1 if 'rng' in component else 0.125)


def test_simultaneous_failures_not_short_circuited():
    a = states(); b = deepcopy(a)
    b['model']['weight'][0] += 1; b['optimizer']['state'][0]['exp_avg'][0] += 1
    b['progress']['step'] = 48; b['cpu_rng'][0] += 1; b['mps_rng'][0] += 1
    report = compare(a, b)
    assert not any(v['exact'] for v in report['components'].values())
    assert report['differing_fields'] == 5


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_nonfinite_tensor_is_safe_metadata(value):
    a = states(); b = deepcopy(a); a['model']['weight'][0] = value
    report = compare(a, b)
    assert not report['all_exact']
    assert report['differences'][0]['nonfinite_actual'] == 1
    assert b'NaN' not in audit.encode(report) and b'Infinity' not in audit.encode(report)


@pytest.mark.parametrize('substitution', ['missing', 'shape', 'sequence', 'scalar_type'])
def test_structural_substitution(substitution):
    a = states(); b = deepcopy(a)
    if substitution == 'missing': del b['model']['weight']
    elif substitution == 'shape': b['model']['weight'] = torch.ones(3)
    elif substitution == 'sequence': b['optimizer'] = []
    else: b['cpu_rng'] = 'invented substitution'
    report = compare(a, b)
    assert not report['all_exact'] and report['differing_fields'] == 1
    assert 'invented substitution' not in audit.encode(report).decode()


def test_dtype_semantics_remain_existing_predicate():
    a = states(); b = deepcopy(a); b['model']['weight'] = b['model']['weight'].to(torch.float64)
    assert compare(a, b)['all_exact'] == launch.core.tree_exact(a['model'], b['model'])


def test_progress_equality_semantics_unchanged():
    a = states(); b = deepcopy(a); b['progress']['step'] = 49.0
    assert compare(a, b)['components']['progress']['exact'] == (a['progress'] == b['progress'])


def test_all_mismatch_counts_with_bounded_paths():
    a = states(); b = deepcopy(a)
    a['model'] = {f'weight_{n}': torch.zeros(2) for n in range(40)}
    b['model'] = {f'weight_{n}': torch.ones(2) for n in range(40)}
    report = compare(a, b)
    assert report['differing_fields'] == 40 and len(report['differences']) == 16
    assert report['paths_truncated'] and len(audit.encode(report)) <= audit.MAX_BYTES
    assert all(v['mismatched_elements'] == 2 for v in report['differences'])


@pytest.mark.parametrize('wrong', ['missing', 'extra'])
def test_all_five_components_required(wrong):
    a = states(); b = deepcopy(a)
    if wrong == 'missing': a.pop('mps_rng')
    else: a['other'] = None
    with pytest.raises(ValueError, match='five'): compare(a, b)


@pytest.mark.parametrize('report', [{'x': 'a' * (audit.MAX_BYTES + 1)}, {'x': float('nan')}])
def test_serialization_envelope(report):
    with pytest.raises(ValueError): audit.encode(report)


def test_failure_retains_attempted_counts_without_exception_payload():
    report = audit.failure(phase='compare_next_update', error=ValueError('secret or tensor values'),
        counts={'forwards': 9, 'optimizer_calls': 1}, restored=22, deltas=[0.0, 0.0],
        native=[{'study_id': 'invented-1', 'step': 48, 'prediction_exact': True}], component_audit=None)
    assert report['model_calls'] == {'forwards': 9, 'optimizer_calls': 1}
    assert report['completed_restores'] == 22 and not report['recovery_qualified']
    assert b'secret' not in audit.encode(report)


@pytest.mark.parametrize('field,value', [('counts', {'forwards': True, 'optimizer_calls': 1}),
    ('deltas', [float('nan')]), ('restored', 129), ('phase', 'x' * 81)])
def test_failure_inventory_refused(field, value):
    kwargs = dict(phase='compare', error=ValueError(), counts={'forwards': 1, 'optimizer_calls': 1},
                  restored=1, deltas=[], native=[], component_audit=None)
    kwargs[field] = value
    with pytest.raises(ValueError): audit.failure(**kwargs)


@pytest.fixture
def fake_cold(tmp_path, monkeypatch):
    # All storage, sessions, native probes and model entry counters are invented fakes.
    from src.operations import segmenter_primary_read_guard_v1 as guard
    from src.operations import segmenter_duration_storage_v1 as storage
    from scripts.diagnostics import segmenter_training_qualification as qualification
    dest = tmp_path / 'controls'; dest.mkdir()
    scenario = {'fault': None}
    counter = SimpleNamespace(counts={'forwards': 0, 'optimizer_calls': 0})
    class FakeSession:
        def __init__(self, step):
            self.step = step; self.parts = states()
            self.parts['progress'] = {'step': step}
            self.model = SimpleNamespace(state_dict=lambda: self.parts['model'])
            self.optimizer = SimpleNamespace(state_dict=lambda: self.parts['optimizer'])
            self.cpu_rng = self.parts['cpu_rng']; self.mps_rng = self.parts['mps_rng']
        def predict(self, image):
            counter.counts['forwards'] += 1
            return np.ones(1, dtype=np.float32) if scenario['fault'] == 'probability' else np.zeros(1, dtype=np.float32)
        def update(self, provider):
            counter.counts['optimizer_calls'] += 1
            if scenario['fault'] == 'update_exception': raise RuntimeError('invented update failed')
            self.step = 49; self.parts['progress']['step'] = 49
            fault = scenario['fault']
            if fault == 'model': self.parts['model']['weight'][0] += 1
            elif fault == 'optimizer': self.parts['optimizer']['state'][0]['exp_avg'][0] += 1
            elif fault == 'progress': self.parts['progress']['step'] = 50
            elif fault in ('cpu_rng', 'mps_rng'): self.parts[fault][0] += 1
    expected = FakeSession(49); recovered = FakeSession(48)
    def attach(s): return s
    counter.attach = attach
    buf = BytesIO(); np.save(buf, np.zeros(1, dtype=np.float32), allow_pickle=False)
    def pair(name): return {'backup': {'id': name}, 'primary': {'id': name}}
    completion = dict(state='complete', screens=[], checkpoints=[{'step': 48, **pair('checkpoint')}],
        recovery=dict(exports=[], images_reference=pair('images'), probe_reference=pair('probes'),
                      next_state_reference=pair('next')))
    producer = completion | {'summary_reference': pair('summary')}
    payloads = {'summary': {'completion.json': launch.canonical(completion)}, 'images': {},
        'probes': {'image.npy': b'fake image', 'prob-48.npy': buf.getvalue(),
                   'manifest.json': b'{"next_weights_sha256":"saved"}'},
        'next': {'kind': 'expected'}, 'checkpoint': {'kind': 'recovered'}}
    def restore(keeper, cold, pair, *args):
        if scenario['fault'] == 'restore': raise OSError('invented restore failure')
        return payloads[pair['id']], {'id': pair['id']}
    for name in ('verify_code', 'validate_readiness'):
        monkeypatch.setattr(launch, name, lambda *a, **k: None)
    monkeypatch.setattr(launch.engine, 'checked_grant', lambda *a: None)
    monkeypatch.setattr(launch.engine, 'CallCounter', lambda *a: counter)
    monkeypatch.setattr(launch, 'stores', lambda *a, **k: (None, SimpleNamespace(root=tmp_path / 'keeper'), None))
    monkeypatch.setattr(storage, 'areas', lambda *a: {'controls': 'controls'})
    monkeypatch.setattr(guard, 'install', lambda: None)
    monkeypatch.setattr(launch, 'read_control', lambda *a: launch.canonical(producer))
    monkeypatch.setattr(launch, 'restore_backup', restore)
    monkeypatch.setattr(launch, 'owned_tree', lambda *a: ([], 0))
    monkeypatch.setattr(qualification, 'power', lambda: (True, 'fake'))
    monkeypatch.setattr(torch.mps, 'driver_allocated_memory', lambda: 0)
    monkeypatch.setattr(torch.mps, 'empty_cache', lambda: None)
    monkeypatch.setattr(launch.core, 'restore_payload', lambda files, identity: expected if files['kind'] == 'expected' else recovered)
    monkeypatch.setattr(launch.core, 'progress', lambda s: deepcopy(s.parts['progress']))
    monkeypatch.setattr(launch.core.cache, 'decode', lambda *a: np.zeros(1, dtype=np.float32))
    monkeypatch.setattr(launch.core.numerical, 'state_hash', lambda *a: 'saved')
    monkeypatch.setattr(launch.inputs, 'InventedInputs', lambda size: SimpleNamespace(control={'fake': True}))
    r = dict(kind='native_rehearsal', identity={}, storage_capability={},
             model_calls={'cold': {'forwards': 1, 'optimizer_calls': 1}},
             limits={'rss_bytes': 10**6, 'recovery_seconds': 10, 'driver_bytes': 10**6},
             targets={'cases': []}, controls={'inputs.json': launch.canonical({'fake': True}).decode()})
    args = SimpleNamespace(dest=str(dest), producer_pin='fake')
    return scenario, r, args, dest


@pytest.mark.parametrize('fault', [*audit.COMPONENTS, 'update_exception', 'probability', 'restore'])
def test_cold_failure_reports_phase_and_nonzero_attempts(fake_cold, fault):
    scenario, r, args, dest = fake_cold; scenario['fault'] = fault
    with pytest.raises((ValueError, RuntimeError, OSError)):
        launch.cold(r, args, None)
    report = json.loads((dest / 'cold-failure-audit.json').read_bytes())
    assert not report['recovery_qualified'] and not (dest / 'cold-result.json').exists()
    assert report['model_calls']['forwards'] == (0 if fault == 'restore' else 1)
    assert report['model_calls']['optimizer_calls'] == (0 if fault in ('restore', 'probability') else 1)
    if fault in audit.COMPONENTS:
        assert report['phase'] == 'compare_next_update'
        assert not report['component_audit']['components'][fault]['exact']
        assert json.loads((dest / 'next-update-audit.json').read_bytes()) == report['component_audit']
    elif fault == 'probability': assert report['probability_max_differences'] == [1.0]


def test_fake_cold_success_preserves_exact_conjunction(fake_cold):
    scenario, r, args, dest = fake_cold
    result = launch.cold(r, args, None)
    assert result['state'] == 'passed' and result['next_update_exact']
    assert json.loads((dest / 'next-update-audit.json').read_bytes())['all_exact']
    assert not (dest / 'cold-failure-audit.json').exists()


def test_failure_report_write_error_preserves_original_exception(fake_cold, monkeypatch):
    scenario, r, args, dest = fake_cold; scenario['fault'] = 'model'
    original_put = audit.publish
    def put(path, raw):
        if path.name == 'cold-failure-audit.json': raise OSError('invented audit disk failure')
        return original_put(path, raw)
    monkeypatch.setattr(audit, 'publish', put)
    with pytest.raises(ValueError, match='Independent full next-update recovery differs') as caught:
        launch.cold(r, args, None)
    assert caught.value.__notes__ == ['Cold failure metadata could not be persisted: OSError']
    assert not (dest / 'cold-result.json').exists()


def test_atomic_audit_publication_is_exclusive(tmp_path):
    path = tmp_path / 'audit.json'; audit.publish(path, {'complete': True})
    with pytest.raises(FileExistsError): audit.publish(path, {'complete': False})
    assert json.loads(path.read_bytes()) == {'complete': True}
    assert sorted(p.name for p in tmp_path.iterdir()) == ['audit.json']
    assert path.stat().st_nlink == 1


def test_atomic_audit_does_not_follow_target_symlink(tmp_path):
    original = tmp_path / 'original.json'; original.write_text('preserved')
    path = tmp_path / 'audit.json'; path.symlink_to(original)
    with pytest.raises(FileExistsError): audit.publish(path, {'complete': True})
    assert original.read_text() == 'preserved'
    assert not list(tmp_path.glob('audit-staging-*'))


def test_ordered_model_mapping_reports_tensor_difference():
    a = states(); b = deepcopy(a)
    a['model'] = OrderedDict(weight=torch.tensor([1., 2.]))
    b['model'] = OrderedDict(weight=torch.tensor([1.25, 2.]))
    report = compare(a, b)
    assert report['differences'][0]['kind'] == 'tensor'
    assert report['differences'][0]['path'] == 'model.weight'
    assert report['components']['model']['max_absolute_difference'] == 0.25
    assert report['components']['model']['mismatched_elements'] == 1


def test_component_maxima_cover_paths_outside_report_limit():
    a = states(); b = deepcopy(a)
    a['model'] = OrderedDict((str(n), torch.zeros(1)) for n in range(40))
    b['model'] = OrderedDict((str(n), torch.ones(1) * (100 if n == 39 else 1)) for n in range(40))
    b['optimizer']['state'][0]['exp_avg'][0] = 200
    report = compare(a, b)
    assert len(report['differences']) == 16 and report['paths_truncated']
    assert report['components']['model']['max_absolute_difference'] == 100
    assert report['components']['optimizer']['max_absolute_difference'] == 200
    assert report['components']['model']['mismatched_elements'] == 40
