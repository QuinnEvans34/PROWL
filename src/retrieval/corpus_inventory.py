"""Bounded, content-verified inventory for the small direct literature collection.

The same identity is derived from canonical frozen batches or PostgreSQL. Collection
names are deliberately excluded so a separate rebuild can prove exact content parity.
"""
import json

from .direct_ingestion import digest, validate_row, vector_values, verify_batch
from .passages import verify_passage, verify_representation_source, passage_text

MAX_PASSAGES = 4096


def verify_sources(batches, bundles):
    """Bind every frozen record to the retained canonical source representation."""
    by_work = {b['work']['work_id']: b for b in bundles}
    if len(by_work) != len(bundles):
        raise ValueError('Duplicate canonical source')
    used = set()
    for bundle in bundles:
        verify_representation_source(bundle['representation'], bundle['original_sections'])
    for batch in batches:
        for item in batch['items']:
            row = item['record']; work = row['passage']['work_id']
            bundle = by_work[work]; used.add(work)
            verify_passage(row['passage'], bundle['representation'])
            if (row['text'] != passage_text(row['passage'], bundle['representation'])
                    or row['rights'] != bundle['rights'] or row['citation'] != bundle['citation']
                    or row['revision_id'] != bundle['revision']['revision_id']
                    or row['source_sha256'] != bundle['source_sha256']):
                raise ValueError('Frozen row differs from canonical source')
    if used != set(by_work):
        raise ValueError('Canonical source inventory mismatch')


def inventory(encoder, batches, sources, passages):
    if not passages or len(passages) > MAX_PASSAGES:
        raise ValueError('Corpus inventory requires 1..4096 passages')
    if len({p['passage_id'] for p in passages}) != len(passages):
        raise ValueError('Duplicate corpus passage')
    actual_sources, counts, members = {}, {}, []
    for p in passages:
        row = validate_row(p['record'])
        if (p['passage_id'] != row['passage']['passage_id'] or p['text'] != row['text']
                or p['work_id'] != row['passage']['work_id']
                or vector_values(p['vector'])[1] != p['vector_sha256']):
            raise ValueError('Corpus passage content mismatch')
        source = (row['revision_id'], row['source_sha256'])
        work = p['work_id']
        if work in actual_sources and actual_sources[work] != source:
            raise ValueError('Corpus source revision conflict')
        actual_sources[work] = source
        counts[p['batch_id']] = counts.get(p['batch_id'], 0) + 1
        members.append(dict(passage_id=p['passage_id'], batch_id=p['batch_id'],
                            record_sha256=digest(row), vector_sha256=p['vector_sha256']))
    if counts != batches or actual_sources != sources:
        raise ValueError('Corpus inventory count/source mismatch')
    payload = dict(version='prowl-corpus-inventory-v1', encoder_id=digest(encoder),
        batches=[dict(batch_id=k, rows=v) for k,v in sorted(batches.items())],
        sources=[dict(work_id=k, revision_id=v[0], source_sha256=v[1]) for k,v in sorted(sources.items())],
        passages=sorted(members, key=lambda p: p['passage_id']))
    return dict(version=payload['version'], encoder_id=payload['encoder_id'],
                batch_count=len(batches), source_count=len(sources), passage_count=len(passages),
                content_sha256=digest(payload))


def frozen_inventory(batches):
    if not batches or len(batches) > 256:
        raise ValueError('Require 1..256 frozen batches')
    encoder = batches[0]['encoder']
    counts, sources, passages = {}, {}, []
    for batch in batches:
        verify_batch(batch)
        if batch['encoder'] != encoder or batch['batch_id'] in counts:
            raise ValueError('Mixed encoder or duplicate batch')
        counts[batch['batch_id']] = len(batch['items'])
        for item in batch['items']:
            row = item['record']
            sources.setdefault(row['passage']['work_id'], (row['revision_id'], row['source_sha256']))
            passages.append(dict(item, passage_id=row['passage']['passage_id'],
                batch_id=batch['batch_id'], work_id=row['passage']['work_id'], text=row['text']))
    return inventory(encoder, counts, sources, passages)


def database_inventory(db, collection):
    """Caller owns a repeatable-read transaction spanning inventory and any search.

    Limits prevent accidentally scanning the full metadata archive. No writes or model calls.
    """
    bound = db.execute('SELECT encoder_id,encoder FROM literature.collections WHERE id=%s',
                       (collection,)).fetchone()
    if not bound or bound[0] != digest(bound[1]):
        raise ValueError('Missing collection or invalid encoder identity')
    batch_rows = db.execute('SELECT batch_id,row_count FROM literature.batches WHERE collection_id=%s LIMIT 257',
                            (collection,)).fetchall()
    if not batch_rows or len(batch_rows) > 256 or sum(r[1] for r in batch_rows) > MAX_PASSAGES:
        raise ValueError('Corpus inventory exceeds bounded slice')
    sources = db.execute('SELECT work_id,revision_id,source_sha256 FROM literature.sources WHERE collection_id=%s LIMIT 4097',
                         (collection,)).fetchall()
    rows = db.execute('SELECT passage_id,batch_id,work_id,record,text,embedding::text,vector_sha256 '
                      'FROM literature.passages WHERE collection_id=%s LIMIT 4097', (collection,)).fetchall()
    passages = [dict(passage_id=p, batch_id=b, work_id=w, record=r, text=t,
                     vector=json.loads(v), vector_sha256=h) for p,b,w,r,t,v,h in rows]
    return inventory(bound[1], dict(batch_rows), {w:(r,h) for w,r,h in sources}, passages)


def snapshot(db, collection):
    with db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        db.execute("SET LOCAL statement_timeout='30s'")
        return database_inventory(db, collection)
