"""Use the same qualified CPU recipe with a disk cache and isolated stages."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import plistlib
import shutil
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.diagnostics import run_mac_local_refiner_20261110 as pilot
from src.operations.mac_teacher_supervision_v3 import run
import numpy as np
import torch

OUT=pilot.BASE/'local-refiner-mac-20261110-a02'
BACKUP=Path.home()/'PROWL-Backups'/OUT.name
LABEL='com.prowl.local-refiner-cpu-20261110-a02'
GIB=1024**3
EXTERNAL_RESERVE=GIB
DEADLINE=pilot.DEADLINE
STEPS=pilot.STEPS
BASE_URI='sqlite:///'+str(OUT/'mlflow.db')
RUNTIME=pilot.CAP


def safety():
    pilot.safety()
    if pilot.tree_bytes(OUT)>2*GIB:
        raise ValueError('New artifact cap')
    if not os.path.ismount('/Volumes/PROWL-Data'):
        raise ValueError('Study drive unmounted')


def backup(path):
    dest=BACKUP/path.relative_to(OUT)
    dest.parent.mkdir(parents=True,exist_ok=True)
    if (dest.parent.stat().st_dev==path.stat().st_dev
            or shutil.disk_usage(dest.parent).free-path.stat().st_size<50_000_000_000
            or pilot.tree_bytes(Path.home()/'PROWL-Backups')+path.stat().st_size>26*GIB):
        raise ValueError('Independent backup or reserve gate')
    with path.open('rb') as source,dest.open('xb') as target:
        shutil.copyfileobj(source,target);target.flush();os.fsync(target.fileno())
    if pilot.sha(path)!=pilot.sha(dest):
        raise ValueError('Independent backup mismatch')
    return dest


def verify(expected):
    p=OUT/'ready.json'
    if pilot.sha(p)!=expected or pilot.sha(BACKUP/'ready.json')!=expected:
        raise ValueError('Disk-cache ready identity changed')
    ready=pilot.read(p)
    pilot.pin_check(ready)
    return ready,pilot.bound(ready['parent_request_sha256'])


def install():
    safety()
    if OUT.exists() or BACKUP.exists() or (pilot.OUT/'science').exists():
        raise ValueError('Preserve prior attempts; no duplicates')
    p=pilot.OUT/'request.json'
    q=pilot.OUT/'pilot/qualification.json'
    r=pilot.OUT/'pilot/resources.json'
    expected=pilot.sha(p);qual=pilot.read(q);res=pilot.read(r)
    parent=pilot.bound(expected)
    ckpt=pilot.OUT/'pilot/checkpoint-0016.pt'
    files=[p,q,r,ckpt]
    if any(pilot.sha(x)!=pilot.sha(pilot.BACKUP/x.relative_to(pilot.OUT)) for x in files):
        raise ValueError('Original request or qualification backup differs')
    if (qual['request_sha256']!=expected or qual['checkpoint_sha256']!=pilot.sha(ckpt) or
            not qual['cold_prediction_exact'] or not res['success'] or not res['workers_reaped'] or
            res['peak_owned_rss_bytes']>4*GIB or res['peak_owned_rss_bytes']+640*1024**2<=4*GIB):
        raise ValueError('Expected verified pilot and a failed in-memory projection')
    patch_bytes=len(parent['train'])*2*pilot.SIZE**3*10
    if patch_bytes>=EXTERNAL_RESERVE or shutil.disk_usage(pilot.BASE).free-EXTERNAL_RESERVE<100*GIB:
        raise ValueError('Cache cannot fit above external floor')
    # Allow additional disk I/O and separate process startup.
    estimate=math.ceil(qual['conservative_seconds']*1.2+300)
    if estimate>min(RUNTIME,DEADLINE-time.time()-300):
        raise ValueError('Conservative projected finish crosses the deadline')
    OUT.mkdir()
    ready=OUT/'ready.json'
    dependencies=[ROOT/path for path in (
        'src/data/segmenter_native_windows_v1.py','src/data/segmenter_content_v1.py',
        'src/data/binary_label_policy.py','src/inference/stunet_margin_screen_20261110.py',
        'src/operations/full_training_platform.py',
        'scripts/diagnostics/probe_stunet_mps_inference_20261108_v2.py',
        'scripts/diagnostics/run_stunet_confidence_mac_20261108_v3.py',
    )]
    pilot.write(ready,dict(schema='prowl.mac-local-refiner-disk-cache.v1',
        parent_request_sha256=expected,
        pins={str(x):pilot.sha(x) for x in files+dependencies+[Path(__file__).resolve()]},
        original_in_memory_admission='blocked: measured peak plus patch residency exceeded 4 GiB',
        pilot_peak_owned_rss_bytes=res['peak_owned_rss_bytes'],
        authorized_at='Nov 10 user requested qualified Mac overnight work before departure',
        device='cpu',nominal_patch_bytes=patch_bytes,projected_seconds=estimate,
        cap_seconds=RUNTIME,cutoff_unix=DEADLINE,
        unchanged_science='Same 108 cases, 216 crops, RNG, model, steps, threshold, diagnostic targets and comparator'))
    backup(ready)
    digest=pilot.sha(ready)
    job=Path.home()/'Library/Application Support/PROWL/owned-jobs'/LABEL
    job.mkdir(parents=True)
    path=job/'job.plist'
    with path.open('xb') as f:
        plistlib.dump(dict(Label=LABEL,RunAtLoad=True,KeepAlive=False,ExitTimeOut=15,ProcessType='Background',
           WorkingDirectory=str(Path.home()),StandardOutPath=str(job/'launchd.stdout.log'),
           StandardErrorPath=str(job/'launchd.stderr.log'),
           ProgramArguments=['/usr/bin/caffeinate','-is',sys.executable,__file__,'--launch',digest],
           EnvironmentVariables=dict(HOME=str(Path.home()),PATH='/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
               PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',
               OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')),f)
    print(json.dumps(dict(plist=str(path),ready_sha256=digest,projected_seconds=estimate)),flush=True)


def cache(dir_,r):
    rng=np.random.default_rng(pilot.SEED)
    records=[]
    for row in r['train']:
        safety()
        patches=pilot.make_patches(row,rng)
        for slot,(x,y,v) in enumerate(patches):
            path=dir_/f'patch-{len(records):04d}.npz'
            with path.open('xb') as f:np.savez(f,image=x,target=y,support=v)
            records.append(dict(file=path.name,sha256=pilot.sha(path),case_id=row['case_id'],slot=slot,
                                group=row['group'],lesion_voxels=int(y.sum()),bytes=path.stat().st_size))
        del patches
        print(json.dumps(dict(event='train_case_cached',completed=len(records)//2,total=len(r['train']))),flush=True)
    if len(records)!=216 or sum(x['bytes'] for x in records)>=EXTERNAL_RESERVE:
        raise ValueError('Expected fixed cache size/census')
    pilot.write(dir_/'manifest.json',dict(records=records,rng_state=rng.bit_generator.state))
    backup(dir_/'manifest.json')


def tracking(dir_):
    from mlflow import MlflowClient
    client=MlflowClient(tracking_uri=BASE_URI)
    experiment=client.create_experiment('PROWL native local refiner CPU pilot',artifact_location=(OUT/'mlflow-artifacts').as_uri())
    run_id=client.create_run(experiment,tags={'mlflow.runName':'Known-location local refiner pilot',
        'prowl.scope':'Exposed development diagnostic; no automatic proposals'}).info.run_id
    p=dir_/'tracking.json';pilot.write(p,dict(uri=BASE_URI,run_id=run_id));backup(p)
    return client,run_id


def fit(dir_,r):
    manifest=OUT/'cache/manifest.json'
    if pilot.sha(manifest)!=pilot.sha(BACKUP/'cache/manifest.json'):
        raise ValueError('Patch manifest backup mismatch')
    m=pilot.read(manifest)
    records=m['records']
    if len(records)!=216 or any(pilot.sha(manifest.parent/x['file'])!=x['sha256'] for x in records):
        raise ValueError('Patch cache integrity')
    rng=np.random.default_rng(pilot.SEED);rng.bit_generator.state=m['rng_state']
    model,opt=pilot.initial()
    client,run_id=tracking(dir_)
    for k,v in dict(steps=STEPS,train_cases=len(r['train']),device='cpu',
                    patch_size=pilot.SIZE,cache_manifest_sha256=pilot.sha(manifest)).items():
        client.log_param(run_id,k,str(v))
    journal=dir_/'loss.jsonl'
    with journal.open('x') as f:
        for i in range(STEPS):
            if i%len(records)==0:order=rng.permutation(len(records))
            record=records[order[i%len(records)]]
            with np.load(manifest.parent/record['file'],allow_pickle=False) as patch:
                sample=tuple(patch[k] for k in ('image','target','support'))
            loss=pilot.update(model,opt,sample)
            step=i+1
            f.write(json.dumps(dict(step=step,loss=loss))+'\n')
            if step==1 or step%25==0:
                f.flush();client.log_metric(run_id,'train/loss',loss,step=step)
                print(json.dumps(dict(event='optimizer_update',step=step,loss=loss)),flush=True)
            if step%600==0:
                p=dir_/f'checkpoint-{step:04}.pt'
                with p.open('xb') as ck:
                    torch.save(dict(step=step,model=model.state_dict(),optimizer=opt.state_dict()),ck)
                    ck.flush();os.fsync(ck.fileno())
                backup(p)
        f.flush();os.fsync(f.fileno())
    backup(journal)
    if any(pilot.sha(manifest.parent/x['file'])!=x['sha256'] for x in records):
        raise ValueError('Patch cache changed during fitting')


def score(dir_,r):
    from mlflow import MlflowClient
    c=MlflowClient(tracking_uri=BASE_URI)
    run_id=pilot.read(OUT/'fit/tracking.json')['run_id']
    p=OUT/'fit/checkpoint-2400.pt'; b=BACKUP/'fit/checkpoint-2400.pt'
    if pilot.sha(p)!=pilot.sha(b):
        raise ValueError('Independent final checkpoint mismatch')
    model,opt=pilot.initial()
    checkpoint=torch.load(b,map_location='cpu',weights_only=True)
    if checkpoint['step']!=STEPS: raise ValueError('Checkpoint step')
    model.load_state_dict(checkpoint['model']);opt.load_state_dict(checkpoint['optimizer'])
    if not opt.state:raise ValueError('Optimizer state absent')
    result=pilot.evaluate(model.eval(),r)
    for group in ('small','larger'):
        for arm,metrics in result[group].items():
            for key,value in metrics.items():c.log_metric(run_id,f'{group}/{arm}/{key}',float(value))
    if c.get_run(run_id).data.metrics['small/refiner/dice']!=result['small']['refiner']['dice']:
        raise ValueError('Diagnostic MLflow metric readback')
    p=dir_/'result.json'
    pilot.write(p,dict(result,updates=STEPS,train_cases=len(r['train']),scope=r['development_scope'],
                       device='cpu',diagnostic_components=24,model_deployed=False))
    backup(p)
    c.set_terminated(run_id,status='FINISHED')


def finish(expected):
    from mlflow import MlflowClient
    safety()
    ready,r=verify(expected)
    manifest=pilot.read(OUT/'cache/manifest.json')
    result=pilot.read(OUT/'score/result.json')
    fit_dir=OUT/'fit'
    run_id=pilot.read(fit_dir/'tracking.json')['run_id']
    client=MlflowClient(tracking_uri=BASE_URI)
    if client.get_run(run_id).info.status!='FINISHED':
        raise ValueError('MLflow not finished')
    journal=[json.loads(s) for s in (fit_dir/'loss.jsonl').read_text().splitlines()]
    if ([x['step'] for x in journal]!=list(range(1,STEPS+1)) or
            not all(math.isfinite(x['loss']) for x in journal) or
            {x.step:x.value for x in client.get_metric_history(run_id,'train/loss')}!=
            {x['step']:x['loss'] for x in journal if x['step']==1 or x['step']%25==0}):
        raise ValueError('Journal or MLflow sampled history mismatch')
    targets={(x[0],x[1]):(x[2],x[3]) for x in r['targets']}
    if len(result['rows'])!=24 or {(x['case_id'],x['component']) for x in result['rows']}!=set(targets):
        raise ValueError('Diagnostic denominators changed')
    for row in result['rows']:
        n,vol=targets[row['case_id'],row['component']]
        if (n,vol)!=(row['target_voxels'],row['volume_ml']):raise ValueError('Target binding')
        for arm in ('incumbent','refiner'):
            x=row[arm]; t,p=x['true_positive'],x['predicted_voxels']
            if not 0<=t<=min(n,p) or x['dice']!=2*t/(n+p):raise ValueError('Independent Dice check failed')
    files=[OUT/'cache/manifest.json',fit_dir/'loss.jsonl',OUT/'score/result.json']+[fit_dir/f'checkpoint-{k:04}.pt' for k in (600,1200,1800,2400)]
    files += [OUT/s/'resources.json' for s in ('cache','fit','score')]
    if any(pilot.sha(x)!=pilot.sha(BACKUP/x.relative_to(OUT)) for x in files):
        raise ValueError('Independent results or checkpoint backup changed')
    snapshot=OUT/'mlflow-snapshot.db'
    with sqlite3.connect((OUT/'mlflow.db').as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(snapshot) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('Tracking DB integrity')
    backup(snapshot)
    p=OUT/'closeout.json'
    pilot.write(p,dict(status='VERIFIED_COMPLETE',request_sha256=expected,mlflow_run_id=run_id,updates=STEPS,
        diagnostic_components=24,patches=len(manifest['records']),device='cpu',gate=result['gate'],
        small=result['small'],larger=result['larger'],policy_deployed=False,
        result_sha256=pilot.sha(OUT/'score/result.json'),workers_reaped=True,independent_artifacts_match=True))
    backup(p)
    print(p.read_text(),flush=True)


def launch(expected):
    ready,_=verify(expected);safety()
    deadline=min(time.time()+RUNTIME,DEADLINE-300)
    if deadline-time.time()<ready['projected_seconds']:raise ValueError('Estimated finish exceeds cutoff')
    (OUT/'dispatch.lock').touch(exist_ok=False)
    try:
        for stage in ('cache','fit','score'):
            safety()
            d=OUT/stage;d.mkdir()
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
                     PYTHONDONTWRITEBYTECODE='1')
            passed=run([sys.executable,__file__,'--worker',stage,expected],d,seconds=deadline-time.time(),
                       rss_bytes=4*GIB,tick=safety,env=env)
            backup(d/'resources.json')
            evidence=pilot.read(d/'resources.json')
            if not passed or not evidence['workers_reaped'] or evidence['exit_code']!=0:
                raise ValueError('Owned stage stopped safely: '+stage)
        finish(expected)
    except Exception as error:
        p=OUT/'failure.json'
        pilot.write(p,dict(reason=repr(error),status='STOPPED_NO_RETRY'))
        backup(p)
        t=OUT/'fit/tracking.json'
        if t.is_file():
            from mlflow import MlflowClient
            c=MlflowClient(tracking_uri=BASE_URI);run_id=pilot.read(t)['run_id']
            if c.get_run(run_id).info.status=='RUNNING':c.set_terminated(run_id,status='FAILED')
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--install',action='store_true');mode.add_argument('--launch');mode.add_argument('--worker',nargs=2)
    a=p.parse_args()
    if a.install:install()
    elif a.launch:launch(a.launch)
    else:
        stage,digest=a.worker
        _,r=verify(digest)
        {'cache':cache,'fit':fit,'score':score}[stage](OUT/stage,r)
