"""Bounded native synthetic readiness and independent recovery, never real CT updates."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from scripts.diagnostics.localizer_context_profile import power, stop_reason, LIMITS
from scripts.diagnostics.localizer_smoke_run import capture, put
from scripts.diagnostics.expanded_localizer_launch import stores
from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require

REPO=Path(__file__).resolve().parents[2]
ROOT=REPO/'outputs/prowl'
PRIMARY='22750B93-2F3F-499D-87F5-902981BFAB59'
BACKUP='542E8B1F-8D50-4783-9250-752DFDC899CD'


def config():
    return dict(schema_version='twomm-adapter-1',patch_size=[144]*3,seed=42,
        learning_rate=.0003,weight_decay=.00001,max_steps=4,loss_id='balanced_ce_dice_v1')


def worker(dest,stage,pin):
    require(dest.parent==ROOT and dest.resolve(strict=True)==dest,'Wrong evidence destination')
    raw=(dest/'invocation.json').read_bytes();require(digest(raw)==pin,'Invocation changed')
    invocation=json.loads(raw)
    source,environment=capture()
    require(digest(source)==invocation['source_sha256'] and digest(environment)==invocation['environment_sha256'],
        'Source/environment drift')
    if stage=='recover':
        def audit(event,args):
            if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
                require(not os.fsdecode(args[0]).startswith('/Volumes/PROWL-Data'),'Primary reads forbidden')
        sys.addaudithook(audit)
    import torch
    from src.training.twomm_session import (Session,synthetic_item,payload,publish_checkpoint,
        validate_payload,restore_payload,weight_digest,POLICY)
    from src.operations.localizer_backup import backup_checkpoint,restore_backup
    torch.set_num_threads(2)
    require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and torch.backends.mps.is_available(),'Native MPS required')
    torch.mps.set_per_process_memory_fraction(min(1.,LIMITS['driver_bytes']/torch.mps.recommended_max_memory()))
    identity=invocation['identity'];started=time.monotonic();memory=[]
    def measured(stage):
        torch.mps.synchronize()
        row=dict(stage=stage,driver_bytes=torch.mps.driver_allocated_memory(),live_bytes=torch.mps.current_allocated_memory())
        require(row['driver_bytes']<=LIMITS['driver_bytes'],'Driver cap');memory.append(row)
    def save_tensor(name,value):
        with (dest/name).open('xb') as stream:torch.save(value,stream);stream.flush();os.fsync(stream.fileno())
    if stage=='produce':
        primary,backup,_=stores()
        for index,store in enumerate((primary,backup)):
            store.quota_bytes=min(store.quota_bytes,invocation['storage_ceilings'][index])
        session=Session(identity);rows=[]
        for _ in range(2):
            start=time.monotonic();row=session.synthetic_update();measured('update');row['seconds']=time.monotonic()-start;rows.append(row)
        before=weight_digest(session);probe,_=session.predict(synthetic_item()['image']);measured('predict')
        require(before==weight_digest(session),'Inference changed weights')
        files=payload(session,identity,{'inputs.json':canonical({'fixture':'internally-generated-v1'}),
            'source.json':source,'environment.json':environment})
        primary_ref=publish_checkpoint(primary,files,identity)
        backup_ref=backup_checkpoint(primary,backup,primary_ref,identity,source_domain=PRIMARY,
                                    destination_domain=BACKUP,validator=validate_payload)
        save_tensor('probe.pt',probe)
        next_row=session.synthetic_update();measured('next-update')
        save_tensor('expected-next.pt',{k:v.detach().cpu() for k,v in session.model.state_dict().items()})
        put(dest/'references.json',canonical(dict(primary=primary_ref,backup=backup_ref,
            probe_sha256=digest((dest/'probe.pt').read_bytes()),next_sha256=digest((dest/'expected-next.pt').read_bytes()),
            weight_sha256=before,next_update=next_row,updates=rows)))
        put(dest/'produce.json',canonical(dict(state='passed',seconds=time.monotonic()-started,memory=memory)))
    else:
        require(digest((dest/'references.json').read_bytes())==invocation['references_sha256'],'Recovery references changed')
        refs=json.loads((dest/'references.json').read_bytes());_,backup,target=stores(recovery_only=True)
        for store in (backup,target):store.quota_bytes=min(store.quota_bytes,invocation['storage_ceilings'][1])
        files,restored_ref=restore_backup(backup,target,refs['backup'],refs['primary'],identity,validator=validate_payload)
        session=restore_payload(files,identity);require(weight_digest(session)==refs['weight_sha256'],'Restored weights differ')
        probe,_=session.predict(synthetic_item()['image']);measured('restored-predict')
        require(digest((dest/'probe.pt').read_bytes())==refs['probe_sha256'],'Probe changed')
        expected=torch.load(dest/'probe.pt',map_location='cpu',weights_only=True)
        difference=float((probe-expected).abs().max());require(difference<=1e-5,'Fresh-process prediction differs')
        next_row=session.synthetic_update();measured('restored-next-update')
        require(next_row['sampling']==refs['next_update']['sampling'],'Next crop differs')
        require(digest((dest/'expected-next.pt').read_bytes())==refs['next_sha256'],'Next weights changed')
        expected=torch.load(dest/'expected-next.pt',map_location='cpu',weights_only=True)
        delta=max(float((v.detach().cpu()-expected[k]).abs().max()) for k,v in session.model.state_dict().items())
        require(delta<=1e-6,'Next-update replay differs')
        put(dest/'recover.json',canonical(dict(state='passed',seconds=time.monotonic()-started,
            primary_reads_forbidden=True,restored=restored_ref,probability_max_difference=difference,
            next_weight_max_difference=delta,next_loss_difference=abs(next_row['loss']-refs['next_update']['loss']),
            memory=memory,completed_step=session.step)))


def supervise(dest,stage,pin):
    start=time.monotonic();peak=0;reason=None
    env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',PYTHONDONTWRITEBYTECODE='1')
    with (dest/(stage+'.log')).open('xb') as log:
        process=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.twomm_session_rehearsal',
            '--worker',str(dest),'--stage',stage,'--pin',pin],cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            next_power=0;ac=True
            while process.poll() is None:
                elapsed=time.monotonic()-start
                if elapsed>=next_power:ac,_=power();next_power=elapsed+10
                observed=subprocess.run(['/bin/ps','-o','rss=','-p',str(process.pid)],capture_output=True,text=True,timeout=5)
                if observed.returncode==0 and observed.stdout.strip():peak=max(peak,int(observed.stdout.strip())*1024)
                elif process.poll() is None:raise RuntimeError('Memory monitor unavailable')
                size=sum(p.stat().st_size for p in dest.iterdir() if p.is_file())
                reason=stop_reason(elapsed,peak,size,shutil.disk_usage(REPO).free,ac)
                require(reason is None,str(reason));time.sleep(.25)
            require(process.returncode==0,'Worker failed')
        except BaseException as error:
            reason=reason or type(error).__name__;raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            put(dest/(stage+'-supervisor.json'),canonical(dict(exit_code=process.returncode,reason=reason,
                peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start)))


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--worker',type=Path)
    p.add_argument('--stage',choices=('produce','recover'));p.add_argument('--pin');a=p.parse_args()
    if a.worker:return worker(a.worker,a.stage,a.pin)
    require(a.run,'Explicit --run required')
    ac,power_text=power();require(ac and shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Power/free floor')
    lock=os.open(ROOT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        from src.training.twomm_session import POLICY
        primary,backup,_=stores();source,environment=capture()
        identity=dict(schema_version='twomm-session-1',run_id='twomm-session-'+str(uuid4()),
            purpose='synthetic-recovery',device='mps',config=config(),sampling_policy=POLICY,
            inputs_sha256=digest(canonical({'fixture':'internally-generated-v1'})),cache_receipt_sha256=digest(b'no-real-cache'),
            source_sha256=digest(source),environment_sha256=digest(environment))
        invocation=dict(identity=identity,source_sha256=digest(source),environment_sha256=digest(environment),
            limits=LIMITS,power=power_text,storage_ceilings=[primary.quota_bytes,backup.quota_bytes],approval='D-301')
        dest=ROOT/identity['run_id'];dest.mkdir();put(dest/'invocation.json',canonical(invocation))
        print(dest,flush=True);supervise(dest,'produce',digest(canonical(invocation)))
        # Preserve the first invocation; separate recovery directory prevents overwriting its identity.
        recovery=ROOT/(identity['run_id']+'-recovery');recovery.mkdir()
        for name in ('references.json','probe.pt','expected-next.pt'):put(recovery/name,(dest/name).read_bytes())
        invocation['references_sha256']=digest((dest/'references.json').read_bytes())
        put(recovery/'invocation.json',canonical(invocation));supervise(recovery,'recover',digest(canonical(invocation)))
        for folder in (dest,recovery):
            inventory={p.name:dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in folder.iterdir() if p.is_file()}
            put(folder/'receipt.json',canonical(dict(state='complete',files=inventory,synthetic_only=True)))
            print(str(folder)+' receipt_sha256='+digest((folder/'receipt.json').read_bytes()),flush=True)
    finally:os.close(lock)

if __name__=='__main__':main()
