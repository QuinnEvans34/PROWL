"""Freeze/verify single-use expanded launch requests; synthetic rehearsal and backup recovery."""
import argparse
import fcntl
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from scripts.diagnostics.expanded_localizer_profile import capture,REPO,ROOT,CAP,RECIPE
from scripts.diagnostics.localizer_smoke_run import encoded,put,sha
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require

DESIGN=REPO/'docs/capstone/operations/CAP-EXP-005-LAUNCH-PLAN-2026-09-29.md'
PROFILE=ROOT/'expanded-profile-aa667930-da3a-4874-b6b5-b28b0d9ee79a'
PROFILE_PIN='0a5f3335a46beabed727b4f2d4f662d80043873c94636b399e1ae64d2e8d99da'


def plan(config,synthetic=False,experiment='CAP-EXP-005'):
    from src.training.expanded_executor import EXPERIMENTS
    settings=dict(EXPERIMENTS[experiment])
    if synthetic:settings.update(config=config,evaluation_steps=[0,2,4],checkpoint_steps=[0,2,4],total_seconds=1200,update_seconds=600)
    else:require(config==settings['config'],'Wrong experiment config')
    return dict(settings,experiment_id='synthetic' if synthetic else experiment,margin_mm=10,export_final=True)


def prepare(experiment='CAP-EXP-005'):
    from src.training.expanded_executor import EXPERIMENTS,REAL_INPUT_PIN
    require(sha((PROFILE/'receipt.json').read_bytes())==PROFILE_PIN,'Profile receipt changed')
    receipt=json.loads((PROFILE/'receipt.json').read_bytes());raw=(PROFILE/'checkpoint/inputs.json').read_bytes()
    require(sha(raw)==receipt['checkpoint/inputs.json']['sha256']==REAL_INPUT_PIN,'Frozen input record differs')
    config=EXPERIMENTS[experiment]['config'];design=DESIGN if experiment=='CAP-EXP-005' else REPO/'docs/capstone/operations/CAP-EXP-006-LAUNCH-PLAN-2026-09-29.md'
    source,env=capture();files={'inputs.json':raw,'source.json':source,'environment.json':env,'recipe.json':RECIPE.read_bytes(),'capability.json':CAP.read_bytes(),'plan.json':canonical(plan(config,experiment=experiment)),'design.md':design.read_bytes()}
    dest=ROOT/('expanded-launch-request-'+str(uuid4()));dest.mkdir()
    for n,b in files.items():put(dest/n,b)
    put(dest/'request.json',canonical(dict(schema_version='1.0.0',experiment_id=experiment,state='prepared_not_authorized',files={n:sha(b) for n,b in files.items()})))
    print(dest);print('request_sha256='+sha((dest/'request.json').read_bytes()))


def checked_request(path,pin,approval=None,approval_pin=None):
    require(path.parent==ROOT and path.resolve(strict=True)==path,'Unsafe request root')
    raw=(path/'request.json').read_bytes();require(sha(raw)==pin,'Request digest differs');req=json.loads(raw)
    require(req['schema_version']=='1.0.0' and req['experiment_id'] in ('CAP-EXP-005','CAP-EXP-006') and req['state']=='prepared_not_authorized','Wrong request scope')
    require(set(req['files'])=={'inputs.json','source.json','environment.json','recipe.json','capability.json','plan.json','design.md'},'Request inventory differs')
    for n,h in req['files'].items():require(sha((path/n).read_bytes())==h,'Changed frozen file')
    source,env=capture();require(source==(path/'source.json').read_bytes() and env==(path/'environment.json').read_bytes(),'Code/environment drift')
    if approval is not None:
        require(sha(approval)==approval_pin,'Approval digest differs');a=json.loads(approval)
        require(a==dict(allowed=True,authority='Quinton Evans',operation='launch_'+req['experiment_id'],request_sha256=pin),'Missing exact launch approval')
    return req


def stores(recovery_only=False):
    from src.operations.localizer_run_storage import run_stores
    p=REPO/'docs/capstone/operations/LOCALIZER-RUN-CAPABILITY-2026-09-28.json'
    return run_stores(REPO/'configs/local/roots.yaml',p.read_bytes(),trusted_capability_sha256='e2651188827877d11888d13e7e0e3555b83b97816c9f10d0db6820ab002d3486',recovery_only=recovery_only)


def capped_stores(invocation,*,recovery_only=False):
    result=stores(recovery_only);limits=invocation['storage_quota_ceilings']
    require(len(limits)==2 and all(type(v)==int and v>0 for v in limits),'Missing shared storage ceilings')
    for index,store in enumerate(result):
        if store is not None:store.quota_bytes=min(store.quota_bytes,limits[0 if index==0 else 1])
    return result


def fixture_cache():
    import numpy as np
    from src.data.localizer_preprocessing_v2 import preprocess
    from src.training.expanded_localizer import RoleCache
    class Fixture:
        def __init__(self,role):self.role=role;self.recipe=json.loads(RECIPE.read_bytes())
        def __len__(self):return 16 if self.role=='optimizer' else 11
        def descriptor(self,i):return dict(study_id=f'synthetic-{self.role}-{i}',operation=self.role,protected_role='train' if self.role=='optimizer' else 'validation')
        def load(self,i,*,operation):
            require(operation==self.role,'Fixture role mismatch');y=np.zeros((24,24,24),np.uint8);y[3:18,4:19,5:20]=1
            a=np.diag([3.,3.,3.,1.]);x=preprocess(y.astype(np.float32)*300-100,a,self.recipe,target=y);x['provenance']={'descriptor':self.descriptor(i)};return x
    return RoleCache({r:Fixture(r) for r in ('optimizer','evaluator')})


def artifact_validator(kind,identity,resolver):
    from src.training.expanded_executor import validate_checkpoint,validate_export,validate_terminal
    if kind=='checkpoint':return lambda f,i:validate_checkpoint(f,i)
    if kind=='case':return lambda f,i:validate_export(f,json.loads(f['record.json']))
    return lambda f,i:validate_terminal(f,i,resolver)


def worker(dest):
    import torch
    from src.training.expanded_localizer import RoleCache
    from src.training.expanded_executor import EXPERIMENTS,execute,REAL_INPUT_PIN
    from src.training.localizer_run import MPSRun
    from src.data.expanded_localizer_inputs import open_expanded_inputs
    from src.operations.localizer_backup import backup_checkpoint
    torch.set_num_threads(2);started=time.monotonic();inv=json.loads((dest/'invocation.json').read_bytes());synthetic=inv['synthetic'];experiment=inv['experiment'];limits=EXPERIMENTS[experiment] if not synthetic else dict(total_seconds=1200,update_seconds=600)
    primary,backup,_=capped_stores(inv);source,env=capture()
    def guard():
        require(time.monotonic()-started<limits['total_seconds'],'Worker total budget');torch.mps.synchronize()
        require(torch.mps.driver_allocated_memory()<16*1024**3,'MPS driver cap')
    if synthetic:cache=fixture_cache();config=dict(EXPERIMENTS[experiment]['config'],max_steps=4);p=plan(config,True,experiment)
    else:
        request=Path(inv['request']);approval=Path(inv['approval']).read_bytes();req=checked_request(request,inv['request_pin'],approval,inv['approval_pin'])
        ds,budget=open_expanded_inputs(repo=REPO,capability_bytes=(request/'capability.json').read_bytes(),trusted_capability_sha256=req['files']['capability.json'],recipe_bytes=(request/'recipe.json').read_bytes(),trusted_recipe_sha256=req['files']['recipe.json'],tick=guard)
        cache=RoleCache(ds,guard=guard);require(budget.files==54 and digest(canonical(cache.inputs))==REAL_INPUT_PIN,'Wrong loaded inputs');config=EXPERIMENTS[experiment]['config'];p=json.loads((request/'plan.json').read_bytes())
    identity=dict(schema_version='2.0.0',purpose='synthetic-expanded-executor' if synthetic else 'qualified-expanded-executor',run_id=dest.name,device='mps',config=config,
        inputs_sha256=digest(canonical(cache.inputs)),source_sha256=sha(source),environment_sha256=sha(env),plan_sha256=digest(canonical(p)))
    a=dict(allowed=True,authority='Codex synthetic fixture' if synthetic else 'Quinton Evans',operation='synthetic_executor_verification' if synthetic else 'launch_'+experiment,bindings={k:identity[k] for k in ('inputs_sha256','source_sha256','environment_sha256','plan_sha256')})
    for name,v in [('identity.json',identity),('plan.json',p),('approval.json',a)]:put(dest/name,canonical(v))
    put(dest/'source.json',source);put(dest/'environment.json',env)
    entries=[]
    def keep(kind,ref):
        guard()
        b=backup_checkpoint(primary,backup,ref,identity,source_domain='22750B93-2F3F-499D-87F5-902981BFAB59',destination_domain='542E8B1F-8D50-4783-9250-752DFDC899CD',validator=artifact_validator(kind,identity,primary))
        entry=dict(kind=kind,primary=ref,backup=b);entries.append(entry)
        # Independent, durable per-checkpoint receipts survive interruption before terminal.
        put(dest/('backup-'+str(len(entries))+'.json'),canonical(entry))
    def event(row):
        with (dest/'events.jsonl').open('ab') as f:f.write(canonical(dict(row,monotonic_seconds=time.monotonic())));f.flush();os.fsync(f.fileno())
        if row['state']=='evaluation_complete':put(dest/('evaluation-'+str(row['step'])+'.json'),canonical(row))
        if row['state']=='checkpoint_complete':keep('checkpoint',row['reference'])
        print(json.dumps(dict(state=row['state'],step=row.get('completed_step',row.get('step')))),flush=True)
    result,terminal=execute(MPSRun(config),cache,identity,p,a,primary,guard=guard,event=event)
    for kind,refs in [('case',[r['reference'] for r in result['exports']]),('terminal',[terminal])]:
        for ref in refs:keep(kind,ref)
    put(dest/'recovery-request.json',canonical(dict(identity=identity,entries=entries,terminal=terminal)))
    if not synthetic:checked_request(Path(inv['request']),inv['request_pin'],Path(inv['approval']).read_bytes(),inv['approval_pin'])
    else:require(capture()==(source,env),'Synthetic source drift')
    put(dest/'result.json',canonical(dict(result,terminal=terminal,backed_up_artifacts=len(entries),real_updates=0 if synthetic else result['completed_steps'])))


def recover(dest):
    import torch
    from src.operations.localizer_backup import restore_backup
    from src.training.expanded_localizer import restore
    torch.set_num_threads(2)
    def audit(event,args):
        if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes)) and os.fsdecode(args[0]).startswith('/Volumes/PROWL-Data'):raise RuntimeError('Primary reads forbidden during restore')
    sys.addaudithook(audit)
    request=json.loads((dest/'recovery-request.json').read_bytes());identity=request['identity'];_,backup,target=capped_stores(json.loads((dest/'invocation.json').read_bytes()),recovery_only=True);loaded={};references=[]
    class Resolver:
        def resolve(self,artifact_id,*,receipt_sha256,expected_derivation,validate):
            payload,ref=loaded[artifact_id];require(ref['receipt_sha256']==receipt_sha256 and ref['derivation_sha256']==expected_derivation,'Recovery reference differs');validate(payload);return payload,{}
    resolver=Resolver()
    for entry in request['entries']:
        payload,ref=restore_backup(backup,target,entry['backup'],entry['primary'],identity,validator=artifact_validator(entry['kind'],identity,resolver))
        loaded[entry['primary']['artifact_id']]=(payload,entry['primary']);references.append(ref)
    terminal=loaded[request['terminal']['artifact_id']][0];result=json.loads(terminal['result.json']);cp=loaded[result['checkpoints'][-1]['artifact_id']][0]
    session=restore({k:v for k,v in cp.items() if k not in {'plan.json','approval.json'}},identity)
    expected=torch.load(BytesIO(terminal['probe.pt']),map_location='cpu',weights_only=True);actual=session.predict(torch.full((1,*identity['config']['patch_size']),.25));delta=float((expected-actual).abs().max())
    require(delta==0,'Backup fixed probe differs');put(dest/'recovery.json',canonical(dict(state='restore_verified',primary_reads_forbidden=True,artifacts=len(references),step=session.step,probe_max_difference=delta,restores=references)))


def supervised(synthetic,request=None,pin=None,approval=None,approval_pin=None,experiment='CAP-EXP-005'):
    from scripts.diagnostics.localizer_resource_profile import power
    from src.training.expanded_executor import EXPERIMENTS
    if not synthetic:experiment=checked_request(request,pin,approval.read_bytes(),approval_pin)['experiment_id']
    limits=EXPERIMENTS[experiment] if not synthetic else dict(total_seconds=1200,update_seconds=600)
    require(power()[0] and shutil.disk_usage(REPO).free>100*1024**3,'AC/free-space preflight')
    fd=os.open(ROOT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    dest=ROOT/('expanded-execution-'+str(uuid4()));dest.mkdir();started=time.monotonic();peak=0
    try:
        if not synthetic:put(ROOT/('expanded-launch-claim-'+pin+'.json'),canonical(dict(result=dest.name,approval_pin=approval_pin)))
        initial_stores=stores();ceilings=[initial_stores[0].quota_bytes,initial_stores[1].quota_bytes]
        put(dest/'invocation.json',canonical(dict(storage_quota_ceilings=ceilings,synthetic=synthetic,experiment=experiment,request=str(request) if request else None,request_pin=pin,approval=str(approval) if approval else None,approval_pin=approval_pin)))
        print(dest,flush=True)
        for mode in ('worker','recover'):
            proc=None;reason=None
            try:
                with (dest/(mode+'.log')).open('xb') as log:
                    proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.expanded_localizer_launch','--'+mode,str(dest)],cwd=REPO,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTORCH_ENABLE_MPS_FALLBACK='0'),stdout=log,stderr=subprocess.STDOUT)
                    while proc.poll() is None:
                        require(time.monotonic()-started<limits['total_seconds'],'Supervisor total cap');require(power()[0],'AC lost')
                        require(shutil.disk_usage(REPO).free>100*1024**3,'Free floor')
                        require(sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())<256*1024**2,'Local evidence cap')
                        journal=dest/'events.jsonl'
                        if mode=='worker' and journal.exists():
                            update_start=None
                            for line in journal.read_bytes().splitlines(keepends=True):
                                if not line.endswith(b'\n'):continue
                                row=json.loads(line)
                                if row['state']=='update_phase_started':update_start=row['monotonic_seconds']
                                elif row['state']=='update_phase_complete':update_start=None
                            if update_start is not None:require(time.monotonic()-update_start<limits['update_seconds'],'Supervisor update phase cap')
                        ps=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                        if ps.returncode==0 and ps.stdout.strip():peak=max(peak,int(ps.stdout.strip())*1024);require(peak<16*1024**3,'RSS cap')
                        elif proc.poll() is None:raise RuntimeError('RSS monitor unavailable')
                        time.sleep(.25)
                    require(proc.returncode==0,'Worker/recovery failed; evidence retained')
            except BaseException as exc:reason=str(exc);raise
            finally:
                if proc is not None and proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
                put(dest/(mode+'-supervisor.json'),canonical(dict(exit_code=None if proc is None else proc.returncode,stop_reason=reason,elapsed_seconds=time.monotonic()-started,peak_rss=peak)))
        put(dest/'receipt.json',canonical({p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in dest.iterdir()}));print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()))
    finally:os.close(fd)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--experiment',choices=['CAP-EXP-005','CAP-EXP-006'],default='CAP-EXP-005');p.add_argument('--synthetic',action='store_true');p.add_argument('--request',type=Path);p.add_argument('--pin');p.add_argument('--approval',type=Path);p.add_argument('--approval-pin');p.add_argument('--worker',type=Path);p.add_argument('--recover',type=Path);a=p.parse_args()
    if a.prepare:prepare(a.experiment)
    elif a.worker:worker(a.worker)
    elif a.recover:recover(a.recover)
    elif a.synthetic:supervised(True,experiment=a.experiment)
    elif a.request and a.pin and a.approval and a.approval_pin:supervised(False,a.request,a.pin,a.approval,a.approval_pin)
    else:p.error('Choose prepare, synthetic or exact pinned request and approval')
