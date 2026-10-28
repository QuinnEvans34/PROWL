#!/usr/bin/env python3
"""Five exposed public packets; run only when the teacher is paused. No promotion."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.operations.full_training_platform import training_guard
from src.retrieval.single_pass_summary import generate
from src.retrieval.natural_answer import api
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        a.output.mkdir(exist_ok=False)
        for name in ['function','function_paraphrase','methods','fat','gap']:
            packet=json.loads((ROOT/'outputs/prowl/general-fallback-20261023'/f'{name}.json').read_text())
            started=time.monotonic();trace=[]
            def call(path,payload=None):
                response=api(path,payload,deadline=started+60)
                if path=='chat':trace.append(dict(request=payload,response=response))
                return response
            result=dict(question=packet['question'],manual_review_required=True,promoted=False)
            try:result['answer']=generate(packet['question'],packet['baseline']['evidence'],call)
            except Exception as error:result['failure']=repr(error)
            result.update(seconds=time.monotonic()-started,calls=trace)
            (a.output/f'{name}.json').write_text(json.dumps(result,indent=2))
