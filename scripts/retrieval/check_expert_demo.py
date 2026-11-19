#!/usr/bin/env python3
"""Public demo rehearsal. Default: CPU context checks only, with no model calls.

Use --live explicitly to record HTTP responses from an already-running loopback
expert. Source candidates and review criteria are never sent to the application.
Neither routing checks nor a successful HTTP response establish answer accuracy.
"""
import argparse
import hashlib
from http.client import HTTPConnection
import json
from pathlib import Path
import sys
from time import monotonic
from urllib.parse import urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.retrieval.development_search import search_scope
from src.retrieval.expert_conversation import resolve_question

CHECKLIST = ROOT/'configs/evidence/evaluation/expert-demo-development-v1.json'
MAX_RESPONSE_BYTES = 1024 * 1024
REQUEST_SECONDS = 120


def load_checklist(path=CHECKLIST):
    raw = Path(path).read_bytes()
    spec = json.loads(raw)
    if (spec.get('version') != 'prowl-expert-demo-development-v1'
            or spec.get('exposed_development') is not True
            or spec.get('independent_evaluation') is not False
            or not isinstance(spec.get('cases'), list) or not 1 <= len(spec['cases']) <= 20):
        raise ValueError('Invalid exposed demo checklist')
    ids = [case['id'] for case in spec['cases']]
    if (len(set(ids)) != len(ids)
            or any(not isinstance(i, str) or not i.replace('_', '').isalnum() for i in ids)):
        raise ValueError('Invalid or duplicate demo case ID')
    return spec, hashlib.sha256(raw).hexdigest()


def local_url(base_url):
    parsed = urlsplit(base_url)
    if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost')
            or parsed.username or parsed.password or parsed.path not in ('', '/')
            or parsed.query or parsed.fragment):
        raise ValueError('Use an HTTP loopback base URL without a path or credentials')
    return parsed.hostname, parsed.port or 80


def post_question(base_url, payload):
    host, port = local_url(base_url)
    deadline = monotonic() + REQUEST_SECONDS
    connection = HTTPConnection(host, port, timeout=REQUEST_SECONDS)
    try:
        connection.connect()
        connection.request('POST', '/literature-search/answer', body=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'})
        connection.sock.settimeout(max(0.001, deadline-monotonic()))
        response = connection.getresponse()
        raw = bytearray()
        while True:
            remaining = deadline-monotonic()
            if remaining <= 0:
                raise TimeoutError('Demo request deadline')
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            chunk = response.read1(min(65536, MAX_RESPONSE_BYTES + 1-len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError('Demo response too large')
        return response.status, json.loads(raw)
    finally:
        connection.close()


def evaluate(spec, *, live=False, base_url='http://127.0.0.1:5180', transport=post_question):
    if live:
        local_url(base_url)
    results = []
    for case in spec['cases']:
        request = dict(schema_version='prowl-expert-request-v1', request_id=str(uuid4()),
            question=case['question'])
        context, reason = resolve_question(request, case['conversation'])
        effective = {**request, 'question': context['resolved_question']}
        reason = reason or search_scope(effective)
        checks_match = reason == case['expected_reason']
        if case.get('expect_unchanged_question'):
            checks_match &= context['resolved_question'] == request['question']
        result = dict(id=case['id'], question=request['question'], context=context,
            context_reason=reason, context_check='matched' if checks_match else 'mismatched',
            source_scope=case['source_scope'], manual_review='pending',
            answer_accuracy='not_assessed', transport='not_called')
        if live:
            started = monotonic()
            try:
                status, response = transport(base_url, dict(request=request,
                    conversation=case['conversation']))
                result.update(transport='completed', http_status=status, response=response)
            except Exception as error:
                result.update(transport='failed', error_type=type(error).__name__)
            result['elapsed_seconds'] = round(monotonic()-started, 3)
        results.append(result)
    return dict(version='prowl-expert-demo-rehearsal-v1',
        mode='live' if live else 'context_only', exposed_development=True,
        independent_evaluation=False, promoted=False, manual_review='pending', results=results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Explicitly call the already-running local expert')
    parser.add_argument('--url', default='http://127.0.0.1:5180', help='Loopback expert base URL')
    parser.add_argument('--output', type=Path, help='New directory for the checklist snapshot and results')
    parser.add_argument('--case', action='append', dest='case_ids', help='Run only the named case; repeat as needed')
    args = parser.parse_args()
    if args.live and args.output is None:
        parser.error('--live requires --output to preserve responses for source review')
    spec, checklist_sha = load_checklist()
    if args.case_ids:
        unknown = set(args.case_ids)-{c['id'] for c in spec['cases']}
        if unknown:
            parser.error('Unknown case ID')
        spec = {**spec, 'cases': [c for c in spec['cases'] if c['id'] in args.case_ids]}
    if args.output:
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output/'checklist.json').write_text(json.dumps(spec, indent=2)+'\n')
    result = evaluate(spec, live=args.live, base_url=args.url)
    result['checklist_sha256'] = checklist_sha
    if args.output:
        (args.output/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(mode=result['mode'], cases=len(result['results']),
        context_checks_matched=sum(r['context_check']=='matched' for r in result['results']),
        http_responses=sum(r.get('http_status')==200 for r in result['results']),
        manual_review='pending', answer_accuracy='not_assessed')))
    completed = all(r['context_check']=='matched' and (not args.live
        or r['transport']=='completed' and r.get('http_status')==200) for r in result['results'])
    return 0 if completed else 1


if __name__ == '__main__':
    raise SystemExit(main())
