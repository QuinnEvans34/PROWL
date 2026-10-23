"""Explicit two-worker continuation of a verified, intentionally stopped audit.

No numerical changes, completed-case replay, new exclusions or automatic retries.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_native_intake import OUT,provider,verify,read_journal,case_check
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256
from src.operations.full_training_platform import training_guard,watch_windows,require_ac
DEST=OUT/'cohort-complete'
_PROVIDER=None


def init_worker():
    global _PROVIDER
    _PROVIDER=provider()


def task(pair):
    name,role=pair
    return case_check(_PROVIDER,name,role,False)


def prepared():
    verify();r=json.loads((DEST/'request.json').read_text())
    if any(sha256(path)!=h for path,h in r['pins'].items()):raise ValueError('Continuation evidence changed')
    return r


def prepare():
    original=verify();p=provider()
    prior=read_journal(OUT/'cohort/cases.jsonl');pilot=read_journal(OUT/'pilot/cases.jsonl')
    expected=[(n,'train') for n in p.control['train']]+[(n,'validation') for n in p.control['validation']]
    if [(r['case_id'],r['role']) for r in prior]!=expected[:len(prior)]:raise ValueError('Stopped journal not exact ordered prefix')
    old_resources=json.loads((OUT/'cohort/resources.json').read_text())
    if not old_resources['workers_reaped']:raise ValueError('Prior workers not reaped')
    if json.loads((OUT/'parser-amendment.json').read_text())['reused_pilot_sha256']!=sha256(OUT/'pilot/cases.jsonl'):
        raise ValueError('Pilot changed')
    done={r['case_id']:r for r in prior}
    for r in pilot:
        if r['case_id'] not in done:done[r['case_id']]=dict(r,reused_pilot=True)
    if not set(done).issubset(dict(expected)):raise ValueError('Unexpected reused member')
    for r in done.values():
        if not r['exact_target_roundtrip'] or r['annotated_field_exposure_18_visits']!=1:raise ValueError('Unqualified reused record')
    DEST.mkdir(exist_ok=False)
    with (DEST/'reused.json').open('xb') as f:f.write(canonical(done))
    inputs=[Path(__file__),OUT/'request.json',OUT/'parser-amendment.json',OUT/'cohort/cases.jsonl',
            OUT/'cohort/resources.json',OUT/'pilot/cases.jsonl',OUT/'pilot/visual-review.json',DEST/'reused.json']
    remaining=[pair for pair in expected if pair[0] not in done]
    request=dict(pins={str(x):sha256(x) for x in inputs},remaining=remaining,expected=expected,
        reused_cases=len(done),stopped_prefix_cases=len(prior),workers=2,
        old_resources=old_resources,seconds_remaining=original['cohort_seconds']-old_resources['seconds'],
        rss_bytes=original['worker_rss_bytes'],
        reason='Intentional stop of CPU-bound serial audit; preserve prefix and use two bounded workers without changing numerical code',
        unjournaled_case='At most the interrupted in-flight case may be read again; completed records never replayed')
    with (DEST/'request.json').open('xb') as f:f.write(canonical(request))
    print(json.dumps(dict(reused=len(done),remaining=len(remaining),workers=2)),flush=True)


def worker():
    request=prepared();records=json.loads((DEST/'reused.json').read_text());begin=time.monotonic()
    with ProcessPoolExecutor(max_workers=2,initializer=init_worker) as pool:
        futures={pool.submit(task,pair):pair for pair in request['remaining']}
        for future in as_completed(futures):
            r=future.result()
            if r['case_id'] in records:raise ValueError('Duplicate case completion')
            records[r['case_id']]=r
            with (DEST/'new-cases.jsonl').open('ab') as f:f.write(canonical(r));f.flush();os.fsync(f.fileno())
            print(json.dumps(dict(completed=len(records),total=1403,seconds=time.monotonic()-begin)),flush=True)
    prepared()
    if set(records)!={name for name,role in request['expected']}:raise ValueError('Incomplete cohort')
    with (DEST/'cases.jsonl').open('xb') as f:
        for name,role in request['expected']:
            if records[name]['role']!=role:raise ValueError('Role mismatch')
            f.write(canonical(records[name]))
        f.flush();os.fsync(f.fileno())
    result=dict(completed=True,cases=1403,train=1333,development=70,reused=request['reused_cases'],
        newly_verified=len(request['remaining']),seconds=time.monotonic()-begin,all_field_coverage=1.,
        all_target_roundtrips_exact=True,all_component_anchors_exposed=True,test_reads=0,scientific_updates=0)
    with (DEST/'results.json').open('xb') as f:f.write(canonical(result))


def run():
    request=prepared()
    def tick():
        require_ac()
        if any(shutil.disk_usage(d).free<100*1024**3 for d in ('C:/','E:/')):raise ValueError('Free space floor')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        tick()
        with (DEST/'worker.log').open('x') as log:
            process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            try:watch_windows(process,seconds=request['seconds_remaining'],rss_bytes=request['rss_bytes'],tick=tick)
            finally:
                current=getattr(process,'duration_resources',{})
                (DEST/'continuation-resources.json').write_bytes(canonical(current))
                old=request['old_resources']
                merged=dict(seconds=old['seconds']+current.get('seconds',0),
                    peak_owned_rss_bytes=max(old['peak_owned_rss_bytes'],current.get('peak_owned_rss_bytes',0)),
                    workers_reaped=bool(old['workers_reaped'] and current.get('workers_reaped',False)))
                (DEST/'resources.json').write_bytes(canonical(merged))
    print('Complete cohort verified; all continuation workers reaped',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--run',action='store_true');ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if a.prepare:prepare()
    elif a.run:run()
    elif a.worker:worker()
