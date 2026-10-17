import json

import pytest
from jsonschema import Draft202012Validator

from src.retrieval import choice_span_answer as a, evidence_spans, span_answer


@pytest.fixture
def passages():
    return [dict(record=dict(passage=dict(passage_id=f'p{i}'), text=text)) for i, text in enumerate([
        'Handcrafted measurements are computed after outlining the region of interest. The fitted model is evaluated using separate images.',
        'A different study examined ultrasound images and measured treatment response. Its result does not describe feature extraction.'
    ])]


def api_for(value, calls, **envelope):
    def api(path, payload=None):
        calls.append((path, payload))
        if path == 'tags':
            return dict(models=[dict(name=a.MODEL, digest=span_answer.MODELS[a.MODEL])])
        content = value if isinstance(value, str) else json.dumps(value)
        return dict(done=True, done_reason='stop', message=dict(content=content), **envelope)
    return api


def test_choices_materialize_exact_text_with_code_derived_status(passages):
    value = dict(choices=dict(P1='P1:1-2', P2=None))
    calls = []
    result = a.generate_answer('Explain feature extraction', passages, call_api=api_for(value, calls))
    assert result['answer'] == dict(status='excerpts', extracts=[dict(passage_id='p0', quote=passages[0]['record']['text'])])
    assert result['validation'] == 'exact_quotes_verified' and result['selection'] == value
    payload = calls[1][1]
    Draft202012Validator.check_schema(payload['format'])
    Draft202012Validator(payload['format']).validate(value)
    assert payload['options'] == dict(temperature=0, seed=42, num_ctx=8192, num_predict=1200)
    assert payload['think'] is False
    assert json.loads(payload['messages'][1]['content']) == dict(question='Explain feature extraction', sources=evidence_spans.catalog(passages)[0])


@pytest.mark.parametrize('value', [
    {'choices': {'P1': 'P1:1-1'}},
    {'choices': {'P1': None, 'P2': None, 'P3': None}},
    {'choices': {'P1': 'P2:1-1', 'P2': None}},
    {'choices': {'P1': 'P9:1-1', 'P2': None}},
    {'choices': {'P1': ['P1:1-1'], 'P2': None}},
    {'choices': {'P1': False, 'P2': None}},
    {'choices': {'P1': '', 'P2': None}},
    {'choices': {'P1': None, 'P2': None}, 'status': 'excerpts'},
    {'choices': {'P1': None, 'P2': None}, 'support': 'direct'},
    {'choices': None}, [], None,
    '{"choices":{"P1":null,"P1":"P1:1-1","P2":null}}',
    '{"choices":{"P1":null,"P2":null},"choices":{"P1":null,"P2":null}}',
    'not JSON',
])
def test_malformed_or_ambiguous_choices_fail_without_answer(passages, value):
    result = a.generate_answer('Question', passages, call_api=api_for(value, []))
    assert result['validation'] == 'generation_rejected' and not result['answer']['extracts']


def test_nulls_are_fresh_abstention_and_empty_catalogs_skip_model(passages):
    calls = []
    result = a.generate_answer('Absent trial?', passages, call_api=api_for(dict(choices=dict(P1=None, P2=None)), calls))
    assert result['answer'] == dict(status='insufficient_evidence', extracts=[])
    assert result['validation'] == 'exact_quotes_verified'
    assert [p for p, _ in calls] == ['tags', 'chat']
    for values, state in [([], 'no_passages'), ([dict(record=dict(passage=dict(passage_id='short'), text='Too short.'))], 'no_selectable_spans')]:
        result = a.generate_answer('Question', values, call_api=lambda *_: pytest.fail('No model call'))
        assert result['model_called'] is False and result['validation'] == state


def test_count_limit_and_order_do_not_depend_on_model_key_order(passages):
    sources, spans = evidence_spans.catalog(passages)
    value = dict(choices=dict(P2='P2:1-1', P1='P1:1-1'))
    assert [e['passage_id'] for e in a.resolve(value, sources, spans)['extracts']] == ['p0', 'p1']
    four = [dict(record=dict(passage=dict(passage_id=f'p{i}'), text=passages[0]['record']['text'])) for i in range(4)]
    value = dict(choices={f'P{i}': f'P{i}:1-1' for i in range(1, 5)})
    assert a.generate_answer('Question', four, call_api=api_for(value, []))['validation'] == 'generation_rejected'
    with pytest.raises(ValueError, match='at most five'):
        a.generate_answer('Question', four * 2, call_api=lambda *_: pytest.fail('No call'))


def test_model_pin_reasoning_and_truncation_rejected(passages):
    with pytest.raises(OSError):
        a.generate_answer('Question', passages, call_api=lambda *_: dict(models=[]))
    with pytest.raises(ValueError):
        a.generate_answer('Question', passages, reasoning=True)
    with pytest.raises(ValueError):
        a.generate_answer('Question', passages, model='qwen3:8b')
    def api(path, payload=None):
        if path == 'tags':
            return dict(models=[dict(name=a.MODEL, digest=span_answer.MODELS[a.MODEL])])
        return dict(done=True, done_reason='length', message=dict(content='{"choices":{"P1":null,"P2":null}}'))
    assert a.generate_answer('Question', passages, call_api=api)['validation'] == 'generation_rejected'


def test_runner_uses_saved_retrieval_without_gold_or_previous_decisions(tmp_path, monkeypatch, passages):
    from scripts.retrieval import compare_scope_evaluator as runner
    from scripts.retrieval.evaluate_answers import checked_read
    suite = json.loads((runner.ROOT/'configs/evidence/evaluation/development-v1.json').read_text())
    monkeypatch.setattr(runner, 'frozen_inputs', lambda *_: ({}, {c['id']: dict(passages=passages) for c in suite['cases']}))
    calls = []
    monkeypatch.setattr(a, 'api', api_for(dict(choices=dict(P1='P1:1-1', P2=None)), calls))
    monkeypatch.setattr('sys.argv', ['compare', '--selection', str(tmp_path/'unused'), '--output', str(tmp_path/'run'), '--policy', 'choice-spans', '--evaluator', a.MODEL])
    assert runner.main() == 0
    manifest = checked_read(tmp_path/'run'/'manifest.json')
    assert manifest['generation_mode'] == 'choice-spans' and manifest['reused_selection_manifest_sha256'] is None
    assert manifest['policy'] == a.POLICY and 'src/retrieval/choice_span_answer.py' in manifest['source_sha256']
    requests = [p for path, p in calls if path == 'chat']
    assert len(requests) == 10
    for case, payload in zip(suite['cases'], requests):
        assert json.loads(payload['messages'][1]['content']) == dict(question=case['question'], sources=evidence_spans.catalog(passages)[0])
