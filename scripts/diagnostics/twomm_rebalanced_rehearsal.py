"""Native synthetic training transaction, variable-volume cache and independent recovery."""
import argparse
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from scripts.diagnostics.localizer_context_profile import power,stop_reason,LIMITS
from scripts.diagnostics.localizer_smoke_run import capture,put
from scripts.diagnostics.expanded_localizer_launch import stores
from scripts.diagnostics.twomm_session_rehearsal import PRIMARY,BACKUP,config
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require

REPO=Path(__file__).resolve().parents[2]
ROOT=REPO/'outputs/prowl'


from scripts.diagnostics.twomm_training_tail_rehearsal import fixture

def controls(binding,cp,source,environment,run_id,parent):
    from src.training.twomm_rebalanced_training import CONTROLS,POLICY,SHUFFLE,PREDICTION,COVERAGE,comparison
    cfg=dict(config(),schema_version='twomm-adapter-5',max_steps=2,parent_steps=parent['step'],learning_rate=.00001,loss_id='class_mean_25_75_ce_dice_v1')
    p=dict(schema_version='twomm-training-plan-5',config=cfg,checkpoint_steps=[0,1,2],
        evaluations=[dict(step=s,roles=['optimizer','evaluator'] if s==2 else ['evaluator']) for s in (0,1,2)],
        total_seconds=600,output_bytes=128*1024**2,reference_policy='fresh_native_references_each_stage_v1',execution_mode='tail_training',
        coverage_guard=dict(COVERAGE,mean_recall_floor=0.,minimum_recall_floor=0.,box_pass_fraction_floor=0.,maximum_mean_recall_drop=1.))
    c={'inputs.json':canonical(binding),'source.json':source,'environment.json':environment,'plan.json':canonical(p),'parent-reference.json':canonical(parent),'comparison.json':canonical(comparison(cfg,real=False))}
    i=dict(schema_version='twomm-training-5',run_id=run_id,purpose='synthetic-training-transaction',device='mps',config=cfg,
        sampling_policy=POLICY,shuffle_policy=SHUFFLE,prediction_policy=PREDICTION,cache_receipt_sha256=cp,**{CONTROLS[n]:digest(v) for n,v in c.items()})
    c['authorization.json']=canonical(dict(allowed=True,operation='synthetic_training_verification',authority='Codex synthetic verification',request_sha256=None,identity=deepcopy(i)))
    i['authorization_sha256']=digest(c['authorization.json']);return i,c


def worker(dest,stage,pin):
    if stage=='baseline':
        from scripts.diagnostics.twomm_training_tail_rehearsal import worker as old_baseline
        return old_baseline(dest,'baseline',pin)
    require(dest.parent==ROOT and dest.resolve(strict=True)==dest,'Wrong evidence path')
    raw=(dest/'invocation.json').read_bytes();require(digest(raw)==pin,'Invocation changed');inv=json.loads(raw)
    source,environment=capture();require(digest(source)==inv['source_sha256'] and
        digest(environment)==inv['environment_sha256'],'Source/environment drift')
    if stage=='recover':
        def audit(event,args):
            if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
                require(not os.fsdecode(args[0]).startswith('/Volumes/PROWL-Data'),'Primary reads forbidden')
        sys.addaudithook(audit)
    import torch
    from src.training.twomm_cache import publish,DiskRoleCache
    from src.training.twomm_rebalanced_training import import_parent,reference,Session,payload,publish_checkpoint,validate_payload,restore_payload,weight_digest
    from src.training.twomm_rebalanced_executor import execute
    from src.training import twomm_rebalanced_evidence as evidence
    from src.operations.localizer_backup import backup_checkpoint,restore_backup
    torch.set_num_threads(2);require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and torch.backends.mps.is_available(),'Native MPS required')
    torch.mps.set_per_process_memory_fraction(min(1.,LIMITS['driver_bytes']/torch.mps.recommended_max_memory()))
    started=time.monotonic();memory=[]
    def guard():
        torch.mps.synchronize();driver=torch.mps.driver_allocated_memory()
        require(driver<=LIMITS['driver_bytes'] and time.monotonic()-started<600,'Worker envelope')
        memory.append(dict(driver_bytes=driver,live_bytes=torch.mps.current_allocated_memory()))
    def tensor(name,value):
        with (dest/name).open('xb') as f:torch.save(value,f);f.flush();os.fsync(f.fileno())
    if stage=='produce':
        ds,b=fixture();path=dest/'cache';bp=digest(canonical(b))
        baseline=json.loads((dest/'baseline-reference.json').read_bytes());cp=baseline['cache_receipt_sha256']
        require(baseline['binding']==b,'Invented parent binding differs');cache=DiskRoleCache(path,cp,b,bp)
        files={n:(dest/'baseline-checkpoint'/n).read_bytes() for n in baseline['files']}
        require({n:digest(v) for n,v in files.items()}==baseline['files'],'Invented parent changed')
        import nibabel as nib,numpy as np
        mask=np.asarray(nib.load(dest/'baseline-attempt/evaluation-0002/evaluator-0000.nii.gz').dataobj)
        prefix=dict(cases=[dict(index=0,study_id=b['roles']['evaluator'][0]['descriptor']['study_id'],shape=list(mask.shape),native_mask_sha256=digest(mask.tobytes()))])
        parent=reference(files,baseline['identity'],dict(scope='invented_local_parent'),prefix)
        identity,c=controls(b,cp,source,environment,inv['run_id'],parent);session=import_parent(files,identity,c)
        primary,backup,_=stores()
        for j,store in enumerate((primary,backup)):store.quota_bytes=min(store.quota_bytes,inv['storage_ceilings'][j])
        refs={};probe=None;evidence_refs=[]
        def keep_evidence(files,suffix):
            pr=evidence.publish(primary,files,identity,suffix)
            br=backup_checkpoint(primary,backup,pr,identity,source_domain=PRIMARY,destination_domain=BACKUP,validator=evidence.validate)
            ref=dict(primary=pr,backup=br);evidence_refs.append(ref);return ref
        def save(files,i):
            nonlocal probe
            guard();pr=publish_checkpoint(primary,files,i)
            br=backup_checkpoint(primary,backup,pr,i,source_domain=PRIMARY,destination_domain=BACKUP,validator=validate_payload)
            ref=dict(primary=pr,backup=br);refs[str(session.step)]=ref
            if session.step==1:
                probe,_=session.predict(cache.get('evaluator',0)['image']);tensor('probe.pt',probe)
            guard();return ref
        class Reference:
            def __init__(self,role):self.role=role;self.seen=set()
            def __len__(self):return len(ds[self.role])
            def descriptor(self,j):return ds[self.role].descriptor(j)
            def load(self,j,*,operation):
                require(operation==self.role and j not in self.seen,'Repeated/wrong fixture reference');self.seen.add(j)
                y,a=ds[self.role].native(j);return y,a,dict(descriptor=self.descriptor(j),scope='invented_fixture')
        def open_refs(stage,check):return {r:Reference(r) for r in stage['roles']}
        attempt=dest/'attempt';attempt.mkdir()
        result=execute(session,cache,attempt,open_references=open_refs,save_checkpoint=save,keep_evaluation=lambda path,i:keep_evidence(evidence.evaluation_files(path,i),path.name),guard=guard,check_parent=__import__('src.training.twomm_rebalanced_parity',fromlist=['check']).check)
        terminal_probe,_=session.predict(torch.full((1,144,144,144),.25));tensor('terminal-probe.pt',terminal_probe)
        keep_evidence(evidence.encode(identity,'terminal',dict(result=result,journal=(attempt/'events.jsonl').read_text(),
            probe_sha256=digest((dest/'terminal-probe.pt').read_bytes()))),'terminal')
        tensor('expected-next.pt',{k:v.detach().cpu() for k,v in session.model.state_dict().items()})
        put(dest/'references.json',canonical(dict(identity=identity,binding=b,cache_receipt_sha256=cp,
            evidence_refs=evidence_refs,terminal_probe_sha256=digest((dest/'terminal-probe.pt').read_bytes()),initial_checkpoint=refs['0'],checkpoint=refs['1'],terminal_checkpoint=refs['2'],next_update=session.history[-1],
            terminal_weight_sha256=weight_digest(session),probe_sha256=digest((dest/'probe.pt').read_bytes()),
            expected_next_sha256=digest((dest/'expected-next.pt').read_bytes()),result=result)))
        put(dest/'produce.json',canonical(dict(state='passed',seconds=time.monotonic()-started,memory=memory,
            processed_shapes={r:[e['transform_record']['processed_shape'] for e in es] for r,es in b['roles'].items()})))
    else:
        require(digest((dest/'references.json').read_bytes())==inv['references_sha256'],'Recovery references changed')
        refs=json.loads((dest/'references.json').read_bytes());i=refs['identity'];b=refs['binding'];cache_path=Path(inv['cache_path'])
        require(cache_path.parent==ROOT/inv['run_id'] and cache_path.name=='cache','Wrong synthetic cache path')
        cache=DiskRoleCache(cache_path,refs['cache_receipt_sha256'],b,digest(canonical(b)))
        _,backup,target=stores(recovery_only=True)
        for store in (backup,target):store.quota_bytes=min(store.quota_bytes,inv['storage_ceilings'][1])
        files,restored=restore_backup(backup,target,refs['checkpoint']['backup'],refs['checkpoint']['primary'],i,validator=validate_payload)
        session=restore_payload(files,i);probe,_=session.predict(cache.get('evaluator',0)['image']);guard()
        require(digest((dest/'probe.pt').read_bytes())==refs['probe_sha256'],'Probe changed')
        expected=torch.load(dest/'probe.pt',map_location='cpu',weights_only=True);delta=float((expected-probe).abs().max())
        require(delta<=1e-5,'Restored prediction differs')
        row=session.update(cache,guard=guard);require(row['sampling']==refs['next_update']['sampling'],'Restored crop differs')
        require(digest((dest/'expected-next.pt').read_bytes())==refs['expected_next_sha256'],'Next weights changed')
        expected=torch.load(dest/'expected-next.pt',map_location='cpu',weights_only=True)
        wd=max(float((v.detach().cpu()-expected[k]).abs().max()) for k,v in session.model.state_dict().items())
        require(wd<=1e-6,'Restored next update differs')
        # Actual MPS update interrupted AFTER optimizer mutation, then refused for save/reuse.
        interrupted=restore_payload(files,i);calls=0
        def inject():
            nonlocal calls
            guard();calls+=1
            if calls==4:raise KeyboardInterrupt('synthetic interruption after completed optimizer update')
        try:interrupted.update(cache,guard=inject)
        except KeyboardInterrupt:pass
        else:raise ValueError('Interruption was not injected')
        require(interrupted.poisoned and interrupted.step==2,'Uncertain update not marked')
        for action in (lambda:payload(interrupted),lambda:interrupted.update(cache)):
            try:action()
            except ValueError:pass
            else:raise ValueError('Interrupted session accepted')
        terminal,terminal_restore=restore_backup(backup,target,refs['terminal_checkpoint']['backup'],refs['terminal_checkpoint']['primary'],i,validator=validate_payload)
        recovered=restore_payload(terminal,i);require(weight_digest(recovered)==refs['terminal_weight_sha256'],'Terminal restore differs')
        initial,initial_restore=restore_backup(backup,target,refs['initial_checkpoint']['backup'],refs['initial_checkpoint']['primary'],i,validator=validate_payload)
        require(validate_payload(initial,i)['step']==0,'Initial imported restore differs')
        restored_evidence=[]
        for ref in refs['evidence_refs']:
            _,er=restore_backup(backup,target,ref['backup'],ref['primary'],i,validator=evidence.validate);restored_evidence.append(er)
        require(digest((dest/'terminal-probe.pt').read_bytes())==refs['terminal_probe_sha256'],'Terminal probe changed')
        expected=torch.load(dest/'terminal-probe.pt',map_location='cpu',weights_only=True)
        actual,_=recovered.predict(torch.full((1,144,144,144),.25));td=float((expected-actual).abs().max())
        require(td<=1e-5,'Terminal probe differs');guard()
        put(dest/'recover.json',canonical(dict(state='passed',seconds=time.monotonic()-started,memory=memory,
            primary_reads_forbidden=True,initial_restore=initial_restore,restored_evidence=restored_evidence,terminal_probe_max_difference=td,step1_restore=restored,terminal_restore=terminal_restore,
            probability_max_difference=delta,next_weight_max_difference=wd,
            next_loss_difference=abs(row['loss']-refs['next_update']['loss']),interruption_after_update_refused=True)))


def supervise(dest,stage,pin):
    start=time.monotonic();peak=0;reason=None
    with (dest/(stage+'.log')).open('xb') as log:
        process=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.twomm_rebalanced_rehearsal',
            '--worker',str(dest),'--stage',stage,'--pin',pin],cwd=REPO,
            env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT)
        try:
            next_power=0;ac=True
            while process.poll() is None:
                elapsed=time.monotonic()-start
                if elapsed>=next_power:ac,_=power();next_power=elapsed+10
                ps=subprocess.run(['/bin/ps','-o','rss=','-p',str(process.pid)],capture_output=True,text=True,timeout=5)
                if ps.returncode==0 and ps.stdout.strip():peak=max(peak,int(ps.stdout.strip())*1024)
                elif process.poll() is None:raise RuntimeError('Memory monitor unavailable')
                size=sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())
                reason=stop_reason(elapsed,peak,size,shutil.disk_usage(REPO).free,ac)
                require(reason is None,str(reason));time.sleep(.25)
            require(process.returncode==0,'Worker failed')
        except BaseException as exc:reason=reason or type(exc).__name__;raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            put(dest/(stage+'-supervisor.json'),canonical(dict(exit_code=process.returncode,reason=reason,
                peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start)))


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--worker',type=Path)
    p.add_argument('--stage',choices=('baseline','produce','recover'));p.add_argument('--pin');a=p.parse_args()
    if a.worker:return worker(a.worker,a.stage,a.pin)
    require(a.run,'Explicit synthetic --run required');ac,ptext=power()
    require(ac and shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Power/free-space floor')
    fd=os.open(ROOT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);primary,backup,_=stores();source,environment=capture()
        run_id='twomm-training-'+str(uuid4());dest=ROOT/run_id;dest.mkdir()
        inv=dict(run_id=run_id,source_sha256=digest(source),environment_sha256=digest(environment),limits=LIMITS,
            power=ptext,storage_ceilings=[primary.quota_bytes,backup.quota_bytes],approval='D-312-synthetic')
        put(dest/'invocation.json',canonical(inv));print(dest,flush=True);supervise(dest,'baseline',digest(canonical(inv)));supervise(dest,'produce',digest(canonical(inv)))
        recovery=ROOT/(run_id+'-recovery');recovery.mkdir()
        for name in ('references.json','probe.pt','expected-next.pt','terminal-probe.pt'):put(recovery/name,(dest/name).read_bytes())
        inv.update(references_sha256=digest((dest/'references.json').read_bytes()),cache_path=str(dest/'cache'))
        put(recovery/'invocation.json',canonical(inv));supervise(recovery,'recover',digest(canonical(inv)))
        for folder in (dest,recovery):
            members={str(p.relative_to(folder)):dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes()))
                for p in folder.rglob('*') if p.is_file()}
            put(folder/'receipt.json',canonical(dict(state='complete',synthetic_only=True,files=members)))
            print(str(folder)+' receipt_sha256='+digest((folder/'receipt.json').read_bytes()),flush=True)
    finally:os.close(fd)

if __name__=='__main__':main()
