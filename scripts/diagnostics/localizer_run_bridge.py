"""Bounded qualified-input forward check and independent checkpoint recovery drill."""
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
CAP=REPO/'docs/capstone/operations/LOCALIZER-RUN-CAPABILITY-2026-09-28.json'
CAP_PIN='e2651188827877d11888d13e7e0e3555b83b97816c9f10d0db6820ab002d3486'


def sha(data):return hashlib.sha256(data).hexdigest()


def write(dest,name,data):
    with (dest/name).open('x') as f:json.dump(data,f,sort_keys=True,allow_nan=False);f.flush();os.fsync(f.fileno())


def stores(recovery_only=False):
    from src.operations.localizer_run_storage import run_stores
    return run_stores(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,
                      create=True,recovery_only=recovery_only)


def fixture():
    import torch
    y=torch.zeros(1,96,96,96);y[:,32:64,32:64,32:64]=1
    return y*.8+.1,y


def setup_mps():
    import torch
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')!='0' or not torch.backends.mps.is_available():raise RuntimeError('Native MPS required')
    torch.set_num_threads(2);torch.mps.set_per_process_memory_fraction(min(1.,16*1024**3/torch.mps.recommended_max_memory()))


def recover(dest):
    setup_mps()
    import torch
    from src.operations.localizer_backup import restore_backup
    from src.training.localizer_run import restore_payload
    # Explicitly refuse primary-path opens in this fresh process. All expected controls are internal.
    def audit(event,args):
        if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes)):
            name=os.fsdecode(args[0])
            if name.startswith('/Volumes/PROWL-Data'):raise RuntimeError('Primary access forbidden during recovery')
    sys.addaudithook(audit)
    request=json.loads((dest/'recovery-request.json').read_bytes())
    _,backup,restore=stores(recovery_only=True)
    start=time.monotonic();files,ref=restore_backup(backup,restore,request['backup'],request['primary'],request['identity'])
    model=restore_payload(files,request['identity'])
    expected=torch.load(dest/'expected-probe.pt',weights_only=True)
    if sha((dest/'expected-probe.pt').read_bytes())!=request['probe_sha256']:raise ValueError('Probe changed')
    x,y=fixture();actual,_=model.forward_patch(x,y,'probe')
    diff=(actual-expected).abs().max().item()
    if not torch.allclose(actual,expected,rtol=0,atol=1e-5):raise ValueError('Backup reload differs')
    row=model.synthetic_update(x,y)
    write(dest,'recovery.json',dict(state='restore_tested',restore=ref,max_probability_difference=diff,
        resumed_update=row,elapsed_seconds=time.monotonic()-start,primary_reads_forbidden=True,
        backup_receipt_sha256=request['backup']['receipt_sha256']))


def worker(dest):
    setup_mps()
    import importlib.metadata
    import torch
    from src.data.manifest_records import canonical
    from src.training.localizer_run import MPSRun,input_record,bind_item,payload,publish_checkpoint
    from src.operations.localizer_backup import backup_checkpoint
    from src.data.localizer_inputs import open_localizer_dataset
    from scripts.diagnostics.localizer_preprocessing_check import CAP as READ_CAP,CAP_PIN as READ_PIN,RECIPE,RECIPE_PIN
    primary,backup,_=stores()
    started=time.monotonic()
    dataset=open_localizer_dataset(repo=REPO,capability_path=READ_CAP,trusted_capability_sha256=READ_PIN,
        recipe_path=RECIPE,trusted_recipe_sha256=RECIPE_PIN)
    inputs=input_record(dataset);request=json.loads((dest/'request.json').read_bytes())
    environment=dict(python=sys.version,packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()},
        device='mps',precision='float32',fallback='0',workers=0,cache='none',torch_threads=2)
    controls={'inputs.json':canonical(inputs),'source.json':canonical(request['source']),'environment.json':canonical(environment)}
    config=dict(patch_size=[96]*3,seed=42,learning_rate=.003,weight_decay=.00001,max_steps=100)
    identity=dict(schema_version='2.0.0',run_id=dest.name,purpose='prelaunch-verification',training_data='synthetic',device='mps',config=config,
        inputs_sha256=sha(controls['inputs.json']),source_sha256=sha(controls['source.json']),environment_sha256=sha(controls['environment.json']))
    write(dest,'identity.json',identity)
    model=MPSRun(config);initial=[p.detach().cpu().clone() for p in model.model.parameters()];cases=[]
    for index in range(2):
        start=time.monotonic();item=bind_item(dataset,index,identity);load=time.monotonic()-start
        probabilities,trace=model.forward_patch(item['image'],item['label'],dataset.descriptors[index]['study_id'])
        cases.append(dict(study_id=dataset.descriptors[index]['study_id'],shape=list(item['image'].shape),
            load_preprocess_seconds=load,sampling=trace,transform_sha256=item['transform_record']['record_sha256'],
            finite=bool(torch.isfinite(probabilities).all()),real_optimizer_updates=0))
        del item,probabilities
    assert model.step==0 and all(torch.equal(p.detach().cpu(),old) for p,old in zip(model.model.parameters(),initial))
    del initial
    x,y=fixture();rows=[model.synthetic_update(x,y) for _ in range(2)]
    expected,_=model.forward_patch(x,y,'probe')
    with (dest/'expected-probe.pt').open('xb') as stream:torch.save(expected,stream)
    files=payload(model,identity,controls);start=time.monotonic();reference=publish_checkpoint(primary,files,identity)
    primary_seconds=time.monotonic()-start
    cap=json.loads(CAP.read_bytes());start=time.monotonic()
    backup_ref=backup_checkpoint(primary,backup,reference,identity,source_domain=cap['primary_volume_uuid'],destination_domain=cap['backup_volume_uuid'])
    backup_seconds=time.monotonic()-start
    write(dest,'recovery-request.json',dict(identity=identity,primary=reference,backup=backup_ref,
        probe_sha256=sha((dest/'expected-probe.pt').read_bytes())))
    write(dest,'bridge.json',dict(state='passed',cases=cases,synthetic_updates=rows,primary=reference,backup=backup_ref,
        primary_publish_seconds=primary_seconds,backup_publish_seconds=backup_seconds,
        checkpoint_payload_bytes=sum(map(len,files.values())),elapsed_seconds=time.monotonic()-started,
        real_optimizer_updates=0,registry_unchanged=sha((REPO/'configs/local/roots.yaml').read_bytes())==cap['registry_sha256']))


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--worker',type=Path);p.add_argument('--recover',type=Path);a=p.parse_args()
    if a.worker or a.recover:
        dest=a.worker or a.recover
        if dest.parent!=REPO/'outputs/prowl' or dest.resolve(strict=True)!=dest:raise ValueError('Wrong destination')
        return worker(dest) if a.worker else recover(dest)
    if not a.run:p.error('--run required')
    from scripts.diagnostics.localizer_resource_profile import power
    if not power()[0] or shutil.disk_usage(REPO).free<100*1024**3:raise RuntimeError('Power/free space')
    lock=os.open(REPO/'outputs/prowl/.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        dest=REPO/'outputs/prowl'/('localizer-bridge-'+str(uuid4()));dest.mkdir()
        names=['src/training/localizer_run.py','src/training/localizer.py','src/training/localizer_checkpoint.py',
            'src/models/segresnet.py','src/operations/localizer_run_storage.py','src/operations/localizer_backup.py',
            'src/operations/artifact_store.py','src/data/localizer_inputs.py','src/data/localizer_preprocessing.py',
            'scripts/diagnostics/localizer_run_bridge.py']
        write(dest,'request.json',dict(source={n:(REPO/n).read_text() for n in names},capability_sha256=CAP_PIN,
            git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
            source_policy='dirty diagnostic, non-promotable',
            plan=(REPO/'docs/capstone/operations/LOCALIZER-RUN-BRIDGE-PLAN-2026-09-28.md').read_text()))
        print(dest,flush=True);started=time.monotonic();peak=0;results=[]
        for mode in ('worker','recover'):
            reason=None
            with (dest/(mode+'.log')).open('xb') as log:
                proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.localizer_run_bridge','--'+mode,str(dest)],
                    cwd=REPO,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTORCH_ENABLE_MPS_FALLBACK='0'),stdout=log,stderr=subprocess.STDOUT)
                try:
                    while proc.poll() is None:
                        if time.monotonic()-started>600:raise RuntimeError('time_cap')
                        if not power()[0]:raise RuntimeError('AC_lost')
                        rss=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                        if rss.returncode==0 and rss.stdout.strip():peak=max(peak,int(rss.stdout.strip())*1024)
                        elif proc.poll() is None:raise RuntimeError('RSS_monitor_failed')
                        if peak>16*1024**3:raise RuntimeError('RSS_cap')
                        if shutil.disk_usage(REPO).free<100*1024**3:raise RuntimeError('internal_floor')
                        time.sleep(.25)
                    if proc.returncode:raise RuntimeError('child_failed')
                except BaseException as error:reason=str(error);raise
                finally:
                    if proc.poll() is None:
                        proc.terminate()
                        try:proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
                    row=dict(mode=mode,exit_code=proc.returncode,reason=reason,peak_rss=peak,elapsed_seconds=time.monotonic()-started)
                    write(dest,mode+'-supervisor.json',row);results.append(row)
        refs={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in dest.iterdir() if p.is_file()}
        write(dest,'receipt.json',dict(state='complete',files=refs,real_optimizer_updates=0))
        print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()),flush=True)
    finally:os.close(lock)


if __name__=='__main__':main()
