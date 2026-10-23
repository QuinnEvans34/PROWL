"""Convert remaining training labels once; reuse pilot members, no CT voxel reads."""
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import setup_fast_varied as setup
from src.training.experiment_config import sha256
from src.operations.full_training_platform import require_ac,watch_windows,training_guard
from src.data.manifest_records import canonical

_provider=None
_admitted=None


def initialize():
    global _provider,_admitted
    import torch
    if torch.cuda.is_available():raise ValueError('CPU cache conversion required')
    torch.set_num_threads(2)
    _provider=setup.varied.provider()
    _admitted={r['case_id']:r for r in map(json.loads,(setup.parent.COHORT/'cases.jsonl').read_text().splitlines())}


def one(name):
    return name,setup.build_member(_provider,name,_admitted)


def worker():
    setup.check_pins();setup.resources()
    for file,pin in setup.read(setup.SETUP/'cache-complete-request.json')['pins'].items():
        if sha256(file)!=pin:raise ValueError('Conversion producer changed')
    if not setup.read(setup.SETUP/'pilot/result.json')['passed'] or not setup.read(setup.SETUP/'pilot-resources.json')['workers_reaped']:
        raise ValueError('Pilot not passed/reaped')
    old=setup.read(setup.CACHE/'pilot-manifest.json');p=setup.varied.provider()
    if p.pin!=old['source_control_sha256']:raise ValueError('Pilot cohort changed')
    members=dict(old['members'])
    for name,member in members.items():
        if sha256(setup.CACHE/(name+'.npz'))!=member['target_sha256'] or sha256(setup.CACHE/(name+'.json'))!=member['metadata_sha256']:
            raise ValueError('Pilot target cache changed')
    remaining=[n for n in p.control['train'] if n not in members];began=time.monotonic()
    output=setup.SETUP/'cache-complete';output.mkdir(exist_ok=False)
    executor=ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context('spawn'),initializer=initialize)
    try:
        futures=[executor.submit(one,n) for n in remaining]
        for future in as_completed(futures):
            name,member=future.result();members[name]=member
            with (output/'members.jsonl').open('ab') as f:f.write(canonical(dict(case_id=name,**member)));f.flush()
            if len(members)%25==0 or len(members)==1333:
                setup.resources();record=dict(completed=len(members),total=1333,seconds=time.monotonic()-began)
                with (output/'progress.jsonl').open('ab') as f:f.write(canonical(record));f.flush()
                print(json.dumps(record),flush=True)
    finally:executor.shutdown(wait=True,cancel_futures=True)
    if set(members)!=set(p.control['train']):raise ValueError('Incomplete training target cache')
    setup.resources()
    setup.write(setup.CACHE/'manifest.json',dict(old,complete=True,members=members,CT_voxel_reads=0))
    setup.write(output/'result.json',dict(completed=True,cases=len(members),reused_pilot=len(old['members']),
        converted_remaining=len(remaining),CT_voxel_reads=0,test_reads=0,new_exclusions=0,
        cache_bytes=sum(v['bytes'] for v in members.values()),seconds=time.monotonic()-began,
        manifest_sha256=sha256(setup.CACHE/'manifest.json')))


def main():
    setup.check_pins();setup.resources();receipt=setup.SETUP/'cache-complete-request.json'
    if receipt.exists():raise ValueError('Conversion already started; no duplicate/retry')
    if not setup.read(setup.SETUP/'pilot/result.json')['passed']:raise ValueError('Pilot incomplete')
    paths=[Path(__file__),ROOT/'scripts/diagnostics/setup_fast_varied.py',ROOT/'src/data/segmenter_fast_varied_v1.py',
        setup.CACHE/'pilot-manifest.json',setup.SETUP/'pilot/result.json']
    setup.write(receipt,dict(pins={str(p):sha256(p) for p in paths},seconds=7200,rss_bytes=12*1024**3,
        workers=2,CT_voxel_reads=0,scientific=False))
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'),(setup.SETUP/'cache-complete.log').open('x') as log:
        process=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_CACHE_BUILD='1'))
        try:watch_windows(process,seconds=7200,rss_bytes=12*1024**3,tick=require_ac)
        finally:setup.write(setup.SETUP/'cache-complete-resources.json',getattr(process,'duration_resources',{}))


if __name__=='__main__':
    if sys.argv[1:]==['--worker']:
        if os.environ.get('PROWL_CACHE_BUILD')!='1':raise ValueError('Supervisor required')
        worker()
    elif not sys.argv[1:]:main()
    else:raise ValueError('Unsupported arguments')
