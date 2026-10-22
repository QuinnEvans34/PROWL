"""Invented cases qualify the disease need without changing old or private admission."""
from copy import deepcopy

import pytest

from src.retrieval.development_set import validate_draft
from tests.retrieval.test_development_set import fixture, seal
from tests.retrieval.test_direct_ingestion import bundle


def revision(fixture):
    suite, *rest = deepcopy(fixture)
    suite.update(schema_version='prowl-development-draft-v3',
                 information_needs_sha256='c'*64, information_needs_parent_sha256='d'*64,
                 information_needs_base_sha256='e'*64)
    case = suite['cases'][0]
    case.update(id='q:dev6-31', primary_need='N1.6')
    case['labels']['question_id'] = case['id']
    case['authorship'].update(author='Quinton Evans', basis='stakeholder_input')
    return [seal(suite), *rest]


def check(data, **overrides):
    kwargs = dict(manifest_sha256='a'*64, regression_sha256='b'*64,
                  information_needs_sha256='c'*64, information_needs_parent_sha256='d'*64,
                  information_needs_base_sha256='e'*64)
    kwargs.update(overrides)
    return validate_draft(*data, **kwargs)


def test_new_need_preserves_real_author_role_and_remains_draft(fixture):
    report = check(revision(fixture))
    assert report['counts']['answered'] == 20 and report['ready_for_tuning'] is False
    assert len(report['human_review_pending']) == 30


@pytest.mark.parametrize('key', ['information_needs_sha256', 'information_needs_parent_sha256',
                                'information_needs_base_sha256'])
def test_all_three_need_versions_must_be_bound(fixture, key):
    with pytest.raises(ValueError, match='information-needs'):
        check(revision(fixture), **{key: 'f'*64})
    with pytest.raises(ValueError, match='information-needs'):
        check(revision(fixture), **{key: None})


@pytest.mark.parametrize('mutate', [
    lambda s: s['cases'][0].update(primary_need='N2.5'),
    lambda s: s['cases'][0].update(family='measurement'),
    lambda s: s['cases'][0].update(split='held_out'),
    lambda s: s['cases'][0]['authorship'].update(exposed=False),
    lambda s: s['cases'][0]['review'].update(human_adjudication='complete'),
    lambda s: s['cases'][0]['finding'].update(patient_id='INVENTED_CANARY'),
])
def test_scope_change_does_not_relax_existing_guards(fixture, mutate):
    suite, *rest = revision(fixture)
    mutate(suite)
    with pytest.raises(ValueError): check([seal(suite), *rest])


@pytest.mark.parametrize('version',['v1','v2'])
def test_older_development_does_not_silently_inherit_new_disease_need(fixture,version):
    suite, *rest = revision(fixture)
    suite['schema_version'] = 'prowl-development-draft-'+version
    suite.pop('information_needs_parent_sha256')
    if version=='v1':
        suite.pop('information_needs_sha256')
        suite.pop('information_needs_base_sha256')
    case = suite['cases'][0]
    case['id'] = case['labels']['question_id'] = 'q:dev2-01'
    case['authorship'].update(author='Codex', basis='literature_inspection')
    with pytest.raises(ValueError, match='Need/family mismatch'):
        check([seal(suite), *rest])


def test_v3_does_not_admit_unlisted_seventh_need(fixture):
    suite,*rest=revision(fixture)
    suite['cases'][0]['primary_need']='N1.7'
    with pytest.raises(ValueError):check([seal(suite),*rest])
