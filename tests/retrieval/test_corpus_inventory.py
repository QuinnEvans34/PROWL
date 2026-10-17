import copy

import pytest
from src.retrieval import direct_ingestion as d
from src.retrieval.corpus_inventory import frozen_inventory, inventory, verify_sources
from tests.retrieval.test_direct_ingestion import bundle, batch


def test_frozen_inventory_order_independent_and_content_bound(bundle):
    b = batch(bundle)
    a = d.frozen_batch([b['items'][0]['record']], [b['items'][0]['vector']], b['encoder'])
    z = d.frozen_batch([b['items'][1]['record']], [b['items'][1]['vector']], b['encoder'])
    assert frozen_inventory([a,z]) == frozen_inventory([z,a])
    verify_sources([a,z], [bundle])
    assert frozen_inventory([b])['passage_count'] == 2
    assert frozen_inventory([b]) != frozen_inventory([a])


@pytest.mark.parametrize('change', ['duplicate_batch', 'duplicate_passage', 'encoder', 'vector', 'record', 'missing'])
def test_bad_frozen_inventory_refused(bundle, change):
    b = batch(bundle); other = copy.deepcopy(b)
    batches = [b]
    if change == 'duplicate_batch': batches.append(other)
    elif change == 'duplicate_passage':
        batches.append(d.frozen_batch([b['items'][0]['record']], [b['items'][0]['vector']], b['encoder']))
    elif change == 'encoder':
        other['encoder']['test'] = 'changed'
        batches.append(d.frozen_batch([other['items'][1]['record']], [other['items'][1]['vector']], other['encoder']))
    elif change == 'vector': b['items'][0]['vector'][0] = 0
    elif change == 'record': b['items'][0]['record']['citation']['title'] = 'changed'
    else: batches = []
    with pytest.raises(ValueError): frozen_inventory(batches)


@pytest.mark.parametrize('change', ['citation', 'source', 'text', 'missing_bundle'])
def test_canonical_binding_refuses_modified_record(bundle, change):
    b = batch(bundle); bundles = [bundle]
    row = b['items'][0]['record']
    if change == 'citation': row['citation'] = dict(row['citation'], title='other')
    elif change == 'source': row['source_sha256'] = 'f'*64
    elif change == 'text': row['text'] += 'invented'
    else: bundles = []
    with pytest.raises((ValueError, KeyError)): verify_sources([b], bundles)


@pytest.mark.parametrize('change', ['batch_count', 'source', 'stored_vector', 'stored_text'])
def test_database_projection_validates_actual_bytes(bundle, change):
    b = batch(bundle)
    rows = [dict(i, passage_id=i['record']['passage']['passage_id'], batch_id=b['batch_id'],
        work_id=i['record']['passage']['work_id'], text=i['record']['text']) for i in b['items']]
    counts = {b['batch_id']: 2}
    sources = {bundle['work']['work_id']: (bundle['revision']['revision_id'], bundle['source_sha256'])}
    assert inventory(b['encoder'], counts, sources, rows) == frozen_inventory([b])
    if change == 'batch_count': counts[b['batch_id']] = 3
    elif change == 'source': sources[bundle['work']['work_id']] = ('other', 'other')
    elif change == 'stored_vector': rows[0]['vector'] = rows[1]['vector']
    else: rows[0]['text'] += 'other'
    with pytest.raises(ValueError): inventory(b['encoder'], counts, sources, rows)
