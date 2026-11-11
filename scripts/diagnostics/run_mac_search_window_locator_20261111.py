"""Matched locator pilot with off-center search crops and mined training negatives."""
import argparse
from collections import Counter
import gc
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
from src.operations.mac_teacher_supervision_v3 import run
from src.training.stunet_candidate_locator_v1 import STRIDE,center_target,focal_heatmap,nonmaximum,translated
from src.training.stunet_local_refiner_v1 import crop,crop_record,valid_support
from src.training.stunet_locator_search_windows_v1 import complete_components,offcenter_order,search_grid,SIZE
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import torch

OUT=old.refiner.BASE/'search-window-locator-mac-20261111-a01'
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
    files=[Path(__file__),ref,previous,check,checkpoint,PROOF,eval_path.OUT/'score/result.json',
           ROOT/'src/training/stunet_locator_search_windows_v1.py',
           ROOT/'src/training/stunet_candidate_locator_v1.py',ROOT/'src/training/stunet_local_refiner_v1.py',
           ROOT/'tests/test_stunet_locator_search_windows_v1.py']
    OUT.mkdir()
    p=OUT/'request.json'
    write(p,dict(pins={str(p.resolve()):sha(p) for p in files},old_request_sha256=sha(previous),
        train=train,train_count=108,dev=dev,seed=old.SEED,updates=old.STEPS,cutoff_unix=DEADLINE,
        windows=dict(native_size=SIZE,training_grid_step=16,positive_offset_voxels=10,
                     hard_negatives_mined_from='frozen previous locator, training reference pancreas search only',
                     max_positive_per_scan=2,max_negative_per_scan=2,minimum_offcenter=72,minimum_mined_negative=36),
        comparison='same architecture, seed, optimizer, 900 steps, development route/scoring; change search window and negative sampling',
        approved_scope='bounded CPU training and development proposal scoring only'))
    backup(p);print(json.dumps(dict(request_sha256=sha(p),train=108,dev=70)),flush=True)


def verify(expected):
    p=OUT/'request.json'
    if sha(p)!=expected or sha(BACKUP/'request.json')!=expected:raise ValueError('Request changed')
    r=read(p);old.refiner.pin_check(r)
    eval_path.verify(r['old_request_sha256'])
    return r


def mined_centers(model,ct,pan,g,tree):
    a=np.asarray(g['affine']);basis=a[:3,:3]
    boxes=eval_path.regions(pan,np.asarray(g['shape']),basis)
    coords=[];scores=[]
    for lo,hi in boxes:
        x=ct[tuple(slice(l,h) for l,h in zip(lo,hi))]
        x=np.ascontiguousarray(np.clip((x+100.)/350.,0.,1.),dtype=np.float32)
        if not np.isfinite(x).all():raise ValueError('Nonfinite training CT')
        with torch.no_grad():h=model(torch.from_numpy(x)[None,None])[0,0].sigmoid().numpy()
        peaks=np.argwhere(h==ndimage.maximum_filter(h,size=3))
        pos=lo+np.minimum(peaks*STRIDE+np.array(STRIDE)//2,hi-lo-1)
        take=tree.query(pos@basis.T,workers=1)[0]<=old.SEARCH_MM
        coords.extend(pos[take].tolist());scores.extend(h[tuple(peaks[take].T)].tolist())
    return [tuple(p) for p,s in nonmaximum(coords,scores,a,limit=24)]


def case_windows(row,model,rng):
    ct,labels,pancreas,g,n=old.refiner.read_case(row)
    a=np.array(g['affine']);basis=a[:3,:3]
    pan=np.argwhere(pancreas)
    del pancreas
    if not len(pan):raise ValueError('No training anatomy support')
    sizes=np.bincount(labels[labels!=0],minlength=n+1)
    expected=row['component']
    if (expected is None and n) or (expected is not None and
            (not 1<=expected<=n or sizes[expected]!=row['component_voxels'])):
        raise ValueError('Frozen training component census changed')
    tree=cKDTree(pan@basis.T)
    points=np.array(search_grid(pan,ct.shape,step=16))
    grid=[tuple(p) for p in points[tree.query(points@basis.T,workers=1)[0]<=old.SEARCH_MM]]
    if not grid:raise ValueError('No valid training grid centers')
    selected=[]
    used=set()
    def select(centers,kind,count):
        before=len(selected)
        for center in centers:
            if center in used:continue
            window=crop_record(ct.shape,a,center,SIZE)
            y=crop(labels,window)
            ids=complete_components(y,sizes)
            if ids is None or (kind=='offcenter_positive' and expected not in ids) or (kind!='offcenter_positive' and ids):
                continue
            if any(i>65535 for i in ids):raise ValueError('Component identifier storage')
            valid=valid_support(window)
            image=crop(ct,window)
            if not np.isfinite(image[valid]).all():raise ValueError('Nonfinite native crop')
            x=np.where(valid,np.clip((image+100.)/350.,0.,1.),0.).astype(np.float32)
            selected.append((kind,x,y.astype(np.uint16),valid))
            used.add(center)
            if len(selected)-before>=count:return
    if expected is not None:
        box=ndimage.find_objects(labels,max_label=n)[expected-1]
        select(offcenter_order(grid,box,rng),'offcenter_positive',2)
    # Take one ordinary search negative even when more mined ones are available.
    select(mined_centers(model,ct,pan,g,tree),'mined_negative',1)
    order=[grid[i] for i in rng.permutation(len(grid))]
    select(order,'grid_negative',1)
    if not selected:raise ValueError('No admissible training window for a frozen scan')
    return selected


def update(model,opt,rec,rng,root):
    with np.load(root/rec['file'],allow_pickle=False) as p:
        x,y,v=translated(p['image'],p['labels'],p['support'],rng.integers(-8,9,3))
    ids=np.unique(y[y>0])
    target,valid=center_target(np.zeros(y.shape,bool),v)
    for i in ids:target=np.maximum(target,center_target(y==i,v)[0])
    logits=model(torch.from_numpy(np.ascontiguousarray(x))[None,None])[0,0]
    loss=focal_heatmap(logits,torch.from_numpy(target),torch.from_numpy(valid))
    if not torch.isfinite(loss):raise ValueError('Nonfinite update')
    opt.zero_grad(set_to_none=True);loss.backward();opt.step()
    return float(loss.detach())


def worker(mode,digest):
    r=verify(digest);safety();d=OUT/mode
    model,opt=old.init()
    rng=np.random.default_rng(old.SEED)
    if mode in ('pilot','cache'):
        checkpoint=old.BACKUP/'fit/checkpoint.pt'
        model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['model']);model.eval()
        probes=[max((r for r in r['train'] if r['group']==name),key=lambda x:math.prod(x['native_shape']))
            for name in ('small','medium','empty')]
        records=[];durations=[]
        for row in (probes if mode=='pilot' else r['train']):
            t=time.monotonic()
            for i,(kind,x,y,v) in enumerate(case_windows(row,model,rng)):
                p=d/f'patch-{len(records):04}.npz'
                with p.open('xb') as f:np.savez(f,image=x,labels=y,support=v)
                records.append(dict(case_id=row['case_id'],kind=kind,slot=i,file=p.name,sha256=sha(p),
                    lesion_voxels=int(np.count_nonzero(y))))
            durations.append(time.monotonic()-t);gc.collect()
            print(json.dumps(dict(cached_cases=len(durations),patches=len(records))),flush=True)
        counts=dict(Counter(x['kind'] for x in records))
        if mode=='pilot':
            torch.manual_seed(old.SEED);trial=old.Locator().cpu()
            opt=torch.optim.AdamW(trial.parameters(),lr=.001,weight_decay=1e-5)
            start=time.monotonic()
            for i in range(12):update(trial,opt,records[i%len(records)],rng,d)
            estimate=2*(max(durations)*108+(time.monotonic()-start)/12*old.STEPS+200)+300
            if not counts.get('offcenter_positive') or not counts.get('mined_negative'):
                raise ValueError('Both novel sample roles must be exercised')
            p=d/'qualification.json'
            write(p,dict(request_sha256=digest,probes=3,update_steps=12,patch_counts=counts,projected_seconds=estimate))
        else:
            if counts.get('offcenter_positive',0)<72 or counts.get('mined_negative',0)<36:
                raise ValueError('Frozen search-window coverage did not qualify')
            p=d/'manifest.json';write(p,dict(request_sha256=digest,records=records,patch_counts=counts,scans=108))
        backup(p);return
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
                loss=update(model,opt,records[order[i%len(records)]],rng,manifest.parent);step=i+1
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
    verify(digest);safety()
    deadline=min(time.time()+CAP,DEADLINE-120)
    for mode in ('pilot','cache','fit','score'):
        d=OUT/mode;d.mkdir()
        limit=min(deadline-time.time(),300) if mode=='pilot' else deadline-time.time()
        if limit<=0:raise ValueError('End of authorized compute window')
        passed=run([sys.executable,__file__,'--worker',mode,digest],d,seconds=limit,rss_bytes=4*GIB,tick=safety,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
                     PYTHONDONTWRITEBYTECODE='1'))
        p=d/'resources.json';backup(p)
        proof=read(p)
        if not passed or not proof['workers_reaped'] or proof['exit_code']!=0:
            t=OUT/'fit/tracking.json'
            if t.exists():
                from mlflow import MlflowClient
                MlflowClient(tracking_uri=URI).set_terminated(read(t)['run_id'],status='FAILED')
            raise ValueError('Owned stage stopped; preserve evidence: '+mode)
        if mode=='pilot':
            q=d/'qualification.json'
            if sha(q)!=sha(BACKUP/'pilot/qualification.json') or read(q)['projected_seconds']>deadline-time.time():
                raise ValueError('Measured work exceeds compute window')
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
