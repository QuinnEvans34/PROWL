import json

import pytest
from src.retrieval import research_workflow as w
from tests.retrieval.test_research_workflow import inputs, request, store_at


@pytest.mark.parametrize('stage', w.STAGES)
def test_interrupt_after_artifact_before_event_preserves_orphan_and_recovers(tmp_path, inputs, monkeypatch, stage):
    original = w.publish
    def interrupt(path, value):
        result = original(path, value)
        if path.name == stage + '.json': raise KeyboardInterrupt
        return result
    monkeypatch.setattr(w, 'publish', interrupt)
    calls = []
    s = store_at(tmp_path, inputs, lambda *_: calls.append('select') or inputs[1],
                 lambda _: calls.append('retrieve') or inputs[0])
    r = request()
    with pytest.raises(KeyboardInterrupt): s.save(r)
    before = {p.name:p.read_bytes() for p in (s.directory/r['request_id']).glob('*.json')}
    assert s.read(r['request_id'])['state'] == 'interrupted'
    assert s.save(r)['state'] == 'interrupted'
    monkeypatch.setattr(w, 'publish', original)
    saved = s.save(request(resume_of=r['request_id']))
    assert saved['state'] == 'completed'
    assert [x['state'] for x in saved['stages']] == ['reused']*w.STAGES.index(stage) + ['completed']*(4-w.STAGES.index(stage))
    assert before == {p.name:p.read_bytes() for p in (s.directory/r['request_id']).glob('*.json')}
    assert calls.count('retrieve') == (2 if stage == 'retrieve' else 1)
    assert calls.count('select') == (2 if stage == 'select' else 1)


@pytest.mark.parametrize('target', ['retrieve.json', 'select.json', 'validate.json', 'save.json'])
def test_missing_published_artifact_refuses_read_and_recovery(tmp_path, inputs, target):
    s = store_at(tmp_path, inputs); result = s.save(request())
    (s.directory/result['run_id']/target).unlink()
    with pytest.raises(FileNotFoundError): s.read(result['run_id'])
    with pytest.raises(FileNotFoundError): s.save(request(resume_of=result['run_id']))


@pytest.mark.parametrize('field', ['collection', 'encoder_id', 'corpus', 'catalog', 'model', 'policy', 'code'])
def test_changed_dependency_requires_new_run_and_preserves_history(tmp_path, inputs, field):
    s = store_at(tmp_path, inputs, lambda *_: (_ for _ in ()).throw(OSError('offline')))
    result = s.save(request()); parent = s.directory/result['run_id']
    before = {p.name:p.read_bytes() for p in parent.glob('*.json')}
    changed = store_at(tmp_path, inputs)
    if field in ('collection', 'encoder_id'): changed.binding[field] = 'new'
    elif field in ('corpus', 'catalog'): changed.binding['retrieval_identity'] = {field:'new'}
    elif field in ('model', 'policy'): changed.binding['generation_identity'][field] = 'new'
    else: changed.binding['code_sha256']['research_workflow.py'] = 'new'
    r = request(resume_of=result['run_id'])
    with pytest.raises(ValueError, match='configuration'): changed.save(r)
    assert not (changed.directory/r['request_id']).exists()
    assert before == {p.name:p.read_bytes() for p in parent.glob('*.json')}


def test_storage_admission_before_calls_and_same_id_reads_remain_available(tmp_path, inputs):
    calls = []
    s = store_at(tmp_path, inputs, lambda *_: calls.append('model') or inputs[1])
    saved = s.save(request())
    def fail(): raise OSError('storage floor')
    s.admit = fail
    assert s.save(saved['request']) == saved
    r = request()
    with pytest.raises(OSError, match='storage'): s.save(r)
    assert calls == ['model'] and not (s.directory/r['request_id']).exists()


def test_storage_drop_after_retrieval_prevents_model_and_can_resume(tmp_path, inputs):
    checks = []
    def admit():
        checks.append(1)
        if len(checks) == 3: raise OSError('storage floor')
    s = store_at(tmp_path, inputs, lambda *_: pytest.fail('No model after storage refusal'), admit=admit)
    failed = s.save(request())
    assert failed['state'] == 'failed' and failed['stages'][1]['reason'] == 'service_unavailable'
    recovered = store_at(tmp_path, inputs).save(request(resume_of=failed['run_id']))
    assert recovered['state'] == 'completed' and recovered['stages'][0]['state'] == 'reused'


def test_database_down_fails_retrieval_without_model_or_false_abstention(tmp_path, inputs):
    def fail(_): raise OSError('private database connection detail')
    s = store_at(tmp_path, inputs, lambda *_: pytest.fail('No model without DB'), fail)
    failed = s.save(request())
    assert failed['stages'][0]['reason'] == 'service_unavailable' and 'response' not in failed
    assert 'private database' not in json.dumps(failed)
