#!/usr/bin/env python3
"""Bounded public development check; three local-model calls, immutable output directory."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
import urllib.request
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from serve_literature_search import create_service,create_record_search,create_measurement_answers,handler_for,LocalFixtureServer
from src.retrieval.measurement_interpretation import POLICY
from src.retrieval.natural_answer import api


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True);parser.add_argument('--baseline',required=True)
    args=parser.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    plan=json.loads((ROOT/'configs/evidence/evaluation/measurement-method-development-v1.json').read_text())
    baseline=json.loads(Path(args.baseline).read_text())
    assert [r['case'] for r in baseline]==plan['questions']
    base=create_service(str(ROOT/'infra/retrieval/.env.ingestion.json'))
    sources,answers=create_measurement_answers(base,create_record_search(base))
    calls=[]; started=time.monotonic()
    def call(path,payload=None):
        if time.monotonic()-started>240:raise RuntimeError('Wall budget exceeded')
        if path=='chat' and sum(x['path']=='chat' for x in calls)>=3:raise RuntimeError('Model call cap')
        entry=dict(path=path,payload=payload);calls.append(entry)
        try:
            response=api(path,payload,deadline=time.monotonic()+30);entry['response']=response;return response
        finally:(out/'model-calls.json').write_text(json.dumps(calls,indent=2)+'\n')
    answers.call=call
    server=LocalFixtureServer(('127.0.0.1',0),handler_for(base,sources,answers))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    cases=[]
    try:
        for case,old in zip(plan['questions'],baseline):
            request=dict(schema_version='prowl-expert-request-v1',request_id=str(uuid4()),question=case['question'])
            route='answer' if case['expected']=='matched' else 'query';start=time.monotonic()
            url=f'http://127.0.0.1:{server.server_port}/literature-search/{route}'
            with urllib.request.urlopen(urllib.request.Request(url,data=json.dumps(request).encode(),headers={'Content-Type':'application/json'}),timeout=40) as r:response=json.load(r)
            elapsed=time.monotonic()-start
            selected=response['record_selection'];new=selected['policy']==POLICY and selected['status']=='matched'
            passed=new==(case['expected']=='matched')
            if new:
                passed &= response['generation']=='completed' and len(response['answer']['claims'])==2
                answers.measurement_composer.material(response) # Exact canonical citation closure.
            else:
                passed &= selected==old['result']['record_selection']
            (out/(case['id']+'.json')).write_text(json.dumps(dict(request=request,response=response,seconds=elapsed),indent=2,ensure_ascii=False)+'\n')
            cases.append(dict(id=case['id'],seconds=elapsed,pass_gate=passed,generation=response['generation'],selection=selected['status']))
            print(case['id'],passed,response['generation'],round(elapsed,3),flush=True)
    finally:server.shutdown();server.server_close();thread.join()
    files=['src/retrieval/measurement_interpretation.py','src/retrieval/volume_answer.py','scripts/serve_literature_search.py','scripts/retrieval/check_measurement_methods.py']
    files += [str(p.relative_to(ROOT)) for p in (ROOT/'configs/evidence').glob('*measurement*v1*.json')]
    files += ['configs/evidence/evaluation/measurement-method-development-v1.json']
    receipt=dict(cases=cases,automated_gate=all(x['pass_gate'] for x in cases) and len(cases)==14,
        model_calls=sum(x['path']=='chat' for x in calls),manual_review='pending',
        pins={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if not receipt['automated_gate']:raise SystemExit('Candidate failed; do not promote')

if __name__=='__main__':main()
