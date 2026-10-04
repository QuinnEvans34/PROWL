"""CAP-EXP-007 single-use request, separate explicit approval, supervised launch/recovery."""
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
from scripts.diagnostics.localizer_smoke_run import capture,put
from scripts.diagnostics.localizer_context_profile import power
from scripts.diagnostics.expanded_localizer_launch import stores
from scripts.diagnostics.twomm_session_rehearsal import PRIMARY,BACKUP
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training.twomm_training import REAL_BINDING,REAL_CACHE,POLICY,SHUFFLE,PREDICTION,CONTROLS

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl'
BINDING=ROOT/'twomm-cache-readiness-20260930/proposed-binding.json'
CACHE=ROOT/'twomm-cache-build-80569d7d-94e0-4c52-91ba-1a128dd076ae/cache'
LIMITS=dict(seconds=2700,rss_bytes=16*1024**3,driver_bytes=16*1024**3,
    output_bytes=4*1024**3,free_bytes=100*1024**3)
DESIGN=REPO/'docs/capstone/operations/CAP-EXP-007-LAUNCH-PLAN-2026-09-30.md'
NAMES={'inputs.json','source.json','environment.json','plan.json','reference-scope.json','design.md','rehearsal.json'}


def plan():
    config=dict(schema_version='twomm-adapter-1',patch_size=[144]*3,seed=42,learning_rate=.0003,
        weight_decay=.00001,max_steps=300,loss_id='balanced_ce_dice_v1')
    return dict(schema_version='twomm-training-plan-1',config=config,checkpoint_steps=[0,113,226,300],
        evaluations=[dict(step=s,roles=['optimizer','evaluator'] if s in (0,300) else ['evaluator']) for s in (0,113,226,300)],
        total_seconds=LIMITS['seconds'],output_bytes=LIMITS['output_bytes'],reference_policy='fresh_native_references_each_stage_v1')


def checked_request(path,pin,*,current=True,approval=None,approval_pin=None):
    path=Path(path);require(path.parent==ROOT and path.resolve(strict=True)==path,'Unsafe request path')
    raw=(path/'request.json').read_bytes();require(digest(raw)==pin,'Request changed');r=json.loads(raw)
    require(set(r)=={'schema_version','experiment','state','limits','files','cache_receipt_sha256','run_id'} and
        r['schema_version']=='twomm-training-request-1' and r['experiment']=='CAP-EXP-007' and
        r['state']=='prepared_not_authorized' and r['limits']==LIMITS and set(r['files'])==NAMES and
        r['cache_receipt_sha256']==REAL_CACHE and r['run_id']==path.name,'Wrong request scope')
    for n,h in r['files'].items():
        require(not (path/n).is_symlink() and digest((path/n).read_bytes())==h,'Frozen control changed')
    require(r['files']['inputs.json']==REAL_BINDING and json.loads((path/'plan.json').read_bytes())==plan(),'Wrong input/plan')
    from src.data.twomm_training_references import scope
    require(json.loads((path/'reference-scope.json').read_bytes())==scope(json.loads((path/'inputs.json').read_bytes()),plan()),'Wrong reference scope')
    if current:require(capture()==((path/'source.json').read_bytes(),(path/'environment.json').read_bytes()),'Source/environment drift')
    if approval is not None:
        require(digest(approval)==approval_pin and json.loads(approval)==dict(allowed=True,authority='Quinton Evans',
            operation='launch_CAP-EXP-007',request_sha256=pin),'Missing exact launch approval')
    return r


def prepare(rehearsal,rehearsal_pin,recovery,recovery_pin):
    from src.training.twomm_cache import DiskRoleCache
    from src.data.twomm_training_references import scope
    from src.training.twomm_training import validate_controls
    binding=BINDING.read_bytes();require(digest(binding)==REAL_BINDING,'Binding changed')
    b=json.loads(binding);DiskRoleCache(CACHE,REAL_CACHE,b,REAL_BINDING)
    # Native rehearsal receipts and all members must still be independently verifiable.
    for path,pin in ((rehearsal,rehearsal_pin),(recovery,recovery_pin)):
        require(path.parent==ROOT and path.resolve(strict=True)==path,'Unsafe rehearsal path')
        raw=(path/'receipt.json').read_bytes();require(digest(raw)==pin,'Rehearsal receipt changed');r=json.loads(raw)
        require(r['state']=='complete' and r['synthetic_only'] is True,'Incomplete rehearsal')
        for name,ref in r['files'].items():
            p=path/name;require(not Path(name).is_absolute() and '..' not in Path(name).parts and p.is_file() and
                not p.is_symlink() and p.stat().st_size==ref['bytes'] and digest(p.read_bytes())==ref['sha256'],'Rehearsal member changed')
    require(json.loads((recovery/'recover.json').read_bytes())['primary_reads_forbidden'] is True,'Missing independent recovery')
    source,environment=capture()
    native=json.loads((rehearsal/'invocation.json').read_bytes())
    require(native['source_sha256']==digest(source) and native['environment_sha256']==digest(environment), 'Native rehearsal source/environment is stale')
    p=plan();dest=ROOT/('twomm-training-'+str(uuid4()));dest.mkdir()
    files={'inputs.json':binding,'source.json':source,'environment.json':environment,'plan.json':canonical(p),
        'reference-scope.json':canonical(scope(b,p)),'design.md':DESIGN.read_bytes(),
        'rehearsal.json':canonical(dict(producer=dict(path=str(rehearsal),sha256=rehearsal_pin),
            recovery=dict(path=str(recovery),sha256=recovery_pin)))}
    for name,raw in files.items():put(dest/name,raw)
    r=dict(schema_version='twomm-training-request-1',experiment='CAP-EXP-007',state='prepared_not_authorized',
        limits=LIMITS,files={n:digest(v) for n,v in files.items()},cache_receipt_sha256=REAL_CACHE,run_id=dest.name)
    put(dest/'request.json',canonical(r));pin=digest(canonical(r));checked_request(dest,pin)
    # Validate the future identity shape in memory; no allowed authorization file is issued.
    identity,controls=authorized_controls(dest)
    validate_controls(identity,controls)
    print(dest,flush=True);print('request_sha256='+pin,flush=True)


def authorized_controls(request):
    controls={n:(request/n).read_bytes() for n in CONTROLS if n!='authorization.json'}
    i=dict(schema_version='twomm-training-1',run_id=request.name,purpose='qualified-twomm-training',device='mps',
        config=plan()['config'],sampling_policy=POLICY,shuffle_policy=SHUFFLE,prediction_policy=PREDICTION,
        cache_receipt_sha256=REAL_CACHE,**{CONTROLS[n]:digest(v) for n,v in controls.items()})
    controls['authorization.json']=canonical(dict(allowed=True,authority='Quinton Evans',operation='launch_CAP-EXP-007',request_sha256=digest((request/'request.json').read_bytes()),identity=deepcopy(i)))
    i['authorization_sha256']=digest(controls['authorization.json']);return i,controls


def checked_invocation(dest,pin):
    require(dest.parent==ROOT and dest.resolve(strict=True)==dest,'Unsafe execution path')
    raw=(dest/'invocation.json').read_bytes();require(digest(raw)==pin,'Invocation changed');return json.loads(raw)


def worker(dest,pin):
    import torch
    from src.training.twomm_cache import DiskRoleCache
    from src.training.twomm_training import Session,publish_checkpoint,validate_payload,weight_digest
    from src.training.twomm_training_executor import execute
    from src.training import twomm_training_evidence as evidence
    from src.data.twomm_training_references import open_training_references,scope
    from src.operations.localizer_backup import backup_checkpoint
    inv=checked_invocation(dest,pin);request=Path(inv['request']);approval=(dest/'launch-approval.json').read_bytes()
    checked_request(request,inv['request_pin'],approval=approval,approval_pin=inv['approval_pin'])
    require(json.loads((request/'consumed.json').read_bytes())['invocation_sha256']==pin,'Missing consumed request')
    put(dest/'worker-started.json',canonical(dict(invocation_sha256=pin)))
    torch.set_num_threads(2);require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and torch.backends.mps.is_available(),'Native MPS required')
    torch.mps.set_per_process_memory_fraction(min(1.,LIMITS['driver_bytes']/torch.mps.recommended_max_memory()))
    started=time.monotonic();memory=[]
    def guard():
        torch.mps.synchronize();d=torch.mps.driver_allocated_memory()
        require(d<=LIMITS['driver_bytes'] and time.monotonic()-started<LIMITS['seconds'] and
            shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Worker resource envelope')
        memory.append(d)
    i,c=authorized_controls(request);cache=DiskRoleCache(CACHE,REAL_CACHE,json.loads(c['inputs.json']),REAL_BINDING)
    session=Session(i,c)
    require(weight_digest(session)=='365306b1aec77681bd651a1e87ca7902b10efffef38607f1618303220d20954e','Fresh initialization differs')
    references=open_training_references(REPO,i,c,tick=guard)
    primary,backup,_=stores()
    for j,store in enumerate((primary,backup)):store.quota_bytes=min(store.quota_bytes,inv['storage_ceilings'][j])
    entries=[]
    def keep(kind,files,suffix):
        guard();validator=validate_payload if kind=='checkpoint' else evidence.validate
        pr=publish_checkpoint(primary,files,i) if kind=='checkpoint' else evidence.publish(primary,files,i,suffix)
        br=backup_checkpoint(primary,backup,pr,i,source_domain=PRIMARY,destination_domain=BACKUP,validator=validator)
        entry=dict(kind=kind,primary=pr,backup=br);entries.append(entry)
        put(dest/f'keeper-{len(entries):02d}.json',canonical(entry));guard();return dict(primary=pr,backup=br)
    attempt=dest/'attempt';attempt.mkdir()
    result=execute(session,cache,attempt,open_references=references.open,
        save_checkpoint=lambda f,identity:keep('checkpoint',f,str(session.step)),
        keep_evaluation=lambda path,identity:keep('evidence',evidence.evaluation_files(path,i),path.name),guard=guard)
    reads=references.completed();expected=scope(session.binding,session.plan)
    require(all(reads[k]==expected[k] for k in reads),'Reference accounting differs')
    probe,_=session.predict(torch.full((1,144,144,144),.25));guard()
    with (dest/'probe.pt').open('xb') as f:torch.save(probe,f);f.flush();os.fsync(f.fileno())
    terminal=evidence.encode(i,'terminal',dict(result=result,journal=(attempt/'events.jsonl').read_text(),probe_sha256=digest((dest/'probe.pt').read_bytes())))
    keep('evidence',terminal,'terminal')
    put(dest/'recovery-request.json',canonical(dict(identity=i,entries=entries,weight_sha256=weight_digest(session),
        probe_sha256=digest((dest/'probe.pt').read_bytes()))))
    checked_request(request,inv['request_pin'],approval=approval,approval_pin=inv['approval_pin'])
    put(dest/'worker-result.json',canonical(dict(state='passed',completed_steps=session.step,reads=reads,
        seconds=time.monotonic()-started,peak_sampled_driver_bytes=max(memory),keepers=len(entries),derived_native_masks_backed_up=False)))


def recover(dest,pin):
    import torch
    from src.operations.localizer_backup import restore_backup
    from src.training.twomm_training import validate_payload,restore_payload,weight_digest
    from src.training import twomm_training_evidence as evidence
    inv=checked_invocation(dest,pin)
    put(dest/'recovery-started.json',canonical(dict(invocation_sha256=pin)))
    def audit(event,args):
        if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
            require(not os.fsdecode(args[0]).startswith('/Volumes/PROWL-Data'),'Primary reads forbidden')
    sys.addaudithook(audit);torch.set_num_threads(2)
    torch.mps.set_per_process_memory_fraction(min(1.,LIMITS['driver_bytes']/torch.mps.recommended_max_memory()))
    raw=(dest/'recovery-request.json').read_bytes();r=json.loads(raw);i=r['identity']
    _,backup,target=stores(recovery_only=True)
    for store in (backup,target):store.quota_bytes=min(store.quota_bytes,inv['storage_ceilings'][1])
    require([e['primary']['step'] for e in r['entries'] if e['kind']=='checkpoint']==[0,113,226,300] and
        len(r['entries'])==9 and all(e['kind'] in ('checkpoint','evidence') for e in r['entries']), 'Incomplete recovery inventory')
    restored=[];terminal_files=None;terminal_record=None;evaluation_records=[]
    for entry in r['entries']:
        validator=validate_payload if entry['kind']=='checkpoint' else evidence.validate
        files,ref=restore_backup(backup,target,entry['backup'],entry['primary'],i,validator=validator);restored.append(ref)
        if entry['kind']=='checkpoint' and validate_payload(files,i)['step']==300:terminal_files=files
        if entry['kind']=='evidence':
            record=json.loads(files['record.json'])
            if record['kind']=='terminal':terminal_record=record
            else:evaluation_records.append((record,entry))
    require(terminal_files is not None and terminal_record is not None,'Missing terminal keeper')
    result=terminal_record['content']['result']
    require([dict(primary=e['primary'],backup=e['backup']) for e in r['entries'] if e['kind']=='checkpoint']==result['checkpoints'], 'Terminal checkpoint references differ')
    require([v['content']['completion']['step'] for v,e in evaluation_records]==[0,113,226,300], 'Incomplete restored evaluations')
    require([dict(primary=e['primary'],backup=e['backup']) for v,e in evaluation_records]==[v['keeper'] for v in result['evaluations']], 'Terminal evaluation references differ')
    for (record,entry),ref in zip(evaluation_records,result['evaluations']):
        require(digest(canonical(record['content']['completion']))==ref['receipt_sha256'], 'Restored evaluation completion differs')
    session=restore_payload(terminal_files,i);require(weight_digest(session)==r['weight_sha256']==terminal_record['content']['result']['weight_sha256'],'Restored weights differ')
    require(digest((dest/'probe.pt').read_bytes())==r['probe_sha256']==terminal_record['content']['probe_sha256'],'Probe changed')
    expected=torch.load(dest/'probe.pt',map_location='cpu',weights_only=True)
    actual,_=session.predict(torch.full((1,144,144,144),.25));delta=float((expected-actual).abs().max())
    require(delta<=1e-5,'Restored probe differs')
    put(dest/'recover.json',canonical(dict(state='passed',primary_reads_forbidden=True,completed_steps=session.step,
        probability_max_difference=delta,restores=restored,derived_native_masks_backed_up=False)))


def run(request,pin,approval,approval_pin):
    raw=approval.read_bytes();checked_request(request,pin,approval=raw,approval_pin=approval_pin)
    require(power()[0] and shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Power/free-space preflight')
    lock=os.open(ROOT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        dest=ROOT/(request.name+'-execution');dest.mkdir();primary,backup,_=stores()
        inv=dict(request=str(request),request_pin=pin,approval_pin=approval_pin,storage_ceilings=[primary.quota_bytes,backup.quota_bytes])
        put(dest/'launch-approval.json',raw);put(dest/'invocation.json',canonical(inv));ip=digest(canonical(inv))
        put(request/'consumed.json',canonical(dict(invocation_sha256=ip)));print(dest,flush=True)
        started=time.monotonic();peak=0
        for stage in ('worker','recover'):
            reason=None
            with (dest/(stage+'.log')).open('xb') as log:
                proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.twomm_training_launch','--'+stage,str(dest),'--pin',ip],
                    cwd=REPO,env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT)
                try:
                    next_power=0;ac=True
                    while proc.poll() is None:
                        elapsed=time.monotonic()-started
                        if elapsed>=next_power:ac,_=power();next_power=elapsed+10
                        ps=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                        if ps.returncode==0 and ps.stdout.strip():peak=max(peak,int(ps.stdout.strip())*1024)
                        elif proc.poll() is None:raise RuntimeError('Memory monitor unavailable')
                        require(elapsed<LIMITS['seconds'] and peak<=LIMITS['rss_bytes'] and ac and
                            shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Supervisor resource limit')
                        require(sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())<=LIMITS['output_bytes'],'Output limit')
                        time.sleep(.25)
                    require(proc.returncode==0,'Worker/recovery failed; evidence retained')
                except BaseException as exc:reason=str(exc);raise
                finally:
                    if proc.poll() is None:
                        proc.terminate()
                        try:proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
                    put(dest/(stage+'-supervisor.json'),canonical(dict(exit_code=proc.returncode,reason=reason,
                        peak_worker_rss=peak,elapsed_total_seconds=time.monotonic()-started)))
        files={str(p.relative_to(dest)):dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in dest.rglob('*') if p.is_file()}
        put(dest/'receipt.json',canonical(dict(state='complete',files=files,request_sha256=pin)))
        print('receipt_sha256='+digest((dest/'receipt.json').read_bytes()),flush=True)
    finally:os.close(lock)


def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--rehearsal',type=Path);p.add_argument('--rehearsal-pin')
    p.add_argument('--recovery',type=Path);p.add_argument('--recovery-pin');p.add_argument('--request',type=Path);p.add_argument('--pin')
    p.add_argument('--approval',type=Path);p.add_argument('--approval-pin');p.add_argument('--worker',type=Path);p.add_argument('--recover',type=Path);a=p.parse_args()
    if a.prepare:prepare(a.rehearsal,a.rehearsal_pin,a.recovery,a.recovery_pin)
    elif a.worker:worker(a.worker,a.pin)
    elif a.recover:recover(a.recover,a.pin)
    elif a.request and a.pin and a.approval and a.approval_pin:run(a.request,a.pin,a.approval,a.approval_pin)
    else:p.error('Choose prepare or an exact request and separately pinned approval')

if __name__=='__main__':main()
