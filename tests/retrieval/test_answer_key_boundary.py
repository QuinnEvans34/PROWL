"""Invented answer-key canaries at the current guided retrieval/generation boundary.

Fake database search and Ollama transport; no model, database or protected data access.
These tests do not qualify free-text summaries or the future 30-case evaluation runner.
"""
from copy import deepcopy
import json
from uuid import uuid4

import pytest

from src.retrieval import grounded_answer as generation
from src.retrieval import guided_research as research
from src.retrieval import guided_retrieval as retrieval
from tests.retrieval.test_direct_ingestion import bundle, batch

CANARY = 'ANSWER_KEY_ONLY: the invented reference answer must never become model evidence.'


def fake_model(monkeypatch, calls, quote=None):
    def api(path, payload=None):
        if path == 'tags':
            return {'models': [{'name': generation.MODEL, 'digest': generation.MODEL_SHA}]}
        assert path == 'chat'
        calls.append(deepcopy(payload))
        inputs = json.loads(payload['messages'][1]['content'])
        passage = inputs['passages'][0]
        answer = {'status': 'excerpts', 'extracts': [dict(
            passage_id=passage['passage_id'], quote=passage['text'] if quote is None else quote)]}
        return {'done': True, 'done_reason': 'stop', 'message': {'content': json.dumps(answer)}}
    monkeypatch.setattr(generation, 'api', api)


def test_prompt_projection_excludes_answer_key_and_gold_metadata(monkeypatch):
    text = 'This invented source sentence is long enough to be a valid quotation.'
    passages = [dict(expected_answer=CANARY, reference_passage_ids=['gold-only'],
        record=dict(text=text, expected_answer=CANARY, concepts=[CANARY],
                    passage=dict(passage_id='p:invented', expected_answer=CANARY)))]
    calls = []; fake_model(monkeypatch, calls)
    result = generation.generate_answer('Invented reviewer question?', passages)
    assert result['validation'] == 'exact_quotes_verified'
    assert calls[0]['messages'] == [
        dict(role='system', content=generation.SYSTEM),
        dict(role='user', content=json.dumps(dict(question='Invented reviewer question?',
             passages=[dict(passage_id='p:invented', text=text)])))]
    assert CANARY not in json.dumps(calls)
    assert 'gold-only' not in json.dumps(calls)


def test_generated_answer_key_text_without_retrieved_support_is_rejected(monkeypatch):
    calls = []; fake_model(monkeypatch, calls, quote=CANARY)
    result = generation.generate_answer('Invented question?', [dict(record=dict(
        passage=dict(passage_id='p:invented'), text='A different invented source sentence provides the evidence.'))])
    assert CANARY not in json.dumps(calls)
    assert result['answer'] == {'status': 'insufficient_evidence', 'extracts': []}
    assert result['validation'] == 'generation_rejected'


@pytest.mark.parametrize('field', ['expected_answer', 'reference_passage_ids', 'concepts'])
def test_request_cannot_supply_answer_key_before_retrieval(tmp_path, field):
    def forbidden(*_):
        pytest.fail('No retrieval/generation is permitted for rejected input')
    store = research.ResearchStore(tmp_path, forbidden, 'invented', 'invented', forbidden)
    request = dict(request_id=str(uuid4()), question_id='radiomics', **{field: CANARY})
    with pytest.raises(ValueError, match='Only guided question IDs'):
        store.save(request)
    assert not list(tmp_path.iterdir())


def test_retrieved_evidence_drives_saved_response_not_catalog_answer_key(tmp_path, bundle, monkeypatch):
    rows = batch(bundle)['items']
    # The body sentence is already longer than the quote validator's minimum.
    hit = dict(record=rows[-1]['record'], score=1.0)
    calls = []; fake_model(monkeypatch, calls)
    query_calls = []
    def search(db, collection, encoder, question, k):
        query_calls.append(question)
        return [deepcopy(hit)]
    monkeypatch.setattr(retrieval, 'search', search)
    question = 'Invented question for boundary testing?'
    monkeypatch.setattr(research, 'QUESTIONS', [dict(id='invented', label=question,
        expected_answer=CANARY, reference_passage_ids=['gold-only'])])
    store = research.ResearchStore(tmp_path, lambda q: retrieval.guided_search(
        None, 'invented', None, q), 'invented', 'invented', generation.generate_answer)
    saved = store.save(dict(request_id=str(uuid4()), question_id='invented'))
    assert query_calls == [question]
    assert saved['generation']['answer']['extracts'] == [dict(
        passage_id=hit['record']['passage']['passage_id'], quote=hit['record']['text'])]
    assert CANARY not in json.dumps(calls) and CANARY not in json.dumps(saved)
    assert 'gold-only' not in json.dumps(calls)

    # A fresh empty retrieval must abstain even though a catalog answer still exists.
    monkeypatch.setattr(retrieval, 'search', lambda *_: [])
    empty = store.save(dict(request_id=str(uuid4()), question_id='invented'))
    assert empty['generation']['answer'] == {'status': 'insufficient_evidence', 'extracts': []}
    assert empty['generation']['model_called'] is False
    assert len(calls) == 1
