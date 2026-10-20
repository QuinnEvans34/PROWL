from copy import deepcopy

import pytest

from src.retrieval.evaluation_delta import extend_exposure
from src.retrieval.public_exposure import DIRECTORY, latest_public_preflight
from tests.retrieval.test_public_exposure import public_fixture, write, sealed
from tests.retrieval.test_public_exposure_v3 import current_fixture


@pytest.fixture
def prepared(current_fixture):
    root, parent, _, _ = current_fixture
    sources = []
    for path in ('configs/evidence/record-search-screen-v1.json', 'configs/evidence/week3-quality-matrix-v1.json'):
        cases = [dict(id='invented', question='Newly exposed question?')]
        pin = write(root, path, dict(exposure='development_only_not_independent', cases=cases))
        sources.append(dict(**pin, exposure='development_only', cases=cases))
    parent_pin = write(root, DIRECTORY+'public-exposure-v3.json', parent)
    data = sealed(dict(version='prowl-public-exposure-v4-preparation',
        status='preparation_not_private_admission', parent=parent_pin, sources=sources,
        inventory=extend_exposure(parent['inventory'], sources), limitations=['Invented fixture']))
    write(root, DIRECTORY+'public-exposure-v4-preparation.json', data)
    return root, data


def test_latest_preflight_counts_new_exposure_but_never_admits(prepared):
    r = latest_public_preflight(prepared[0])
    assert r['exposed_records'] == 48 and r['distinct_exposed_wordings'] == 38
    assert not r['ready_for_private_authoring'] and not r['ready_for_tuning']
    assert not r['private_content_read']


@pytest.mark.parametrize('mutation', ['drop_matrix', 'drop_wording', 'drop_union', 'admit', 'external'])
def test_resealed_bad_preparation_refused(prepared, mutation):
    root, data = prepared; data = deepcopy(data)
    if mutation == 'drop_matrix': data['sources'].pop()
    if mutation == 'drop_wording': data['sources'][0]['cases'] = []
    if mutation == 'drop_union': data['inventory']['rows'].pop()
    if mutation == 'admit': data['status'] = 'ready'
    if mutation == 'external': data['parent']['path'] = '/private/never-open.json'
    write(root, DIRECTORY+'public-exposure-v4-preparation.json', sealed(data))
    with pytest.raises(ValueError): latest_public_preflight(root)
