import json
import pytest
from src.retrieval import grounded_answer as g

TEXT = 'This is a complete research sentence with qualifications retained.'
PASSAGES = [{'record': {'passage': {'passage_id': 'p1'}, 'text': TEXT}}]


def test_exact_quote_and_abstention():
    assert g.validate_answer({'status': 'excerpts', 'extracts': [{'passage_id': 'p1', 'quote': TEXT}]}, PASSAGES)
    assert g.generate_answer('question', [])['model_called'] is False


@pytest.mark.parametrize('answer', [
 {'status': 'excerpts', 'extracts': [{'passage_id': 'invented', 'quote': TEXT}]},
 {'status': 'excerpts', 'extracts': [{'passage_id': 'p1', 'quote': TEXT + ' invented claim'}]},
 {'status': 'excerpts', 'extracts': []},
 {'status': 'insufficient_evidence', 'extracts': [{'passage_id': 'p1', 'quote': TEXT}]},
 {'status': 'excerpts', 'extracts': [{'passage_id': 'p1', 'quote': TEXT, 'advice': 'invented'}]},
])
def test_unsupported_generation_rejected(answer):
    with pytest.raises(ValueError):
        g.validate_answer(answer, PASSAGES)


def test_malformed_model_response_abstains(monkeypatch):
    monkeypatch.setattr(g, 'api', lambda path, payload=None: {'models': [{'name': g.MODEL, 'digest': g.MODEL_SHA}]} if path == 'tags' else {'done': True, 'message': {'content': 'not JSON'}})
    result = g.generate_answer('question', PASSAGES)
    assert result['answer']['status'] == 'insufficient_evidence'
    assert result['validation'] == 'generation_rejected'


def test_changed_model_refused(monkeypatch):
    monkeypatch.setattr(g, 'api', lambda *args: {'models': []})
    with pytest.raises(OSError):
        g.generate_answer('question', PASSAGES)


@pytest.mark.parametrize('envelope', [[], None, 'unexpected'])
def test_nonobject_model_envelope_abstains(monkeypatch, envelope):
    monkeypatch.setattr(g, 'api', lambda path, payload=None:
        {'models': [{'name': g.MODEL, 'digest': g.MODEL_SHA}]} if path == 'tags' else envelope)
    result = g.generate_answer('question', PASSAGES)
    assert result['answer'] == {'status': 'insufficient_evidence', 'extracts': []}
    assert result['validation'] == 'generation_rejected'
    assert result['model_called'] is True


def test_saved_abstention_does_not_regenerate(tmp_path):
    from uuid import uuid4
    from src.retrieval.guided_research import ResearchStore
    calls = []
    def generate(q, passages):
        calls.append(q)
        return g.generate_answer(q, passages)
    store = ResearchStore(tmp_path, lambda q: [], 'research-v1', 'encoder', generate)
    request = dict(request_id=str(uuid4()), question_id='radiomics')
    saved = store.save(request)
    assert saved['schema_version'] == 'prowl-research-answer-v1'
    assert store.save(request) == saved
    assert len(calls) == 1


def test_overlapping_source_sentences_not_repeated():
    sentence = 'This is the same substantive study sentence in overlapping passages.'
    answer = {'status': 'excerpts', 'extracts': [
        {'passage_id': 'a', 'quote': sentence},
        {'passage_id': 'b', 'quote': sentence + ' Another study uses a different modality.'}]}
    assert g.distinct_extracts(answer)['extracts'] == answer['extracts'][:1]
