"""One actual-corpus source-fact canary: one source-only search, no model generation."""
import hashlib
import json
from pathlib import Path
import signal
from time import monotonic
from urllib.request import Request, urlopen
from uuid import uuid4

from src.retrieval.evidence_experiment import corpus_records
from src.retrieval.fact_records import FactCatalog

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/prowl/source-facts-volume-v1-20261018'


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def pin(path):
    return dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    OUT.mkdir(exist_ok=False)
    start=monotonic();receipt=dict(state='started',search_calls=0,model_calls=0,answers=[],selections=[])
    write(OUT/'receipt.json',receipt)
    def timeout(signum,frame): raise TimeoutError('Source-fact canary60second limit')
    previous=signal.signal(signal.SIGALRM,timeout);signal.alarm(60)
    try:
        paths=[ROOT/p for p in ['src/retrieval/fact_records.py','src/retrieval/evidence_experiment.py',
            'src/retrieval/development_set.py','configs/evidence/source-facts-volume-v1.json',
            'configs/evidence/source-facts-volume-v1-review.json','scripts/retrieval/check_source_facts.py',
            'tests/retrieval/test_fact_records.py','docs/capstone/retrieval/SOURCE-FACT-PLAN-2026-10-18.md',
            'configs/evidence/evaluation/answer-quality-plan-v1.json']]
        catalog=json.loads(paths[3].read_text());review=json.loads(paths[4].read_text())
        paths.append(ROOT/catalog['manifest']['path'])
        receipt['pins']=[pin(p) for p in paths]
        for p in paths:
            target=OUT/'producing'/p.relative_to(ROOT);target.parent.mkdir(exist_ok=True,parents=True)
            target.write_bytes(p.read_bytes())
        write(OUT/'receipt.json',receipt)
        canonical=corpus_records(ROOT,catalog['manifest'])
        engine=FactCatalog(catalog,review,canonical)
        receipt['canonical_passages_checked']=len(canonical)
        question=next(c['question'] for c in json.loads(paths[8].read_text())['cases'] if c['id']=='quality-03')
        with urlopen('http://127.0.0.1:8016/literature-search/health',timeout=5) as response:
            receipt['live_health']=json.load(response)
        if receipt['live_health']['answer_policy']!='natural-literature-answer-v6.1':
            raise ValueError('Unexpected live policy')
        request=dict(schema_version='prowl-expert-request-v1',request_id=str(uuid4()),question=question)
        receipt['search_calls']=1;write(OUT/'receipt.json',receipt);begin=monotonic()
        with urlopen(Request('http://127.0.0.1:8016/literature-search/query',data=json.dumps(request).encode(),
                            headers={'Content-Type':'application/json'}),timeout=30) as response:
            result=json.load(response)
        write(OUT/'live-search.json',dict(request=request,response=result,seconds=monotonic()-begin))
        receipt['search_seconds']=monotonic()-begin
        hits=[h['record'] for h in result['evidence']]
        lookup={s['passage_id']:s['record'] for s in canonical.values()}
        if any(h != lookup[h['passage']['passage_id']] for h in hits):raise ValueError('Noncanonical live hit')
        intent=dict(object='pancreas',extent='whole_organ',quantity='volume',
            population='normal_glucose_tolerance_comparison',method='MRI',uncertainty_kind='SEM',use='literature_example')
        receipt['intent_origin']='explicit_diagnostic_structured_intents_not_natural_language_routing'
        for population in ['normal_glucose_tolerance_comparison','well_controlled_type2_metformin']:
            selected_intent=dict(intent,population=population);selection=engine.select(hits,selected_intent)
            receipt['selections'].append(dict(intent=selected_intent,selection=selection))
            if len(selection['record_ids'])!=1:raise ValueError('Expected one eligible reviewed group')
            rid=selection['record_ids'][0];begin=monotonic();answer=engine.render(rid)
            engine.verify_answer(answer,record_id=rid)
            receipt['answers'].append(dict(record_id=rid,render_seconds=monotonic()-begin,
                statement_count=len(answer['statements']),citation_count=len(answer['citations']),
                expanded_passages=sorted(set(c['passage_id'] for c in answer['citations'])-
                                         set(h['passage']['passage_id'] for h in hits))))
            write(OUT/(population+'-answer.json'),answer)
        # These exercise typed metadata boundaries, not natural-language understanding.
        for field,value in [('object','lesion'),('extent','head'),('quantity','diameter'),
                            ('population','healthy_adults'),('method','CT'),('uncertainty_kind','SD'),
                            ('use','patient_normality')]:
            changed=dict(intent);changed[field]=value;selection=engine.select(hits,changed)
            if selection['record_ids']:raise ValueError('Mismatched request selected a fact')
            receipt['selections'].append(dict(intent=changed,selection=selection))
        # The earlier field-correspondence punctuation failure is preserved as preparation history.
        receipt['preparation_history']=['Initial catalog construction refused sentence-ending sex. '
            'because a numeric-boundary regex treated the period as a decimal continuation. '
            'Fixed before canary; dedicated positive/negative punctuation/partial-number test passes. '
            'No HTTP/model work occurred during that failed construction.']
        if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>12*1024**2:raise ValueError('Output budget')
        receipt['state']='completed'
    except Exception as error:
        receipt.update(state='failed',error=dict(type=type(error).__name__,message=str(error)))
        raise
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        receipt['seconds']=monotonic()-start;write(OUT/'receipt.json',receipt)
        print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':main()
