#!/usr/bin/env python3
"""Rebuild a separate bounded collection from explicit canonical files; no generation.

Interrupted loads can be rerun with the same inputs/destination and a new receipt
directory. Each batch verifies existing bytes or commits atomically. No deletions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from direct_corpus import read_config, connect, limits, encoder
from src.retrieval.direct_ingestion import load_batch, write_once
from src.retrieval.corpus_inventory import frozen_inventory, verify_sources, snapshot
from src.retrieval.guided_retrieval import guided_search, CATALOG


def read_inputs(paths, maximum_bytes):
    records, pins = [], []
    total = 0
    for path in paths:
        path = Path(path).resolve(strict=True)
        size = path.stat().st_size
        total += size
        if size > maximum_bytes or total > 64 * 1024**2:
            raise ValueError('Canonical file exceeds size bound')
        data = path.read_bytes()
        records.append(json.loads(data))
        pins.append(dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
    return records, pins


def rebuild(args):
    start = time.monotonic()
    if args.reference == args.destination or not 1 <= len(args.batches) <= 256 or not 1 <= len(args.bundles) <= 256:
        raise ValueError('Separate destination and bounded explicit inputs required')
    c = read_config(args.config); limits(c)
    batches, batch_pins = read_inputs(args.batches, 8 * 1024**2)
    bundles, bundle_pins = read_inputs(args.bundles, 32 * 1024**2)
    expected = frozen_inventory(batches)
    verify_sources(batches, bundles)
    root = Path(args.output); root.mkdir(parents=True, exist_ok=False)
    write_once(root / 'plan.json', dict(reference=args.reference, destination=args.destination,
        inventory=expected, batches=batch_pins, bundles=bundle_pins, max_seconds=300,
        verify_guided_queries=args.verify_guided_queries))
    def admit(db):
        limits(c)
        if time.monotonic() - start > 300:
            raise TimeoutError('Rebuild time budget reached')
        if db.execute('SELECT pg_database_size(current_database())').fetchone()[0] > 8 * 1024**3:
            raise OSError('Database size cap reached')
    with connect(c) as db:
        if snapshot(db, args.reference) != expected:
            raise ValueError('Reference differs from complete canonical inventory')
        for n, batch in enumerate(batches):
            admit(db)
            write_once(root / f'batch-{n:04d}.json', load_batch(db, args.destination, batch))
        if snapshot(db, args.destination) != expected or snapshot(db, args.reference) != expected:
            raise ValueError('Rebuilt/reference inventory differs')
        comparisons = []
        if args.verify_guided_queries:
            admit(db)
            model = encoder(c)
            if model.id != expected['encoder_id']:
                raise ValueError('Pinned query encoder differs')
            # Encode each unique facet once; identical vectors drive both collection queries.
            class CachedEncoder:
                id = model.id
                def __init__(self): self.cache = {}
                def encode(self, texts):
                    for text in texts:
                        if text not in self.cache: self.cache[text] = model.encode([text])[0]
                    return [self.cache[text] for text in texts]
            cached = CachedEncoder()
            with db.transaction():
                db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                from src.retrieval.corpus_inventory import database_inventory
                if (database_inventory(db, args.reference) != expected
                        or database_inventory(db, args.destination) != expected):
                    raise ValueError('Corpus changed before query verification')
                for q in CATALOG:
                    admit(db)
                    a = guided_search(db, args.reference, cached, q['label'])
                    b = guided_search(db, args.destination, cached, q['label'])
                    if a != b: raise ValueError('Rebuild query parity failed')
                    comparisons.append(dict(question_id=q['id'], exact=True,
                        passage_ids=[p['record']['passage']['passage_id'] for p in a]))
        # Completion is last, after parity. The reference collection is never written.
        report = dict(state='verified', inventory=expected, queries=comparisons,
                      seconds=time.monotonic()-start, generation_calls=0)
        write_once(root / 'COMPLETE.json', report)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default='infra/retrieval/.env.ingestion.json')
    p.add_argument('--batches', nargs='+', required=True)
    p.add_argument('--bundles', nargs='+', required=True)
    p.add_argument('--reference', default='research-v1')
    p.add_argument('--destination', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--verify-guided-queries', action='store_true')
    print(json.dumps(rebuild(p.parse_args()), indent=2))
