"""Bounded source-only disease canary; seeded assembly and replay never count as live hits."""
import hashlib
import json
from pathlib import Path
import signal
from time import monotonic
from urllib.request import Request, urlopen
from uuid import uuid4

from src.retrieval.disease_fact_records import DiseaseFactCatalog
from src.retrieval.evidence_experiment import corpus_records

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'outputs/prowl/source-facts-disease-v1-20261018'
BUDGET = 16*1024**2


def save(path, data):
    size = sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    if size + len(data) - (path.stat().st_size if path.exists() else 0) > BUDGET:
        raise ValueError('Output budget exceeded')
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)


def write(path, value):
    save(path, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode())


def pin(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    OUT.mkdir(exist_ok=False); start=monotonic()
    receipt=dict(state='started', search_calls=0, model_calls=0, selections=[],
        intent_origin='explicit_diagnostic_structured_intents_not_natural_language_routing')
    write(OUT/'receipt.json',receipt)
    def timeout(signum,frame): raise TimeoutError('Disease fact canary90second limit')
    previous=signal.signal(signal.SIGALRM,timeout);signal.alarm(90)
    try:
        rels=['src/retrieval/disease_fact_records.py','src/retrieval/fact_records.py',
            'src/retrieval/evidence_experiment.py','src/retrieval/development_set.py',
            'configs/evidence/source-facts-disease-v1.json','configs/evidence/source-facts-disease-v1-review.json',
            'tests/retrieval/test_disease_fact_records.py','scripts/retrieval/check_disease_source_facts.py',
            'docs/capstone/retrieval/DISEASE-FACT-PLAN-2026-10-18.md',
            'configs/evidence/evaluation/answer-quality-plan-v1.json',
            'outputs/prowl/section-answers-v9-20261017/quality-01.json',
            'outputs/prowl/section-answers-v9-20261017/quality-02.json']
        catalog=json.loads((ROOT/rels[4]).read_text());review=json.loads((ROOT/rels[5]).read_text())
        rels.append(catalog['manifest']['path']);receipt['pins']=[pin(ROOT/p) for p in rels]
        for p in rels:save(OUT/'producing'/p,(ROOT/p).read_bytes())
        canonical=corpus_records(ROOT,catalog['manifest']);receipt['canonical_passages_checked']=len(canonical)
        engine=DiseaseFactCatalog(catalog,review,canonical)
        cases=json.loads((ROOT/rels[9]).read_text())['cases']
        questions={c['id']:c['question'] for c in cases if c['id'] in ('quality-01','quality-02')}
        with urlopen('http://127.0.0.1:8016/literature-search/health',timeout=5) as response:
            receipt['live_health']=json.load(response)
        if receipt['live_health']['answer_policy']!='natural-literature-answer-v6.1':
            raise ValueError('Unexpected live policy')
        intents=[('quality-01','head',['MFCP','PDAC'],'focal_head_mass',7),
                 ('quality-02','mfcp',['MFCP','PDAC'],'imaging_differentiation',22),
                 ('quality-02','aip',['focal_AIP','PDAC'],'imaging_differentiation',44)]
        live={}; replay={}; unique={}
        for qid,question in questions.items():
            request=dict(schema_version='prowl-expert-request-v1',request_id=str(uuid4()),question=question)
            receipt['search_calls']+=1;write(OUT/'receipt.json',receipt);begin=monotonic()
            with urlopen(Request('http://127.0.0.1:8016/literature-search/query',data=json.dumps(request).encode(),
                         headers={'Content-Type':'application/json'}),timeout=30) as response:
                result=json.load(response)
            write(OUT/f'{qid}-live.json',dict(request=request,response=result,seconds=monotonic()-begin))
            live[qid]=[h['record'] for h in result['evidence']]
            retained=json.loads((ROOT/f'outputs/prowl/section-answers-v9-20261017/{qid}.json').read_text())
            replay[qid]=[h['record'] for h in retained['response']['evidence']]
        for mode in ['live_dense','retained_r8_with_context','canonical_seed_not_retrieval']:
            for qid,label,pair,topic,ordinal in intents:
                hits=(live[qid] if mode=='live_dense' else replay[qid] if mode=='retained_r8_with_context'
                      else [canonical['work:pmid:32703312',ordinal]['record']])
                intent=dict(organ='pancreas',comparison=pair,topic=topic,use='literature_comparison')
                selection=engine.select(hits,intent)
                entry=dict(mode=mode,question_id=qid,label=label,intent=intent,selection=selection,
                           retrieved_passage_ids=[h['passage']['passage_id'] for h in hits],answers=[])
                if mode=='canonical_seed_not_retrieval' and len(selection['record_ids'])!=1:
                    raise ValueError('Seeded record did not assemble')
                for rid in selection['record_ids']:
                    answer=engine.render(rid);engine.verify_answer(answer,record_id=rid)
                    if rid in unique and answer != unique[rid]:raise ValueError('Assembly varies across modes')
                    unique[rid]=answer;filename=f'{mode}-{label}-answer.json';write(OUT/filename,answer)
                    entry['answers'].append(dict(record_id=rid,path=filename,
                        statement_count=len(answer['statements']),
                        expanded_passages=sorted({c['passage_id'] for c in answer['citations']}
                                                 -set(entry['retrieved_passage_ids']))))
                receipt['selections'].append(entry)
        receipt['distinct_answers']=len(unique)
        receipt['distinct_source_statements']=sum(sum(s['kind']=='source_fact' for s in a['statements']) for a in unique.values())
        receipt['distinct_application_limits']=len(unique)
        lines=['# Disease comparisons: local fact-record review','',
            'Engineering-curated, independent review pending. Structured intents are supplied by the harness. '
            'Seeded examples below test assembly; they are not proof of live retrieval or UI behavior.','',
            '| Evidence mode | Head mass | MFCP imaging | Focal AIP imaging |','|---|---|---|---|']
        for mode in ['live_dense','retained_r8_with_context','canonical_seed_not_retrieval']:
            rows=[s for s in receipt['selections'] if s['mode']==mode]
            lines.append('| '+mode+' | '+' | '.join('Selected' if s['selection']['record_ids'] else 'No eligible record' for s in rows)+' |')
        for rid,a in unique.items():
            lines+=['',f'## {rid}','']
            refs={c['passage_id']:i+1 for i,c in enumerate(a['citations'])}
            for s in a['statements']:
                citation=' '.join(f'[{refs[p]}]' for p in s['citations'])
                prefix='Application limit: ' if s['kind']=='application_limit' else ''
                lines+=[prefix+s['text']+' '+citation,'']
            lines+=['### Exact source evidence','']
            for c in a['citations']:
                meta=c['citation'];lines += [f"**[{refs[c['passage_id']]}] [{meta['title']}]({meta['url']}) — passage {c['ordinal']}**",'',
                    f"{meta['attribution']}; [license]({meta['license_url']}).",'', '> '+c['quote'],'']
        save(OUT/'readable-review.md',('\n'.join(lines)+'\n').encode())
        with urlopen('http://127.0.0.1:8016/literature-search/health',timeout=5) as response:
            receipt['closing_health']=json.load(response)
        if receipt['closing_health']!=receipt['live_health']:raise ValueError('Live policy changed during check')
        receipt['state']='completed'
    except Exception as error:
        receipt.update(state='failed',error=dict(type=type(error).__name__,message=str(error)));raise
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        receipt['seconds']=monotonic()-start;write(OUT/'receipt.json',receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k not in ('pins','selections')},indent=2),flush=True)


if __name__=='__main__': main()
