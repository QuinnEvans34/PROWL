"""One exposed24-question HTTP source screen; no answers, model calls or protected inputs."""
import hashlib
import json
from pathlib import Path
import signal
from time import monotonic
from urllib.request import Request, urlopen
from uuid import uuid4
from src.retrieval.evidence_experiment import corpus_records

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/prowl/record-search-v1-attempt2-20261018'
BASE='http://127.0.0.1:8017'


def write(path,value):
    data=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())+len(data)>20*1024**2:
        raise ValueError('Output budget')
    path.write_bytes(data)


def main():
    OUT.mkdir(exist_ok=False);start=monotonic();receipt=dict(state='started',cases=[],source_calls=0,answer_calls=0)
    def timeout(signum,frame):raise TimeoutError('120second screen limit')
    previous=signal.signal(signal.SIGALRM,timeout);signal.alarm(120)
    try:
        files=['src/retrieval/record_search.py','src/retrieval/disease_fact_records.py','src/retrieval/fact_records.py',
            'src/retrieval/evidence_experiment.py','src/retrieval/development_search.py','src/retrieval/development_set.py',
            'src/retrieval/literature_adapter.py','src/retrieval/question_routing.py','src/retrieval/direct_ingestion.py',
            'scripts/serve_literature_search.py','scripts/retrieval/check_record_search.py',
            'configs/evidence/development-search-v3-records.json','configs/evidence/source-facts-disease-v1.json',
            'configs/evidence/source-facts-disease-v1-review.json','configs/evidence/record-search-screen-v1.json',
            'docs/capstone/retrieval/RECORD-SEARCH-PLAN-2026-10-18.md','tests/retrieval/test_record_search.py',
            'tests/retrieval/test_development_search.py','ui/src/components/LiteratureSearchPanel.jsx',
            'ui/tests/LiteratureSearchPanel.test.jsx']
        receipt['pins']=[]
        for rel in files:
            data=(ROOT/rel).read_bytes();receipt['pins'].append(dict(path=rel,sha256=hashlib.sha256(data).hexdigest()))
            p=OUT/'producing'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        config=json.loads((ROOT/files[11]).read_text());cat=json.loads((ROOT/files[12]).read_text())
        canonical=corpus_records(ROOT,config['manifest']);by_id={v['passage_id']:v['record'] for v in canonical.values()}
        record_by_id={r['id']:r for r in cat['records']};receipt['canonical_passages_checked']=len(canonical)
        with urlopen(BASE+'/literature-search/health',timeout=5) as r:receipt['health']=json.load(r)
        if (receipt['health']['retrieval_policy']!=config['retriever']
                or receipt['health']['answer_policy']!='natural-literature-answer-v6.1'
                or receipt['health']['answer_retrieval_policy']!='dense-exact-cosine-v1'):
            raise ValueError('Unexpected candidate policy')
        write(OUT/'receipt.json',receipt)
        for case in json.loads((ROOT/files[14]).read_text())['cases']:
            request=dict(schema_version='prowl-expert-request-v1',request_id=str(uuid4()),question=case['question'])
            receipt['source_calls']+=1;write(OUT/'receipt.json',receipt);begin=monotonic()
            with urlopen(Request(BASE+'/literature-search/query',data=json.dumps(request).encode(),
                         headers={'Content-Type':'application/json'}),timeout=10) as r:result=json.load(r)
            seconds=monotonic()-begin;write(OUT/(case['id']+'.json'),dict(request=request,response=result,seconds=seconds))
            selection=result['record_selection'];observed=sorted(m['record_id'] for m in selection['matches'])
            context={pid for rid in observed for f in record_by_id[rid]['facts'] for sid in f['evidence']
                     for pid in [cat['spans'][sid]['passage_id']]}
            hits={h['record']['passage']['passage_id'] for h in result['evidence']}
            checks=dict(selection=observed==case['expected_record_ids'],
                canonical=all(h['record']==by_id[h['record']['passage']['passage_id']] for h in result['evidence']),
                complete_context=(hits==context if observed else True),
                no_generation=result['answer'] is None and result['generation']=='not_called',
                request_binding=result['request_id']==request['request_id'] and result['question']==request['question'],
                latency=seconds<10)
            receipt['cases'].append(dict(id=case['id'],question=case['question'],expected=case['expected_record_ids'],
                observed=observed,selection_status=selection['status'],reason=selection['reason'],
                evidence_count=len(hits),seconds=seconds,checks=checks,passed=all(checks.values())))
            write(OUT/'receipt.json',receipt)
        receipt['passed']=sum(c['passed'] for c in receipt['cases']);receipt['state']='completed'
        receipt['promotion_gate']=receipt['passed']==24
    except Exception as error:
        receipt.update(state='failed',error=dict(type=type(error).__name__,message=str(error)));raise
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous);receipt['seconds']=monotonic()-start
        write(OUT/'receipt.json',receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k not in ('pins','cases')},indent=2),flush=True)


if __name__=='__main__':main()
