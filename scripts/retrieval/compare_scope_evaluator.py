#!/usr/bin/env python3
"""One bounded generation/review run over frozen development inputs; no database or gold inputs."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import signal
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.retrieval.evaluate_answers import checked_read, save, run_case
from src.retrieval import scope_answer
from src.retrieval.direct_ingestion import digest


class BudgetExpired(BaseException):
    """Bypass broad model-error handlers so a timed-out run cannot continue."""


@contextmanager
def time_limit(seconds):
    """POSIX main-thread wall-clock alarm; nested limits preserve the outer deadline."""
    def expire(*_):
        raise BudgetExpired('Evaluation wall-clock limit reached')
    started = time.monotonic()
    previous_handler = signal.signal(signal.SIGALRM, expire)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0]:
            remaining = max(0.000001, previous_timer[0] - (time.monotonic() - started))
            signal.setitimer(signal.ITIMER_REAL, remaining, previous_timer[1])


def frozen_inputs(directory, suite):
    manifest = checked_read(directory/'manifest.json')
    if (manifest['suite_sha256'] != digest(suite) or manifest['suite'] != suite
            or manifest['policy'] != 'verified-spans-v1'
            or manifest['corpus_record_sha256'] != suite['corpus_record_sha256']):
        raise ValueError('Frozen selection manifest mismatch')
    receipts = {}
    for case in suite['cases']:
        old = checked_read(directory/(case['id']+'.json'))
        if ('error' in old or old['case_id'] != case['id'] or old['question'] != case['question']
                or old['suite_sha256'] != digest(suite)):
            raise ValueError('Frozen selection receipt mismatch')
        receipts[case['id']] = old
    return manifest, receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True,
                        help='Frozen structured-span baseline; spans policy reuses only its retrieval')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--evaluator', choices=scope_answer.EVALUATORS, required=True)
    parser.add_argument('--policy', choices=['scope', 'records', 'spans'], default='scope')
    parser.add_argument('--bundles', type=Path, help='Retained source bundle directory for records')
    args = parser.parse_args()
    selected = scope_answer
    bundles = {}
    if args.policy == 'spans':
        from src.retrieval import span_answer as selected
    if args.policy == 'records':
        from src.retrieval import study_evidence as selected
        if args.evaluator != selected.MODEL or not args.bundles:
            raise ValueError('Records require the pinned30B evaluator and retained bundles')
        for path in sorted(args.bundles.glob('rev-*.json')):
            bundle = json.loads(path.read_text())
            key = bundle['representation']['representation_id']
            if key in bundles:
                raise ValueError('Duplicate representation')
            bundles[key] = bundle
        if not bundles:
            raise ValueError('No retained source bundles')
    suite = json.loads((ROOT/'configs/evidence/evaluation/development-v1.json').read_text())
    previous, inputs = frozen_inputs(args.selection, suite)
    args.output.mkdir(parents=True, exist_ok=False)
    source_paths = ['scripts/retrieval/compare_scope_evaluator.py', 'scripts/retrieval/evaluate_answers.py',
                    'src/retrieval/scope_answer.py', 'src/retrieval/evidence_spans.py',
                    'src/retrieval/span_answer.py', 'src/retrieval/grounded_answer.py',
                    'src/retrieval/direct_ingestion.py',
                    'docs/capstone/retrieval/EVALUATOR-COMPARISON-2026-10-15.md']
    if args.policy == 'records':
        source_paths += ['src/retrieval/study_evidence.py', 'src/retrieval/passages.py',
                         'src/retrieval/records.py',
                         'docs/capstone/retrieval/STUDY-EVIDENCE-2026-10-15.md']
    if args.policy == 'spans':
        source_paths += ['docs/capstone/retrieval/DIRECT-SPAN-COMPARISON-2026-10-15.md']
    sources = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths}
    for p in source_paths:
        destination = args.output/'producing-sources'/p
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT/p).read_bytes())
    manifest = dict(suite=suite, suite_sha256=digest(suite), policy=selected.POLICY,
        started_at=datetime.now(timezone.utc).isoformat(), evaluator=args.evaluator,
        evaluator_sha256=scope_answer.EVALUATORS[args.evaluator], scope_reasoning=False,
        prompt_sha256=digest(selected.SYSTEM) if args.policy in ('scope', 'spans') else None, source_sha256=sources,
        record_prompt_sha256=digest(selected.RECORD_SYSTEM) if args.policy == 'records' else None,
        match_prompt_sha256=digest(selected.MATCH_SYSTEM) if args.policy == 'records' else None,
        source_bundle_sha256={k: digest(v) for k, v in bundles.items()},
        reused_selection_manifest_sha256=digest(previous) if args.policy != 'spans' else None,
        reused_retrieval_manifest_sha256=digest(previous),
        generation_mode=args.policy,
        corpus_record_sha256=suite['corpus_record_sha256'],
        input_receipt_sha256={k: digest(v) for k, v in inputs.items()},
        total_limit_seconds=600, call_limit_seconds=60, retries=0)
    save(args.output/'manifest.json', manifest)
    started = time.monotonic()
    completed, current, raw = [], None, []
    original_api = selected.api
    cache = {}
    def save_record(key, record):
        folder = args.output/'records'
        folder.mkdir(exist_ok=True)
        save(folder/(key+'.json'), record)
    def recorded_api(path, payload=None):
        remaining = 600 - (time.monotonic() - started)
        if remaining <= 0:
            raise BudgetExpired('Total budget exhausted')
        with time_limit(min(60, remaining)):
            response = original_api(path, payload)
        if path == 'chat':
            raw.append(response)
            save(args.output/f'{current}-call-{len(raw)}.json',
                 dict(request_sha256=digest(payload), request=payload, response=response))
        return response
    stop_reason = 'completed'
    try:
        with time_limit(600), patch.object(selected, 'api', recorded_api):
            for case in suite['cases']:
                current, raw = case['id'], []
                old = inputs[current]
                def generate(q, p):
                    if args.policy == 'spans':
                        return selected.generate_answer(q, p, model=args.evaluator)
                    if args.policy == 'records':
                        return selected.verify_answer(q, p, old['generation'], bundles, cache, save_record=save_record)
                    return selected.verify_answer(q, p, old['generation'], evaluator=args.evaluator)
                result = run_case(case, lambda _: old['passages'], generate)
                result.update(retrieval_reused=True, raw_model_responses=raw, suite_sha256=digest(suite))
                save(args.output/(current+'.json'), result)
                completed.append(current)
                print(json.dumps(dict(case_id=current, seconds=result['total_seconds'],
                      status=result['generation']['answer']['status'],
                      validation=result['generation']['validation'])), flush=True)
    except (BudgetExpired, KeyboardInterrupt, Exception) as exc:
        stop_reason = type(exc).__name__
        save(args.output/'interruption.json', dict(reason=stop_reason, case_id=current,
             completed=completed, raw_model_responses=raw, elapsed_seconds=time.monotonic()-started))
    save(args.output/'completion.json', dict(reason=stop_reason, completed=completed,
         unscored=[c['id'] for c in suite['cases'] if c['id'] not in completed],
         elapsed_seconds=time.monotonic()-started))
    print(json.dumps(dict(reason=stop_reason, completed=len(completed))), flush=True)
    return 0 if stop_reason == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
