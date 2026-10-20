from copy import deepcopy

import pytest

from src.retrieval.evaluation_delta import CORE, delta_cases, extend_exposure


def case():
    c = {k: 'same' for k in CORE}
    c.update(id='q:dev-1', split='development', expected={'status': 'answered'},
             labels={'spans': [{'start': 1, 'end': 3, 'grade': 'direct'}]},
             source_judgments=[{'work_id': 'w1', 'grade': 'direct'}])
    return c


def test_unchanged_is_not_new_acceptance():
    report = delta_cases([case()], [case()])
    assert not report['cases'][0]['changed_core_fields']
    assert not report['acceptance_recorded'] and not report['ready_for_tuning']


def test_changed_and_removed_evidence_is_not_hidden():
    old = case(); new = deepcopy(old)
    new['labels']['spans'][0]['grade'] = 'partial_context'
    new['source_judgments'][0]['grade'] = 'partial_context'
    r = delta_cases([old], [new])['cases'][0]
    assert r['removed_spans'] == old['labels']['spans']
    assert r['added_or_changed_spans'] == new['labels']['spans']
    assert r['removed_judgments'] == old['source_judgments']
    assert not r['changed_core_fields']


def test_replacement_keeps_removed_identity_and_new_review():
    old = case(); new = deepcopy(old); new['id'] = 'q:dev-2'
    r = delta_cases([old], [new])
    assert r['removed_ids'] == [old['id']]
    assert r['cases'][0]['new'] and set(r['cases'][0]['changed_core_fields']) == set(CORE)


def test_gap_recheck_survives_identical_empty_labels():
    c = case(); c['expected']['status'] = 'insufficient_evidence'; c['labels']['spans'] = []
    assert delta_cases([c], [c])['cases'][0]['gap_recheck_required']


@pytest.mark.parametrize('kind', ['duplicate', 'protected'])
def test_invalid_case_roles_refused(kind):
    cases = [case(), case()] if kind == 'duplicate' else [dict(case(), split='held_out')]
    with pytest.raises(ValueError): delta_cases([], cases)


def test_exposure_preserves_origins_without_mutating_parent():
    inventory = dict(rows=[dict(normalized_wording='old?', variants=['Old?'], origins=[{'old': True}])],
                     record_count=1, distinct_wording_count=1, intent_groups=['old-intent'])
    original = deepcopy(inventory)
    src = dict(path='public.json', sha256='a'*64, exposure='development_only',
               cases=[dict(id='a', question='OLD?'), dict(id='b', question='New?')])
    r = extend_exposure(inventory, [src])
    assert inventory == original and r['record_count'] == 3 and r['distinct_wording_count'] == 2
    old = next(x for x in r['rows'] if x['normalized_wording'] == 'old?')
    assert len(old['origins']) == 2 and old['origins'][0] == {'old': True}
    assert r['intent_groups'] == ['old-intent']  # no invented semantic grouping


def test_private_exposure_input_refused():
    with pytest.raises(ValueError):
        extend_exposure(dict(rows=[], record_count=0), [dict(exposure='held_out')])
