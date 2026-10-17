import json
import pytest
from src.retrieval import evidence_spans as s, span_answer as g

FIRST = 'Dr. Lane et al. report a CT model with AUC 0.91 on external testing [7].'
SECOND = 'A separate MRI study evaluated a different patient cohort [8].'
PASSAGES = [{'record': {'passage': {'passage_id': 'long-immutable-source-id'},
                        'text': FIRST + '  ' + SECOND}}]


def test_exact_offsets_abbreviations_references_and_context():
    sources, spans = s.catalog(PASSAGES)
    assert [p['text'] for p in sources[0]['sentences']] == [FIRST, SECOND]
    assert spans['P1:1-1']['quote'] == FIRST
    assert spans['P1:1-2']['quote'] == FIRST + '  ' + SECOND
    for span in spans.values():
        assert PASSAGES[0]['record']['text'][span['start']:span['end']] == span['quote']
    assert s.resolve({'status': 'excerpts', 'span_ids': ['P1:1-1']}, spans) == {
        'status': 'excerpts', 'extracts': [{'passage_id': 'long-immutable-source-id', 'quote': FIRST}]}


@pytest.mark.parametrize('selection', [
    {'status': 'excerpts', 'span_ids': ['P9:1-1']},
    {'status': 'excerpts', 'span_ids': ['P1:1-1', 'P1:1-1']},
    {'status': 'excerpts', 'span_ids': []},
    {'status': 'insufficient_evidence', 'span_ids': ['P1:1-1']},
    {'status': 'excerpts', 'span_ids': [True]},
    {'status': 'excerpts', 'span_ids': [['P1:1-1']]},
    {'status': 'excerpts', 'span_ids': ['P1:1-1'], 'quote': 'invented'},
])
def test_malformed_or_invented_selection_rejected(selection):
    with pytest.raises(ValueError):
        s.resolve(selection, s.catalog(PASSAGES)[1])


def test_context_is_retained_but_sources_cannot_be_stitched():
    other = {'record': {'passage': {'passage_id': 'other'}, 'text': SECOND}}
    sources, spans = s.catalog(PASSAGES + [other])
    assert len(sources) == 2
    assert all(span['quote'] in next(p['record']['text'] for p in PASSAGES+[other]
                                   if p['record']['passage']['passage_id'] == span['passage_id'])
               for span in spans.values())
    with pytest.raises(ValueError):
        s.resolve({'status': 'excerpts', 'span_ids': ['P1:1-P2:1']}, spans)


def test_generation_constrains_ids_and_server_copies_text(monkeypatch):
    seen = []
    def api(path, payload=None):
        if path == 'tags':
            return {'models': [{'name': g.MODEL, 'digest': g.MODEL_SHA}]}
        seen.append(payload)
        return {'done': True, 'message': {'content': json.dumps(
            {'status': 'excerpts', 'span_ids': ['P1:1-1']})}}
    monkeypatch.setattr(g, 'api', api)
    result = g.generate_answer('CT model?', PASSAGES)
    assert result['answer']['extracts'] == [{'passage_id': 'long-immutable-source-id', 'quote': FIRST}]
    assert result['validation'] == 'exact_quotes_verified'
    assert seen[0]['format']['properties']['span_ids']['items']['enum'] == list(s.catalog(PASSAGES)[1])
    user_input = json.loads(seen[0]['messages'][1]['content'])
    assert user_input['sources'][0]['sentences'][1]['text'] == SECOND
    assert 'long-immutable-source-id' not in seen[0]['messages'][1]['content']
    assert result['provenance']['span_catalog_sha256'] == g.digest(s.catalog(PASSAGES)[1])


def test_invalid_id_from_model_still_fails_closed(monkeypatch):
    monkeypatch.setattr(g, 'api', lambda path, payload=None:
        {'models': [{'name': g.MODEL, 'digest': g.MODEL_SHA}]} if path == 'tags' else
        {'done': True, 'message': {'content': '{"status":"excerpts","span_ids":["P99:1-1"]}'}})
    result = g.generate_answer('question', PASSAGES)
    assert result['validation'] == 'generation_rejected'
    assert result['answer']['extracts'] == []


def test_no_valid_span_skips_model_and_duplicate_sources_refused(monkeypatch):
    monkeypatch.setattr(g, 'api', lambda *args: pytest.fail('No model call expected'))
    result = g.generate_answer('question', [{'record': {'passage': {'passage_id': 'short'}, 'text': 'Too short.'}}])
    assert result['model_called'] is False
    assert result['validation'] == 'no_selectable_spans'
    with pytest.raises(ValueError, match='Duplicate'):
        s.catalog(PASSAGES * 2)


def test_model_selection_changes_only_model_and_provenance():
    requests = []
    def api(path, payload=None):
        if path == 'tags':
            return dict(models=[dict(name=k, digest=v) for k, v in g.MODELS.items()])
        requests.append(payload)
        return dict(done=True, message=dict(content=json.dumps(dict(status='excerpts',span_ids=['P1:1-1']))))
    default = g.generate_answer('CT model?', PASSAGES, call_api=api)
    larger = g.generate_answer('CT model?', PASSAGES, call_api=api, model='qwen3:30b')
    assert requests[0]['model'] == g.MODEL
    assert requests[1]['model'] == 'qwen3:30b'
    assert dict(requests[0],model='same') == dict(requests[1],model='same')
    assert default['answer'] == larger['answer']
    assert larger['provenance']['model_sha256'] == g.MODELS['qwen3:30b']
    with pytest.raises(ValueError, match='Unknown'):
        g.generate_answer('CT model?', PASSAGES, call_api=api, model='unknown')


def test_larger_model_wrong_pin_refused_before_chat():
    def api(path, payload=None):
        assert path == 'tags'
        return dict(models=[dict(name='qwen3:30b',digest=g.MODEL_SHA)])
    with pytest.raises(OSError):
        g.generate_answer('CT model?', PASSAGES, call_api=api, model='qwen3:30b')


def test_reasoning_profile_keeps_sources_and_schema_and_rejects_token_exhaustion():
    calls = []
    def api(path, payload=None):
        if path == 'tags':return dict(models=[dict(name='qwen3:30b',digest=g.MODELS['qwen3:30b'])])
        calls.append(payload)
        return dict(done=True,done_reason='length',message=dict(content='',thinking='unfinished'))
    baseline = g.generate_answer('CT model?',PASSAGES,call_api=api,model='qwen3:30b')
    reasoned = g.generate_answer('CT model?',PASSAGES,call_api=api,model='qwen3:30b',reasoning=True)
    assert reasoned['validation'] == 'generation_rejected' and reasoned['answer']['extracts'] == []
    assert reasoned['provenance']['reasoning'] is True and reasoned['provenance']['output_limit'] == 2048
    assert 'reasoning' not in baseline['provenance']
    assert calls[0]['format'] == calls[1]['format']
    assert calls[0]['messages'][1] == calls[1]['messages'][1]
    assert calls[1]['think'] is True and calls[1]['options']['num_predict'] == 2048
    assert calls[1]['messages'][0]['content'] == g.SYSTEM.replace('/no_think','/think')
