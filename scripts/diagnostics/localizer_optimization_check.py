"""D-276 bounded, read-only CAP-EXP-001 checkpoint investigation."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4

REPO=Path(__file__).resolve().parents[2]
RUN=REPO/'outputs/prowl/localizer-smoke-c5f0d7d6-47f6-455b-adb7-e70c63d71bd3'
PIN='a470008bf2bf45cda5f3aaf1de451c64efe3b17687227486d750f232ca26f34a'
OUTPUT=REPO/'outputs/prowl'


def sha(v):return hashlib.sha256(v).hexdigest()
def put(p,v):
    raw=json.dumps(v,sort_keys=True,allow_nan=False).encode()+b'\n'
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())


def verify_original():
    raw=(RUN/'receipt.json').read_bytes()
    if sha(raw)!=PIN:raise ValueError('Changed original receipt')
    for name,row in json.loads(raw)['files'].items():
        if Path(name).name!=name or sha((RUN/name).read_bytes())!=row['sha256']:raise ValueError('Changed original evidence')
    for name,text in json.loads((RUN/'source.json').read_bytes())['files'].items():
        if (REPO/name).read_text()!=text:raise ValueError('Original executing source changed: '+name)


def worker(dest):
    import gc
    import torch
    from scripts.diagnostics.localizer_run_bridge import setup_mps,CAP,CAP_PIN
    from scripts.diagnostics.localizer_smoke_run import load_dataset
    from src.operations.localizer_run_storage import run_stores
    from src.training.localizer_run import bind_item,restore_payload,validate_payload
    from src.training.localizer import patch_batch,foreground_dice
    from src.training.localizer_smoke import probability_metrics
    from src.training.localizer_diagnostics import probability_summary,logit_diagnostics
    setup_mps();verify_original();started=time.monotonic();peak=0
    request=json.loads((dest/'request.json').read_bytes())
    if request['original_receipt_sha256']!=PIN:raise ValueError('Wrong request')
    identity=json.loads((RUN/'identity.json').read_bytes());cfg=identity['config']
    store,_,_=run_stores(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,create=False)
    dataset=load_dataset();items=[bind_item(dataset,i,identity) for i in range(2)]
    original_rows=[json.loads(line) for line in (RUN/'events.jsonl').read_text().splitlines()]
    updates=[r for r in original_rows if r['state']=='update_complete']
    members=[d['study_id'] for d in dataset.descriptors];replay=[];fixed={}
    def guard():
        nonlocal peak
        torch.mps.synchronize();peak=max(peak,torch.mps.driver_allocated_memory())
        if peak>16*1024**3 or time.monotonic()-started>600:raise RuntimeError('Worker budget exceeded')
    for row in updates:
        guard();sid=row['sampling']['member_id'];i=members.index(sid);step=row['sampling']['step']
        x,y,trace=patch_batch(items[i]['image'],items[i]['label'],cfg,step=step,member_id=sid)
        if trace!=row['sampling']:raise ValueError('Crop replay differs')
        n=int(y.sum());replay.append(dict(step=step,study_id=sid,center_class=trace['center_class'],target_voxels=n,
            patch_voxels=y.numel(),target_fraction=n/y.numel(),full_target_coverage=n/int(items[i]['label'].sum())))
        if trace['center_class']==1 and sid not in fixed:fixed[sid]=(x,y,trace)
    put(dest/'crop-replay.json',replay)
    refs=json.loads((RUN/'result.json').read_bytes())['checkpoint_references']
    if [r['step'] for r in refs]!=[0,25,50,75,100] or len(fixed)!=2:raise ValueError('Wrong checkpoint/patch selection')
    before=next(r['metrics'] for r in original_rows if r['state']=='before_evaluation')
    terminal=json.loads((RUN/'result.json').read_bytes())['terminal_reference']
    terminal_path=store.root/sha(terminal['artifact_id'].encode())
    # Terminal metric bytes are covered by its pinned complete member hashes.
    complete=(terminal_path/'complete.json').read_bytes()
    if sha(complete)!=terminal['receipt_sha256']:raise ValueError('Terminal receipt changed')
    after_bytes=(terminal_path/'after.json').read_bytes()
    if sha(after_bytes)!=json.loads(complete)['members']['after.json']['sha256']:raise ValueError('After metrics changed')
    after=json.loads(after_bytes)
    def weights(model):
        h=hashlib.sha256()
        for key,value in model.state_dict().items():h.update(key.encode());h.update(value.detach().cpu().numpy().tobytes())
        return h.hexdigest()
    for ref in refs:
        guard();files,_=store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],
            expected_derivation=ref['derivation_sha256'],validate=lambda f:validate_payload(f,identity))
        session=restore_payload(files,identity);session.model.eval();initial=weights(session.model);cases=[]
        for i,sid in enumerate(members):
            guard();item=items[i];p=session.predict(item['image'])
            metrics=probability_metrics(p,item['label'],item['transform_record']['processed_affine'])
            if ref['step'] in (0,100):
                expected=(before if ref['step']==0 else after)['cases'][i]
                if abs(metrics['loss']-expected['loss'])>1e-5 or abs(metrics['dice']-expected['dice'])>1e-5:raise ValueError('Original metrics not reproduced')
            full=probability_summary(p[1],item['label'][0]);full['argmax_metrics']=metrics
            x,y,trace=fixed[sid]
            with torch.no_grad():logits=session.model(x.to('mps')).cpu()
            patch_p=logits.softmax(1)[:,1];patch=probability_summary(patch_p,y[:,0])
            gradients=logit_diagnostics(logits,y)
            cases.append(dict(study_id=sid,full_volume=full,fixed_patch=dict(sampling=trace,probability=patch,logit_gradients=gradients)))
            del p,logits,patch_p;guard()
        if weights(session.model)!=initial or session.step!=ref['step']:raise ValueError('Read-only model changed')
        row=dict(step=ref['step'],reference=ref,cases=cases,weights_sha256=initial,weights_unchanged=True,
            optimizer_lr=session.optimizer.param_groups[0]['lr'],scheduler_last_epoch=session.scheduler.last_epoch)
        put(dest/('checkpoint-'+str(ref['step'])+'.json'),row);print(json.dumps(dict(state='checkpoint_inspected',step=ref['step'])),flush=True)
        del session,files;gc.collect();torch.mps.empty_cache()
    guard();verify_original()
    put(dest/'result.json',dict(state='complete',original_receipt_sha256=PIN,optimizer_updates=0,
        full_volume_passes=10,fixed_patch_passes=10,replayed_crops=len(replay),source_loads=2,
        original_endpoint_metrics_reproduced=True,peak_boundary_driver_bytes=peak,elapsed_seconds=time.monotonic()-started))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',type=Path);args=parser.parse_args()
    if args.worker:
        if args.worker.parent!=OUTPUT or args.worker.resolve(strict=True)!=args.worker:raise ValueError('Wrong worker destination')
        return worker(args.worker)
    from scripts.diagnostics.localizer_resource_profile import power
    from scripts.diagnostics.localizer_smoke_run import capture
    verify_original()
    if not power()[0] or shutil.disk_usage(REPO).free<100*1024**3:raise RuntimeError('Power/space preflight')
    fd=os.open(OUTPUT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        dest=OUTPUT/('localizer-optimization-'+str(uuid4()));dest.mkdir();source,env=capture()
        for name,raw in [('source.json',source),('environment.json',env)]:
            with (dest/name).open('xb') as f:f.write(raw)
        plan=REPO/'docs/capstone/operations/LOCALIZER-OPTIMIZATION-INVESTIGATION-PLAN-2026-09-28.md'
        put(dest/'request.json',dict(decision='D-276',original_receipt_sha256=PIN,plan_sha256=sha(plan.read_bytes()),
            source_sha256=sha(source),environment_sha256=sha(env),optimizer_updates_allowed=False))
        print(dest,flush=True);started=time.monotonic();peak=0;reason=None
        with (dest/'worker.log').open('xb') as log:
            proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.localizer_optimization_check','--worker',str(dest)],cwd=REPO,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTORCH_ENABLE_MPS_FALLBACK='0'),stdout=log,stderr=subprocess.STDOUT)
            try:
                while proc.poll() is None:
                    if time.monotonic()-started>600 or not power()[0]:raise RuntimeError('Time/power stop')
                    rss=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                    if rss.returncode==0 and rss.stdout.strip():peak=max(peak,int(rss.stdout.strip())*1024)
                    elif proc.poll() is None:raise RuntimeError('RSS monitor failed')
                    if peak>16*1024**3 or shutil.disk_usage(REPO).free<100*1024**3:raise RuntimeError('Memory/space stop')
                    if sum(p.stat().st_size for p in dest.iterdir() if p.is_file())>256*1024**2:raise RuntimeError('Output cap')
                    time.sleep(.25)
                if proc.returncode:raise RuntimeError('Worker failed')
            except BaseException as error:reason=str(error);raise
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
                put(dest/'supervisor.json',dict(exit_code=proc.returncode,stop_reason=reason,peak_worker_rss=peak,elapsed_seconds=time.monotonic()-started))
        put(dest/'receipt.json',dict(state='complete',files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in dest.iterdir() if p.is_file()}))
        print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()),flush=True)
    finally:os.close(fd)


if __name__=='__main__':main()
