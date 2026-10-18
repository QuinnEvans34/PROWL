#!/usr/bin/env python3
"""Fixed R6 development experiment. No protected-input argument or live promotion."""
import json
import statistics
import time
from pathlib import Path

from retrieval.compare_development_rankings import score, pin, write
from retrieval.direct_corpus import read_config, connect, limits
from src.retrieval.corpus_inventory import database_inventory
from src.retrieval.thinking_section_search import SectionSearch
from src.retrieval.development_set import checked_json
from src.retrieval.literature_adapter import FrozenLiterature

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = ROOT/'outputs/prowl/section-search-r6-20261017'
    out.mkdir(exist_ok=False, parents=True)
    paths = ['docs/capstone/retrieval/RETRIEVAL-R6-PLAN-2026-10-17.md',
             'src/retrieval/thinking_section_search.py','scripts/retrieval/compare_thinking_section_search.py',
             'scripts/retrieval/compare_development_rankings.py',
             'configs/evidence/reranker-minilm-v1.json',
             'configs/evidence/development-retrieval-comparison-checkpoint-v1.json']
    receipt = dict(state='started', scope='exposed_development', pins=[pin(p) for p in paths],
                   rankings=[], metrics=[], answer_model_calls=0)
    write(out/'receipt.json', receipt)
    start = time.monotonic()
    try:
        baseline = json.loads((ROOT/paths[-1]).read_text())
        pinned = {p['path']:p for p in baseline['pins']}
        manifest = checked_json(pinned['configs/evidence/corpus-disease-v1.json'], ROOT)
        suite = checked_json(pinned['configs/evidence/evaluation/development-v6-draft.json'], ROOT)
        previous = checked_json(pinned['outputs/prowl/retrieval-comparison-v1-attempt2-20261017/receipt.json'], ROOT)
        if previous['state'] != 'completed' or previous['validation']['state'] != 'draft_mechanically_valid':
            raise ValueError('Missing validated baseline')
        batches = [checked_json(p, ROOT) for p in manifest['batches']]
        bundles = [checked_json(s['bundle'], ROOT) for s in manifest['sources']]
        FrozenLiterature(batches=batches, bundles=bundles, inventory=manifest['inventory'],
            manifest_sha256=pinned['configs/evidence/corpus-disease-v1.json']['sha256'])
        records = sorted([i['record'] for b in batches for i in b['items']], key=lambda r:r['passage']['passage_id'])
        config = read_config(ROOT/'infra/retrieval/.env.ingestion.json'); limits(config)
        with connect(config) as db:
            with db.transaction():
                db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                db.execute("SET LOCAL statement_timeout='30s'")
                if database_inventory(db, 'research-disease-v1') != manifest['inventory']:
                    raise ValueError('DB differs from immutable corpus')
        receipt['inventory_verified'] = True
        model = SectionSearch(bundles,records)
        cases = [c for c in suite['cases'] if c['expected']['status']=='answered']
        for case in cases:
            limits(config)
            if time.monotonic()-start > 1800:
                raise TimeoutError('Experiment deadline')
            begin = time.monotonic()
            trace=[]
            from src.retrieval.natural_answer import api
            deadline=time.monotonic()+60
            def call(path,payload=None):
                response=api(path,payload,deadline=deadline)
                trace.append(dict(path=path,payload=payload,response=response))
                write(out/(case['id'].replace(':','-')+'-trace.json'),trace)
                return response
            selected=model.search(case['question'],call)
            hits=selected['hits']
            receipt['rankings'].append(dict(id=case['id'], question=case['question'],
                selection=selected["selection"],characters=selected["characters"], seconds=time.monotonic()-begin, hits=[dict(passage_id=h['record']['passage']['passage_id'],
                score=h['score']) for h in hits]))
            write(out/'receipt.json',receipt)
            print(case['id'], round(receipt['rankings'][-1]['seconds'],3), flush=True)
        by_id = {r['passage']['passage_id']:r for r in records}
        for entry, case in zip(receipt['rankings'], cases):
            receipt['metrics'].append(dict(id=case['id'], values=score(entry['hits'],case,by_id,
                                              [b['representation'] for b in bundles])))
        receipt['means'] = {key:statistics.mean(row['values'][key] for row in receipt['metrics'])
                            for key in receipt['metrics'][0]['values']}
        receipt['questions_with_direct_top5'] = sum(r['values']['top5_direct_hits']>0 for r in receipt['metrics'])
        receipt['median_seconds'] = statistics.median(r['seconds'] for r in receipt['rankings'])
        receipt['max_seconds'] = max(r['seconds'] for r in receipt['rankings'])
        dense = previous['means']['dense']
        receipt['checks'] = dict(old_top5_coverage=receipt['questions_with_direct_top5']>=16,
            passage_recall=receipt['means']['passage_recall_at_5']>dense['passage_recall_at_5'],
            source_mrr=receipt['means']['source_mrr']>=dense['source_mrr'],
            disease_hits=all(r['values']['top5_direct_hits']>0 for r in receipt['metrics'] if r['id'] in ('q:dev6-31','q:dev6-32')),
            latency=receipt['median_seconds']<=10 and receipt['max_seconds']<=30)
        from src.retrieval.labels import contains
        coverage=[]
        for entry,case in zip(receipt['rankings'],cases):
            passages=[by_id[h['passage_id']]['passage'] for h in entry['hits']]
            spans=[s for s in case['labels']['spans'] if s['grade']=='direct']
            hit=[s for s in spans if any(contains(p,s) for p in passages)]
            concepts=set(c for s in hit for c in s['concept_ids'])
            required=set(case['labels']['required_concepts'])
            coverage.append(dict(id=case['id'],any_direct=bool(hit),full_concepts=required<=concepts,
                concept_coverage=len(concepts)/len(required),span_coverage=len(hit)/len(spans),passages=len(passages)))
        receipt['package_coverage']=coverage
        receipt['package_checks']=dict(direct_questions=sum(c['any_direct'] for c in coverage)>=18,
            full_concept_questions=sum(c['full_concepts'] for c in coverage)>=16,
            disease_concepts=all(c['full_concepts'] for c in coverage if c['id'] in ('q:dev6-31','q:dev6-32')),
            latency=receipt['median_seconds']<=30 and receipt['max_seconds']<=60)
        receipt['comparative_evidence_review'] = 'pending_source_reading'
        receipt['state'] = 'completed'
    except Exception as exc:
        receipt.update(state='failed',failure_type=type(exc).__name__)
        raise
    finally:
        receipt['seconds'] = time.monotonic()-start
        write(out/'receipt.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k in ('means','checks','questions_with_direct_top5','median_seconds','max_seconds','package_coverage','package_checks')},indent=2))


if __name__ == '__main__':
    main()
