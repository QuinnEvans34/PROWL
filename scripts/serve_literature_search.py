#!/usr/bin/env python3
"""Loopback development literature search and local cited summaries; no query storage."""
import argparse
import json
import logging
import math
from contextlib import contextmanager
from datetime import datetime, timezone
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
LOG = logging.getLogger('prowl.literature')


def report_failure(stage, error, backend_pid=None):
    """Retain correlation metadata, never exception text, SQL, or user content."""
    state = getattr(error, 'sqlstate', None)
    LOG.error(json.dumps(dict(event='literature_backend_failure',
        at=datetime.now(timezone.utc).isoformat(), stage=stage,
        error_type=type(error).__name__,
        sqlstate=state if isinstance(state, str) and len(state) == 5 and state.isalnum() else None,
        backend_pid=backend_pid)))


@contextmanager
def backend_stage(stage, db=None):
    backend_pid = getattr(getattr(db, 'info', None), 'backend_pid', None)
    try:
        yield
    except Exception as error:
        report_failure(stage, error, backend_pid)
        raise


def check_database(db, spec, inventory, *, vector_probe=False):
    with backend_stage('database_size', db):
        if db.execute('SELECT pg_database_size(current_database())').fetchone()[0] > 8*1024**3:
            raise OSError('Database size cap reached')
    with backend_stage('corpus_inventory', db):
        if database_inventory(db, spec['collection']) != inventory:
            raise ValueError('Corpus changed; restart after review')
    if vector_probe:
        with backend_stage('vector_probe', db):
            row = db.execute('SELECT embedding <=> embedding FROM literature.passages '
                'WHERE collection_id=%s ORDER BY passage_id LIMIT 1', (spec['collection'],)).fetchone()
            if row is None or not math.isfinite(row[0]) or abs(row[0]) > 1e-5:
                raise ValueError('Stored vector probe failed')


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

    @contextmanager
    def checked_connection():
        with backend_stage('configuration'):
            current = read_config(config_path); limits(current)
            if current != config:
                raise OSError('Configuration changed; restart required')
        with backend_stage('connect'):
            db = connect(config)
        with db:
            with db.transaction():
                with backend_stage('transaction', db):
                    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                    db.execute("SET LOCAL statement_timeout='30s'")
                yield db

    def check_backend():
        with checked_connection() as db:
            check_database(db, spec, manifest['inventory'], vector_probe=True)

    check_backend()

    def retrieve(question):
        with checked_connection() as db:
            check_database(db, spec, manifest['inventory'])
            with backend_stage('retrieval', db):
                return search(db, spec['collection'], model, question, spec['top_k'])

    service = DevelopmentSearch(corpus, spec, retrieve)
    service.check_backend = check_backend
    return service


def create_record_search(baseline):
    from src.retrieval.record_search import RecordSearchIndex, RecordAwareSearch, disease_scope
    from src.retrieval.evidence_experiment import corpus_records
    spec = json.loads((ROOT/'configs/evidence/development-search-v3-records.json').read_text())
    catalog = checked_json(spec['catalog'], ROOT)
    review = checked_json(spec['review'], ROOT)
    if catalog['manifest'] != spec['manifest']:
        raise ValueError('Catalog/corpus mismatch')
    index = RecordSearchIndex(catalog, review, corpus_records(ROOT, spec['manifest']))
    disease_baseline = DevelopmentSearch(baseline.corpus, baseline.config, baseline.retrieve, scope_policy=disease_scope)
    return RecordAwareSearch(disease_baseline, index, spec)


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
    from src.retrieval.volume_answer import VolumeAwareSearch, VolumeComposer, LiteratureSearch, LiteratureAnswers, volume_scope
    from src.retrieval.evidence_experiment import corpus_records
    spec = json.loads((ROOT/'configs/evidence/development-volume-search-v1.json').read_text())
    catalog, review = checked_json(spec['catalog'], ROOT), checked_json(spec['review'], ROOT)
    if catalog['manifest'] != spec['manifest']:
        raise ValueError('Volume catalog/corpus mismatch')
    index = VolumeRecordSearchIndex(catalog, review, corpus_records(ROOT, spec['manifest']))
    volume_baseline = DevelopmentSearch(baseline.corpus, baseline.config, baseline.retrieve, scope_policy=volume_scope)
    volume = VolumeAwareSearch(volume_baseline, index, spec)
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
            try:
                service.check_backend()
            except Exception as error:
                report_failure('readiness', error)
                return self.reply(503, {'backend':'unavailable', 'error':'Literature backend unavailable.'})
            self.reply(200, {'mode':'local_development_excerpts','backend':'checked',
                'generation_checked':False,'collection':service.config['collection'],
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
            except Exception as error:
                report_failure('answer' if self.path.endswith('/answer') else 'source_request', error)
                return self.reply(503, {'error':'Literature search unavailable. Check the service and drive, then retry.'})
            self.reply(200, result)
    return Handler


def create_measurement_answers(baseline, disease_search):
    from src.retrieval.measurement_interpretation import MeasurementIndex, MeasurementSearch, MeasurementComposer, measurement_scope
    from src.retrieval.evidence_experiment import corpus_records
    from src.retrieval.volume_answer import LiteratureSearch, LiteratureAnswers
    sources, answers = create_volume_answers(baseline, disease_search)
    spec = json.loads((ROOT/'configs/evidence/development-measurement-search-v1.json').read_text())
    catalog, review = checked_json(spec['catalog'], ROOT), checked_json(spec['review'], ROOT)
    if catalog['manifest'] != spec['manifest']:
        raise ValueError('Measurement catalog/corpus mismatch')
    index = MeasurementIndex(catalog, review, corpus_records(ROOT, spec['manifest']))
    base = DevelopmentSearch(baseline.corpus, baseline.config, baseline.retrieve, scope_policy=measurement_scope)
    measurement = MeasurementSearch(base, index, spec)
    config = json.loads((ROOT/'configs/evidence/measurement-answer-v1.json').read_text())
    composer = MeasurementComposer(index.engine, catalog, review, checked_json(config['wording'], ROOT), config)
    sources = LiteratureSearch(sources.disease, sources.volume, measurement)
    return sources, LiteratureAnswers(sources, answers.disease_composer, answers.volume_composer,
                                      measurement_composer=composer)


def create_study_answers(baseline):
    from src.retrieval.study_answer import StudyIndex, StudySearch, StudyComposer, study_scope
    from src.retrieval.evidence_experiment import corpus_records
    from src.retrieval.volume_answer import LiteratureSearch, LiteratureAnswers
    sources, answers = create_measurement_answers(baseline, create_record_search(baseline))
    spec = json.loads((ROOT/'configs/evidence/development-study-search-v4.json').read_text())
    catalog, review = checked_json(spec['catalog'], ROOT), checked_json(spec['review'], ROOT)
    if catalog['manifest'] != spec['manifest']:
        raise ValueError('Study catalog/corpus mismatch')
    index = StudyIndex(catalog, review, corpus_records(ROOT, spec['manifest']))
    base = DevelopmentSearch(baseline.corpus, baseline.config, baseline.retrieve, scope_policy=study_scope)
    study = StudySearch(base, index, spec)
    config = json.loads((ROOT/'configs/evidence/ct-study-answer-v4.json').read_text())
    composer = StudyComposer(index.engine, catalog, review, checked_json(config['wording'], ROOT), config)
    sources = LiteratureSearch(sources.disease, sources.volume, sources.measurement, study)
    return sources, LiteratureAnswers(sources, answers.disease_composer, answers.volume_composer,
        measurement_composer=answers.measurement_composer, study_composer=composer)


def create_evidence_answers(baseline, model='qwen3:8b', trace=False, thinking=False):
    from src.retrieval.evidence_answer import EvidenceAnswers, INSTRUCTION_MODEL
    from src.retrieval.natural_answer import api
    from functools import partial
    manifest = checked_json(baseline.config['manifest'], ROOT)
    bundles = [checked_json(s['bundle'], ROOT) for s in manifest['sources']]
    records = [i['record'] for pin in manifest['batches'] for i in checked_json(pin, ROOT)['items']]
    return EvidenceAnswers(baseline, bundles, records, model=model, trace=trace, thinking=thinking,
        transport=partial(api,port=11436 if model==INSTRUCTION_MODEL else 11435 if model=='qwen2.5:14b' else 11434))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default=str(ROOT/'infra/retrieval/.env.ingestion.json'))
    parser.add_argument('--port', type=int, default=8016)
    parser.add_argument('--record-search', action='store_true', help='Enable reviewed disease-record search for sources only')
    parser.add_argument('--record-answers', action='store_true', help='Enable reviewed-record local AI composition (includes record search)')
    parser.add_argument('--volume-answers', action='store_true', help='Enable reviewed MRI volume composition alongside disease answers')
    parser.add_argument('--measurement-answers', action='store_true', help='Include CT tumor measurement-method composition with volume and disease answers')
    parser.add_argument('--study-answers', action='store_true', help='Include CT visibility and named study limitations')
    parser.add_argument('--evidence-answers', action='store_true', help='Evidence-led general local answers (candidate)')
    parser.add_argument('--evidence-model', choices=['qwen3:8b','qwen3:30b','qwen2.5:14b','qwen3:30b-a3b-instruct-2507-q4_K_M'], default='qwen3:8b')
    parser.add_argument('--evidence-thinking', action='store_true', help='Reasoning in evidence selection and review (candidate only)')
    parser.add_argument('--evidence-trace', action='store_true', help='Include candidate drafts in local regression responses; never enable for the demo')
    args = parser.parse_args()
    service = create_service(args.config)
    sources = create_record_search(service) if args.record_search or args.record_answers or args.volume_answers or args.measurement_answers else None
    answers = create_record_answers(sources) if args.record_answers else None
    if args.volume_answers:
        sources, answers = create_volume_answers(service, sources)
    if args.measurement_answers:
        sources, answers = create_measurement_answers(service, create_record_search(service))
    if args.study_answers:
        sources, answers = create_study_answers(service)
    if args.evidence_answers:
        sources = answers = create_evidence_answers(service, args.evidence_model, args.evidence_trace, args.evidence_thinking)
    server = LocalFixtureServer(('127.0.0.1',args.port),handler_for(service, sources, answers))
    print(f'Development literature search ready on 127.0.0.1:{args.port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
