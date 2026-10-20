from copy import deepcopy

import pytest

from src.retrieval.development_review import new_record, validate_prepared_delta_review
from src.retrieval.records import sha256_hex
from tests.retrieval.test_development_set import fixture, seal
from tests.retrieval.test_direct_ingestion import bundle
from tests.retrieval.test_development_review import delta_fixture, event


def chain(fixture):
    old, old_record, answers, middle, middle_record = delta_fixture(fixture)
    event(middle_record, middle, 'evidence_labels')
    event(middle_record, middle, 'second_consistency')
    latest = deepcopy(middle)
    for c in latest['cases']: c['labels']['label_version'] = 'new-provenance-version'
    seal(latest)
    record = new_record(latest, 'a'*64)
    kw = dict(packet_sha256='a'*64, prior_suite=middle, prior_record=middle_record,
        prior_answers=answers, earlier_suite=old, earlier_record=old_record, earlier_answers=answers)
    return latest, record, kw


def test_complete_chain_carries_semantics_not_consistency(fixture):
    suite, record, kw = chain(fixture)
    r = validate_prepared_delta_review(record, suite, **kw)
    assert len(r['inherited_acceptances']['wording_and_answer']) == 30
    assert len(r['inherited_acceptances']['evidence_labels']) == 30
    assert len(r['pending']['second_consistency']) == 30
    event(record, suite, 'second_consistency')
    r = validate_prepared_delta_review(record, suite, **kw)
    assert r['development_review_attested_complete'] and not r['ready_for_tuning']


def test_changed_evidence_reopens_only_that_evidence(fixture):
    suite, _, kw = chain(fixture)
    suite['cases'][0]['source_judgments'][0]['rationale'] = 'Changed evidence rationale'
    seal(suite); record = new_record(suite, 'a'*64)
    r = validate_prepared_delta_review(record, suite, **kw)
    assert r['pending']['evidence_labels'] == [suite['cases'][0]['id']]
    assert not r['pending']['wording_and_answer']


def test_changed_meaning_does_not_inherit_wording(fixture):
    suite, _, kw = chain(fixture); suite['cases'][0]['question'] += ' Explain limits.'
    seal(suite); record = new_record(suite, 'a'*64)
    r = validate_prepared_delta_review(record, suite, **kw)
    assert r['pending']['wording_and_answer'] == [suite['cases'][0]['id']]


@pytest.mark.parametrize('mutation', ['parent', 'packet', 'incomplete'])
def test_broken_acceptance_lineage_refused(fixture, mutation):
    suite, record, kw = chain(fixture)
    if mutation == 'parent': kw['earlier_record']['content_sha256'] = 'f'*64
    if mutation == 'packet': kw['packet_sha256'] = 'b'*64
    if mutation == 'incomplete': event(kw['prior_record'], kw['prior_suite'], 'wording_and_answer', 'revise', count=1)
    with pytest.raises(ValueError): validate_prepared_delta_review(record, suite, **kw)
