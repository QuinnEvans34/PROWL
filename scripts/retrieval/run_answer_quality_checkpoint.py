#!/usr/bin/env python3
"""Run one pinned public development batch against the existing loopback UI API."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from time import monotonic
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.retrieval.direct_ingestion import digest, write_once
from src.retrieval.development_set import checked_json
from src.retrieval.literature_adapter import FrozenLiterature
from src.retrieval.quality_checkpoint import observe

PLAN = ROOT/'configs/evidence/evaluation/answer-quality-plan-v1.json'


def http(path, payload=None):
    request = Request('http://127.0.0.1:8016/literature-search/'+path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Content-Type':'application/json'})
    with urlopen(request, timeout=90) as response: raw=response.read(1024*1024+1)
    if len(raw)>1024*1024: raise ValueError('Oversized response')
    return json.loads(raw)


def pins(plan):
    for item in plan['pins']:
        path=(ROOT/item['path']).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Preregistered input changed')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    plan=json.loads(PLAN.read_text())
    if (plan['split']!='exposed_development_diagnostic' or len(plan['cases'])!=10
            or len({c['id'] for c in plan['cases']})!=10
            or plan['content_sha256']!=digest({k:v for k,v in plan.items() if k!='content_sha256'})):
        raise ValueError('Invalid pinned ten-case plan')
    pins(plan)
    search=json.loads((ROOT/'configs/evidence/development-search-v1.json').read_text())
    answer=json.loads((ROOT/'configs/evidence/natural-answer-v6.json').read_text())
    manifest=checked_json(search['manifest'],ROOT)
    bundles=[checked_json(s['bundle'],ROOT) for s in manifest['sources']]
    batches=[checked_json(b,ROOT) for b in manifest['batches']]
    corpus=FrozenLiterature(batches=batches,bundles=bundles,inventory=manifest['inventory'],
        manifest_sha256=search['manifest']['sha256'])
    records={i['record']['passage']['passage_id']:i['record'] for b in batches for i in b['items']}
    if http('health')['answer_policy']!=answer['version']: raise ValueError('Live policy mismatch')
    # Refuse overwriting/replaying an existing attempt, including interrupted runs.
    args.output.mkdir(parents=True,exist_ok=False)
    receipt=dict(plan=plan,started_at=datetime.now(timezone.utc).isoformat(),
                 target=corpus.target,observations=[],state='running')
    write_once(args.output/'admission.json',receipt)
    started=monotonic()
    for case in plan['cases']:
        if monotonic()-started>plan['budget']['maximum_total_seconds']: break
        pins(plan)
        result=observe(case,lambda request:http('answer',request),search=search,answer=answer,
                       target=corpus.target,records=records)
        result['plan_sha256']=plan['content_sha256']
        result['content_sha256']=digest(result)
        write_once(args.output/(case['id']+'.json'),result)
        receipt['observations'].append(dict(case_id=case['id'],content_sha256=result['content_sha256']))
        print(json.dumps(dict(case=case['id'],seconds=round(result['elapsed_seconds'],3),
            state=result.get('response',{}).get('generation'),validation=result['transport_validation'])),flush=True)
        if result['transport_validation']!='passed': break
    pins(plan)
    receipt.update(state='complete' if len(receipt['observations'])==10 else 'stopped',
                   elapsed_seconds=monotonic()-started)
    receipt['content_sha256']=digest(receipt)
    write_once(args.output/'manifest.json',receipt)


if __name__=='__main__':main()
