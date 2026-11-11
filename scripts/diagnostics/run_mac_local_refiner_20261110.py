"""Bounded CPU refiner pilot; known-location development evaluation only."""
import argparse
from collections import Counter
import csv
import json
import math
import os
from pathlib import Path
import plistlib
import shutil
from statistics import mean
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.diagnostics.audit_stunet_selected_dice_20261110 import STUDY, admitted_cases, read, sha
from scripts.diagnostics.probe_stunet_mps_inference_20261108_v2 import safety as platform_safety
from scripts.diagnostics.run_stunet_confidence_mac_20261108_v3 import write,tree_bytes
from scripts.diagnostics.screen_stunet_lesion_core_20261110 import core_support
from src.data.segmenter_native_windows_v1 import geometry,orient
from src.data.segmenter_content_v1 import target_content
from src.inference.stunet_margin_screen_20261110 import STRUCTURE,unpack
from src.training.stunet_local_refiner_v1 import Refiner,channels,crop,crop_record,objective,valid_support

import nibabel as nib
import numpy as np
from scipy import ndimage
import torch

BASE=Path('/Volumes/PROWL-Data/PROWL/artifacts')
MANIFEST=BASE/'distillation-mac-20261023/rsuper-training-sources-01'
OUT=BASE/'local-refiner-mac-20261110-a01'
BACKUP=Path.home()/'PROWL-Backups'/OUT.name
LOCAL_AUDIT=Path('/tmp/prowl-dice-audit-20261110.F93Yd2/audit.json')
LOCAL_CORE=Path('/tmp/prowl-core-screen-20261110.ImvTkV/result.json')
AUDIT_PROOF=ROOT/'docs/capstone/evaluation/STUNET-24K-SELECTED-DICE-AUDIT-20261110.json'
CORE_PROOF=ROOT/'docs/capstone/evaluation/STUNET-24K-CONFIDENT-CORE-RESULTS-20261110.json'
POLICY=ROOT/'docs/capstone/weeks/WEEK-06-WORK-PLAN.md'
LABEL='com.prowl.local-refiner-cpu-20261110-a01'
DEADLINE=1794411900  # 2026-11-11 08:45 America/Denver
GIB=1024**3
SIZE=64
STEPS=2400
CASE_VOXELS=120_000_000
CAP=8*3600
SEED=20261110
ERRATA={'PanTS_'+n for n in ('00000044','00001819','00003059','00003548','00005693','00007933','00007947')}


def safety():
    if not os.path.ismount('/Volumes/PROWL-Data') or time.time()>=DEADLINE:
        raise ValueError('External drive or departure cutoff')
    platform_safety()
    if tree_bytes(OUT)>2*GIB or tree_bytes(Path.home()/'PROWL-Backups')>26*GIB:
        raise ValueError('Pilot artifact or retained-backup cap')


def backup(path):
    dest=BACKUP/path.relative_to(OUT)
    dest.parent.mkdir(parents=True,exist_ok=True)
    size=path.stat().st_size
    if dest.parent.stat().st_dev==path.stat().st_dev or tree_bytes(Path.home()/'PROWL-Backups')+size>26*GIB:
        raise ValueError('Independent backup and cap required')
    if shutil.disk_usage(dest.parent).free-size<50_000_000_000:
        raise ValueError('Internal reserve')
    with path.open('rb') as src,dest.open('xb') as out:
        shutil.copyfileobj(src,out);out.flush();os.fsync(out.fileno())
    if sha(path)!=sha(dest):
        raise ValueError('Backup hash mismatch')
    return dest


def pin_check(request):
    if any(sha(p)!=h for p,h in request['pins'].items()):
        raise ValueError('Frozen input, source or protocol changed')


def prepare():
    safety()
    if OUT.exists() or BACKUP.exists():
        raise ValueError('Preserve existing attempt; no retry')
    if sha(LOCAL_AUDIT)!=read(AUDIT_PROOF)['full_local_audit_sha256']:
        raise ValueError('Prior component inventory changed')
    dev, receipts=admitted_cases()
    audit=read(LOCAL_AUDIT)
    incumbent=read(CORE_PROOF)
    if sha(LOCAL_CORE)!=incumbent['full_local_result_sha256']:
        raise ValueError('Verified core comparison rows changed')
    if incumbent['selected']!='tier3_trim4mm_grow1.5mm':
        raise ValueError('Frozen comparator policy changed')
    cases={r['case_id']:r for r in dev}
    groups={'small':[],'medium':[],'empty':[]}
    with (MANIFEST/'manifest.csv').open() as f:
        rows=list(csv.DictReader(f))
    train=[r for r in rows if r['protected_role']=='train']
    if (len(train),len({r['case_id'] for r in train}),len(cases))!=(1333,1333,70):
        raise ValueError('Frozen train/development membership changed')
    if set((MANIFEST/'train.txt').read_text().split())!={r['case_id'] for r in train} or set(cases)!=set((MANIFEST/'development.txt').read_text().split()):
        raise ValueError('Independent split files differ')
    for r in train:
        case=r['case_id']
        if case in cases:
            raise ValueError('Development case in training')
        if case in ERRATA:
            continue  # Pilot excludes all seven corrected cases; never uses obsolete labels.
        path=MANIFEST/'metadata'/(case+'.json')
        m=read(path); g=m['transform']; shape=g['source_shape']; affine=g['source_affine']
        if m['case_id']!=case or math.prod(shape)>CASE_VOXELS:
            continue
        voxel=abs(np.linalg.det(np.asarray(affine)[:3,:3]))
        comps=[(x['component_id'],x['native_voxels']*voxel/1000,x['native_voxels'])
               for x in m['fidelity']['components']]
        group='small' if any(0<v<1 for i,v,n in comps) else 'medium' if any(1<=v<=5 for i,v,n in comps) else 'empty' if not comps else None
        if group is None:
            continue
        if bool(comps)!=(r['target_state']=='positive'):
            raise ValueError('Training target state disagrees with metadata')
        ids=sorted((v,i,n) for i,v,n in comps if (0<v<1 if group=='small' else 1<=v<=5))
        sources={k:dict(path=r[k+'_path'],sha256=m['source_sha256'][k]) for k in ('ct','pancreas','lesion')}
        groups[group].append(dict(case_id=case,group=group,component=ids[0][1] if ids else None,
            component_voxels=ids[0][2] if ids else 0,
            native_affine=affine,native_shape=shape,sources=sources,meta=str(path)))
    rng=np.random.default_rng(SEED)
    selected=[]
    for group,limit in [('small',48),('medium',24),('empty',36)]:
        pool=sorted(groups[group],key=lambda r:r['case_id'])
        selected += [pool[i] for i in rng.choice(len(pool),size=limit,replace=False)]
    digest_sets={key:{x['sources'][key]['sha256'] for x in cases.values()} for key in ('ct',)}
    if any(x['sources']['ct']['sha256'] in digest_sets['ct'] for x in selected):
        raise ValueError('Exact image duplicate crosses split')
    smaller=[]; larger=[]
    for r in audit['cases']:
        for i,c in enumerate(r['components'],1):
            item=(r['case'],i,c['voxels'],c['volume_ml'])
            if c['volume_ml']<1:
                smaller.append(item)
            elif c['volume_ml']<=5 and math.prod(cases[r['case']]['native_shape'])<=CASE_VOXELS:
                larger.append(item)
    targets=smaller+sorted(larger,key=lambda x:abs(x[3]-2.5))[:12]
    if len(smaller)!=12 or len(targets)!=24 or any(math.prod(cases[r[0]]['native_shape'])>CASE_VOXELS for r in targets):
        raise ValueError('Fixed small/medium diagnostic cohort inadmissible')
    chosen={r[0]:cases[r[0]] for r in targets}
    probes=[max((r for r in selected if r['group']==g),key=lambda r:math.prod(r['native_shape'])) for g in groups]
    extra=[Path(__file__),ROOT/'src/training/stunet_local_refiner_v1.py',POLICY,AUDIT_PROOF,CORE_PROOF,LOCAL_AUDIT,LOCAL_CORE,
           MANIFEST/'manifest.csv',MANIFEST/'train.txt',MANIFEST/'development.txt',STUDY/'request.json',STUDY/'result.json',
           ROOT/'scripts/diagnostics/audit_stunet_selected_dice_20261110.py',
           ROOT/'scripts/diagnostics/screen_stunet_lesion_core_20261110.py',
           ROOT/'src/operations/mac_teacher_supervision_v3.py',ROOT/'src/operations/mac_teacher_watch_v3.py',
           ROOT/'src/operations/mac_worker_cleanup_v3.py',ROOT/'tests/test_stunet_local_refiner_v1.py']
    pins={str(p.resolve()):sha(p) for p in extra+[Path(r['meta']) for r in selected]+[STUDY/(k+'.json') for k in chosen]}
    OUT.mkdir()
    core_rows={r['case_id']:r['arms'][incumbent['selected']] for r in read(LOCAL_CORE)['rows']}
    request=dict(schema='prowl.mac-local-refiner-known-location.v1',
        pins=pins, train=selected, probes=probes, dev=chosen, targets=targets,
        comparator={k:{x:core_rows[k][x] for x in ('p','t','hits')} for k in chosen},
        deadline=DEADLINE,steps=STEPS,patch_size=SIZE,seed=SEED, hard_seconds=CAP,
        torch_version=torch.__version__,negative_and_positive_counts=dict(Counter(r['group'] for r in selected)),
        eligible_training_pool_counts={k:len(v) for k,v in groups.items()},
        development_scope='known-location component crops; exposed development, not an autonomous result',
        test_reads=0, excluded_corrected_case_count=len(ERRATA))
    write(OUT/'request.json',request);backup(OUT/'request.json')
    print(json.dumps(dict(request=sha(OUT/'request.json'),train=request['negative_and_positive_counts'],
                          dev_scans=len(chosen),dev_components=len(targets))),flush=True)


def bound(expected):
    path=OUT/'request.json'
    if sha(path)!=expected:
        raise ValueError('Request digest changed')
    r=read(path);pin_check(r)
    if (r['deadline'],r['steps'],r['patch_size'],r['seed'],r['torch_version'])!=(DEADLINE,STEPS,SIZE,SEED,torch.__version__):
        raise ValueError('Run or runtime identity changed')
    return r


def read_case(row):
    safety()
    source={}
    for k,v in row['sources'].items():
        if sha(v['path'])!=v['sha256']:
            raise ValueError('Source digest mismatch')
        source[k]=nib.load(v['path'])
    shape=tuple(row['native_shape']);affine=np.array(row['native_affine'])
    if math.prod(shape)>CASE_VOXELS or any(img.shape!=shape or not np.allclose(img.affine,affine,atol=1e-5,rtol=0) for img in source.values()):
        raise ValueError('Source geometry or memory envelope changed')
    g=geometry(shape,affine)
    lesion,panc=[target_content(source[k].dataobj.get_unscaled(),
       dict(slope=float(source[k].dataobj.slope),intercept=float(source[k].dataobj.inter)))[0] for k in ('lesion','pancreas')]
    labels,n=ndimage.label(lesion,structure=STRUCTURE)
    del lesion
    ct=orient(source['ct'].get_fdata(dtype=np.float32,caching='unchanged'),g)
    return ct,orient(labels,g),orient(panc,g),g,n


def make_patches(row, rng):
    ct,labels,pancreas,g,n=read_case(row)
    a=g['affine'];target=row['component']
    if target is not None:
        if not 1<=target<=n: raise ValueError('Missing admitted training component')
        box=ndimage.find_objects(labels,max_label=n)[target-1]
        center=np.array([(s.start+s.stop-1)//2 for s in box])
        total=int(np.count_nonzero(labels==target))
        if total!=row['component_voxels'] or total<=0: raise ValueError('Training component census changed')
        centers=[center, np.clip(center+rng.integers(-4,5,3),0,np.asarray(ct.shape)-1)]
    else:
        if n: raise ValueError('Nonempty annotation in negative training case')
        coords=np.argwhere(pancreas!=0)
        if not len(coords): raise ValueError('Empty pancreas training reference')
        centers=coords[rng.choice(len(coords),size=2,replace=len(coords)==1)]
        total=0
    patches=[]
    for c in centers:
        window=crop_record(ct.shape,a,c,SIZE)
        valid=valid_support(window)
        raw=crop(ct,window)
        y=(crop(labels,window)==target).astype(np.uint8) if target else np.zeros((SIZE,)*3,np.uint8)
        # Retry only the predefined jitter geometry with the known unjittered
        # center; an otherwise clipped selected lesion fails the whole pilot.
        if y.sum()!=total:
            window=crop_record(ct.shape,a,centers[0],SIZE)
            valid=valid_support(window);raw=crop(ct,window)
            y=(crop(labels,window)==target).astype(np.uint8)
        if y.sum()!=total or not np.isfinite(raw[valid]).all():
            raise ValueError('Training component clipped or CT nonfinite')
        patches.append((channels(raw,valid),y,valid))
    return patches


def tensor(sample):
    x,y,valid=sample
    return torch.from_numpy(x)[None],torch.from_numpy(y)[None,None].float(),torch.from_numpy(valid)[None,None]


def initial():
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.manual_seed(SEED)
    if torch.cuda.is_initialized():
        raise ValueError('CUDA must remain unused')
    model=Refiner().cpu()
    return model,torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-5)


def update(model,opt,sample):
    x,y,valid=tensor(sample)
    opt.zero_grad(set_to_none=True)
    loss=objective(model(x),y,valid)
    if not torch.isfinite(loss): raise ValueError('Nonfinite CPU loss')
    loss.backward();opt.step()
    return float(loss.detach())


def checkpoint(dir_,model,opt,step):
    path=dir_/f'checkpoint-{step:04}.pt'
    with path.open('xb') as f:
        torch.save(dict(model=model.state_dict(),optimizer=opt.state_dict(),step=step),f);f.flush();os.fsync(f.fileno())
    return path,backup(path)


def qualify(dir_,expected):
    r=bound(expected)
    model,opt=initial()
    rng=np.random.default_rng(SEED)
    times=[];examples=[]
    for row in r['probes']:
        start=time.monotonic();examples.extend(make_patches(row,rng));times.append(time.monotonic()-start)
    start=time.monotonic()
    for i in range(16):
        update(model,opt,examples[i%len(examples)])
    step_seconds=(time.monotonic()-start)/16
    p,b=checkpoint(dir_,model,opt,16)
    fixture=tensor(examples[0])[0]
    path=dir_/'fixture.pt'
    with path.open('xb') as f:torch.save(fixture,f)
    with torch.no_grad(): gold=model(fixture)
    received=subprocess.check_output([sys.executable,__file__,'--cold',str(b),str(path)],text=True,timeout=120).strip()
    import hashlib
    if hashlib.sha256(gold.numpy().tobytes()).hexdigest()!=received:
        raise ValueError('Independent cold checkpoint prediction differs')
    projected=2*(max(times)*len(r['train'])+step_seconds*STEPS+60*len(r['dev']))+300
    write(dir_/'qualification.json',dict(request_sha256=expected,train_probe_cases=len(times),updates=16,
        cold_prediction_exact=True,checkpoint_sha256=sha(p),max_prepare_seconds=max(times),
        update_seconds=step_seconds,conservative_seconds=projected))
    backup(dir_/'qualification.json')


def cold(path,fixture):
    import hashlib
    model,opt=initial();state=torch.load(path,map_location='cpu',weights_only=True)
    model.load_state_dict(state['model']);opt.load_state_dict(state['optimizer'])
    if not opt.state: raise ValueError('Missing restored optimizer')
    x=torch.load(fixture,map_location='cpu',weights_only=True)
    with torch.no_grad():print(hashlib.sha256(model(x).numpy().tobytes()).hexdigest())


def evaluate(model,r):
    scores=[]
    for case,row in r['dev'].items():
        ct,labels,pancreas,g,n=read_case(row)
        del pancreas
        receipt=read(STUDY/(case+'.json'))
        artifact=receipt['artifact']
        if sha(artifact['backup'])!=artifact['sha256']:raise ValueError('Incumbent code backup differs')
        with np.load(artifact['backup'],allow_pickle=False) as a:
            code=unpack(a['packed'],[int(x) for x in a['shape']])
        if tuple(row['native_shape'])!=code.shape:raise ValueError('Incumbent native grid mismatch')
        idx,tier,dist,shell=core_support(code,row['native_affine'],trim_levels=[2,3],grow_radii=[0,1.5,3])
        b=np.zeros(code.shape,dtype=np.uint8)
        b.flat[idx[(tier>3)|(dist<=4)]]=1;b.flat[shell[1.5]]=1
        prior=orient(b,g);del code
        hit_ids=labels[prior!=0]
        actual=dict(p=len(hit_ids),t=int(np.count_nonzero(hit_ids)),
                    hits=[int(x) for x in np.unique(hit_ids) if x])
        if actual!=r['comparator'][case]:
            raise ValueError('Incumbent full-native mask replay differs')
        boxes=ndimage.find_objects(labels,max_label=n)
        for k,i,total,vol in r['targets']:
            if k!=case:continue
            box=boxes[i-1]
            center=[(s.start+s.stop-1)//2 for s in box]
            window=crop_record(ct.shape,g['affine'],center,SIZE)
            truth=crop(labels,window)==i
            if int(np.count_nonzero(labels==i))!=total:raise ValueError('Diagnostic component changed')
            valid=valid_support(window)
            x=channels(crop(ct,window),valid)
            with torch.no_grad():pred=(model(torch.from_numpy(x)[None])[0,0].sigmoid().numpy()>=.5)&valid
            control=crop(prior,window)!=0
            def score(mask):
                p,t=int(mask.sum()),int(np.count_nonzero(mask&truth))
                return dict(predicted_voxels=p,true_positive=t,dice=2*t/(total+p))
            scores.append(dict(case_id=case,component=i,volume_ml=vol,target_voxels=total,
                target_in_crop=int(truth.sum()),incumbent=score(control),refiner=score(pred)))
        print(json.dumps(dict(event='diagnostic_case',completed_components=len(scores))),flush=True)
    if len(scores)!=24 or len({(s['case_id'],s['component']) for s in scores})!=24:
        raise ValueError('Diagnostic denominator changed')
    small=[s for s in scores if s['volume_ml']<1]; larger=[s for s in scores if s['volume_ml']>=1]
    if len(small)!=12 or any(x['target_in_crop']!=x['target_voxels'] for x in small):
        raise ValueError('Small diagnostic coverage gate')
    def summarize(xs):
        return {key:dict(dice=mean(s[key]['dice'] for s in xs),
                hits=sum(s[key]['true_positive']>0 for s in xs),
                fp_voxels=sum(s[key]['predicted_voxels']-s[key]['true_positive'] for s in xs))
                for key in ('incumbent','refiner')}
    a,b=summarize(small),summarize(larger)
    return dict(small=a,larger=b,rows=scores,gate=a['refiner']['dice']-a['incumbent']['dice']>=.03 and
                b['refiner']['dice']>=b['incumbent']['dice'])


def train(dir_,expected):
    from mlflow import MlflowClient
    r=bound(expected);rng=np.random.default_rng(SEED);model,opt=initial()
    uri='sqlite:///'+str(OUT/'mlflow.db');c=MlflowClient(tracking_uri=uri)
    e=c.create_experiment('PROWL native local lesion refiner CPU pilot',artifact_location=(OUT/'mlflow-artifacts').as_uri())
    run=c.create_run(e,tags={'mlflow.runName':'Known-location local refiner pilot','prowl.scope':r['development_scope']}).info.run_id
    write(dir_/'tracking.json',dict(uri=uri,run_id=run));backup(dir_/'tracking.json')
    for k,v in dict(steps=STEPS,train_cases=len(r['train']),device='cpu',patch_size=SIZE,request_sha256=expected).items():
        c.log_param(run,k,str(v))
    patches=[]
    for row in r['train']:
        patches.extend(make_patches(row,rng))
        print(json.dumps(dict(event='train_cases_prepared',completed=len(patches)//2)),flush=True)
    with (dir_/'loss.jsonl').open('x') as journal:
        for step in range(1,STEPS+1):
            if (step-1)%len(patches)==0: order=rng.permutation(len(patches))
            loss=update(model,opt,patches[order[(step-1)%len(patches)]])
            journal.write(json.dumps(dict(step=step,loss=loss))+'\n')
            if step==1 or step%25==0:
                journal.flush();c.log_metric(run,'train/loss',loss,step=step)
                print(json.dumps(dict(event='update',step=step,loss=loss)),flush=True)
            if step%600==0: checkpoint(dir_,model,opt,step)
        journal.flush();os.fsync(journal.fileno())
    backup(dir_/'loss.jsonl')
    del patches
    result=evaluate(model.eval(),r)
    for group in ('small','larger'):
        for arm,metrics in result[group].items():
            for k,v in metrics.items():c.log_metric(run,f'{group}/{arm}/{k}',float(v))
    stored=c.get_run(run).data.metrics
    if stored['small/refiner/dice']!=result['small']['refiner']['dice']:raise ValueError('Tracking readback')
    pin_check(r)
    write(dir_/'result.json',dict(result,updates=STEPS,train_cases=len(r['train']),
        device='cpu',diagnostic_components=24,scope=r['development_scope'],request_sha256=expected))
    backup(dir_/'result.json')
    c.set_terminated(run,status='FINISHED')


def finish(dir_,expected):
    import sqlite3
    from mlflow import MlflowClient
    r=bound(expected)
    resources=read(dir_/'resources.json')
    if not resources['success'] or not resources['workers_reaped'] or resources['exit_code']!=0:
        raise ValueError('Unverified worker closeout')
    t=read(dir_/'tracking.json');run_id=t['run_id'];client=MlflowClient(tracking_uri=t['uri'])
    if client.get_run(run_id).info.status!='FINISHED':
        raise ValueError('MLflow closeout status')
    for p in [dir_/'loss.jsonl',dir_/'result.json',*[dir_/f'checkpoint-{step:04}.pt' for step in (600,1200,1800,2400)]]:
        if sha(p)!=sha(BACKUP/p.relative_to(OUT)):
            raise ValueError('Independent artifact differs')
    loss=[json.loads(s) for s in (dir_/'loss.jsonl').read_text().splitlines()]
    if [x['step'] for x in loss]!=list(range(1,STEPS+1)) or not all(math.isfinite(x['loss']) for x in loss):
        raise ValueError('Loss journal count or finiteness')
    observed={x.step:x.value for x in client.get_metric_history(run_id,'train/loss')}
    if observed!={x['step']:x['loss'] for x in loss if x['step']==1 or x['step']%25==0}:
        raise ValueError('Stored loss history differs')
    result=read(dir_/'result.json')
    actual={(row['case_id'],row['component']):row for row in result['rows']}
    if len(actual)!=24 or set(actual)!={(t[0],t[1]) for t in r['targets']}:
        raise ValueError('Diagnostic identity census')
    for k,i,n,v in r['targets']:
        row=actual[k,i]
        if row['target_voxels']!=n or row['volume_ml']!=v:
            raise ValueError('Reference count changed')
        for arm in ('refiner','incumbent'):
            p,tp,d=(row[arm][x] for x in ('predicted_voxels','true_positive','dice'))
            if not 0<=tp<=min(n,p) or not math.isclose(d,2*tp/(n+p),abs_tol=1e-12):
                raise ValueError('Independent Dice calculation differs')
    state=torch.load(BACKUP/dir_.name/'checkpoint-2400.pt',map_location='cpu',weights_only=True)
    if state['step']!=STEPS or not state['optimizer']['state']:
        raise ValueError('Independent final checkpoint cold read failed')
    with sqlite3.connect((OUT/'mlflow.db').as_uri()+'?mode=ro',uri=True) as source, sqlite3.connect(dir_/'mlflow-snapshot.db') as dest:
        source.backup(dest)
        if dest.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
            raise ValueError('Tracking backup integrity check failed')
    backup(dir_/'mlflow-snapshot.db')
    p=dir_/'closeout.json'
    write(p,dict(status='VERIFIED_COMPLETE',request_sha256=expected,mlflow_run_id=run_id,
        result_sha256=sha(dir_/'result.json'),independent_artifacts_match=True,resources=resources,
        training_updates=STEPS,scope=r['development_scope'],policy_deployed=False))
    backup(p)
    print(json.dumps(dict(status='VERIFIED_COMPLETE',small=result['small'],larger=result['larger'],gate=result['gate'])),flush=True)


def supervised(mode,expected):
    from src.operations.mac_teacher_supervision_v3 import run
    safety();bound(expected)
    directory=OUT/mode
    if mode=='science':
        q=read(OUT/'pilot/qualification.json')
        qres=read(OUT/'pilot/resources.json')
        if (q['request_sha256']!=expected or not q['cold_prediction_exact'] or not qres['success'] or
                not qres['workers_reaped'] or sha(OUT/'pilot/qualification.json')!=sha(BACKUP/'pilot/qualification.json') or
                sha(OUT/'pilot/resources.json')!=sha(BACKUP/'pilot/resources.json')):
            raise ValueError('Pilot must finish with independent proof')
    limit=min(CAP,DEADLINE-time.time()-300) if mode=='science' else 600
    if mode=='science' and (limit<q['conservative_seconds'] or
            time.time()-read(OUT/'ready.json')['created_unix']>1200):
        raise ValueError('Science request does not fit admitted budget')
    directory.mkdir()  # atomic one-shot; no existing attempt can be rerun
    args=[sys.executable,__file__,'--worker',mode,expected]
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
        PYTHONDONTWRITEBYTECODE='1')
    success=run(args,directory,seconds=limit,rss_bytes=4*GIB,tick=safety,env=env)
    backup(directory/'resources.json')
    if not success:
        if (directory/'tracking.json').is_file():
            from mlflow import MlflowClient
            t=read(directory/'tracking.json')
            MlflowClient(tracking_uri=t['uri']).set_terminated(t['run_id'],status='FAILED')
        raise ValueError('Owned worker stopped; preserve evidence, no retry')
    if mode=='science':finish(directory,expected)


def install(expected):
    safety();bound(expected)
    q=read(OUT/'pilot/qualification.json');r=read(OUT/'pilot/resources.json')
    if (q['request_sha256']!=expected or not q['cold_prediction_exact'] or not r['success'] or not r['workers_reaped']
            or r['peak_owned_rss_bytes']+640*1024**2>4*GIB
            or q['conservative_seconds']>min(CAP,DEADLINE-time.time()-300)):
        raise ValueError('Preflight failed or too little time before cutoff')
    job=Path.home()/'Library/Application Support/PROWL/owned-jobs'/LABEL
    if job.exists() or (OUT/'science').exists():
        raise ValueError('Existing launch or attempt')
    p=OUT/'ready.json';write(p,dict(request_sha256=expected,created_unix=time.time(),
        qualification_sha256=sha(OUT/'pilot/qualification.json'),effective_cutoff_unix=DEADLINE,
        projected_seconds=q['conservative_seconds'],worker_cap_seconds=CAP,device='cpu'))
    backup(p)
    job.mkdir(parents=True)
    path=job/'job.plist'
    with path.open('xb') as f:
        plistlib.dump(dict(Label=LABEL,RunAtLoad=True,KeepAlive=False,ExitTimeOut=15,ProcessType='Background',
          WorkingDirectory=str(ROOT),StandardOutPath=str(job/'launchd.stdout.log'),
          StandardErrorPath=str(job/'launchd.stderr.log'),
          ProgramArguments=['/usr/bin/caffeinate','-is',sys.executable,__file__,'--launch',expected],
          EnvironmentVariables=dict(HOME=str(Path.home()),PATH='/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
              PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',
              CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')),f)
    print(json.dumps(dict(plist=str(path),ready_sha256=sha(p),estimated_seconds=q['conservative_seconds'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--pilot')
    mode.add_argument('--install')
    mode.add_argument('--launch')
    mode.add_argument('--worker',nargs=2)
    mode.add_argument('--cold',nargs=2)
    a=parser.parse_args()
    if a.prepare: prepare()
    elif a.pilot: supervised('pilot',a.pilot)
    elif a.install: install(a.install)
    elif a.launch:
        if sha(OUT/'ready.json')!=sha(BACKUP/'ready.json') or read(OUT/'ready.json')['request_sha256']!=a.launch:
            raise ValueError('Independent readiness identity changed')
        supervised('science',a.launch)
    elif a.worker:
        m,h=a.worker
        if m not in ('pilot','science'): raise ValueError('Unknown worker role')
        (qualify if m=='pilot' else train)(OUT/m,h)
    else:cold(*a.cold)
