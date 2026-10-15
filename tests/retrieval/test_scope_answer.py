import copy
import json
import pytest
from src.retrieval import scope_answer as g, span_answer, evidence_spans as s

METHOD = 'The CT radiomics study evaluated a cohort of 123 patients [8].'
RESULT = 'The same study reported an external validation AUC of 0.91 [8].'
OTHER = 'A different MRI study evaluated another patient population [9].'
PASSAGES = [{'record': {'passage': {'passage_id': 'p1'}, 'text': METHOD+' '+RESULT+' '+OTHER}},
            {'record': {'passage': {'passage_id': 'p2'}, 'text': OTHER}}]


def base():
    spans = s.catalog(PASSAGES)[1]
    selection = dict(status='excerpts', span_ids=['P1:2-2'])
    return dict(answer=s.resolve(selection, spans), selection=selection,
                provenance=dict(policy=span_answer.POLICY, span_catalog_sha256=g.digest(spans)),
                validation='exact_quotes_verified', model_called=True, total_duration_ns=10)


def assessment(**changes):
    value = dict(checks={axis: 'match' for axis in g.AXES}, support_span_id='P1:1-2', reason='Same study method and result.')
    value.update(changes)
    return value


def mock_model(monkeypatch, value, captured=None):
    def api(path, payload=None):
        if path == 'tags':
            return {'models': [{'name': g.MODEL, 'digest': g.MODEL_SHA}]}
        if captured is not None:
            captured.append(payload)
        return dict(done=True, total_duration=5, message=dict(content=json.dumps(value)))
    monkeypatch.setattr(g, 'api', api)


def test_same_source_expansion_preserves_context_and_exact_text(monkeypatch):
    calls = []
    mock_model(monkeypatch, assessment(), calls)
    result = g.verify_answer('CT study?', PASSAGES, base())
    assert result['answer']['extracts'] == [dict(passage_id='p1', quote=METHOD+' '+RESULT)]
    assert result['scope_assessments'][0]['decision'] == 'keep'
    assert result['total_duration_ns'] == 5  # reused selection time is not counted again
    inputs = json.loads(calls[0]['messages'][1]['content'])
    assert inputs['source']['sentences'][2]['text'] == OTHER
    assert len(inputs['source']['sentences']) == 3
    assert 'P2:1-1' not in calls[0]['format']['properties']['support_span_id']['enum']


@pytest.mark.parametrize('verdict', ['mismatch', 'uncertain'])
def test_requested_constraint_failure_removes_excerpt(monkeypatch, verdict):
    value = assessment(support_span_id='')
    value['checks']['technique'] = verdict
    mock_model(monkeypatch, value)
    result = g.verify_answer('nCLE?', PASSAGES, base())
    assert result['answer'] == dict(status='insufficient_evidence', extracts=[])
    assert result['scope_assessments'][0]['decision'] == 'reject'


@pytest.mark.parametrize('change', ['foreign', 'shrink', 'missing_axis', 'contradiction', 'no_directness'])
def test_invalid_assessment_cannot_publish_unchecked_answer(monkeypatch, change):
    value = assessment()
    if change == 'foreign': value['support_span_id'] = 'P2:1-1'
    elif change == 'shrink': value['support_span_id'] = 'P1:1-1'
    elif change == 'missing_axis': del value['checks']['study']
    elif change == 'contradiction': value['checks']['task'] = 'mismatch'
    else: value['checks']['directness'] = 'not_requested'
    mock_model(monkeypatch, value)
    result = g.verify_answer('question', PASSAGES, base())
    assert result['validation'] == 'generation_rejected'
    assert result['answer']['extracts'] == []


def test_backend_failure_does_not_fall_back_to_unchecked_selection(monkeypatch):
    monkeypatch.setattr(g, 'api', lambda *args: (_ for _ in ()).throw(OSError('offline')))
    with pytest.raises(OSError):
        g.verify_answer('question', PASSAGES, base())


def test_changed_source_and_tampered_selection_rejected_before_model(monkeypatch):
    monkeypatch.setattr(g, 'api', lambda *args: pytest.fail('No model call expected'))
    changed = copy.deepcopy(PASSAGES)
    changed[0]['record']['text'] += ' Altered context.'
    with pytest.raises(ValueError, match='catalog'):
        g.verify_answer('question', changed, base())
    changed_base = base()
    changed_base['selection']['span_ids'] = ['P1:1-1']
    with pytest.raises(ValueError, match='resolve'):
        g.verify_answer('question', PASSAGES, changed_base)


def test_existing_abstention_skips_verifier(monkeypatch):
    monkeypatch.setattr(g, 'api', lambda *args: pytest.fail('No model call expected'))
    old = base()
    old.update(answer=dict(status='insufficient_evidence', extracts=[]),
               selection=dict(status='insufficient_evidence', span_ids=[]))
    result = g.verify_answer('missing question', PASSAGES, old)
    assert result['scope_assessments'] == [] and result['model_called'] is False


def test_live_pipeline_routes_selection_and_scope_through_recorder(monkeypatch):
    calls = []
    def api(path, payload=None):
        if path == 'tags': return {'models': [{'name': g.MODEL, 'digest': g.MODEL_SHA}]}
        calls.append(payload)
        value = dict(status='excerpts', span_ids=['P1:2-2']) if len(calls) == 1 else assessment()
        return dict(done=True, total_duration=5, message=dict(content=json.dumps(value)))
    monkeypatch.setattr(g, 'api', api)
    result = g.generate_answer('CT study?', PASSAGES)
    assert len(calls) == 2
    assert result['selection_reused'] is False and result['total_duration_ns'] == 10
    assert result['answer']['extracts'][0]['quote'] == METHOD+' '+RESULT


def test_reasoning_profile_is_explicit_and_retained(monkeypatch):
    calls = []
    mock_model(monkeypatch, assessment(), calls)
    result = g.verify_answer('CT study?', PASSAGES, base(), reasoning=True)
    assert calls[0]['think'] is True and calls[0]['options']['num_predict'] == 4096
    assert '/no_think' not in calls[0]['messages'][0]['content']
    assert result['provenance']['scope_reasoning'] is True
    assert result['provenance']['prompt_sha256'] == g.digest(calls[0]['messages'][0]['content'])


def test_repeated_quote_cannot_move_to_another_studys_context(monkeypatch):
    repeated = 'The reported external AUC was 0.91 in the validation cohort.'
    passages = [{'record': {'passage': {'passage_id': 'p1'},
        'text': METHOD+' '+repeated+' '+OTHER+' '+repeated}}]
    spans = s.catalog(passages)[1]
    selection = dict(status='excerpts', span_ids=['P1:4-4'])
    old = dict(answer=s.resolve(selection, spans), selection=selection,
               provenance=dict(policy=span_answer.POLICY, span_catalog_sha256=g.digest(spans)),
               validation='exact_quotes_verified', model_called=True)
    mock_model(monkeypatch, assessment(support_span_id='P1:1-2'))
    result = g.verify_answer('question', passages, old)
    assert result['validation'] == 'generation_rejected'
    assert result['answer']['extracts'] == []
