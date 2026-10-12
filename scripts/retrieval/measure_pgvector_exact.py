#!/usr/bin/env python3
"""Read-only exact retrieval and synthetic MPS coexistence on the retained trial.

No models/training. Nine 3-second GPU windows; client latency includes docker exec,
psql connection, query and result delivery. Preserve data and always stop owned DB.
"""
import argparse
import concurrent.futures
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import statistics
import subprocess
import threading
import time
import check_pgvector_platform as p

SCOPES={'broad':'permitted','one_percent':'permitted AND bucket=7',
        'fewer_than_k':'permitted AND id<=5','empty':'permitted AND bucket=0'}


def query(j,scope):
    if type(j) is not int or not 1 <= j <= 20 or scope not in SCOPES:
        raise ValueError('Only fixed synthetic query identities are allowed')
    return f"""WITH q AS (SELECT ARRAY(SELECT sin((100000+{j})::double precision*d*d*.0001)::real FROM generate_series(1,128) d)::vector v),
 scored AS MATERIALIZED (SELECT id,embedding <=> (SELECT v FROM q) distance,
 ts_rank_cd(terms,plainto_tsquery('english','pancreas')) lexical_score,
 terms @@ plainto_tsquery('english','pancreas') lexical_match
 FROM benchmark.passages WHERE {SCOPES[scope]}),
 dense AS (SELECT id,row_number() OVER (ORDER BY distance,id) r FROM scored ORDER BY distance,id LIMIT 10),
 lexical AS (SELECT id,row_number() OVER (ORDER BY lexical_score DESC,id) r
 FROM scored WHERE lexical_match ORDER BY lexical_score DESC,id LIMIT 10),
 hybrid AS (SELECT id,sum(1.0/(60+r)) score FROM (SELECT * FROM dense UNION ALL SELECT * FROM lexical) a GROUP BY id ORDER BY score DESC,id LIMIT 10)
 SELECT json_build_object('dense',coalesce((SELECT json_agg(id ORDER BY r) FROM dense),'[]'::json),
 'hybrid',coalesce((SELECT json_agg(id ORDER BY score DESC,id) FROM hybrid),'[]'::json));"""


def percentile95(values):
    values=sorted(values)
    if not values: raise ValueError('No measurements')
    return values[math.ceil(.95*len(values))-1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--qualification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    c=json.loads(args.config.read_text());p.validate_config(c)
    lock=(p.ROOT/'outputs/prowl/pgvector-platform.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    admission=p.preflight(c)
    if admission['errors'] not in ([],['Existing trial container: preserve/review before a fresh run']): raise ValueError(admission)
    base=['docker','--context','desktop-linux','compose','-p','prowl-retrieval-qualification','-f',str(args.qualification/'prowl-retrieval-qualification.json')]
    cid=p.command(base+['ps','-aq','db']).stdout.decode().strip()
    meta=json.loads(p.command(['docker','--context','desktop-linux','inspect',cid]).stdout)[0]
    expected=str(Path(c['mount'])/'PROWL/scratch/literature/pgvector-qualification-01/source')
    if meta['State']['Running'] or meta['Config']['Image']!=p.IMAGE or not any(m['Source']==expected and m['Destination']=='/var/lib/postgresql/data' for m in meta['Mounts']):
        raise ValueError('Retained stopped trial identity mismatch')
    for project in ['prowl-retrieval-smoke','prowl-retrieval-restore']:
        if p.command(['docker','--context','desktop-linux','ps','-q','--filter',f'label=com.docker.compose.project={project}']).stdout.strip():
            raise ValueError('Another trial is running')
    expected_rows=json.loads((args.qualification/'measurements.stdout').read_text())
    expected_ids={(r['query'],r['scope']):r['exact_ids'] for r in expected_rows}
    args.output.mkdir(parents=True,exist_ok=False)
    runtime=dict(c,data=str(Path(expected).parent));started=time.monotonic()
    result={'state':'running','admission':admission,'measurements':[],'gpu':[]}
    stop=threading.Event()
    def interrupted(signum,frame): raise KeyboardInterrupt('Requested stop')
    signal.signal(signal.SIGTERM,interrupted)
    def measure(j,scope):
        begin=time.perf_counter()
        raw=p.command(base+['exec','-T','db','psql','-X','-At','-v','ON_ERROR_STOP=1','-U','prowl_trial','-d','prowl_synthetic','-c',query(j,scope)]).stdout
        elapsed=(time.perf_counter()-begin)*1000
        answer=json.loads(raw)
        if answer['dense']!=expected_ids[(j,scope)] or len(answer['hybrid'])!=len(answer['dense']):
            raise RuntimeError('Exact search differs from frozen reference')
        return {'query':j,'scope':scope,'milliseconds':elapsed}
    try:
        p.command(base+['start','db'])
        for _ in range(60):
            p.sample_resources(runtime,started,args.output)
            ready=subprocess.run(base+['exec','-T','db','pg_isready','-h','127.0.0.1','-U','prowl_trial','-d','prowl_synthetic'],capture_output=True,timeout=5)
            if ready.returncode==0:break
            time.sleep(1)
        else: raise RuntimeError('Readiness timeout')
        for scope in SCOPES:
            for j in range(1,21):
                p.sample_resources(runtime,started,args.output)
                result['measurements'].append(measure(j,scope))
        result['client_p95_ms']={scope:percentile95([r['milliseconds'] for r in result['measurements'] if r['scope']==scope]) for scope in SCOPES}
        import torch
        if not torch.backends.mps.is_available():raise RuntimeError('MPS unavailable')
        torch.manual_seed(20261012)
        with torch.inference_mode():
            a=torch.randn((1024,1024),device='mps');b=torch.randn_like(a);out=torch.empty_like(a)
            for _ in range(20):torch.mm(a,b,out=out)
            torch.mps.synchronize()
            def gpu_window():
                start=time.perf_counter();count=0
                while time.perf_counter()-start<3:
                    for _ in range(10):torch.mm(a,b,out=out)
                    torch.mps.synchronize();count+=10
                return count/(time.perf_counter()-start)
            def load():
                values=[];j=1
                while not stop.is_set():
                    values.append(measure(j,'broad'));j=j%20+1
                return values
            for pair in range(3):
                p.sample_resources(runtime,started,args.output)
                before=gpu_window()
                stop.clear()
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future=executor.submit(load)
                    try:
                        during=gpu_window()
                    finally:stop.set()
                    queries=future.result(timeout=35)
                after=gpu_window()
                if not queries:raise RuntimeError('No concurrent retrieval samples')
                result['gpu'].append({'pair':pair,'baseline_before_ops_s':before,'concurrent_ops_s':during,'baseline_after_ops_s':after,'retrieval':queries})
            baseline=statistics.median((x['baseline_before_ops_s']+x['baseline_after_ops_s'])/2 for x in result['gpu'])
            concurrent_rate=statistics.median(x['concurrent_ops_s'] for x in result['gpu'])
            result['gpu_reduction_fraction']=1-concurrent_rate/baseline
            result['torch_version']=torch.__version__
        result['concurrent_client_p95_ms']=percentile95([r['milliseconds'] for x in result['gpu'] for r in x['retrieval']])
        result['passed']=max(result['client_p95_ms'].values())<=500 and result['concurrent_client_p95_ms']<=500 and result['gpu_reduction_fraction']<=.10
        result['state']='measured'
    except BaseException as exc:
        result.update(state='failed',error=str(exc));raise
    finally:
        stop.set()
        result.update(p.stop_trial(base,os.environ,args.output))
        result['seconds']=time.monotonic()-started
        (args.output/'result.json').write_text(json.dumps(result,indent=2))
        if not result['stop_confirmed']:raise RuntimeError('Stop unconfirmed')


if __name__=='__main__':main()
