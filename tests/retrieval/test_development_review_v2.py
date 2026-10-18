"""Invented attestations only; the actual expanded review starts empty."""
import pytest

from src.retrieval.development_review import new_record
from tests.retrieval.test_development_review import check, event, reseal
from tests.retrieval.test_development_v3 import revision
from tests.retrieval.test_development_set import fixture
from tests.retrieval.test_direct_ingestion import bundle


def test_new_question_review_starts_pending(fixture):
    suite = revision(fixture)[0]
    record = new_record(suite, 'a'*64)
    assert record['schema_version'] == 'prowl-development-review-v2'
    result = check(record, suite)
    assert all(len(ids) == 30 for ids in result['pending'].values())
    event(record, suite, 'wording_and_answer', count=1)
    assert 'q:dev6-31' not in check(record, suite)['pending']['wording_and_answer']
    assert 'q:dev6-31' in check(record, suite)['pending']['evidence_labels']


def test_hypothetical_complete_review_cannot_release_tuning(fixture):
    suite = revision(fixture)[0]; record = new_record(suite, 'a'*64)
    for stage in ('wording_and_answer', 'evidence_labels', 'second_consistency'):
        event(record, suite, stage)
    assert check(record, suite)['development_review_attested_complete']
    assert not check(record, suite)['ready_for_tuning']


@pytest.mark.parametrize('old_suite', [False, True])
def test_review_version_must_match_draft_generation(fixture, old_suite):
    suite = fixture[0] if old_suite else revision(fixture)[0]
    record = new_record(suite, 'a'*64)
    record['schema_version'] = 'prowl-development-review-v2' if old_suite else 'prowl-development-review-v1'
    reseal(record)
    with pytest.raises(ValueError, match='review schema violation'): check(record, suite)


def test_new_case_attestation_requires_exact_hash(fixture):
    suite = revision(fixture)[0]; record = new_record(suite, 'a'*64)
    event(record, suite, 'wording_and_answer', count=1)
    record['events'][0]['targets'][0]['content_sha256'] = 'f'*64
    reseal(record)
    with pytest.raises(ValueError, match='case binding mismatch'): check(record, suite)
