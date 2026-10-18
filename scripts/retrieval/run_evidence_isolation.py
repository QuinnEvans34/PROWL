#!/usr/bin/env python3
"""Prepare once, then run one fixed three-by-three diagnostic; never deploy answers."""
import argparse
import hashlib
import json
from pathlib import Path
from time import monotonic
from urllib.request import Request, urlopen
from uuid import uuid4

from jsonschema import validate
from src.retrieval.evidence_experiment import corpus_records, curated_sources, body, review_body, WRITE
from src.retrieval.conservative_answer import draft_schema
from src.retrieval.answer_feedback import collect_claim_feedback
from src.retrieval.separate_review_answer import SUPPORT, support_schema
from src.retrieval.natural_answer import api

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'outputs/prowl/evidence-isolation-v1-20261018'
CONFIG = ROOT/'configs/evidence/evidence-isolation-v1.json'


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def pin(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def prepare():
    config = json.loads(CONFIG.read_text())
    records = corpus_records(ROOT, config['manifest'])
    by_id = {s['passage_id']: s for s in records.values()}
    questions = {c['id']: c['question'] for c in json.loads((ROOT/config['question_plan']).read_text())['cases']}
    OUT.mkdir(parents=True, exist_ok=False)
    prepared = dict(state='preparing', cases=[], search_calls=0)
    write(OUT/'preparation.json', prepared)
    with urlopen('http://127.0.0.1:8016/literature-search/health', timeout=5) as response:
        prepared['live_health'] = json.load(response)
    if prepared['live_health']['answer_policy'] != 'natural-literature-answer-v6.1':
        raise ValueError('Unexpected live selection')
    for recipe in config['cases']:
        cid = recipe['id']; question = questions[cid]
        request = dict(schema_version='prowl-expert-request-v1', request_id=str(uuid4()), question=question)
        start = monotonic(); prepared['search_calls'] += 1
        write(OUT/'preparation.json', prepared)
        with urlopen(Request('http://127.0.0.1:8016/literature-search/query', data=json.dumps(request).encode(),
                            headers={'Content-Type': 'application/json'}), timeout=30) as response:
            result = json.load(response)
        write(OUT/(cid+'-live-search.json'), dict(request=request, response=result, seconds=monotonic()-start))
        retrieved = []
        for hit in result['evidence']:
            source = by_id[hit['record']['passage']['passage_id']]
            if source['record'] != hit['record']:
                raise ValueError('Live result differs from canonical corpus')
            retrieved.append(source)
        curated = curated_sources(recipe, records)
        arms = dict(retrieved_flat=body(question, retrieved), curated_flat=body(question, curated),
                    curated_linked=body(question, curated, recipe['evidence_links']))
        assert arms['curated_flat']['sources'] == arms['curated_linked']['sources']
        for arm, value in arms.items(): write(OUT/(cid+'-'+arm+'-input.json'), value)
        prepared['cases'].append(dict(id=cid, question=question, retrieved_sources=len(retrieved),
            curated_sources=len(curated), curated_passages_in_top5=len(set(s['source'] for s in retrieved)&set(s['source'] for s in curated))))
        write(OUT/'preparation.json', prepared)
    prepared['state'] = 'prepared'
    prepared['input_pins'] = [pin(p) for p in sorted(OUT.glob('*-input.json'))]
    write(OUT/'preparation.json', prepared)
    print(json.dumps(prepared, indent=2), flush=True)


def run():
    config = json.loads(CONFIG.read_text())
    prepared = json.loads((OUT/'preparation.json').read_text())
    if prepared['state'] != 'prepared': raise ValueError('Preparation incomplete')
    if hashlib.sha256(WRITE.encode()).hexdigest() != config['prompt_sha256']: raise ValueError('Prompt drift')
    for item in prepared['input_pins']:
        if pin(ROOT/item['path']) != item: raise ValueError('Prepared evidence drift')
    # Exclusive run marker prevents replay over prior results, including failed attempts.
    with (OUT/'run-started.json').open('x') as f: json.dump(dict(state='started'), f)
    paths = [CONFIG, ROOT/config['manifest']['path'], ROOT/config['question_plan'], OUT/'preparation.json',
        ROOT/'docs/capstone/retrieval/EVIDENCE-ISOLATION-PLAN-2026-10-18.md',
        ROOT/'scripts/retrieval/run_evidence_isolation.py', ROOT/'scripts/retrieval/supervise_evidence_isolation.py']
    paths += [ROOT/'src/retrieval'/name for name in ['evidence_experiment.py', 'conservative_answer.py',
        'natural_answer.py', 'answer_feedback.py', 'separate_review_answer.py', 'development_set.py']]
    receipt = dict(state='started', pins=[pin(p) for p in paths], outcomes=[], calls=[])
    for path in paths:
        if path.is_relative_to(OUT): continue
        target = OUT/'producing'/path.relative_to(ROOT); target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    write(OUT/'receipt.json', receipt)
    started = monotonic(); count = 0

    def transport(stage, path, payload, seconds):
        nonlocal count
        if path == 'chat':
            count += 1
            if count > config['budget']['chat_calls']: raise ValueError('Chat budget')
        entry = dict(stage=stage, path=path, payload=payload)
        receipt['calls'].append(entry); write(OUT/'receipt.json', receipt)
        begin = monotonic()
        try:
            entry['response'] = api(path, payload, port=11435, deadline=begin+seconds)
            return entry['response']
        except Exception as error:
            entry['error'] = dict(type=type(error).__name__, message=str(error))
            raise
        finally:
            entry['seconds'] = monotonic()-begin; write(OUT/'receipt.json', receipt)

    def ask(stage, prompt, value, schema):
        payload = dict(model=config['model'], stream=False, keep_alive='20m', options=config['options'],
            format=schema, messages=[dict(role='system', content=prompt),
            dict(role='user', content=json.dumps(value, ensure_ascii=False))])
        response = transport(stage, 'chat', payload, config['budget']['call_seconds'])
        if response.get('model') != config['model'] or response.get('done') is not True or response.get('done_reason') != 'stop':
            raise ValueError('Incomplete or foreign response')
        raw = json.loads(response['message']['content']); validate(raw, schema)
        return raw

    try:
        tags = api('tags', port=11435)
        if not any(m['name']==config['model'] and m['digest']==config['model_sha256'] for m in tags['models']):
            raise ValueError('Pinned model unavailable')
        receipt['resident_before'] = api('ps', port=11435)
        response = transport('cold_readiness', 'generate', dict(model=config['model'], prompt='',
            keep_alive='20m', options=config['options']), config['budget']['readiness_seconds'])
        if response.get('done') is not True or response.get('model') != config['model']: raise ValueError('Readiness failed')
        receipt['resident_after'] = api('ps', port=11435)
        if not any(m['name']==config['model'] and m['digest']==config['model_sha256'] and m['context_length']==16384
                   for m in receipt['resident_after']['models']): raise ValueError('Readiness identity/context failed')
        for index, case in enumerate(config['cases']):
            for arm in config['order'][index]:
                if monotonic()-started > config['budget']['batch_seconds']: raise TimeoutError('Batch deadline')
                if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) > config['budget']['output_bytes']:
                    raise ValueError('Output budget')
                cid = case['id']; value = json.loads((OUT/(cid+'-'+arm+'-input.json')).read_text())
                outcome = dict(id=cid, arm=arm, state='started'); receipt['outcomes'].append(outcome)
                begin = monotonic()
                try:
                    raw = ask(cid+'/'+arm+'/draft', WRITE, value, draft_schema(value['sources']))
                    outcome['draft'] = raw; outcome['draft_seconds'] = monotonic()-begin
                    write(OUT/'receipt.json', receipt)  # Preserve before checks; no validator can hide the draft.
                    _, issues = collect_claim_feedback(raw, value['sources'], value['question'])
                    outcome['mechanical_issues'] = issues
                    outcome['review_input'] = review_body(value['question'], raw, value['sources'])
                    if raw['claims']:
                        outcome['support_review'] = ask(cid+'/'+arm+'/support', SUPPORT,
                            outcome['review_input'], support_schema(len(raw['claims'])))
                        if [c['claim'] for c in outcome['support_review']['checks']] != list(range(1,len(raw['claims'])+1)):
                            raise ValueError('Review identity mismatch')
                    else: outcome['support_review'] = None
                    outcome['state'] = 'observed'
                except Exception as error:
                    outcome.update(state='failed', error=dict(type=type(error).__name__, message=str(error)))
                    # Abort on transport failure: never overlap a possibly still-running provider request.
                    if isinstance(error, (TimeoutError, OSError)): raise
                finally:
                    outcome['seconds'] = monotonic()-begin
                    write(OUT/(cid+'-'+arm+'-outcome.json'), outcome)
                    write(OUT/'receipt.json', receipt)
                    print(json.dumps({k: outcome[k] for k in ('id','arm','state','seconds')}), flush=True)
        receipt['state'] = 'completed'
    except Exception as error:
        receipt.update(state='failed', error=dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        try:
            response = transport('cleanup', 'generate', dict(model=config['model'], keep_alive=0), 10)
            receipt['cleanup_ok'] = response.get('done') is True and response.get('model') == config['model']
        except Exception as error:
            receipt['cleanup_ok'] = False
        receipt['seconds'] = monotonic()-started; write(OUT/'receipt.json', receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['prepare','run'])
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else run()
