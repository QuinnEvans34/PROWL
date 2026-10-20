#!/usr/bin/env python3
"""Loopback development literature search and local cited summaries; no query storage."""
import argparse
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from serve_evidence_fixture import LocalFixtureServer
from retrieval.direct_corpus import read_config, connect, encoder, limits
from src.retrieval.development_set import checked_json
from src.retrieval.corpus_inventory import database_inventory
from src.retrieval.direct_ingestion import search
from src.retrieval.literature_adapter import FrozenLiterature
from src.retrieval.development_search import DevelopmentSearch
from src.retrieval.natural_answer import NaturalAnswerService, POLICY
from src.retrieval.records import canonical_bytes

ROOT = Path(__file__).resolve().parents[1]


def create_service(config_path):
    config = read_config(config_path); limits(config)
    spec = json.loads((ROOT/'configs/evidence/development-search-v1.json').read_text())
    manifest = checked_json(spec['manifest'], ROOT)
    corpus = FrozenLiterature(batches=[checked_json(p, ROOT) for p in manifest['batches']],
        bundles=[checked_json(s['bundle'], ROOT) for s in manifest['sources']],
        inventory=manifest['inventory'], manifest_sha256=spec['manifest']['sha256'])
    model = encoder(config)
    if model.id != spec['encoder_id']:
        raise ValueError('Configured encoder differs from corpus')

    def check(db):
        if db.execute('SELECT pg_database_size(current_database())').fetchone()[0] > 8*1024**3:
            raise OSError('Database size cap reached')
        if database_inventory(db, spec['collection']) != manifest['inventory']:
            raise ValueError('Corpus changed; restart after review')

    with connect(config) as db:
        with db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            db.execute("SET LOCAL statement_timeout='30s'")
            check(db)

    def retrieve(question):
        current = read_config(config_path); limits(current)
        if current != config:
            raise OSError('Configuration changed; restart required')
        with connect(config) as db:
            with db.transaction():
                db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                db.execute("SET LOCAL statement_timeout='30s'")
                check(db)
                return search(db, spec['collection'], model, question, spec['top_k'])

    return DevelopmentSearch(corpus, spec, retrieve)


def create_record_search(baseline):
    from src.retrieval.record_search import RecordSearchIndex, RecordAwareSearch
    from src.retrieval.evidence_experiment import corpus_records
    spec = json.loads((ROOT/'configs/evidence/development-search-v3-records.json').read_text())
    catalog = checked_json(spec['catalog'], ROOT)
    review = checked_json(spec['review'], ROOT)
    if catalog['manifest'] != spec['manifest']:
        raise ValueError('Catalog/corpus mismatch')
    index = RecordSearchIndex(catalog, review, corpus_records(ROOT, spec['manifest']))
    return RecordAwareSearch(baseline, index, spec)


def create_record_answers(source_search):
    from src.retrieval.record_answer import RecordComposer, RecordAnswerService
    spec = json.loads((ROOT/'configs/evidence/record-answer-v1.json').read_text())
    wording = checked_json(spec['wording'], ROOT)
    search_spec = source_search.config
    composer = RecordComposer(source_search.index.engine, checked_json(search_spec['catalog'], ROOT),
        checked_json(search_spec['review'], ROOT), wording, spec)
    return RecordAnswerService(source_search, composer)


def create_volume_answers(baseline, disease_search):
    from src.retrieval.volume_record_search import VolumeRecordSearchIndex
    from src.retrieval.volume_answer import VolumeAwareSearch, VolumeComposer, LiteratureSearch, LiteratureAnswers
    from src.retrieval.evidence_experiment import corpus_records
    spec = json.loads((ROOT/'configs/evidence/development-volume-search-v1.json').read_text())
    catalog, review = checked_json(spec['catalog'], ROOT), checked_json(spec['review'], ROOT)
    if catalog['manifest'] != spec['manifest']:
        raise ValueError('Volume catalog/corpus mismatch')
    index = VolumeRecordSearchIndex(catalog, review, corpus_records(ROOT, spec['manifest']))
    volume = VolumeAwareSearch(baseline, index, spec)
    config = json.loads((ROOT/'configs/evidence/volume-answer-v1.json').read_text())
    composer = VolumeComposer(index.engine, catalog, review, checked_json(config['wording'], ROOT), config)
    sources = LiteratureSearch(disease_search, volume)
    return sources, LiteratureAnswers(sources, create_record_answers(disease_search).composer, composer)


def handler_for(service, source_search=None, record_answers=None):
    source_search = source_search or service
    answers = record_answers or NaturalAnswerService(service)
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup(); self.connection.settimeout(10)

        def log_message(self, *_):
            pass

        def reply(self, status, payload):
            body = canonical_bytes(payload)
            self.send_response(status)
            for key, value in [('Content-Type','application/json'), ('Content-Length',str(len(body))),
                               ('Cache-Control','no-store'), ('X-Content-Type-Options','nosniff')]:
                self.send_header(key,value)
            self.end_headers()
            try: self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError): pass

        def local(self):
            hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}',
                     '127.0.0.1:5180', 'localhost:5180'}
            origin = self.headers.get('Origin')
            return (self.headers.get('Host') in hosts
                    and (origin is None or origin in {'http://127.0.0.1:5180','http://localhost:5180'})
                    and self.headers.get('Sec-Fetch-Site') != 'cross-site')

        def do_GET(self):
            if not self.local(): return self.reply(403, {'error':'Local access required.'})
            if self.path != '/literature-search/health': return self.reply(404, {'error':'Unknown route.'})
            self.reply(200, {'mode':'local_development_excerpts','collection':service.config['collection'],
                'answer_policy':getattr(record_answers, 'policy', 'source-record-answer-v1') if record_answers else POLICY,
                'retrieval_policy':source_search.config.get('retriever', 'dense-exact-cosine-v1'),
                'answer_retrieval_policy':(source_search if record_answers else service).config.get('retriever', 'dense-exact-cosine-v1')})

        def do_POST(self):
            if not self.local(): return self.reply(403, {'error':'Local access required.'})
            if self.path not in {'/literature-search/query', '/literature-search/answer'}:
                return self.reply(404, {'error':'Unknown route.'})
            try:
                size = int(self.headers.get('Content-Length','0'))
                if (not 0 < size <= 4096 or self.headers.get('Content-Type') != 'application/json'
                        or self.headers.get('Transfer-Encoding')):
                    raise ValueError('Invalid body')
                request = json.loads(self.rfile.read(size))
                # Validate user input before provider work, without echoing invalid content.
                from src.retrieval.development_search import search_scope
                search_scope(request)
            except (ValueError, TypeError, KeyError, UnicodeError, OSError):
                return self.reply(400, {'error':'Use a general literature question of 1–500 characters.'})
            try:
                result = answers.answer(request) if self.path.endswith('/answer') else source_search.search(request)
            except Exception:
                return self.reply(503, {'error':'Literature search unavailable. Check the service and drive, then retry.'})
            self.reply(200, result)
    return Handler


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default=str(ROOT/'infra/retrieval/.env.ingestion.json'))
    parser.add_argument('--port', type=int, default=8016)
    parser.add_argument('--record-search', action='store_true', help='Enable reviewed disease-record search for sources only')
    parser.add_argument('--record-answers', action='store_true', help='Enable reviewed-record local AI composition (includes record search)')
    parser.add_argument('--volume-answers', action='store_true', help='Enable reviewed MRI volume composition alongside disease answers')
    args = parser.parse_args()
    service = create_service(args.config)
    sources = create_record_search(service) if args.record_search or args.record_answers or args.volume_answers else None
    answers = create_record_answers(sources) if args.record_answers else None
    if args.volume_answers:
        sources, answers = create_volume_answers(service, sources)
    server = LocalFixtureServer(('127.0.0.1',args.port),handler_for(service, sources, answers))
    print(f'Development literature search ready on 127.0.0.1:{args.port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
