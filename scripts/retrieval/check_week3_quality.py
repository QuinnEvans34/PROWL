"""Fixed exposed HTTP quality batch, with retained model plans and separate dimensions."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
from threading import Thread
from time import monotonic
from urllib.request import Request, urlopen
from uuid import uuid4

from serve_literature_search import create_service, create_record_search, create_volume_answers, handler_for, LocalFixtureServer
from src.retrieval.natural_answer import api
from src.retrieval.evidence_experiment import corpus_records

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT/'configs/evidence/week3-quality-matrix-v1.json'


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    start = monotonic()
    receipt = dict(state='started', cases=[], chat_attempts=0, matrix_sha256=hashlib.sha256(MATRIX.read_bytes()).hexdigest(),
                   git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    trace = []
    server = worker = None
    active = None
    deadline = 0

    def write(name, value):
        data = (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode()
        if sum(p.stat().st_size for p in output.rglob('*') if p.is_file())+len(data) > 50*1024**2:
            raise ValueError('50 MiB output ceiling')
        (output/name).write_bytes(data)

    def call(path, payload=None):
        entry = dict(case_id=active, path=path, payload=payload)
        trace.append(entry)
        begin = monotonic()
        if path == 'chat':
            receipt['chat_attempts'] += 1
            if receipt['chat_attempts'] > 20:
                raise ValueError('20-call ceiling')
        try:
            entry['response'] = api(path, payload, deadline=deadline)
            return entry['response']
        except Exception as error:
            entry['error'] = type(error).__name__
            raise
        finally:
            entry['seconds'] = monotonic()-begin
            write('trace.json', trace)

    def expired(*_):
        raise TimeoutError('20-minute batch watchdog')

    previous = signal.signal(signal.SIGALRM, expired)
    signal.alarm(1200)
    try:
        # Snapshot the actual producers, including uncommitted candidate changes.
        names = subprocess.check_output(['git', 'ls-files', 'src/retrieval', 'configs/evidence',
            'scripts/serve_literature_search.py', 'scripts/retrieval/check_week3_quality.py'], cwd=ROOT, text=True).splitlines()
        receipt['pins'] = []
        for name in names:
            data = (ROOT/name).read_bytes()
            receipt['pins'].append(dict(path=name, sha256=hashlib.sha256(data).hexdigest()))
            target = output/'producing'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        receipt['resident_before'] = api('ps')
        base = create_service(ROOT/'infra/retrieval/.env.ingestion.json')
        sources, answers = create_volume_answers(base, create_record_search(base))
        canonical = {s['passage_id']: s['record'] for s in corpus_records(ROOT, sources.config['manifest']).values()}
        answers.call = call
        server = LocalFixtureServer(('127.0.0.1', 0), handler_for(base, sources, answers))
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        write('receipt.json', receipt)
        for case in json.loads(MATRIX.read_text())['cases']:
            active = case['id']
            request = dict(schema_version='prowl-expert-request-v1', request_id=str(uuid4()), question=case['question'])
            begin = monotonic()
            deadline = begin+30
            before = receipt['chat_attempts']
            with urlopen(Request(f'http://127.0.0.1:{server.server_port}/literature-search/answer',
                    data=json.dumps(request).encode(), headers={'Content-Type': 'application/json'}), timeout=40) as response:
                result = json.load(response)
            seconds = monotonic()-begin
            write(active+'.json', dict(request=request, response=result, seconds=seconds))
            matches = [m['record_id'] for m in result['record_selection']['matches']]
            answer = result.get('answer')
            calls = receipt['chat_attempts']-before
            checks = dict(selection=set(matches) == set(case['expected_records']),
                          canonical=all(e['record'] == canonical[e['record']['passage']['passage_id']] for e in result['evidence']),
                          request_binding=result['question'] == case['question'] and result['request_id'] == request['request_id'],
                          latency=seconds < 40)
            if case['kind'] == 'supported':
                checks.update(model_composition=result['generation'] == 'completed', one_call=calls == 1,
                              completeness=False, citations=False, reviewed_wording=False)
                if answer:
                    composer = answers.volume_composer if answer['policy'] == answers.volume_composer.policy else answers.disease_composer
                    records, evidence = composer.material(result)
                    plan = dict(paragraphs=[dict(record_id=c['record_id'], sentences=c['units']) for c in answer['claims']])
                    reconstructed = composer.assemble(plan, records, evidence)
                    checks.update(completeness=True, citations=all(c['citations'] == r['citations'] for c, r in zip(answer['claims'], reconstructed)),
                                  reviewed_wording=answer['claims'] == reconstructed)
            else:
                checks.update(no_answer=answer is None, no_model=calls == 0 and result['generation'] == 'not_called')
            category = None
            if not checks['selection']:
                category = 'refusal' if result['state'] == 'not_searched' and case['kind'] == 'supported' else 'routing'
            elif case['kind'] == 'supported' and not checks['model_composition']:
                category = 'composition'
            if not checks['canonical'] or (answer and not checks.get('citations', True)):
                category = 'missing_evidence'
            row = dict(id=active, kind=case['kind'], question=case['question'], records=matches, seconds=seconds,
                       generation=result['generation'], reason=result['record_selection']['reason'], checks=checks,
                       failure_category=category, passed=all(checks.values()))
            if answer: row['failure'] = answer['failure']
            receipt['cases'].append(row)
            write('receipt.json', receipt)
            print(active, result['generation'], category or 'ok', round(seconds, 2), flush=True)
        supported = [r for r in receipt['cases'] if r['kind'] == 'supported']
        boundaries = [r for r in receipt['cases'] if r['kind'] == 'boundary']
        receipt.update(state='completed', supported_passed=sum(r['passed'] for r in supported),
                       boundaries_passed=sum(r['passed'] for r in boundaries))
        receipt['automated_gate'] = receipt['supported_passed'] >= 18 and receipt['boundaries_passed'] == 10 and all(
            r['checks']['canonical'] and r['checks']['request_binding'] and r['checks']['latency']
            and r['checks'].get('citations', True) and r['checks'].get('reviewed_wording', True)
            for r in receipt['cases'] if r['kind'] == 'boundary' or r['records'])
        receipt['manual_review'] = 'pending'
    except Exception as error:
        receipt.update(state='failed', error=dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        if server: server.shutdown(); server.server_close()
        if worker: worker.join(3)
        receipt['seconds'] = monotonic()-start
        write('receipt.json', receipt)
        print(json.dumps({k: v for k, v in receipt.items() if k not in ('pins', 'cases', 'resident_before')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
