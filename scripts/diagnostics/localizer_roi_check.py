"""D-280 read-only CAP-EXP-004 localization geometry diagnostic."""
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
RUN=REPO/'outputs/prowl/localizer-smoke-274c7bca-dc33-43a6-b025-8bd8aa110737'
PIN='1de1d74746ed79c365beadeee528a60fd6f3b61fc2b3d0e429a96ee8c9d39f2c'
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
    import torch
    from scripts.diagnostics.localizer_run_bridge import setup_mps,CAP,CAP_PIN
    from scripts.diagnostics.localizer_smoke_run import load_dataset,capture
    from src.operations.localizer_run_storage import run_stores
    from src.training.localizer_run import bind_item,restore_payload
    from src.training.localizer_smoke import validate_terminal,checkpoint_files,model_digest
    from src.training.localizer_roi import select_region,evaluate_region
    setup_mps();verify_original();started=time.monotonic();peak=0
    request=json.loads((dest/'request.json').read_bytes())
    if request['original_receipt_sha256']!=PIN:raise ValueError('Wrong request')
    def verify_current():
        source,env=capture()
        if sha(source)!=request['source_sha256'] or sha(env)!=request['environment_sha256']:raise ValueError('Diagnostic source/environment changed')
        if sha((REPO/'docs/capstone/operations/LOCALIZATION-TARGET-2026-09-29.md').read_bytes())!=request['plan_sha256']:raise ValueError('Diagnostic plan changed')
    verify_current()
    identity=json.loads((RUN/'identity.json').read_bytes())
    store,_,_=run_stores(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,create=False)
    ref=json.loads((RUN/'result.json').read_bytes())['terminal_reference']
    files,_=store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],expected_derivation=ref['derivation_sha256'],validate=lambda f:validate_terminal(f,identity))
    session=restore_payload(checkpoint_files(files),identity);session.model.eval();initial=model_digest(session.model)
    if session.step!=300:raise ValueError('Wrong endpoint')
    dataset=load_dataset();expected=json.loads(files['after.json'])['cases'];cases=[]
    def guard():
        nonlocal peak
        torch.mps.synchronize();peak=max(peak,torch.mps.driver_allocated_memory())
        if peak>16*1024**3 or time.monotonic()-started>600:raise RuntimeError('Worker budget exceeded')
    for i in range(2):
        guard();item=bind_item(dataset,i,identity);p=session.predict(item['image']);mask=p.argmax(0).numpy();target=item['label'][0].numpy();policies=[]
        for strategy in ('all','largest'):
            selected,region=select_region(mask,item['transform_record']['processed_affine'],strategy=strategy,margin_mm=10.)
            metrics=evaluate_region(selected,target,region)
            if strategy=='all' and (abs(metrics['dice']-expected[i]['dice'])>1e-8 or metrics['predicted_voxels']!=expected[i]['predicted_foreground']):raise ValueError('Endpoint reproduction mismatch')
            policies.append(dict(region=region,metrics=metrics))
        cases.append(dict(study_id=dataset.descriptors[i]['study_id'],policies=policies));guard()
    if model_digest(session.model)!=initial or session.step!=300:raise ValueError('Read-only model changed')
    verify_original();verify_current()
    put(dest/'result.json',dict(state='complete',original_receipt_sha256=PIN,terminal_reference=ref,optimizer_updates=0,full_volume_passes=2,source_loads=2,weights_unchanged=True,weights_sha256=initial,endpoint_metrics_reproduced=True,cases=cases,peak_boundary_driver_bytes=peak,elapsed_seconds=time.monotonic()-started))


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
        dest=OUTPUT/('localizer-roi-'+str(uuid4()));dest.mkdir();source,env=capture()
        for name,raw in [('source.json',source),('environment.json',env)]:
            with (dest/name).open('xb') as f:f.write(raw)
        plan=REPO/'docs/capstone/operations/LOCALIZATION-TARGET-2026-09-29.md'
        put(dest/'request.json',dict(decision='D-280',original_receipt_sha256=PIN,plan_sha256=sha(plan.read_bytes()),
            source_sha256=sha(source),environment_sha256=sha(env),optimizer_updates_allowed=False))
        print(dest,flush=True);started=time.monotonic();peak=0;reason=None
        with (dest/'worker.log').open('xb') as log:
            proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.localizer_roi_check','--worker',str(dest)],cwd=REPO,
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
