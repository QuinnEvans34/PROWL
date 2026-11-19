"""Synthetic rehearsal checks; these never establish medical answer quality."""
from copy import deepcopy
import pytest
from scripts.retrieval import check_expert_demo as runner


def test_default_rehearsal_never_calls_network_or_model():
    spec, _ = runner.load_checklist()
    def forbidden(*args):
        pytest.fail('Context-only rehearsal must not call a transport')
    result = runner.evaluate(spec, transport=forbidden)
    assert result['mode'] == 'context_only' and result['independent_evaluation'] is False
    assert all(r['transport']=='not_called' and r['manual_review']=='pending'
        and r['answer_accuracy']=='not_assessed' for r in result['results'])


def test_requested_demo_sequence_keeps_questions_and_bounded_history():
    spec, _ = runner.load_checklist()
    cases = {c['id']: c for c in spec['cases']}
    sequence = ['function', 'insulin_followup', 'loss_of_function',
        'location_followup', 'disease_signs_followup']
    result = runner.evaluate({**spec, 'cases': [cases[i] for i in sequence]})
    for row, case_id in zip(result['results'], sequence):
        assert row['question'] == cases[case_id]['question']
        assert len(row['context']['previous_questions']) <= 3
        assert row['context_check'] == 'matched'
    assert result['results'][1]['context']['previous_questions'] == ['What does the pancreas do?']


def test_stubbed_live_transport_records_responses_without_claiming_quality():
    spec, _ = runner.load_checklist()
    spec = {**spec, 'cases': spec['cases'][:3]}
    seen = []
    def transport(url, payload):
        seen.append(deepcopy(payload))
        assert set(payload) == {'request', 'conversation'}
        assert 'source_candidates' not in str(payload)
        request = payload['request']
        return 200, dict(request_id=request['request_id'], question=request['question'],
            generation='unavailable', answer=None, evidence=[])
    result = runner.evaluate(spec, live=True, transport=transport)
    assert len(seen) == 3
    assert [p['request']['question'] for p in seen] == [c['question'] for c in spec['cases']]
    assert all(r['transport']=='completed' and r['manual_review']=='pending'
        and r['answer_accuracy']=='not_assessed' for r in result['results'])
    assert all(r['response']['answer'] is None for r in result['results'])


@pytest.mark.parametrize('url', ['https://127.0.0.1:5180', 'http://example.com',
    'http://localhost.example.com', 'http://user:secret@localhost',
    'http://127.0.0.1:5180/private', 'http://127.0.0.1:5180?token=secret'])
def test_live_rehearsal_rejects_nonlocal_or_credential_urls_before_transport(url):
    spec, _ = runner.load_checklist()
    def forbidden(*args):
        pytest.fail('Invalid URLs must not reach transport')
    with pytest.raises(ValueError, match='loopback'):
        runner.evaluate(spec, live=True, base_url=url, transport=forbidden)


def test_checklist_preserves_partial_function_loss_and_nonexhaustive_signs():
    spec, _ = runner.load_checklist()
    assert 'Partial coverage' in spec['source_scopes']['loss_of_function']['limits']
    assert 'exhaustive' in spec['source_scopes']['disease_signs']['limits']
    assert spec['exposed_development'] is True and spec['independent_evaluation'] is False
