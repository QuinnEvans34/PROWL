from copy import deepcopy
import pytest
import torch
from scripts.diagnostics import control_original_repeatability as control


def state():
    return dict(raw=dict(model={'weight':torch.tensor([0.1, 0.2])}, optimizer={},
        step=33, exposure={'a':33}, cpu_rng=torch.tensor([1,2]), cuda_rng=None,
        mps_rng=None), focused={'a':25})


def test_exact_and_outside_bound_are_distinct():
    a = state(); b = deepcopy(a)
    assert control.compare_states(a,b)['passes_original_bound']
    b['raw']['model']['weight'][0] += 0.001
    result = control.compare_states(a,b)
    assert not result['passes_original_bound']
    assert result['mismatched_elements'] == 1
    assert result['groups']['model']['max_absolute_difference'] > 0.0009


def test_rng_change_not_mislabelled_as_floating_drift():
    a = state(); b = deepcopy(a); b['raw']['cpu_rng'][0] = 4
    result = control.compare_states(a,b)
    assert not result['scalar_integer_rng_counters_exact']
    assert not result['passes_original_bound']


def test_bad_tensor_signature_refused():
    a = state(); b = deepcopy(a); b['raw']['model']['weight'] = torch.zeros(3)
    with pytest.raises(ValueError, match='signature'): control.compare_states(a,b)


def test_original_function_called_once_and_destination_restored(monkeypatch,tmp_path):
    old = control.qualification.OUT; seen = []
    monkeypatch.setattr(control.qualification,'original_worker',lambda:seen.append(control.qualification.OUT))
    control.run_original(tmp_path)
    assert seen == [tmp_path]
    assert control.qualification.OUT == old


def test_duplicate_refused_before_prior_checks(monkeypatch,tmp_path):
    monkeypatch.setattr(control,'OUT',tmp_path)
    monkeypatch.setattr(control,'check_prior',lambda:pytest.fail('Must reject before checks'))
    with pytest.raises(ValueError,match='already started'): control.admission()


def test_input_sequence_and_count_must_match():
    a = [dict(step=i+1,member_id='a',batch_sha256={'image':str(i)},input_view={},
        learning_rate=0.01,loss=1.) for i in range(33)]
    b = deepcopy(a)
    assert control.input_comparison(a,b)['exact_inputs']
    b[2]['batch_sha256']['image'] = 'different'
    with pytest.raises(ValueError,match='sequence'): control.input_comparison(a,b)
    with pytest.raises(ValueError,match='sequence'): control.input_comparison(a,a[:-1])


def test_execution_limits_and_no_scientific_target():
    assert control.SECONDS == 600
    assert control.RSS_BYTES == 12*1024**3
    assert control.UPDATES == 33
    assert control.OUT.parent == control.setup.SETUP
    assert control.OUT != control.qualification.OUT
