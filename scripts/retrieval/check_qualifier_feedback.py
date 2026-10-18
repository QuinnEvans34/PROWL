#!/usr/bin/env python3
"""Fixed ten-case source-bound answer checkpoint. No live policy change or retries."""
import json
from pathlib import Path
from time import monotonic
from uuid import uuid4
from retrieval.compare_development_rankings import pin,write
from src.retrieval.qualified_answer import generate_qualified
from src.retrieval.development_set import checked_json
from src.retrieval.literature_adapter import FrozenLiterature
from src.retrieval.development_search import DevelopmentSearch
from src.retrieval.natural_answer import NaturalAnswerService,generate,api

ROOT=Path(__file__).resolve().parents[2]


def main():
    out=ROOT/'outputs/prowl/section-answers-v18-20261018'
    out.mkdir(exist_ok=False,parents=True)
    paths=['docs/capstone/retrieval/QUALIFIER-FEEDBACK-REPAIR-V18-2026-10-18.md',
        'scripts/retrieval/check_qualifier_feedback.py','scripts/retrieval/supervise_qualifier_feedback.py',
        'outputs/prowl/instruction-model-v15-20261017/pull-receipt.json',
        'outputs/prowl/instruction-model-v15-20261017/verification-receipt.json',
        'outputs/prowl/instruction-model-v15-20261017/registry-manifest.json','src/retrieval/natural_answer.py','src/retrieval/isolated_answer.py','src/retrieval/single_source_answer.py','src/retrieval/qualified_answer.py',
        'src/retrieval/source_context.py',
        'src/retrieval/development_search.py','configs/evidence/development-search-v2-candidate.json',
        'configs/evidence/natural-answer-v18-candidate.json','configs/evidence/evaluation/answer-quality-plan-v1.json',
        'outputs/prowl/section-answers-v9-20261017/receipt.json']
    receipt=dict(state='started',pins=[pin(p) for p in paths],outcomes=[])
    write(out/'receipt.json',receipt)
    spec=json.loads((ROOT/'configs/evidence/development-search-v2-candidate.json').read_text())
    manifest=checked_json(spec['manifest'],ROOT)
    batches=[checked_json(p,ROOT) for p in manifest['batches']]
    bundles=[checked_json(s['bundle'],ROOT) for s in manifest['sources']]
    corpus=FrozenLiterature(batches=batches,bundles=bundles,inventory=manifest['inventory'],manifest_sha256=spec['manifest']['sha256'])
    records=[i['record'] for b in batches for i in b['items']];by_id={r['passage']['passage_id']:r for r in records}
    cases=json.loads((ROOT/'configs/evidence/evaluation/answer-quality-plan-v1.json').read_text())['cases']
    cases=[c for c in cases if c['id'] in ('quality-03',)]
    saved={}
    for case in cases:
        path=ROOT/'outputs/prowl/section-answers-v9-20261017'/(case['id']+'.json')
        receipt['pins'].append(pin(str(path.relative_to(ROOT))))
        old=json.loads(path.read_text())
        saved[case['question']]=[dict(record=by_id[e['record']['passage']['passage_id']],score=e['score']) for e in old['response']['evidence']]
    write(out/'receipt.json',receipt)
    def retrieve(question):
        return saved[question]
    search=DevelopmentSearch(corpus,spec,retrieve)
    initial_path=ROOT/'outputs/prowl/section-answers-v17-20261018/quality-03-trace.json'
    receipt['pins'].append(pin(str(initial_path.relative_to(ROOT))))
    retained=next(t for t in json.loads(initial_path.read_text()) if t['path']=='chat')
    start=monotonic()
    try:
        for case in cases:
            if monotonic()-start>900:raise TimeoutError('Batch deadline')
            trace=[]
            def answer(question,evidence):
                deadline=monotonic()+60
                chats=0;actual=0
                def call(path,payload=None):
                    nonlocal chats,actual
                    reused=path=='chat' and chats==0
                    if path=='chat':chats+=1
                    if reused:response=retained['response']
                    else:
                        if path=='chat':
                            actual+=1
                            if actual>2:raise RuntimeError('Regression call budget exceeded')
                        response=api(path,payload,deadline=deadline,port=11435)
                    trace.append(dict(path=path,payload=payload,response=response,reused_prior_generation=reused))
                    write(out/(case['id']+'-trace.json'),trace)
                    return response
                return generate_qualified(question,evidence,call)
            service=NaturalAnswerService(search,answer)
            request=dict(schema_version='prowl-expert-request-v1',request_id=str(uuid4()),question=case['question'])
            begin=monotonic();response=service.answer(request)
            outcome=dict(id=case['id'],request=request,response=response,seconds=monotonic()-begin,
                         retained_ranking_reused=case['question'] in saved)
            write(out/(case['id']+'.json'),outcome)
            receipt['outcomes'].append(dict(id=case['id'],generation=response['generation'],
                failure=response.get('generation_failure'),status=(response.get('answer') or {}).get('status'),seconds=outcome['seconds']))
            write(out/'receipt.json',receipt)
            print(receipt['outcomes'][-1],flush=True)
        receipt['state']='completed'
    except Exception as error:
        receipt.update(state='failed',failure_type=type(error).__name__)
        raise
    finally:
        receipt['seconds']=monotonic()-start;write(out/'receipt.json',receipt)


if __name__=='__main__':main()
