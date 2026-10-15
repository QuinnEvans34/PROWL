#!/usr/bin/env python3
"""Bounded development evaluation; frozen references never enter model inputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.retrieval.direct_ingestion import digest, write_once
from src.retrieval import grounded_answer as answers
from src.retrieval.guided_retrieval import guided_search


def run_case(case, retrieve, generate):
    start = time.monotonic()
    passages = retrieve(case['question'])
    retrieved = time.monotonic()
    generation = generate(case['question'], passages)
    return dict(case_id=case['id'], question=case['question'], passages=passages,
                generation=generation, retrieval_seconds=retrieved-start,
                answer_seconds=time.monotonic()-retrieved,
                total_seconds=time.monotonic()-start)


def checked_read(path):
    value = json.loads(Path(path).read_text())
    expected = value.pop('content_sha256')
    if digest(value) != expected:
        raise ValueError('Evaluation receipt hash mismatch')
    return value


def save(path, value):
    write_once(path, dict(value, content_sha256=digest(value)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=Path, default=ROOT/'configs/evidence/evaluation/development-v1.json')
    parser.add_argument('--config', default=str(ROOT/'infra/retrieval/.env.ingestion.json'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reuse-retrieval', type=Path,
                        help='Reuse a prior run with identical suite/corpus to isolate generation changes')
    args = parser.parse_args()
    suite = json.loads(args.suite.read_text())
    if suite['split'] != 'development' or not 1 <= len(suite['cases']) <= 20:
        raise ValueError('Only bounded development suites supported')
    if len({c['id'] for c in suite['cases']}) != len(suite['cases']):
        raise ValueError('Duplicate case ID')
    for case in suite['cases']:
        if not case['id'] or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in case['id']):
            raise ValueError('Invalid case ID')
    previous = checked_read(args.reuse_retrieval/'manifest.json') if args.reuse_retrieval else None
    if previous and previous['suite_sha256'] != digest(suite):
        raise ValueError('Cannot reuse retrieval across changed suites')
    # Refuse reuse of any run directory, including failed attempts.
    args.output.mkdir(parents=True, exist_ok=False)
    from direct_corpus import read_config, connect, encoder
    config = read_config(args.config)
    with connect(config) as db:
        records = [r[0] for r in db.execute(
            'SELECT record FROM literature.passages WHERE collection_id=%s ORDER BY passage_id',
            (suite['collection'],)).fetchall()]
    if len(records) != suite['corpus_passages'] or digest(records) != suite['corpus_record_sha256']:
        raise ValueError('Frozen corpus identity differs')
    model = None if previous else encoder(config)
    manifest = dict(suite_sha256=digest(suite), suite=suite,
                    started_at=datetime.now(timezone.utc).isoformat(),
                    corpus_record_sha256=digest(records),
                    encoder_id=previous['encoder_id'] if previous else model.id,
                    model=answers.MODEL, model_sha256=answers.MODEL_SHA,
                    policy=answers.POLICY, prompt_sha256=digest(answers.SYSTEM),
                    reused_manifest_sha256=digest(previous) if previous else None,
                    source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
                        'scripts/retrieval/evaluate_answers.py', 'src/retrieval/grounded_answer.py',
                        'src/retrieval/guided_retrieval.py', 'src/retrieval/direct_ingestion.py',
                        'configs/evidence/research-questions-v1.json')})
    save(args.output/'manifest.json', manifest)
    for case in suite['cases']:
        raw = []
        original_api = answers.api
        def recorded_api(path, payload=None):
            response = original_api(path, payload)
            if path == 'chat':
                raw.append(response)
            return response
        def retrieve(question):
            if previous:
                old = checked_read(args.reuse_retrieval/(case['id']+'.json'))
                if old['question'] != question or 'error' in old:
                    raise ValueError('Invalid retrieval reuse')
                return old['passages']
            read_config(args.config)
            with connect(config) as db:
                return guided_search(db, suite['collection'], model, question, 5)
        try:
            with patch.object(answers, 'api', recorded_api):
                result = run_case(case, retrieve, answers.generate_answer)
            result['retrieval_reused'] = bool(previous)
        except Exception as exc:
            result = dict(case_id=case['id'], question=case['question'], error=type(exc).__name__)
        result['raw_model_responses'] = raw
        result['suite_sha256'] = digest(suite)
        save(args.output/(case['id']+'.json'), result)
        print(json.dumps(dict(case_id=case['id'], error=result.get('error'),
            status=result.get('generation', {}).get('answer', {}).get('status'),
            seconds=result.get('total_seconds'))), flush=True)


if __name__ == '__main__':
    main()
