#!/usr/bin/env python3
"""Opt-in local research workflow service; explicit requests only, no automatic inference."""
import argparse
import hashlib
from pathlib import Path
from serve_evidence_fixture import LocalFixtureServer, handler_for
from retrieval.direct_corpus import read_config, connect, encoder, limits
from src.retrieval.guided_retrieval import guided_search, CATALOG
from src.retrieval.direct_ingestion import digest
from src.retrieval.corpus_inventory import snapshot, database_inventory
from src.retrieval.research_workflow import ResearchWorkflow


def workflow_handler(store):
    base = handler_for(store, '/research-workflow/runs', 'research-workflow')
    class Handler(base):
        def do_GET(self):
            prefix = '/research-workflow/responses/'
            if not self.path.startswith(prefix):
                return super().do_GET()
            try:
                run = store.read(self.path[len(prefix):])
                if run['state'] != 'completed':
                    return self.reply(404, {'error': 'No completed response.'})
                self.reply(200, run['response'])
            except FileNotFoundError:
                self.reply(404, {'error': 'Response not found.'})
            except (ValueError, TypeError, KeyError, OSError):
                self.reply(503, {'error': 'Response could not be verified.'})
    return Handler


def create_store(config_path, output_dir):
    config = read_config(config_path)
    limits(config)
    with connect(config) as db:
        corpus = snapshot(db, 'research-v1')
    model = encoder(config)
    if corpus['encoder_id'] != model.id:
        raise ValueError('Corpus encoder differs from configured model')
    def admit():
        current = read_config(config_path)
        if current != config:
            raise ValueError('Restart service after configuration changes')
        limits(current)
    def retrieve(question):
        try:
            with connect(config) as db:
                with db.transaction():
                    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                    db.execute("SET LOCAL statement_timeout='30s'")
                    if database_inventory(db, 'research-v1') != corpus:
                        raise ValueError('Restart service after corpus changes')
                    return guided_search(db, 'research-v1', model, question, 5)
        except Exception as exc:
            raise OSError('Research retrieval unavailable') from exc
    root = Path(__file__).resolve().parents[1]
    identity = dict(snapshot_policy='reuse-original-retrieval', top_k=5,
        volume_uuid=config['volume_uuid'], encoder=model.descriptor, corpus=corpus,
        catalog_sha256=digest(CATALOG),
        producer_sha256={name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'src/retrieval/guided_retrieval.py', 'src/retrieval/query.py',
            'src/retrieval/corpus_inventory.py',
            'scripts/retrieval/direct_corpus.py', 'scripts/serve_research_workflow.py')})
    store = ResearchWorkflow(output_dir, retrieve, 'research-v1', model.id, identity, admit=admit)
    return store


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default='infra/retrieval/.env.ingestion.json')
    p.add_argument('--output-dir', type=Path, default=Path('outputs/prowl/research-workflow'))
    p.add_argument('--port', type=int, default=8015)
    args = p.parse_args()
    store = create_store(args.config, args.output_dir)
    server = LocalFixtureServer(('127.0.0.1', args.port), workflow_handler(store))
    print(f'Research workflow ready on 127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
