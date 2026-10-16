import json
import signal
import time
import pytest
from scripts.retrieval.compare_scope_evaluator import BudgetExpired, time_limit, frozen_inputs
from scripts.retrieval.evaluate_answers import save
from src.retrieval.direct_ingestion import digest


def test_wall_clock_expiration_bypasses_exception_handlers_and_cleans_alarm():
    handler = signal.getsignal(signal.SIGALRM)
    with pytest.raises(BudgetExpired):
        with time_limit(0.02):
            try:
                time.sleep(1)
            except Exception:
                pytest.fail('Deadline was swallowed')
    assert signal.getitimer(signal.ITIMER_REAL) == (0, 0)
    assert signal.getsignal(signal.SIGALRM) == handler


def test_nested_calls_do_not_extend_total_deadline():
    with pytest.raises(BudgetExpired):
        with time_limit(0.06):
            with time_limit(0.02):
                time.sleep(0.01)
            remaining = signal.getitimer(signal.ITIMER_REAL)[0]
            assert 0 < remaining < 0.06
            time.sleep(1)
    assert signal.getitimer(signal.ITIMER_REAL) == (0, 0)


def test_frozen_inputs_bind_question_suite_policy_and_receipt(tmp_path):
    suite = dict(cases=[dict(id='case', question='question')], corpus_record_sha256='corpus')
    save(tmp_path/'manifest.json', dict(suite=suite, suite_sha256=digest(suite),
         policy='verified-spans-v1', corpus_record_sha256='corpus'))
    save(tmp_path/'case.json', dict(case_id='case', question='different', suite_sha256=digest(suite)))
    with pytest.raises(ValueError, match='receipt mismatch'):
        frozen_inputs(tmp_path, suite)
    changed = json.loads((tmp_path/'case.json').read_text())
    changed['question'] = 'question'
    (tmp_path/'case.json').write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='hash mismatch'):
        frozen_inputs(tmp_path, suite)


def test_interrupted_run_preserves_completed_call_and_never_retries(tmp_path, monkeypatch):
    from scripts.retrieval import compare_scope_evaluator as runner
    from src.retrieval import evidence_spans, span_answer, scope_answer
    from scripts.retrieval.evaluate_answers import checked_read
    passages = [{'record': {'passage': {'passage_id': f'p{i}'},
                            'text': f'Study {i} reports quantitative image features in this artificial source.'}}
                for i in (1, 2)]
    spans = evidence_spans.catalog(passages)[1]
    selection = dict(status='excerpts', span_ids=['P1:1-1', 'P2:1-1'])
    base = dict(answer=evidence_spans.resolve(selection, spans), selection=selection,
                provenance=dict(policy=span_answer.POLICY, span_catalog_sha256=digest(spans)),
                validation='exact_quotes_verified', model_called=True)
    suite = json.loads((runner.ROOT/'configs/evidence/evaluation/development-v1.json').read_text())
    old = dict(passages=passages, generation=base)
    monkeypatch.setattr(runner, 'frozen_inputs', lambda *_: ({}, {c['id']: old for c in suite['cases']}))
    calls = []
    def api(path, payload=None):
        if path == 'tags':
            return {'models': [{'name': scope_answer.MODEL, 'digest': scope_answer.MODEL_SHA}]}
        calls.append(payload)
        if len(calls) == 2:
            raise BudgetExpired('simulated deadline')
        value = dict(checks={a: 'match' for a in scope_answer.AXES},
                     support_span_id='P1:1-1', reason='Artificial source match.')
        return dict(done=True, message=dict(content=json.dumps(value)))
    monkeypatch.setattr(scope_answer, 'api', api)
    output = tmp_path/'run'
    monkeypatch.setattr(runner.sys, 'argv', ['compare', '--selection', str(tmp_path),
                        '--output', str(output), '--evaluator', scope_answer.MODEL])
    assert runner.main() == 1 and len(calls) == 2
    assert checked_read(output/'radiomics-call-1.json')['response']['done'] is True
    assert len(checked_read(output/'interruption.json')['raw_model_responses']) == 1
    completion = checked_read(output/'completion.json')
    assert completion['completed'] == [] and len(completion['unscored']) == 10
    assert not (output/'radiomics.json').exists()
    assert signal.getitimer(signal.ITIMER_REAL) == (0, 0)


def test_direct_span_mode_uses_passages_without_saved_selection_or_review(tmp_path, monkeypatch):
    from scripts.retrieval import compare_scope_evaluator as runner
    from scripts.retrieval.evaluate_answers import checked_read
    from src.retrieval import span_answer, scope_answer
    suite = json.loads((runner.ROOT/'configs/evidence/evaluation/development-v1.json').read_text())
    passage = dict(record=dict(passage=dict(passage_id='invented'),
                   text='An invented study describes an imaging method in this sentence.'))
    # No generation field: a review stage or reused selection would fail this test.
    old = dict(passages=[passage])
    monkeypatch.setattr(runner, 'frozen_inputs', lambda *_: ({}, {c['id']: old for c in suite['cases']}))
    monkeypatch.setattr(scope_answer, 'verify_answer', lambda *_a, **_k: pytest.fail('No review stage'))
    calls = []
    def api(path, payload=None):
        if path == 'tags':
            return dict(models=[dict(name='qwen3:30b',digest=span_answer.MODELS['qwen3:30b'])])
        calls.append(payload)
        return dict(done=True,message=dict(content='{"status":"excerpts","span_ids":["P1:1-1"]}'))
    monkeypatch.setattr(span_answer, 'api', api)
    output = tmp_path/'run'
    monkeypatch.setattr(runner.sys,'argv',['compare','--selection',str(tmp_path),'--output',str(output),
                                         '--evaluator','qwen3:30b','--policy','spans'])
    assert runner.main() == 0 and len(calls) == 10
    manifest = checked_read(output/'manifest.json')
    assert manifest['policy'] == span_answer.POLICY and manifest['reused_selection_manifest_sha256'] is None
    assert manifest['prompt_sha256'] == digest(span_answer.SYSTEM)
    for request, case in zip(calls, suite['cases']):
        content = json.loads(request['messages'][1]['content'])
        assert set(content) == {'question','sources'} and content['question'] == case['question']
        assert request['model'] == 'qwen3:30b'
    assert checked_read(output/'completion.json')['unscored'] == []
