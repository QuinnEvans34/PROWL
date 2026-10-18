"""Invented revision chains; no protected data or actual model calls."""
import pytest

from src.retrieval.public_exposure import (
    DIRECTORY, extend_with_development, load_current_exposure, current_public_preflight,
)
from tests.retrieval.test_public_exposure import public_fixture, write, sealed


@pytest.fixture
def current_fixture(public_fixture):
    root, _, old = public_fixture
    corpus = write(root, 'configs/evidence/corpus-disease-v1.json',
                   dict(inventory=dict(source_count=14, passage_count=1179, content_sha256='c'*64)))
    suite = sealed(dict(schema_version='prowl-development-draft-v3', status='draft_pending_human_review',
        corpus_manifest_sha256=corpus['sha256'], corpus_content_sha256='c'*64,
        cases=[dict(id=f'q:dev6-{i:02}', question=f'New invented wording {i}?',
                    intent_group='new-invented-intent', split='development', authorship=dict(exposed=True))
               for i in range(30)]))
    proposed = write(root, DIRECTORY+'development-v6-draft.json', suite)
    exposure = sealed(dict(version='prowl-public-exposure-v3', parent=old['exposure'], development=proposed,
        inventory=extend_with_development(root, old['exposure'], proposed)))
    exposure_pin = write(root, DIRECTORY+'public-exposure-v3.json', exposure)
    state = sealed(dict(version='prowl-evaluation-reconciliation-v2',
        state='engineering_review_complete_human_review_pending', ready_for_private_authoring=False,
        ready_for_tuning=False, final_development=None, corpus=corpus, exposure=exposure_pin,
        proposed_development=proposed, pending=['Invented human review pending']))
    write(root, DIRECTORY+'evaluation-reconciliation-v2.json', state)
    return root, exposure, state, suite


def test_revision_retains_previous_origins_and_adds_new_intents(current_fixture):
    root, _, _, _ = current_fixture
    inventory = load_current_exposure(root)['inventory']
    assert inventory['record_count'] == 46 and inventory['distinct_wording_count'] == 37
    assert inventory['intent_groups'] == ['invented-intent', 'new-invented-intent']
    report = current_public_preflight(root)
    assert report['proposed_development_cases'] == 30
    assert not report['ready_for_private_authoring'] and not report['ready_for_tuning']


def test_resealed_revision_cannot_drop_an_old_wording(current_fixture):
    root, exposure, _, _ = current_fixture
    exposure['inventory']['rows'].pop(0)
    write(root, DIRECTORY+'public-exposure-v3.json', sealed(exposure))
    with pytest.raises(ValueError, match='Current public exposure mismatch'):
        load_current_exposure(root)


@pytest.mark.parametrize('mutation', ['split', 'unexposed', 'hash', 'wrong_path'])
def test_new_input_must_be_pinned_exposed_development(current_fixture, mutation):
    root, exposure, _, suite = current_fixture
    if mutation == 'split': suite['cases'][0]['split'] = 'held_out'
    if mutation == 'unexposed': suite['cases'][0]['authorship']['exposed'] = False
    if mutation == 'hash': suite['content_sha256'] = 'f'*64
    elif mutation != 'wrong_path': suite = sealed(suite)
    proposed = write(root, DIRECTORY+'development-v6-draft.json', suite)
    if mutation == 'wrong_path': proposed['path'] = '/private/never-open.json'
    with pytest.raises(ValueError): extend_with_development(root, exposure['parent'], proposed)


@pytest.mark.parametrize('mutation', ['ready', 'final', 'corpus', 'exposure'])
def test_human_pending_record_cannot_become_admission(current_fixture, mutation):
    root, _, state, _ = current_fixture
    if mutation == 'ready': state['ready_for_private_authoring'] = True
    if mutation == 'final': state['final_development'] = state['proposed_development']
    if mutation == 'corpus': state['corpus']['path'] = 'configs/evidence/corpus-coverage-v2.json'
    if mutation == 'exposure': state['exposure']['path'] = DIRECTORY+'public-exposure-v2.json'
    write(root, DIRECTORY+'evaluation-reconciliation-v2.json', sealed(state))
    with pytest.raises(ValueError): current_public_preflight(root)
