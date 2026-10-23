"""Measured original-vs-fast CUDA qualification, independent backup and cold replay."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import setup_fast_varied as setup
from src.training.experiment_config import sha256
from src.operations.full_training_platform import training_guard,watch_windows,require_ac,durable_replace
from src.data.manifest_records import canonical,digest

SPEC=ROOT/'docs/capstone/operations/PANTS-VARIED-FOCUS-FAST-24K-20261022.json'
OUT=setup.SETUP/'cuda'
BACKUP=setup.parent.BACKUP_ROOT/(setup.varied.NAME+'-fast-qualification')


def preparation():
    import torch
    from src.training.segmenter_fast_varied_session_v1 import member_at
    from src.data.segmenter_varied_region_v1 import coverage_slots
    setup.check_pins();setup.resources()
    if not setup.read(setup.SETUP/'cache-complete/result.json')['completed'] or not setup.read(setup.SETUP/'cache-complete-resources.json')['workers_reaped']:
        raise ValueError('Training cache incomplete or worker active')
    visual=setup.read(setup.SETUP/'visual-review.json')
    if not visual['accepted'] or visual['reviewed_cases']!=12:raise ValueError('Pilot visual review required')
    if (setup.SETUP/'cuda-request.json').exists():raise ValueError('Qualification already prepared/started')
    p=setup.provider(prefetch=False)
    try:
        names=setup.read(setup.varied.SETUP/'pilot-selection.json')['cases'];focus=dict.fromkeys(names,0);kinds=[];horizon=None
        for step in range(40):
            name=member_at(names,step,42);meta=setup.read(setup.CACHE/(name+'.json'))
            slots=coverage_slots(p.planned_counts[name],len(meta['cover']))
            if focus[name]>=p.planned_counts[name] and step%4!=3:raise ValueError('Qualification focus plan exhausted')
            kind='context' if step%4==3 else 'reserved' if focus[name] in slots else 'jitter'
            kinds.append(kind)
            if step%4!=3:focus[name]+=1
            if step>=31 and kind=='jitter':horizon=step+1;break
        if horizon is None or set(kinds)!={'context','reserved','jitter'}:raise ValueError('Qualification path coverage')
        config=setup.varied.cfg();config['session'].update(max_steps=horizon,warmup_steps=1,lr_horizon_steps=horizon)
        plan=dict(train=names,validation=setup.read(setup.varied.SETUP/'pilot-selection.json')['validation'],
            updates=horizon,kinds=kinds,config=config,nonpromotable=True)
        setup.write(setup.SETUP/'cuda-plan.json',plan)
        files=[Path(__file__),ROOT/'src/data/segmenter_fast_varied_v1.py',ROOT/'src/training/segmenter_fast_varied_session_v1.py',
            ROOT/'scripts/diagnostics/setup_fast_varied.py',SPEC,setup.SETUP/'cuda-plan.json',setup.SETUP/'visual-review.json',setup.CACHE/'manifest.json']
        setup.write(setup.SETUP/'cuda-request.json',dict(pins={str(f):sha256(f) for f in files},config=config,seconds=3600,
            rss_bytes=12*1024**3,scientific=False))
    finally:p.close()


def provider():
    p=setup.provider();p.control['train']=setup.read(setup.SETUP/'cuda-plan.json')['train']
    p.control['qualification_only']=True;p.pin=digest(canonical(p.control));return p


def check():
    setup.check_pins();setup.resources()
    for f,pin in setup.read(setup.SETUP/'cuda-request.json')['pins'].items():
        if sha256(f)!=pin:raise ValueError('Qualification producer changed: '+f)


def save(path,state):
    import torch
    with Path(path).open('xb') as f:torch.save(state,f);f.flush();os.fsync(f.fileno())


def copy_saved(path):
    setup.resources();destination=BACKUP/path.name
    if destination.exists():raise ValueError('Backup already exists')
    if setup.parent.tree_bytes(setup.parent.BACKUP_ROOT)+path.stat().st_size>27917287424:raise ValueError('Backup cap')
    shutil.copyfile(path,destination)
    if sha256(destination)!=sha256(path):raise ValueError('Independent backup mismatch')


def original_worker():
    import torch
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_varied_region_session_v1 import VariedSession
    check();torch.set_num_threads(2);torch.cuda.reset_peak_memory_stats()
    plan=setup.read(setup.SETUP/'cuda-plan.json');p=setup.varied.provider()
    p.control['train']=plan['train'];p.control['qualification_only']=True;p.pin=digest(canonical(p.control))
    c=plan['config'];s=VariedSession(Session(c['session'],p.control,device='cuda',initialization=c['initialization']))
    rows=[];start=time.monotonic();last_check=start
    for _ in range(plan['updates']):
        if time.monotonic()-last_check>30:setup.resources();last_check=time.monotonic()
        t=time.monotonic();row=s.update(p);row['update_seconds']=time.monotonic()-t;rows.append(row)
        with (OUT/'reference-updates.jsonl').open('ab') as f:f.write(canonical(row));f.flush()
    save(OUT/'reference-final.pt',s.state())
    setup.write(OUT/'reference.json',dict(updates=rows,seconds=time.monotonic()-start,
        peak_gpu_reserved=torch.cuda.max_memory_reserved(),nonpromotable=True))


def candidate_worker():
    import torch
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from src.training.segmenter_pancreas_region_executor_v1 import execute
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    check();torch.set_num_threads(2);torch.cuda.reset_peak_memory_stats()
    plan=setup.read(setup.SETUP/'cuda-plan.json');reference=setup.read(OUT/'reference.json');p=provider();c=plan['config']
    s=FastVariedSession(Session(c['session'],p.control,device='cuda',initialization=c['initialization']))
    rows=[]
    class Measured:
        def __getattr__(self,k):return getattr(s,k)
        def update(self,provider):
            t=time.monotonic();row=s.update(provider);row['update_seconds']=time.monotonic()-t
            expected=reference['updates'][len(rows)]
            if any(row[k]!=expected[k] for k in ('member_id','batch_sha256','input_view','learning_rate')):
                raise ValueError('Actual optimizer input/sequence mismatch')
            rows.append(row)
            if s.step==plan['updates']-1:
                save(OUT/'saved.pt',s.state());copy_saved(OUT/'saved.pt')
            return row
    try:
        last_check=[0.]
        def tick():
            if time.monotonic()-last_check[0]>30:setup.resources();last_check[0]=time.monotonic()
        result=execute(Measured(),p,OUT/'execution',validate_every=plan['updates'],checkpoint_every=5,
            tick=tick,validation_names=plan['validation'])
        save(OUT/'expected.pt',s.state());maxima=[]
        original=torch.load(OUT/'reference-final.pt',map_location='cpu',weights_only=True);current=s.state()
        for key in ('step','exposure','model','optimizer','cpu_rng','cuda_rng','mps_rng'):
            compare(current['raw'][key],original['raw'][key],maxima=maxima)
        compare(current['focused'],original['focused'],exact=True)
        expected_kinds={'reserved_cover','component_jitter','region_context'}
        if {r['input_view']['window']['kind'] for r in rows}!=expected_kinds or rows[-1]['input_view']['window']['kind']!='component_jitter':
            raise ValueError('Actual path coverage incomplete')
        import statistics
        indices=[i for i in range(6,len(rows)) if i%5!=0]
        old=statistics.mean(reference['updates'][i]['update_seconds'] for i in indices)
        new=statistics.mean(rows[i]['update_seconds'] for i in indices);speedup=old/new
        setup.write(OUT/'producer.json',dict(updates=rows,result=result,all_batch_hashes_and_traces_exact=True,
            numerical_state_close=True,max_state_difference=max(maxima,default=0),nonpromotable=True,
            reference_mean_seconds=old,candidate_mean_seconds=new,speedup=speedup,
            timed_steps=[rows[i]['step'] for i in indices],timing_scope='After six warmups; checkpoint-boundary successors excluded; twelve difficult train cases; warm/unknown OS cache',
            speed_gate_passed=speedup>=setup.read(SPEC)['qualification']['minimum_measured_mean_update_speedup'],
            peak_gpu_reserved=torch.cuda.max_memory_reserved(),backup_sha256=sha256(BACKUP/'saved.pt')))
        if speedup<setup.read(SPEC)['qualification']['minimum_measured_mean_update_speedup']:
            raise ValueError('Measured speed improvement below engineering gate; investigate')
    finally:p.close()


def cold_worker():
    import torch
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    check();torch.set_num_threads(2);torch.cuda.reset_peak_memory_stats();p=provider()
    try:
        saved=torch.load(BACKUP/'saved.pt',map_location='cpu',weights_only=True)
        expected=torch.load(OUT/'expected.pt',map_location='cpu',weights_only=True)
        s=FastVariedSession.restore(saved,saved['identity']);compare(s.state(),saved,exact=True)
        row=s.update(p);reference=setup.read(OUT/'producer.json')['updates'][-1]
        if any(row[k]!=reference[k] for k in ('member_id','batch_sha256','input_view','learning_rate')):raise ValueError('Cold input mismatch')
        maxima=[];compare(s.state(),expected,maxima=maxima)
        setup.write(OUT/'cold.json',dict(exact_restore=True,exact_next_input=True,numerical_next_state_close=True,
            max_state_difference=max(maxima,default=0),updates=1,nonpromotable=True,
            peak_gpu_reserved=torch.cuda.max_memory_reserved()))
    finally:p.close()


def stage(name):
    check();log=setup.SETUP/('cuda-'+name+'.log')
    if log.exists():raise ValueError('Stage already started; no retry')
    if name=='reference':
        OUT.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False)
        if OUT.stat().st_dev==BACKUP.stat().st_dev:raise ValueError('Independent backup required')
    else:
        previous='reference' if name=='producer' else 'producer'
        prior=setup.read(setup.SETUP/('cuda-'+previous+'-resources.json'))
        if not prior['workers_reaped'] or not prior.get('success') or prior.get('exit_code')!=0:
            raise ValueError('Previous worker not reaped')
        evidence=setup.read(OUT/('reference.json' if name=='producer' else 'producer.json'))
        if name=='cold' and not evidence['speed_gate_passed']:raise ValueError('Producer speed gate failed')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'),log.open('x') as stream:
        env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_FAST_CUDA='1')
        env.pop('CUDA_VISIBLE_DEVICES',None)
        process=subprocess.Popen([sys.executable,__file__,'--worker',name],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,env=env)
        success=False
        try:
            watch_windows(process,seconds=3600,rss_bytes=12*1024**3,tick=require_ac);success=True
        finally:
            setup.write(setup.SETUP/('cuda-'+name+'-resources.json'),dict(getattr(process,'duration_resources',{}),
                success=success,exit_code=process.returncode))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--stage',choices=['reference','producer','cold'])
    g.add_argument('--worker',choices=['reference','producer','cold']);args=parser.parse_args()
    if args.prepare:preparation()
    elif args.stage:stage(args.stage)
    else:
        if os.environ.get('PROWL_FAST_CUDA')!='1':raise ValueError('Supervisor required')
        {'reference':original_worker,'producer':candidate_worker,'cold':cold_worker}[args.worker]()
