"""Bounded CPU feasibility: learn centers, compare proposals, never fuse masks."""
import argparse
import gc
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
from statistics import mean
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.diagnostics import run_mac_local_refiner_20261110 as refiner
from scripts.diagnostics.audit_stunet_selected_dice_20261110 import admitted_cases,read,sha,STUDY
from scripts.diagnostics.audit_mac_refiner_routing_20261111 import CORE,CORE_PROOF
from scripts.diagnostics.screen_stunet_lesion_core_20261110 import core_support
from src.data.segmenter_content_v1 import target_content
from src.data.segmenter_native_windows_v1 import geometry,orient
from src.inference.stunet_margin_screen_20261110 import STRUCTURE,decode,unpack
from src.training.stunet_candidate_locator_v1 import Locator,STRIDE,center_target,focal_heatmap,nonmaximum,translated
from src.operations.mac_teacher_supervision_v3 import run
import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
import torch

SOURCE=refiner.BASE/'local-refiner-mac-20261110-a02'
OUT=refiner.BASE/'candidate-locator-mac-20261111-a01'
BACKUP=Path.home()/'PROWL-Backups'/OUT.name
CACHE=SOURCE/'cache'
DEADLINE=1794411900  # Nov 11 08:45 Mountain
CAP=3000
STEPS=900
SEED=20261111
GIB=1024**3
TRAIN='fit'
TEST='score'
MATCH_MM=5.
COVERAGE=.9
SEARCH_MM=10.
LIMIT=3
SCHEMA='prowl.mac.candidate-locator-cpu.v1'


def safety():
    refiner.safety()
    if time.time()>=DEADLINE or refiner.tree_bytes(OUT)>512*1024**2:
        raise ValueError('Departure cutoff or locator artifact cap')


def backup(path):
    dest=BACKUP/path.relative_to(OUT)
    dest.parent.mkdir(parents=True,exist_ok=True)
    size=path.stat().st_size
    if (dest.parent.stat().st_dev==path.stat().st_dev or
            shutil.disk_usage(dest.parent).free-size<50_000_000_000 or
            refiner.tree_bytes(Path.home()/'PROWL-Backups')+size>26*GIB):
        raise ValueError('Independent backup or reserve gate')
    with path.open('rb') as src,dest.open('xb') as out:
        shutil.copyfileobj(src,out);out.flush();os.fsync(out.fileno())
    if sha(path)!=sha(dest):raise ValueError('Independent backup differs')


def prepare():
    safety()
    if OUT.exists() or BACKUP.exists():raise ValueError('Existing attempt; no retry')
    oldback=Path.home()/'PROWL-Backups'/SOURCE.name
    close=SOURCE/'closeout.json'
    manifest=CACHE/'manifest.json'
    if read(close)['status']!='VERIFIED_COMPLETE' or any(sha(p)!=sha(oldback/p.relative_to(SOURCE)) for p in (close,manifest)):
        raise ValueError('Source refiner/cache closeout proof mismatch')
    prev=refiner.bound(read(SOURCE/'ready.json')['parent_request_sha256'])
    rows=read(manifest)['records']
    pairs={(r['case_id'],r['slot']) for r in rows}
    if len(rows)!=216 or len(pairs)!=216 or pairs!={(x['case_id'],i) for x in prev['train'] for i in (0,1)}:
        raise ValueError('Cache role or census mismatch')
    dev,receipts=admitted_cases()
    if ({r['case_id'] for r in dev}&{r['case_id'] for r in rows} or
            sha(CORE)!=read(CORE_PROOF)['full_local_result_sha256']):
        raise ValueError('Split or comparison identity mismatch')
    selected=read(CORE)['selected']
    if selected!='tier3_trim4mm_grow1.5mm':raise ValueError('Incumbent changed')
    for r in rows:
        p=CACHE/r['file']
        if p.parent!=CACHE or p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:
            raise ValueError('Training patch changed')
    pins=[Path(__file__),manifest,close,CORE,CORE_PROOF,STUDY/'request.json',
        ROOT/'src/training/stunet_candidate_locator_v1.py',ROOT/'src/operations/mac_teacher_supervision_v3.py',
        ROOT/'src/operations/mac_teacher_watch_v3.py',ROOT/'src/operations/mac_worker_cleanup_v3.py',
        ROOT/'scripts/diagnostics/run_mac_local_refiner_20261110.py',
        ROOT/'scripts/diagnostics/audit_stunet_selected_dice_20261110.py',
        ROOT/'scripts/diagnostics/screen_stunet_lesion_core_20261110.py',
        ROOT/'src/data/segmenter_content_v1.py',ROOT/'src/data/segmenter_native_windows_v1.py',
        ROOT/'src/inference/stunet_margin_screen_20261110.py',
        ROOT/'tests/test_stunet_candidate_locator_v1.py']
    pins.extend(STUDY/(row['case_id']+'.json') for row in dev)
    OUT.mkdir()
    p=OUT/'request.json'
    refiner.write(p,dict(schema=SCHEMA,pins={str(x.resolve()):sha(x) for x in pins},steps=STEPS,
        train_scans=108,training_patches=216,dev=dev,torch=str(torch.__version__),seed=SEED,
        cpu_seconds=CAP,rss_bytes=4*GIB,cutoff_unix=DEADLINE,
        input='one CT channel, no known-location hint',grid_stride=list(STRIDE),search_mm=SEARCH_MM,
        nms_mm=8.,max_proposals=LIMIT,match_mm=MATCH_MM,minimum_crop_fraction=COVERAGE,
        selection='Frozen top1/2/3 plus descriptive matched false-proposal curve; no fusion or independent claim'))
    backup(p)
    print(json.dumps(dict(request_sha256=sha(p),train_scans=108,development=70)),flush=True)


def verify(expected):
    p=OUT/'request.json'
    if sha(p)!=expected or sha(BACKUP/'request.json')!=expected:
        raise ValueError('Locator request identity changed')
    r=read(p);refiner.pin_check(r)
    if (r['schema'],r['steps'],r['seed'],r['torch'])!=(SCHEMA,STEPS,SEED,str(torch.__version__)):
        raise ValueError('Locator recipe or runtime changed')
    return r


def init():
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.manual_seed(SEED)
    model=Locator().cpu()
    return model,torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=1e-5)


def optimize(model,opt,records,rng,steps,log):
    for i in range(steps):
        if i%len(records)==0:order=rng.permutation(len(records))
        p=CACHE/records[order[i%len(records)]]['file']
        with np.load(p,allow_pickle=False) as f:
            x,y,v=translated(f['image'][0],f['target']!=0,f['support']!=0,rng.integers(-8,9,3))
        y,valid=center_target(y,v)
        logits=model(torch.from_numpy(np.ascontiguousarray(x))[None,None])[0,0]
        loss=focal_heatmap(logits,torch.from_numpy(y),torch.from_numpy(valid))
        if not torch.isfinite(loss):raise ValueError('Nonfinite loss')
        opt.zero_grad(set_to_none=True);loss.backward();opt.step()
        log(i+1,float(loss.detach()))


def load_code(case):
    receipt=read(STUDY/(case['case_id']+'.json'))
    artifact=receipt['artifact']
    if sha(artifact['backup'])!=artifact['sha256']:raise ValueError('Saved code changed')
    with np.load(artifact['backup'],allow_pickle=False) as f:
        return unpack(f['packed'],[int(x) for x in f['shape']])


def ct_roi(case,g,low,high):
    binding=case['sources']['ct']
    if sha(binding['path'])!=binding['sha256']:raise ValueError('CT hash changed')
    ct=nib.load(binding['path'])
    if list(ct.shape)!=case['native_shape'] or not np.allclose(ct.affine,case['native_affine'],atol=1e-5,rtol=0):
        raise ValueError('CT affine or shape changed')
    transform=nib.orientations.inv_ornt_aff(np.array(g['forward']),ct.shape)
    corners=np.array([low,high-1])@transform[:3,:3].T+transform[:3,3]
    a,b=corners.min(0).astype(int),corners.max(0).astype(int)+1
    raw=np.asarray(ct.dataobj[tuple(slice(x,y) for x,y in zip(a,b))],dtype=np.float32)
    x=nib.orientations.apply_orientation(raw,np.array(g['forward']))
    if tuple(x.shape)!=tuple(high-low) or not np.isfinite(x).all():raise ValueError('Native ROI geometry')
    return np.ascontiguousarray(np.clip((x+100.)/350.,0.,1.),dtype=np.float32)


def predict(model,case,code,g):
    a=np.array(g['affine']);basis=a[:3,:3]
    pan=np.argwhere(orient(decode(code,0.)==1,g))
    if not len(pan):return [],'predicted_pancreas_missing'
    margin=np.ceil(SEARCH_MM*np.linalg.norm(np.linalg.inv(basis),axis=1)).astype(int)
    lo=np.maximum(0,pan.min(0)-margin)
    hi=np.minimum(np.array(g['shape']),pan.max(0)+margin+1)
    if np.prod(hi-lo)>12_000_000 or np.any(hi-lo<STRIDE):
        raise ValueError('Locator ROI envelope failed')
    ct=ct_roi(case,g,lo,hi)
    with torch.no_grad():h=model(torch.from_numpy(ct)[None,None])[0,0].sigmoid().numpy()
    if not np.isfinite(h).all():raise ValueError('Nonfinite proposal score')
    maxima=np.argwhere(h==ndimage.maximum_filter(h,size=3))
    coords=lo+np.minimum(maxima*STRIDE+np.array(STRIDE)//2,hi-lo-1)
    take=cKDTree(pan@basis.T).query(coords@basis.T,workers=1)[0]<=SEARCH_MM
    proposals=nonmaximum(coords[take],h[tuple(maxima[take].T)],a,limit=LIMIT)
    return [dict(center=p,score=s) for p,s in proposals],None


def baseline(case,code,g,expected):
    i,tier,d,shell=core_support(code,case['native_affine'],trim_levels=[2,3],grow_radii=[0,1.5,3])
    mask=np.zeros(code.shape,dtype=bool)
    mask.flat[i[(tier>3)|(d<=4)]]=True;mask.flat[shell[1.5]]=True
    if int(mask.sum())!=expected['p']:raise ValueError('Incumbent mask size mismatch')
    mask=orient(mask,g)
    labels,n=ndimage.label(mask,structure=STRUCTURE)
    size=np.bincount(labels[mask],minlength=n+1)
    v=abs(np.linalg.det(np.asarray(g['affine'])[:3,:3]))/1000
    boxes=ndimage.find_objects(labels)
    pts=[dict(center=[(s.start+s.stop-1)//2 for s in boxes[j-1]]) for j in range(1,n+1) if size[j]*v<=2.]
    return pts,mask


def truth_scores(case,g,mask,expected,lists):
    source=case['sources']['lesion']
    if sha(source['path'])!=source['sha256']:raise ValueError('Reference changed')
    img=nib.load(source['path'])
    if list(img.shape)!=case['native_shape'] or not np.allclose(img.affine,case['native_affine'],atol=1e-5,rtol=0):
        raise ValueError('Reference geometry')
    y,_=target_content(img.dataobj.get_unscaled(),dict(slope=float(img.dataobj.slope),intercept=float(img.dataobj.inter)))
    labels,n=ndimage.label(y,structure=STRUCTURE)
    del y
    labels=orient(labels,g)
    overlap=labels[mask]
    if int(np.count_nonzero(overlap))!=expected['t'] or [int(i) for i in np.unique(overlap) if i]!=expected['hits']:
        raise ValueError('Incumbent reference overlap mismatch')
    sizes=np.bincount(labels[labels!=0],minlength=n+1)
    basis=np.asarray(g['affine'])[:3,:3]
    volume=abs(np.linalg.det(basis))/1000
    small=[i for i in range(1,n+1) if sizes[i]*volume<1.]
    if n==0:
        return dict(small=small,n=n,incumbent_hits=expected['hits'],
                    arms={arm:[dict(p,edges=[]) for p in points] for arm,points in lists.items()})
    xyz=np.argwhere(labels)
    groups=labels[tuple(xyz.T)]
    trees={i:cKDTree(xyz[groups==i]@basis.T) for i in range(1,n+1)}
    arms={}
    for arm,points in lists.items():
        output=[]
        for p in points:
            center=np.array(p['center'])
            box=tuple(slice(max(0,c-32),min(nv,c+32)) for c,nv in zip(center,labels.shape))
            counts=np.bincount(labels[box].ravel(),minlength=n+1)
            edges=[]
            for i in np.flatnonzero(counts[1:]>=COVERAGE*sizes[1:])+1:
                distance=float(trees[i].query(center@basis.T)[0])
                if distance<=MATCH_MM:edges.append([int(i),distance])
            output.append(dict(p,edges=edges))
        arms[arm]=output
    return dict(small=small,n=n,incumbent_hits=expected['hits'],arms=arms)


def matching(proposals,n):
    if not proposals or not n:return set()
    cost=np.zeros((len(proposals),n+len(proposals)))
    cost[:,:n]=1e6
    for j,p in enumerate(proposals):
        for i,d in p['edges']:cost[j,i-1]=-1000+d
    j,k=linear_sum_assignment(cost)
    return {int(i+1) for a,i in zip(j,k) if i<n and cost[a,i]<0}


def totals(rows,arm,threshold=-1.,limit=None,add_baseline=False):
    matches=[]
    for r in rows:
        p=[x for x in r['arms'][arm] if x.get('score',1)>=threshold][:limit]
        if add_baseline:p=r['arms']['baseline']+p
        hit=matching(p,r['n'])
        matches.append((r,hit,len(p)-len(hit)))
    return dict(matched=sum(len(x) for _,x,_ in matches),
        small_hits=sum(len(set(r['small'])&hit) for r,hit,_ in matches),
        newly_located_small=sum(len(set(r['small'])&hit-set(r['incumbent_hits'])) for r,hit,_ in matches),
        false_proposals=sum(fp for _,_,fp in matches),
        empty_scans_with_proposals=sum(bool(fp) and r['n']==0 for r,_,fp in matches))


def summarize(rows):
    if (len(rows),sum(r['n'] for r in rows),sum(len(r['small']) for r in rows),
           sum(r['n']>0 for r in rows))!=(70,45,12,36):
        raise ValueError('Fixed development census mismatch')
    base=totals(rows,'baseline')
    ladder={str(k):totals(rows,'locator',limit=k) for k in (1,2,3)}
    scores=sorted({p['score'] for r in rows for p in r['arms']['locator']},reverse=True)
    curve=[dict(totals(rows,'locator',threshold=s),threshold=s) for s in scores]
    eligible=[x for x in curve if x['false_proposals']<=base['false_proposals']]
    best=max(eligible,key=lambda r:(r['small_hits'],r['matched'],-r['false_proposals'])) if eligible else None
    return dict(baseline=base,fixed_top_k=ladder,exploratory_at_baseline_false_proposals=best,
                matched_curve=curve,gate=bool(best and best['small_hits']>base['small_hits'] and
                                              best['newly_located_small']>0))


def stage(mode,expected):
    r=verify(expected);safety();d=OUT/mode
    model,opt=init()
    patches=read(CACHE/'manifest.json')['records']
    rng=np.random.default_rng(SEED)
    if mode=='pilot':
        start=time.monotonic();optimize(model,opt,patches,rng,24,lambda *x:None)
        update=(time.monotonic()-start)/24
        times=[];counts=[]
        for case in sorted(r['dev'],key=lambda x:math.prod(x['native_shape']),reverse=True)[:2]:
            start=time.monotonic()
            code=load_code(case)
            points,reason=predict(model.eval(),case,code,geometry(code.shape,case['native_affine']))
            times.append(time.monotonic()-start);counts.append(len(points))
            del code;gc.collect()
        if not sum(counts):raise ValueError('Pilot produced no candidate from either scan')
        q=dict(steps=24,seconds_per_update=update,seconds_per_largest_proposal=max(times),
               projected_seconds=2*(update*STEPS+max(times)*70)+300,request_sha256=expected)
        p=d/'qualification.json';refiner.write(p,q);backup(p)
        return
    from mlflow import MlflowClient
    client=MlflowClient(tracking_uri='sqlite:///'+str(OUT/'mlflow.db'))
    if mode==TRAIN:
        e=client.create_experiment('PROWL CT-only candidate locator CPU pilot')
        t=client.create_run(e,tags={'prowl.scope':'development only','mlflow.runName':'900-step native candidate locator'}).info.run_id
        p=d/'tracking.json';refiner.write(p,dict(run_id=t));backup(p)
        client.log_param(t,'request_sha256',expected)
        journal=d/'loss.jsonl'
        with journal.open('x') as f:
            def log(step,loss):
                f.write(json.dumps(dict(step=step,loss=loss))+'\n')
                if step==1 or step%25==0:
                    f.flush();client.log_metric(t,'train/loss',loss,step=step)
                    print(json.dumps(dict(step=step,loss=loss)),flush=True)
            optimize(model,opt,patches,rng,STEPS,log)
            f.flush();os.fsync(f.fileno())
        backup(journal)
        p=d/'checkpoint.pt'
        with p.open('xb') as f:
            torch.save(dict(model=model.state_dict(),optimizer=opt.state_dict(),steps=STEPS),f);f.flush();os.fsync(f.fileno())
        backup(p)
        return
    checkpoint=BACKUP/TRAIN/'checkpoint.pt'
    if sha(checkpoint)!=sha(OUT/TRAIN/'checkpoint.pt'):raise ValueError('Cold backup mismatch')
    state=torch.load(checkpoint,map_location='cpu',weights_only=True)
    if state['steps']!=STEPS or not state['optimizer']['state']:raise ValueError('Final training state')
    model.load_state_dict(state['model']);model.eval()
    saved=read(CORE);expected_rows={row['case_id']:row['arms'][saved['selected']] for row in saved['rows']}
    rows=[]
    for case in r['dev']:
        safety()
        k=case['case_id']; code=load_code(case)
        g=geometry(code.shape,case['native_affine'])
        points,reason=predict(model,case,code,g)
        controls,mask=baseline(case,code,g,expected_rows[k])
        del code
        # Lock the inputs to scoring before reading annotations.
        lists=dict(locator=points,baseline=controls)
        row=truth_scores(case,g,mask,expected_rows[k],lists)
        rows.append(dict(row,case_id=k,locator_context=reason))
        del mask
        gc.collect()
        print(json.dumps(dict(cases=len(rows))),flush=True)
    result=summarize(rows)
    rid=read(OUT/TRAIN/'tracking.json')['run_id']
    client.log_metric(rid,'top3/small_hits',result['fixed_top_k']['3']['small_hits'])
    client.log_metric(rid,'top3/false_proposals',result['fixed_top_k']['3']['false_proposals'])
    p=d/'result.json';refiner.write(p,dict(result,rows=rows,request_sha256=expected));backup(p)
    client.set_terminated(rid,status='FINISHED')


def supervise(mode,digest):
    safety();verify(digest)
    if mode=='full':
        p=OUT/'pilot/qualification.json';q=read(p)
        if (sha(p)!=sha(BACKUP/'pilot/qualification.json') or q['request_sha256']!=digest or
                not read(OUT/'pilot/resources.json')['success'] or
                q['projected_seconds']>min(CAP,DEADLINE-time.time()-120)):
            raise ValueError('Pilot or bounded time admission failed')
    end=min(time.time()+(300 if mode=='pilot' else CAP),DEADLINE-120)
    for phase in (('pilot',) if mode=='pilot' else (TRAIN,TEST)):
        d=OUT/phase;d.mkdir()
        ok=run([sys.executable,__file__,'--worker',phase,digest],d,seconds=end-time.time(),rss_bytes=4*GIB,
            tick=safety,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',
                                OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
        backup(d/'resources.json')
        if not ok:
            t=OUT/TRAIN/'tracking.json'
            if t.exists():
                from mlflow import MlflowClient
                c=MlflowClient(tracking_uri='sqlite:///'+str(OUT/'mlflow.db'))
                c.set_terminated(read(t)['run_id'],status='FAILED')
            raise ValueError('Owned worker stopped; no retry')
    if mode=='full':
        rid=read(OUT/TRAIN/'tracking.json')['run_id']
        db=OUT/'mlflow-snapshot.db'
        with sqlite3.connect((OUT/'mlflow.db').as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(db) as dst:
            src.backup(dst)
            if dst.execute('pragma integrity_check').fetchone()!=('ok',) or dst.execute(
                'select status from runs where run_uuid=?',(rid,)).fetchone()!=('FINISHED',):
                raise ValueError('Tracking closeout invalid')
        backup(db)
        r=OUT/TEST/'result.json'
        result=read(r)
        if result['request_sha256']!=digest or sha(r)!=sha(BACKUP/TEST/'result.json') or any(
            summarize(result['rows'])[k]!=result[k] for k in ('baseline','fixed_top_k','gate')):
            raise ValueError('Independent proposal reduction mismatch')
        p=OUT/'closeout.json';refiner.write(p,dict(status='VERIFIED_COMPLETE',result_sha256=sha(r),
             mlflow_run_id=rid,request_sha256=digest,gate=result['gate'],device='cpu',no_fusion=True))
        backup(p)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--pilot');g.add_argument('--full');g.add_argument('--worker',nargs=2)
    a=p.parse_args()
    if a.prepare:prepare()
    elif a.pilot:supervise('pilot',a.pilot)
    elif a.full:supervise('full',a.full)
    else:stage(*a.worker)
