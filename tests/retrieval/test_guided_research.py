import json
from uuid import uuid4
import pytest
from src.retrieval.guided_research import ResearchStore


def test_saved_retry_conflict_and_corruption(tmp_path):
    calls = []
    store = ResearchStore(tmp_path, lambda q: calls.append(q) or [], 'research-v1', 'encoder')
    request = dict(request_id=str(uuid4()), question_id='radiomics')
    saved = store.save(request)
    assert saved['state'] == 'no_results'
    assert store.save(request) == saved and len(calls) == 1
    with pytest.raises(FileExistsError):
        store.save(dict(request, question_id='eus'))
    saved['question'] = 'altered'
    (tmp_path / f"{request['request_id']}.json").write_text(json.dumps(saved))
    with pytest.raises(ValueError):
        store.read(request['request_id'])


def test_reject_private_input_and_failure_not_saved(tmp_path):
    def fail(q):
        raise OSError('offline')
    store = ResearchStore(tmp_path, fail, 'research-v1', 'encoder')
    request = dict(request_id=str(uuid4()), question_id='radiomics')
    with pytest.raises(ValueError):
        store.save(dict(request, patient_id='private'))
    with pytest.raises(OSError):
        store.save(request)
    assert not list(tmp_path.iterdir())


def test_invalid_generation_does_not_poison_request_retry(tmp_path):
    invalid = {'answer': {'status': 'excerpts', 'extracts': [
        {'passage_id': 'invented', 'quote': 'This unsupported quotation must never be published.'}]},
        'provenance': {'model': 'test'}}
    valid = {'answer': {'status': 'insufficient_evidence', 'extracts': []},
        'provenance': {'model': 'test'}}
    attempts = iter([invalid, valid])
    store = ResearchStore(tmp_path, lambda q: [], 'research-v1', 'encoder',
                          lambda q, passages: next(attempts))
    request = dict(request_id=str(uuid4()), question_id='radiomics')
    with pytest.raises(ValueError):
        store.save(request)
    assert not list(tmp_path.iterdir())
    saved = store.save(request)
    assert saved['generation'] == valid
    assert store.save(request) == saved
