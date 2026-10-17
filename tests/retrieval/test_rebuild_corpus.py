"""Explicit opt-in real DB rebuild interruption; fixture text and vectors only."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/retrieval'))
import rebuild_corpus as cli
from src.retrieval import direct_ingestion as d
from tests.retrieval.test_direct_ingestion import bundle, batch, live_db


def test_rebuild_rejects_alias_destination_before_io(tmp_path):
    args = SimpleNamespace(reference='same', destination='same', batches=['missing'], bundles=['missing'])
    with pytest.raises(ValueError, match='Separate'): cli.rebuild(args)


def test_live_rebuild_resumes_committed_batch_and_preserves_failure(live_db, bundle, tmp_path, monkeypatch):
    import os
    b = batch(bundle)
    reference = 'test-rebuild-reference-' + uuid4().hex
    destination = 'test-rebuild-destination-' + uuid4().hex
    paths = []
    for n, item in enumerate(b['items']):
        part = d.frozen_batch([item['record']], [item['vector']], b['encoder'])
        d.load_batch(live_db, reference, part)
        path = tmp_path/f'{n}.json'; d.write_once(path, part); paths.append(str(path))
    canonical = tmp_path/'source.json'; d.write_once(canonical, bundle)
    args = SimpleNamespace(config=os.environ['PROWL_TEST_INGESTION_CONFIG'], batches=paths,
        bundles=[str(canonical)], reference=reference, destination=destination,
        output=str(tmp_path/'attempt01'), verify_guided_queries=False)
    original = cli.load_batch
    def interrupt(*a):
        original(*a)
        raise KeyboardInterrupt('Injected after first committed batch')
    monkeypatch.setattr(cli, 'load_batch', interrupt)
    with pytest.raises(KeyboardInterrupt): cli.rebuild(args)
    assert not (tmp_path/'attempt01'/'COMPLETE.json').exists()
    plan_bytes = (tmp_path/'attempt01'/'plan.json').read_bytes()
    assert live_db.execute('SELECT count(*) FROM literature.passages WHERE collection_id=%s', (destination,)).fetchone()[0] == 1
    monkeypatch.setattr(cli, 'load_batch', original)
    args.output = str(tmp_path/'attempt02')
    result = cli.rebuild(args)
    assert result['inventory']['passage_count'] == 2
    receipts = [json.loads(p.read_text()) for p in sorted((tmp_path/'attempt02').glob('batch-*.json'))]
    assert [r['already_published'] for r in receipts] == [True, False]
    assert (tmp_path/'attempt01'/'plan.json').read_bytes() == plan_bytes
    # Missing canonical member and corrupt batch fail without publishing completion.
    args.output = str(tmp_path/'missing'); args.batches = paths[:1]
    with pytest.raises(ValueError, match='Reference differs'): cli.rebuild(args)
    assert not (tmp_path/'missing'/'COMPLETE.json').exists()
    broken = json.loads(Path(paths[1]).read_text()); broken['items'][0]['vector_sha256'] = '0'*64
    Path(paths[1]).write_text(json.dumps(broken))
    args.output = str(tmp_path/'corrupt'); args.batches = paths
    with pytest.raises(ValueError, match='hash/content'): cli.rebuild(args)
    assert not (tmp_path/'corrupt').exists()
    assert live_db.execute('SELECT count(*) FROM literature.passages WHERE collection_id=%s', (destination,)).fetchone()[0] == 2
