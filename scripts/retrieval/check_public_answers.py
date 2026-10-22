"""Bounded public development replay through a running UI/API. No hidden questions.

Saves actual responses and mechanical checks; semantic correctness remains a separate
manual decision. Expected answers/labels never leave this evaluator in HTTP requests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from time import monotonic
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def run(suite, output, port):
    if port not in (5180, 8016, 8019):
        raise ValueError('Only local production/candidate ports allowed')
    suite = suite.resolve()
    allowed = {ROOT/'configs/evidence/evaluation'/name for name in (
        'development-v6-draft.json', 'rag-interpretation-development-v1.json',
        'rag-contour-development-v1.json', 'rag-study-coverage-development-v1.json')}
    allowed.add(ROOT/'configs/evidence/week3-quality-matrix-v1.json')
    if suite not in allowed:
        raise ValueError('Only the named exposed development suites are allowed')
    data = json.loads(suite.read_text())
    cases = data['cases']
    if not 1 <= len(cases) <= 60 or any(c.get('split', 'development') != 'development' for c in cases):
        raise ValueError('Public development only, at most 60 requests')
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(suite=str(suite.relative_to(ROOT)), suite_sha256=hashlib.sha256(suite.read_bytes()).hexdigest(),
        git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        port=port, state='started', cases=[], semantic_review='pending')
    begin = monotonic()
    receipt['producing_files'] = []
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard',
        'src/retrieval', 'configs/evidence', 'scripts/serve_literature_search.py',
        'scripts/retrieval/check_public_answers.py', 'ui/src/components'], cwd=ROOT, text=True).splitlines()
    for name in names:
        content = (ROOT/name).read_bytes()
        target = output/'producing'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        receipt['producing_files'].append(dict(path=name, sha256=hashlib.sha256(content).hexdigest()))

    def write():
        (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')

    try:
        with urlopen(f'http://127.0.0.1:{port}/literature-search/health', timeout=40) as response:
            receipt['health'] = json.load(response)
        from src.retrieval.evidence_experiment import corpus_records
        spec = json.loads((ROOT/'configs/evidence/development-search-v1.json').read_text())
        canonical = {s['passage_id']: s['record'] for s in corpus_records(ROOT, spec['manifest']).values()}
        for index, case in enumerate(cases):
            if monotonic()-begin > 1200:
                raise TimeoutError('20-minute batch ceiling')
            request = dict(schema_version='prowl-expert-request-v1', request_id=str(uuid4()), question=case['question'])
            start = monotonic()
            # Only the public question and request identity go to the application.
            with urlopen(Request(f'http://127.0.0.1:{port}/literature-search/answer',
                    data=json.dumps(request).encode(), headers={'Content-Type': 'application/json'}), timeout=45) as response:
                result = json.load(response)
            elapsed = monotonic()-start
            evidence = result['evidence']; answer = result.get('answer')
            canonical_ok = all(e['record'] == canonical.get(e['record']['passage']['passage_id']) for e in evidence)
            citations_ok = all(any(c['rank'] == e['rank'] and c['quote'] == e['record']['text'] for e in evidence)
                for claim in (answer or {}).get('claims', []) for c in claim['citations'])
            row = dict(id=case['id'], question=case['question'], generation=result['generation'],
                records=[m['record_id'] for m in result['record_selection']['matches']],
                reason=result['record_selection']['reason'], seconds=elapsed,
                answer_available=bool(answer and answer.get('claims')),
                canonical=canonical_ok, citations=bool(answer) and citations_ok,
                request_binding=result['request_id'] == request['request_id'] and result['question'] == case['question'],
                expected=case.get('expected', case.get('kind')), semantic_review='pending')
            receipt['cases'].append(row)
            (output/f'{index+1:02d}.json').write_text(json.dumps(dict(request=request, response=result, seconds=elapsed), indent=2)+'\n')
            if not canonical_ok or not citations_ok or not row['request_binding']:
                raise ValueError('Source/request integrity failed; stopped batch')
            write()
            print(index+1, case['id'], result['generation'], row['records'], round(elapsed, 2), flush=True)
        receipt['state'] = 'completed'
    except Exception as error:
        receipt.update(state='failed', error_type=type(error).__name__)
        raise
    finally:
        receipt['seconds'] = monotonic()-begin
        write()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=5180)
    args = parser.parse_args()
    run(args.suite, args.output, args.port)
