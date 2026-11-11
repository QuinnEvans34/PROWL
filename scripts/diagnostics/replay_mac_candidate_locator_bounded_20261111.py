"""Score the already-trained CPU locator without exceeding the original ROI cap."""
import argparse
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
from scripts.diagnostics import run_mac_candidate_locator_20261111 as original
from src.operations.mac_teacher_supervision_v3 import run
from src.training.stunet_candidate_locator_v1 import STRIDE, nonmaximum
from src.data.segmenter_native_windows_v1 import geometry, orient
from src.inference.stunet_margin_screen_20261110 import decode
import numpy as np
import torch
from scipy import ndimage
from scipy.spatial import cKDTree

OUT=original.refiner.BASE/'candidate-locator-mac-20261111-a02'
BACKUP=Path.home()/'PROWL-Backups'/OUT.name
BUDGET=original.CAP
ROI_CAP=12_000_000
GIB=1024**3
read,sha,write=original.read,original.sha,original.refiner.write


def safety():
    original.safety()
    if original.refiner.tree_bytes(OUT)>128*1024**2:
        raise ValueError('Additive score evidence cap')


def backup(path):
    dest=BACKUP/path.relative_to(OUT)
    dest.parent.mkdir(parents=True,exist_ok=True)
    if (dest.parent.stat().st_dev==path.stat().st_dev or
            shutil.disk_usage(dest.parent).free-path.stat().st_size<50_000_000_000 or
            original.refiner.tree_bytes(Path.home()/'PROWL-Backups')+path.stat().st_size>26*GIB):
        raise ValueError('Independent backup or reserve gate')
    with path.open('rb') as src,dest.open('xb') as dst:
        shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
    if sha(path)!=sha(dest):raise ValueError('Independent backup mismatch')


def regions(pan,shape,basis):
    margin=np.ceil(original.SEARCH_MM*np.linalg.norm(np.linalg.inv(basis),axis=1)).astype(int)
    def split(points,depth):
        lo=np.maximum(0,points.min(0)-margin)
        hi=np.minimum(shape,points.max(0)+margin+1)
        if np.any(hi-lo<STRIDE):
            raise ValueError('Insufficient region dimensions')
        if np.prod(hi-lo)<=ROI_CAP:
            yield lo,hi
            return
        if depth>=8 or len(points)<2:raise ValueError('Cannot partition oversized region')
        span=np.ptp(points,axis=0)*np.linalg.norm(basis,axis=0)
        axis=int(np.argmax(span))
        i=len(points)//2
        perm=np.argpartition(points[:,axis],i)
        yield from split(points[perm[:i]],depth+1)
        yield from split(points[perm[i:]],depth+1)
    return list(split(pan,0))


def predict(model,case,code,g):
    a=np.asarray(g['affine']);basis=a[:3,:3]
    pan=np.argwhere(orient(decode(code,0.)==1,g))
    if not len(pan):return [],'predicted_pancreas_missing',0
    boxes=regions(pan,np.asarray(g['shape']),basis)
    # Unchanged forward and score path on every case fitting the original cap.
    if len(boxes)==1:
        p,reason=original.predict(model,case,code,g)
        return p,reason,1
    allowed=cKDTree(pan@basis.T)
    coords=[];scores=[]
    for lo,hi in boxes:
        x=original.ct_roi(case,g,lo,hi)
        with torch.no_grad():h=model(torch.from_numpy(x)[None,None])[0,0].sigmoid().numpy()
        if not np.isfinite(h).all():raise ValueError('Nonfinite tile score')
        peaks=np.argwhere(h==ndimage.maximum_filter(h,size=3))
        points=lo+np.minimum(peaks*STRIDE+np.array(STRIDE)//2,hi-lo-1)
        take=allowed.query(points@basis.T,workers=1)[0]<=original.SEARCH_MM
        coords.extend(points[take].tolist());scores.extend(h[tuple(peaks[take].T)].tolist())
    ranked=nonmaximum(coords,scores,a,limit=original.LIMIT)
    return [dict(center=c,score=s) for c,s in ranked],None,len(boxes)


def prepare():
    safety()
    if OUT.exists() or BACKUP.exists():raise ValueError('Existing additive attempt')
    req=original.OUT/'request.json'
    h=sha(req);r=original.verify(h)
    ck=original.OUT/'fit/checkpoint.pt'
    cold=original.BACKUP/'fit/checkpoint.pt'
    stopped=original.OUT/'score/resources.json'
    first=read(stopped)
    tracking=original.OUT/'fit/tracking.json'
    stage=['pilot','fit','score']
    receipts=[original.OUT/k/'resources.json' for k in stage]
    if (sha(ck)!=sha(cold) or any(sha(p)!=sha(original.BACKUP/p.relative_to(original.OUT)) for p in receipts) or
            first['success'] or not first['workers_reaped'] or
            'Locator ROI envelope failed' not in (original.OUT/'score/worker.log').read_text()):
        raise ValueError('Expected stopped scoring and exact trained backup')
    rid=read(tracking)['run_id']
    with sqlite3.connect((original.OUT/'mlflow.db').as_uri()+'?mode=ro',uri=True) as c:
        if c.execute('select status from runs where run_uuid=?',(rid,)).fetchone()!=('FAILED',):
            raise ValueError('Preserve failed prior run')
    # Charge conservatively for all prior measured work plus startup overhead.
    remaining=BUDGET-math.ceil(sum(read(p)['seconds'] for p in receipts))-120
    if min(remaining,original.DEADLINE-time.time()-120)<600:raise ValueError('Original budget not available')
    OUT.mkdir()
    p=OUT/'request.json'
    pins=[Path(__file__).resolve(),req,ck,cold,tracking,*receipts,
          original.OUT/'score/worker.log',original.OUT/'pilot/qualification.json']
    write(p,dict(pins={str(p):sha(p) for p in pins},first_request_sha256=h,
        failed_run_id=rid,checkpoint_sha256=sha(ck),remaining_seconds=remaining,
        maximum_roi_voxels=ROI_CAP,cohort_cases=len(r['dev']),training_updates=0,
        oversized_scan_strategy='Median partition of predicted pancreas support along longest physical axis; independent bounded forwards and global world-space suppression. All support retained.'))
    backup(p)
    print(json.dumps(dict(request_sha256=sha(p),remaining_seconds=remaining)),flush=True)


def verify(expected):
    p=OUT/'request.json'
    if sha(p)!=expected or sha(BACKUP/'request.json')!=expected:raise ValueError('Request changed')
    req=read(p);original.refiner.pin_check(req)
    return req,original.verify(req['first_request_sha256'])


def stage(expected):
    req,r=verify(expected)
    model,_=original.init()
    cold=original.BACKUP/'fit/checkpoint.pt'
    if sha(cold)!=req['checkpoint_sha256']:raise ValueError('Checkpoint identity')
    state=torch.load(cold,map_location='cpu',weights_only=True)
    if state['steps']!=original.STEPS:raise ValueError('Trained checkpoint step')
    model.load_state_dict(state['model']);model.eval()
    from mlflow import MlflowClient
    uri='sqlite:///'+str(OUT/'mlflow.db')
    client=MlflowClient(tracking_uri=uri)
    exp=client.create_experiment('PROWL candidate locator bounded scoring replay')
    rid=client.create_run(exp,tags={'mlflow.runName':'Frozen 900-step locator: bounded ROI scoring only',
       'prowl.previous_fit_run':req['failed_run_id'],'prowl.scope':'development proposal benchmark'}).info.run_id
    d=OUT/'score'
    write(d/'tracking.json',dict(run_id=rid));backup(d/'tracking.json')
    client.log_param(rid,'checkpoint_sha256',req['checkpoint_sha256'])
    client.log_param(rid,'optimizer_updates',0)
    old=read(original.CORE); prior={x['case_id']:x['arms'][old['selected']] for x in old['rows']}
    rows=[]
    for case in r['dev']:
        safety();k=case['case_id']
        code=original.load_code(case)
        g=geometry(code.shape,case['native_affine'])
        p,reason,tiles=predict(model,case,code,g)
        controls,mask=original.baseline(case,code,g,prior[k])
        del code
        result=original.truth_scores(case,g,mask,prior[k],dict(locator=p,baseline=controls))
        rows.append(dict(result,case_id=k,locator_context=reason,roi_windows=tiles))
        del mask;gc.collect()
        print(json.dumps(dict(cases=len(rows),roi_windows=tiles)),flush=True)
    summary=original.summarize(rows)
    for k,v in summary['fixed_top_k']['3'].items():
        client.log_metric(rid,'top3/'+k,v)
    if client.get_run(rid).data.metrics['top3/small_hits']!=summary['fixed_top_k']['3']['small_hits']:
        raise ValueError('Tracking metric readback')
    p=d/'result.json'
    write(p,dict(summary,rows=rows,request_sha256=expected,training_updates=0));backup(p)
    client.set_terminated(rid,status='FINISHED')


def launch(expected):
    req,_=verify(expected);safety()
    d=OUT/'score';d.mkdir()
    limit=min(req['remaining_seconds'],original.DEADLINE-time.time()-120)
    if limit<600:raise ValueError('Original budget too short')
    passed=run([sys.executable,__file__,'--worker',expected],d,seconds=limit,rss_bytes=4*GIB,tick=safety,
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
    resource=d/'resources.json';backup(resource)
    outcome=read(resource)
    rid=read(d/'tracking.json')['run_id'] if (d/'tracking.json').exists() else None
    if not passed or not outcome['workers_reaped'] or outcome['exit_code']!=0:
        if rid:
            from mlflow import MlflowClient
            MlflowClient(tracking_uri='sqlite:///'+str(OUT/'mlflow.db')).set_terminated(rid,status='FAILED')
        raise ValueError('Owned worker stopped; preserve attempts')
    p=d/'result.json';results=read(p)
    if (results['request_sha256']!=expected or sha(p)!=sha(BACKUP/'score/result.json') or
        any(v!=results[k] for k,v in original.summarize(results['rows']).items())):
        raise ValueError('Independent score reduction mismatch')
    db=OUT/'mlflow-snapshot.db'
    with sqlite3.connect((OUT/'mlflow.db').as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(db) as dst:
        src.backup(dst)
        if dst.execute('pragma integrity_check').fetchone()!=('ok',) or dst.execute(
            'select status from runs where run_uuid=?',(rid,)).fetchone()!=('FINISHED',):
            raise ValueError('MLflow closeout')
    backup(db)
    close=OUT/'closeout.json'
    write(close,dict(status='VERIFIED_COMPLETE',request_sha256=expected,result_sha256=sha(p),
         score_mlflow_run_id=rid,failed_fit_and_score_run_id=req['failed_run_id'],
         trained_checkpoint_sha256=req['checkpoint_sha256'],device='cpu',gate=results['gate'],
         workers_reaped=True,training_updates=0,no_fusion=True))
    backup(close)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--prepare',action='store_true');m.add_argument('--launch');m.add_argument('--worker')
    a=p.parse_args()
    if a.prepare:prepare()
    elif a.launch:launch(a.launch)
    else:stage(a.worker)
