"""Train the same locator with fresh, memory-bounded training cache workers."""
import argparse
from collections import Counter
import gc
import re
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.diagnostics import run_mac_candidate_locator_20261111 as old
from scripts.diagnostics import replay_mac_candidate_locator_small_regions_20261111 as eval_path
from scripts.diagnostics import run_mac_search_window_locator_20261111 as initial
from scripts.diagnostics import run_mac_search_window_locator_20261111_v2 as masked
from src.operations.mac_teacher_supervision_v3 import run
from src.training.stunet_locator_search_windows_v1 import SIZE
import numpy as np
import torch

OUT=old.refiner.BASE/'search-window-locator-mac-20261111-a03'
BACKUP=Path.home()/'PROWL-Backups'/OUT.name
PROOF=ROOT/'docs/capstone/operations/LOCAL-CANDIDATE-LOCATOR-MAC-RESULTS-20261111.json'
CAP=4200
GIB=1024**3
DEADLINE=old.DEADLINE
read,sha,write=old.read,old.sha,old.refiner.write
URI='sqlite:///'+str(OUT/'mlflow.db')


def safety():
    old.safety()
    if old.refiner.tree_bytes(OUT)>2*GIB:raise ValueError('Cache/output cap')


def backup(p):
    target=BACKUP/p.relative_to(OUT)
    target.parent.mkdir(parents=True,exist_ok=True)
    size=p.stat().st_size
    if (p.stat().st_dev==target.parent.stat().st_dev or
            old.refiner.tree_bytes(Path.home()/'PROWL-Backups')+size>26*GIB or
            shutil.disk_usage(target.parent).free-size<50_000_000_000):
        raise ValueError('Independent backup or reserve')
    with p.open('rb') as f,target.open('xb') as g:
        shutil.copyfileobj(f,g);g.flush();os.fsync(g.fileno())
    if sha(p)!=sha(target):raise ValueError('Independent backup hash mismatch')


def prepare():
    safety()
    if OUT.exists() or BACKUP.exists():raise ValueError('Preserve old attempt')
    ref=old.refiner.OUT/'request.json'
    fit=old.refiner.bound(sha(ref))
    previous=eval_path.OUT/'request.json'
    q,benchmark=eval_path.verify(sha(previous))
    check=eval_path.OUT/'closeout.json'
    checkpoint=old.BACKUP/'fit/checkpoint.pt'
    if (read(check)['status']!='VERIFIED_COMPLETE' or sha(check)!=sha(eval_path.BACKUP/'closeout.json') or
            sha(checkpoint)!=read(PROOF)['trained_checkpoint_sha256'] or
            read(check)['result_sha256']!=read(PROOF)['result_sha256']):
        raise ValueError('Frozen locator or comparison evidence changed')
    train=fit['train'];dev=benchmark['dev']
    if len(train)!=108 or len(dev)!=70 or {x['case_id'] for x in train}&{x['case_id'] for x in dev}:
        raise ValueError('Train or development role mismatch')
    if {x['sources']['ct']['sha256'] for x in train}&{x['sources']['ct']['sha256'] for x in dev}:
        raise ValueError('Exact image identity overlaps split')
    if shutil.disk_usage(old.refiner.BASE).free-2*GIB<100*GIB:raise ValueError('External reserve')
    prior_pins=[]
    charged=0
    for attempt in (initial,masked):
        paths=[attempt.OUT/name for name in
               ('request.json','pilot/qualification.json','pilot/resources.json','cache/resources.json')]
        if any(sha(p)!=sha(attempt.BACKUP/p.relative_to(attempt.OUT)) for p in paths):
            raise ValueError('Original attempt evidence differs from backup')
        stopped=read(paths[-1])
        if stopped['success'] or not stopped['workers_reaped'] or stopped['surviving_workers']:
            raise ValueError('Original worker cleanup not verified')
        charged+=math.ceil(sum(read(p)['seconds'] for p in paths[-2:]))+60
        prior_pins.extend(paths)
    last=read(prior_pins[-1])
    if last['peak_owned_rss_bytes']<=4*GIB or last['exit_code']!=-15:
        raise ValueError('Expected memory-limit stop')
    previous_log=masked.OUT/'cache/worker.log'
    log=previous_log.read_text().splitlines()
    last_progress=json.loads(log[-1])
    previous_cache={p.name:sha(p) for p in (masked.OUT/'cache').glob('patch-*.npz')}
    if last_progress!={'cached_cases':34,'patches':134} or len(previous_cache)!=134:
        raise ValueError('Original complete prefix differs')
    files=[Path(__file__),Path(initial.__file__),Path(masked.__file__),*prior_pins,previous_log,
           ref,previous,check,checkpoint,PROOF,eval_path.OUT/'score/result.json',
           ROOT/'src/training/stunet_locator_search_windows_v1.py',
           ROOT/'src/training/stunet_locator_search_windows_v2.py',
           ROOT/'src/training/stunet_candidate_locator_v1.py',ROOT/'src/training/stunet_local_refiner_v1.py']
    chunks=cache_ranges(train)
    OUT.mkdir()
    p=OUT/'request.json'
    write(p,dict(pins={str(p.resolve()):sha(p) for p in files},old_request_sha256=sha(previous),
        previous_attempt_charged_seconds=charged,cumulative_seconds=CAP,
        chunks=chunks,previous_cache=previous_cache,
        train=train,train_count=108,dev=dev,seed=old.SEED,updates=old.STEPS,cutoff_unix=DEADLINE,
        windows=dict(native_size=SIZE,training_grid_step=16,positive_offset_voxels=10,
                     hard_negatives_mined_from='frozen previous locator, training reference pancreas search only',
                     max_positive_per_scan=2,max_negative_per_scan=2,minimum_offcenter=72,minimum_mined_negative=36,
                     partial_policy='ignore clipped lesion footprint and adjacent heatmap cells',
                     fallback='one partial-context window with ignored lesion cells if no other window qualifies'),
        comparison='same architecture, seed, optimizer, 900 steps, development route/scoring; change search window and negative sampling',
        approved_scope='bounded CPU training and development proposal scoring only'))
    backup(p);print(json.dumps(dict(request_sha256=sha(p),train=108,dev=70)),flush=True)


def verify(expected):
    p=OUT/'request.json'
    if sha(p)!=expected or sha(BACKUP/'request.json')!=expected:raise ValueError('Request changed')
    r=read(p);old.refiner.pin_check(r)
    if r['chunks']!=cache_ranges(r['train']):raise ValueError('Cache chunk boundaries changed')
    eval_path.verify(r['old_request_sha256'])
    return r


def cache_ranges(rows):
    """Process very large native arrays alone and bound the length of every worker."""
    start=0
    total=0
    ranges=[]
    for index,row in enumerate(rows):
        voxels=math.prod(row['native_shape'])
        if index>start and (index-start>=10 or total+voxels>170_000_000 or voxels>75_000_000):
            ranges.append([start,index])
            start,total=index,0
        total+=voxels
        if voxels>75_000_000:
            ranges.append([start,index+1])
            start,total=index+1,0
    if start<len(rows):
        ranges.append([start,len(rows)])
    return ranges


def cache_chunk(request, digest, number):
    d=OUT/f'cache-{number:02}'
    cache=OUT/'cache'
    low,high=request['chunks'][number]
    rng=np.random.default_rng(old.SEED)
    offset=0
    if number:
        last=f'cache-{number-1:02}/manifest.json'
        if sha(OUT/last)!=sha(BACKUP/last):raise ValueError('Previous cache state differs')
        state=read(OUT/last)
        if state['request_sha256']!=digest or state['high']!=low:raise ValueError('Cache boundary state')
        rng.bit_generator.state=state['rng']
        offset=state['next_patch']

    model,_=old.init()
    checkpoint=old.BACKUP/'fit/checkpoint.pt'
    model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['model'])
    model.eval()
    records=[]
    for index,row in enumerate(request['train'][low:high],start=low+1):
        for slot,(kind,x,y,support) in enumerate(masked.case_windows(row,model,rng)):
            p=cache/f'patch-{offset+len(records):04}.npz'
            with p.open('xb') as f:np.savez(f,image=x,labels=y,support=support)
            digest_patch=sha(p)
            if p.name in request['previous_cache'] and digest_patch!=request['previous_cache'][p.name]:
                raise ValueError('Previously completed patch changed')
            records.append(dict(case_id=row['case_id'],kind=kind,slot=slot,file=p.name,sha256=digest_patch,
                lesion_voxels=int(np.count_nonzero(y)),ignored_lesion_voxels=int(np.count_nonzero(support==2))))
        del x,y,support
        gc.collect()
        print(json.dumps(dict(cached_cases=index,patches=offset+len(records))),flush=True)
    p=d/'manifest.json'
    write(p,dict(low=low,high=high,next_patch=offset+len(records),records=records,
                 rng=rng.bit_generator.state,request_sha256=digest))
    backup(p)


def worker(mode,digest):
    r=verify(digest)
    safety()
    if re.fullmatch(r'cache-[0-9]{2}',mode):
        cache_chunk(r,digest,int(mode[-2:]))
        return
    d=OUT/mode
    model,opt=old.init()
    rng=np.random.default_rng(old.SEED)
    from mlflow import MlflowClient
    c=MlflowClient(tracking_uri=URI)
    if mode=='fit':
        manifest=OUT/'cache/manifest.json'
        if sha(manifest)!=sha(BACKUP/'cache/manifest.json'):raise ValueError('Independent cache manifest')
        records=read(manifest)['records']
        if any(sha(manifest.parent/x['file'])!=x['sha256'] for x in records):raise ValueError('Cache changed')
        exp=c.create_experiment('PROWL search-window candidate locator')
        rid=c.create_run(exp,tags={'mlflow.runName':'Off-center search and mined negatives','prowl.scope':'development pilot'}).info.run_id
        p=d/'tracking.json';write(p,dict(run_id=rid));backup(p)
        c.log_param(rid,'request_sha256',digest)
        c.log_param(rid,'patch_count',len(records))
        journal=d/'loss.jsonl'
        with journal.open('x') as f:
            for i in range(old.STEPS):
                if i%len(records)==0: order=rng.permutation(len(records))
                loss=masked.update(model,opt,records[order[i%len(records)]],rng,manifest.parent);step=i+1
                f.write(json.dumps(dict(step=step,loss=loss))+'\n')
                if step==1 or step%25==0:
                    f.flush();c.log_metric(rid,'train/loss',loss,step=step)
                    print(json.dumps(dict(step=step,loss=loss)),flush=True)
            f.flush();os.fsync(f.fileno())
        backup(journal)
        p=d/'checkpoint.pt'
        with p.open('xb') as f:
            torch.save(dict(model=model.state_dict(),optimizer=opt.state_dict(),steps=old.STEPS),f);f.flush();os.fsync(f.fileno())
        backup(p)
        return
    p=BACKUP/'fit/checkpoint.pt'
    if sha(p)!=sha(OUT/'fit/checkpoint.pt'):raise ValueError('Independent checkpoint')
    state=torch.load(p,map_location='cpu',weights_only=True)
    if state['steps']!=old.STEPS or not state['optimizer']['state']:raise ValueError('Final checkpoint state')
    model.load_state_dict(state['model']);model.eval()
    old_rows=read(eval_path.OUT/'score/result.json')
    core=read(old.CORE);prior={x['case_id']:x['arms'][core['selected']] for x in core['rows']}
    rows=[]
    output=d/'cases';output.mkdir()
    for case in r['dev']:
        safety();k=case['case_id']
        code=old.load_code(case);g=old.geometry(code.shape,case['native_affine'])
        proposals,why,tiles=eval_path.predict(model,case,code,g)
        controls,mask=old.baseline(case,code,g,prior[k])
        del code
        row=old.truth_scores(case,g,mask,prior[k],dict(locator=proposals,baseline=controls))
        row.update(case_id=k,locator_context=why,roi_windows=tiles)
        rows.append(row);write(output/(k+'.json'),row)
        del mask;gc.collect()
        print(json.dumps(dict(cases=len(rows))),flush=True)
    result=old.summarize(rows)
    if result['baseline']!=old_rows['baseline']:raise ValueError('Incumbent changed between runs')
    rid=read(OUT/'fit/tracking.json')['run_id']
    for key,value in result['fixed_top_k']['3'].items():c.log_metric(rid,'top3/'+key,value)
    if c.get_run(rid).data.metrics['top3/small_hits']!=result['fixed_top_k']['3']['small_hits']:
        raise ValueError('Metric readback')
    p=d/'result.json';write(p,dict(result,rows=rows,request_sha256=digest));backup(p)
    c.set_terminated(rid,status='FINISHED')


def supervise(digest):
    request=verify(digest);safety()
    deadline=min(time.time()+request['cumulative_seconds']-request['previous_attempt_charged_seconds'],DEADLINE-120)
    original_pilot=read(masked.OUT/'pilot/qualification.json')
    if original_pilot['projected_seconds']+10*len(request['chunks'])>deadline-time.time():
        raise ValueError('Measured work exceeds remaining compute window')

    def stage(mode):
        d=OUT/mode
        d.mkdir()
        limit=deadline-time.time()
        if limit<=0:raise ValueError('End of authorized compute window')
        passed=run([sys.executable,__file__,'--worker',mode,digest],d,seconds=limit,rss_bytes=4*GIB,tick=safety,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
                     PYTHONDONTWRITEBYTECODE='1'))
        p=d/'resources.json'
        backup(p)
        proof=read(p)
        if not passed or not proof['workers_reaped'] or proof['exit_code']!=0:
            t=OUT/'fit/tracking.json'
            if t.exists():
                from mlflow import MlflowClient
                MlflowClient(tracking_uri=URI).set_terminated(read(t)['run_id'],status='FAILED')
            raise ValueError('Owned stage stopped; preserve evidence: '+mode)

    cache=OUT/'cache'
    cache.mkdir()
    records=[]
    for n,(low,high) in enumerate(request['chunks']):
        mode=f'cache-{n:02}'
        stage(mode)
        manifest=OUT/mode/'manifest.json'
        r=read(manifest)
        if (sha(manifest)!=sha(BACKUP/mode/'manifest.json') or (r['low'],r['high'])!=(low,high)
                or r['next_patch']!=len(records)+len(r['records'])
                or {x['case_id'] for x in r['records']}!={x['case_id'] for x in request['train'][low:high]}):
            raise ValueError('Cache chunk coverage mismatch')
        records.extend(r['records'])
    counts=dict(Counter(x['kind'] for x in records))
    if counts.get('offcenter_positive',0)<72 or counts.get('mined_negative',0)<36:
        raise ValueError('Frozen search-window coverage did not qualify')
    p=cache/'manifest.json'
    write(p,dict(request_sha256=digest,records=records,patch_counts=counts,scans=len(request['train']),
                 identical_prefix_patches=len(request['previous_cache'])))
    backup(p)
    stage('fit')
    stage('score')
    verify(digest)
    p=OUT/'score/result.json';result=read(p)
    if sha(p)!=sha(BACKUP/'score/result.json') or any(
            read(OUT/'score/cases'/(x['case_id']+'.json'))!=x for x in result['rows']):
        raise ValueError('Score evidence differs')
    if any(result[k]!=v for k,v in old.summarize(result['rows']).items()):
        raise ValueError('Independent reduction differs')
    rid=read(OUT/'fit/tracking.json')['run_id'];db=OUT/'mlflow-snapshot.db'
    with sqlite3.connect((OUT/'mlflow.db').as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(db) as dst:
        src.backup(dst)
        if dst.execute('pragma integrity_check').fetchone()!=('ok',) or dst.execute(
           'select status from runs where run_uuid=?',(rid,)).fetchone()!=('FINISHED',):
            raise ValueError('MLflow closeout')
    backup(db)
    f=OUT/'closeout.json';write(f,dict(status='VERIFIED_COMPLETE',request_sha256=digest,
        result_sha256=sha(p),mlflow_run_id=rid,updates=old.STEPS,workers_reaped=True,gate=result['gate'],no_fusion=True));backup(f)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--prepare',action='store_true');m.add_argument('--run');m.add_argument('--worker',nargs=2)
    a=p.parse_args()
    if a.prepare:prepare()
    elif a.run:supervise(a.run)
    else:worker(*a.worker)
