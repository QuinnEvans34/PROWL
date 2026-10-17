#!/usr/bin/env python3
"""Loopback research retrieval API with durable response snapshots."""
import argparse
from pathlib import Path
from serve_evidence_fixture import LocalFixtureServer, handler_for
from retrieval.direct_corpus import read_config, connect, encoder
from src.retrieval.guided_retrieval import guided_search
from src.retrieval.guided_research import ResearchStore

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default='infra/retrieval/.env.ingestion.json')
    p.add_argument('--output-dir', type=Path)
    p.add_argument('--answers', action='store_true')
    p.add_argument('--port', type=int, default=None)
    args = p.parse_args()
    args.port = args.port or (8014 if args.answers else 8013)
    prefix = '/research-answers' if args.answers else '/research-evidence'
    args.output_dir = args.output_dir or Path('outputs/prowl' + prefix + '/responses')
    from src.retrieval.grounded_answer import generate_answer
    config = read_config(args.config)
    model = encoder(config)

    def retrieve(question):
        try:
            read_config(args.config)  # Check drive identity for every live search.
            with connect(config) as db:
                return guided_search(db, 'research-v1', model, question, 5)
        except Exception as exc:
            raise OSError('Research retrieval unavailable') from exc

    store = ResearchStore(args.output_dir, retrieve, 'research-v1', model.id, generate_answer if args.answers else None)
    server = LocalFixtureServer(('127.0.0.1', args.port), handler_for(store, prefix + '/responses', 'research-answers' if args.answers else 'research-retrieval'))
    print(f'Research retrieval ready on 127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
