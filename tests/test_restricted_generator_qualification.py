import json
import pytest
from scripts.diagnostics import qualify_restricted_generator as q


def write(path, value):
    path.write_text(json.dumps(value))


def test_bounded_config_is_valid_and_does_not_mutate_science():
    from src.training.segmenter_full_session_v1 import validate_config
    original = dict(session=dict(max_steps=24000, warmup_steps=500, lr_horizon_steps=24000,
        lr_schedule='warmup_cosine', seed=42, learning_rate=1e-4, weight_decay=1e-5,
        tensor_shape=[144,144,144]))
    prepared = q.qualification_config(original)
    validate_config(prepared['session'])
    assert original['session']['max_steps'] == 24000
    assert prepared['session']['max_steps'] == prepared['session']['lr_horizon_steps'] == 5


@pytest.fixture
def stage(tmp_path, monkeypatch):
    monkeypatch.setattr(q, 'OUT', tmp_path)
    monkeypatch.setattr(q, 'check', lambda: None)
    monkeypatch.setattr(q, 'parent_gate', lambda: None)
    return tmp_path


def test_no_gpu_before_parent_completion(stage, monkeypatch):
    def busy(): raise ValueError('Parent still running')
    monkeypatch.setattr(q, 'parent_gate', busy)
    with pytest.raises(ValueError, match='still running'): q.stage_admission('producer')
    assert not list(stage.iterdir())


@pytest.mark.parametrize('name', ['producer', 'cold'])
def test_no_retry_or_duplicate(stage, name):
    (stage / (name + '.log')).touch()
    with pytest.raises(ValueError, match='already started'): q.stage_admission(name)


@pytest.mark.parametrize('field,value', [('success', False), ('exit_code', 1), ('workers_reaped', False)])
def test_cold_requires_successful_reaped_producer(stage, field, value):
    evidence = dict(success=True, exit_code=0, workers_reaped=True)
    evidence[field] = value
    write(stage / 'producer-resources.json', evidence)
    with pytest.raises(ValueError, match='reaped'): q.stage_admission('cold')


def test_cold_requires_quality_pass(stage):
    write(stage / 'producer-resources.json', dict(success=True, exit_code=0, workers_reaped=True))
    write(stage / 'producer.json', dict(passed=False))
    with pytest.raises(ValueError, match='failed'): q.stage_admission('cold')


def test_stage_admission(stage):
    q.stage_admission('producer')
    write(stage / 'producer-resources.json', dict(success=True, exit_code=0, workers_reaped=True))
    write(stage / 'producer.json', dict(passed=True))
    q.stage_admission('cold')
    with pytest.raises(ValueError, match='Unknown'): q.stage_admission('launch')


def pilot(tmp_path, monkeypatch):
    monkeypatch.setattr(q, 'PILOT', tmp_path)
    names = [str(i) for i in range(12)]
    rows = []
    for name in names:
        figure = tmp_path / (name + '.png'); figure.write_bytes(name.encode())
        rows.append(dict(case_id=name, figure=figure.name, figure_sha256=q.sha(figure), roundtrip_exact=True))
    write(tmp_path / 'request.json', dict(cases=names))
    write(tmp_path / 'result.json', dict(passed=True, cases=rows))
    write(tmp_path / 'resources.json', dict(workers_reaped=True))
    review = dict(passed=True, result_sha256=q.sha(tmp_path / 'result.json'), cases=[dict(case_id=n) for n in names])
    write(tmp_path / 'visual-review.json', review)
    return review


def test_pilot_binding(tmp_path, monkeypatch):
    pilot(tmp_path, monkeypatch)
    q.pilot_gate()
    (tmp_path / '0.png').write_bytes(b'changed')
    with pytest.raises(ValueError, match='figure changed'): q.pilot_gate()


@pytest.mark.parametrize('bad', ['missing', 'order', 'result'])
def test_visual_review_must_bind_all_cases(tmp_path, monkeypatch, bad):
    review = pilot(tmp_path, monkeypatch)
    if bad == 'missing': review['cases'].pop()
    if bad == 'order': review['cases'].reverse()
    if bad == 'result': review['result_sha256'] = 'incorrect'
    write(tmp_path / 'visual-review.json', review)
    with pytest.raises(ValueError, match='binding'): q.pilot_gate()
