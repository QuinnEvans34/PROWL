"""Bounded two-arm comparison on five public development packets; manual review required.
Run only with teacher GPU ownership released. Never promotes or changes live service.
"""
import argparse,json,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.retrieval.general_extract import generate
from src.retrieval.natural_answer import api
from src.operations.full_training_platform import training_guard

NAMES=['function','function_paraphrase','methods','fat','gap']


def configured_call(call, arm):
    count=0
    def invoke(path,payload=None):
        nonlocal count
        if path=='chat':
            count+=1
            if count>2:raise ValueError('Two-call budget')
            payload=dict(payload,think=(arm=='baseline' or count==2))
        return call(path,payload)
    return invoke


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--run',action='store_true');a=p.parse_args()
    if not a.run:raise SystemExit('Explicit --run required; acquire teacher-free GPU before model calls')
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        a.output.mkdir(exist_ok=False);started=time.monotonic();summary=[]
        for index,name in enumerate(NAMES):
            source=ROOT/'outputs/prowl/general-fallback-20261023'/f'{name}.json';packet=json.loads(source.read_text())
            # Counterbalance order; do not present this small exposed set as independent evaluation.
            for arm in (['baseline','fast_select'] if index%2==0 else ['fast_select','baseline']):
                if time.monotonic()-started>1000:raise TimeoutError('Comparison total budget')
                t=time.monotonic();trace=[]
                def call(path,payload=None):
                    response=api(path,payload,deadline=t+90)
                    if path=='chat':trace.append(dict(request=payload,response=response))
                    return response
                record=dict(case_id=name,arm=arm,question=packet['question'],packet_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
                try:
                    answer=generate(packet['question'],packet['baseline']['evidence'],call=configured_call(call,arm))
                    evidence={x['rank']:x['record']['text'] for x in packet['baseline']['evidence']}
                    assert all(c['quote'] in evidence[c['rank']] for cl in answer['claims'] for c in cl['citations'])
                    record.update(answer=answer,citations_exact=True)
                except Exception as e:record.update(failure=repr(e))
                record.update(seconds=time.monotonic()-t,calls=trace)
                (a.output/f'{name}-{arm}.json').write_text(json.dumps(record,indent=2));summary.append({k:v for k,v in record.items() if k not in ['calls','answer']})
        (a.output/'summary.json').write_text(json.dumps(dict(results=summary,manual_semantic_review_required=True,promoted=False),indent=2))
if __name__=='__main__':main()
