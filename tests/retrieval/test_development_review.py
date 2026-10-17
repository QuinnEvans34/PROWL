"""Review bookkeeping with invented cases; no real human decisions or protected content."""
from copy import deepcopy

import pytest

from src.retrieval.development_review import new_record, read_public_json, validate_review
from src.retrieval.direct_ingestion import digest
from tests.retrieval.test_development_set import fixture, seal
from tests.retrieval.test_direct_ingestion import bundle


def reseal(record):
    record.pop('content_sha256', None)
    record['content_sha256'] = digest(record)


def event(record, suite, stage, decision='accept', count=30):
    record['events'].append(dict(sequence=len(record['events']) + 1,
        reviewer='Quinton Evans', reviewed_at='2026-10-17T22:00:00Z', stage=stage,
        decision=decision, human_statement='Invented test attestation; not an actual review.',
        targets=[dict(id=c['id'], content_sha256=c['content_sha256']) for c in suite['cases'][:count]]))
    reseal(record)


def check(record, suite):
    return validate_review(record, suite, answers_sha256='a'*64)


def test_blank_record_does_not_infer_any_approval(fixture):
    suite = fixture[0]
    record = new_record(suite, 'a'*64)
    result = check(record, suite)
    assert record['events'] == []
    assert all(len(pending) == 30 for pending in result['pending'].values())
    assert not result['development_review_attested_complete']
    assert not result['ready_for_tuning']


def test_wording_feedback_does_not_approve_evidence_or_second_pass(fixture):
    suite = fixture[0]; record = new_record(suite, 'a'*64)
    event(record, suite, 'wording_and_answer', count=10)
    result = check(record, suite)
    assert [len(result['pending'][s]) for s in result['pending']] == [20, 30, 30]


def test_complete_attestations_never_release_tuning_and_corrections_reopen_consistency(fixture):
    suite = fixture[0]; record = new_record(suite, 'a'*64)
    for stage in ('wording_and_answer', 'evidence_labels', 'second_consistency'):
        event(record, suite, stage)
    result = check(record, suite)
    assert result['development_review_attested_complete'] and not result['ready_for_tuning']
    event(record, suite, 'evidence_labels', 'revise', count=1)
    result = check(record, suite)
    assert len(result['pending']['evidence_labels']) == 1
    assert len(result['pending']['second_consistency']) == 30
    assert len(record['events']) == 4  # Keep the superseded acceptance in the history.


@pytest.mark.parametrize('stage,count', [('wording_and_answer',30), ('evidence_labels',30), ('evidence_labels',10)])
def test_premature_consistency_refused(fixture, stage, count):
    suite = fixture[0]; record = new_record(suite, 'a'*64)
    event(record, suite, stage, count=count)
    event(record, suite, 'second_consistency')
    with pytest.raises(ValueError, match='Resolve wording and evidence'):
        check(record, suite)


def test_partial_second_pass_refused(fixture):
    suite = fixture[0]; record = new_record(suite, 'a'*64)
    for stage in ('wording_and_answer','evidence_labels'):
        event(record, suite, stage)
    event(record, suite, 'second_consistency', count=10)
    with pytest.raises(ValueError, match='complete development set'):
        check(record, suite)


@pytest.mark.parametrize('change', [
    lambda r: r.update(ready_for_tuning=True),
    lambda r: r['events'][0].update(reviewer='Codex'),
    lambda r: r['events'][0].update(reviewed_at='not-a-date'),
    lambda r: r['events'][0].update(human_statement=' '),
    lambda r: r['events'][0].update(private_path='/invented/private'),
    lambda r: r['events'][0]['targets'][0].update(id='q:heldout-01'),
])
def test_closed_record_and_human_event_fields(fixture, change):
    suite=fixture[0]; record=new_record(suite, 'a'*64)
    event(record, suite, 'wording_and_answer'); change(record); reseal(record)
    with pytest.raises(ValueError, match='review schema violation'):
        check(record, suite)


@pytest.mark.parametrize('change', [
    lambda e: e.update(sequence=2),
    lambda e: e['targets'][0].update(content_sha256='f'*64),
    lambda e: e['targets'].__setitem__(1, deepcopy(e['targets'][0])),
])
def test_order_and_exact_case_bindings(fixture, change):
    suite=fixture[0]; record=new_record(suite, 'a'*64)
    event(record, suite, 'wording_and_answer'); change(record['events'][0]); reseal(record)
    with pytest.raises(ValueError): check(record, suite)


def test_question_and_answer_edits_invalidate_review(fixture):
    suite=deepcopy(fixture[0]); record=new_record(suite, 'a'*64)
    with pytest.raises(ValueError, match='content binding mismatch'):
        validate_review(record,suite,answers_sha256='b'*64)
    suite['cases'][0]['question']='A changed invented question?'; seal(suite)
    with pytest.raises(ValueError, match='content binding mismatch'): check(record,suite)


def test_tampered_case_or_record_hash_refused(fixture):
    suite=deepcopy(fixture[0]); record=new_record(suite, 'a'*64)
    record['answers_sha256']='b'*64
    with pytest.raises(ValueError,match='hash mismatch'): check(record,suite)
    record=new_record(suite, 'a'*64)
    suite['cases'][0]['question']='Another invented question?'
    reseal(suite)  # Rehashing only the parent cannot conceal a changed child.
    with pytest.raises(ValueError,match='hash mismatch'): check(record,suite)


def test_heldout_and_external_paths_refused_before_read(tmp_path, fixture):
    with pytest.raises(ValueError, match='repository development'):
        read_public_json(tmp_path/'private/development-review.json',tmp_path)
    with pytest.raises(ValueError, match='repository development'):
        read_public_json(tmp_path/'configs/evidence/evaluation/heldout.json',tmp_path)
    suite=deepcopy(fixture[0]); suite['cases'][0]['split']='held_out'; seal(suite)
    with pytest.raises(ValueError,match='draft schema violation'): new_record(suite,'a'*64)
