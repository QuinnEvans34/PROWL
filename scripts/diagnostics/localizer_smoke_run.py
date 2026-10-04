"""Prepare an immutable launch request or run its explicitly authorized bounded worker."""
import argparse
from io import BytesIO
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from uuid import uuid4

REPO=Path(__file__).resolve().parents[2]
OUTPUT=REPO/'outputs/prowl'


def encoded(value):return json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':')).encode()+b'\n'
def sha(data):return hashlib.sha256(data).hexdigest()

def put(path,data):
    with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())


def capture():
    roots=['src/data','src/training','src/models','src/operations','src/contracts','src/utils','scripts/diagnostics']
    files={str(p.relative_to(REPO)):p.read_text() for root in roots for p in sorted((REPO/root).rglob('*.py'))}
    for folder,pattern in [('docs/capstone/contracts','*.json'),('configs/capstone','*.json'),('docs/capstone/operations','*CAPABILITY*.json'),('docs/capstone/data','*CAPABILITY*.json')]:
        for p in sorted((REPO/folder).rglob(pattern)):files[str(p.relative_to(REPO))]=p.read_text()
    source=dict(files=files,git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        tracked_diff=subprocess.check_output(['git','--no-optional-locks','diff','HEAD','--',*roots],cwd=REPO,text=True),
        source_policy='allowlisted exact source snapshot; dirty smoke non-promotable')
    environment=dict(python=sys.version,platform=platform.platform(),machine=platform.machine(),
        packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()},precision='float32',
        workers=0,cache='none',threads=2,mps_fallback='0')
    return encoded(source),encoded(environment)


def load_dataset():
    from scripts.diagnostics.localizer_preprocessing_check import CAP,CAP_PIN,RECIPE,RECIPE_PIN
    from src.data.localizer_inputs import open_localizer_dataset
    return open_localizer_dataset(repo=REPO,capability_path=CAP,trusted_capability_sha256=CAP_PIN,
        recipe_path=RECIPE,trusted_recipe_sha256=RECIPE_PIN)


def prepare(balanced=False,experiment=None):
    from src.data.manifest_records import canonical
    from src.training.localizer_run import input_record
    from src.training.localizer_smoke import REAL_CONFIG,BALANCED_EXPERIMENTS
    from src.data.cohort_registry import MEMBERS
    dest=OUTPUT/('localizer-launch-request-'+str(uuid4()));dest.mkdir()
    source,environment=capture();dataset=load_dataset()
    experiment=experiment or ('CAP-EXP-002' if balanced else 'CAP-EXP-001')
    balanced=experiment in BALANCED_EXPERIMENTS
    plan=dict(schema_version='1.0.0',experiment_id=experiment,config=BALANCED_EXPERIMENTS[experiment] if balanced else REAL_CONFIG,member_ids=MEMBERS,
        checkpoint_every=75 if experiment=='CAP-EXP-004' else 25,update_seconds=600,total_seconds=1200,
        design_sha256=sha((REPO/f'docs/capstone/operations/{experiment}-LAUNCH-PLAN-2026-09-28.md').read_bytes()))
    if balanced:plan['evaluation_policy']='balanced_and_legacy_v1'
    controls={'source.json':source,'environment.json':environment,'inputs.json':canonical(input_record(dataset)),'plan.json':canonical(plan)}
    for name,data in controls.items():put(dest/name,data)
    bindings={key:sha(controls[name]) for name,key in [('inputs.json','inputs_sha256'),('source.json','source_sha256'),('environment.json','environment_sha256'),('plan.json','plan_sha256')]}
    pending=dict(bindings=bindings,allowed=False,data_mode='qualified_cohort',operation='launch_'+experiment,authority='Quinton Evans')
    put(dest/'authorization-PENDING.json',canonical(pending))
    request=dict(schema_version='1.0.0',state='prepared_not_authorized',files={n:sha(v) for n,v in controls.items()},bindings=bindings)
    put(dest/'request.json',encoded(request))
    print(json.dumps(dict(request_directory=str(dest),request_sha256=sha((dest/'request.json').read_bytes()),state=request['state'])),flush=True)


def checked_request(path,pin,approval,approval_pin,*,verify_current=True):
    if path.parent!=OUTPUT or path.resolve(strict=True)!=path:raise ValueError('Unsafe request directory')
    raw=(path/'request.json').read_bytes()
    if sha(raw)!=pin:raise ValueError('Request pin differs')
    req=json.loads(raw);expected={'source.json','environment.json','inputs.json','plan.json'}
    if set(req['files'])!=expected:raise ValueError('Unexpected request members')
    controls={name:(path/name).read_bytes() for name in expected}
    if any(sha(controls[n])!=h for n,h in req['files'].items()):raise ValueError('Prepared control changed')
    expected_bindings={key:sha(controls[name]) for name,key in [('inputs.json','inputs_sha256'),('source.json','source_sha256'),('environment.json','environment_sha256'),('plan.json','plan_sha256')]}
    if req['bindings']!=expected_bindings:raise ValueError('Request bindings differ from controls')
    auth_bytes=approval.read_bytes()
    if sha(auth_bytes)!=approval_pin:raise ValueError('Unreviewed authorization bytes')
    auth=json.loads(auth_bytes);plan=json.loads(controls['plan.json']);experiment=plan['experiment_id']
    if auth.get('allowed') is not True:raise ValueError('Launch is not authorized')
    if experiment not in ('CAP-EXP-001','CAP-EXP-002','CAP-EXP-003','CAP-EXP-004'):raise ValueError('Unsupported experiment')
    if auth.get('allowed') is not True or auth.get('bindings')!=req['bindings'] or auth.get('authority')!='Quinton Evans' or auth.get('operation')!='launch_'+experiment or auth.get('data_mode')!='qualified_cohort':raise ValueError('Launch is not authorized')
    if verify_current:
        source,env=capture()
        if source!=controls['source.json'] or env!=controls['environment.json']:raise ValueError('Executing source/environment changed; prepare a new request')
        plan=json.loads(controls['plan.json'])
        if plan['design_sha256']!=sha((REPO/f'docs/capstone/operations/{experiment}-LAUNCH-PLAN-2026-09-28.md').read_bytes()):raise ValueError('Launch design changed')
    controls['authorization.json']=auth_bytes
    return controls


def synthetic_dataset():
    from copy import deepcopy
    import numpy as np
    from src.data.cohort_registry import COHORT_ID,MEMBERS
    from src.data.localizer_preprocessing import preprocess
    class Dataset:
        descriptors=[dict(study_id=s,cohort_id=COHORT_ID) for s in MEMBERS]
        recipe=json.loads((REPO/'configs/capstone/localizer-preprocessing-v1.json').read_bytes())
        def __getitem__(self,index):
            y=np.zeros((96,96,96),np.uint8);y[30+index:64,32:64,32:64]=1
            result=preprocess((y*200).astype(np.float32),np.diag([3,3,3,1]),self.recipe,target=y)
            result['provenance']=deepcopy(self.descriptors[index]);return result
        def __len__(self):return 2
    return Dataset()


def worker(dest,synthetic):
    import torch
    from src.data.manifest_records import canonical
    from src.training.localizer_run import input_record,MPSRun
    from src.training.localizer_smoke import execute,validate_terminal
    from src.operations.localizer_backup import backup_checkpoint
    from scripts.diagnostics.localizer_run_bridge import stores
    from src.data.cohort_registry import MEMBERS
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')!='0' or not torch.backends.mps.is_available():raise ValueError('Native MPS required')
    torch.set_num_threads(2);torch.mps.set_per_process_memory_fraction(min(1.,16*1024**3/torch.mps.recommended_max_memory()))
    request=json.loads((dest/'invocation.json').read_bytes())
    balanced=request.get('balanced',False)
    if synthetic:
        dataset=synthetic_dataset();source,environment=capture()
        config=dict(patch_size=[96]*3,seed=42,learning_rate=.003,weight_decay=.00001,max_steps=2)
        if balanced:
            config['loss_id']='balanced_ce_dice_v1'
            if request.get('experiment') in ('CAP-EXP-003','CAP-EXP-004'):config['learning_rate']=.0003
        plan=dict(schema_version='1.0.0',experiment_id='synthetic-executor',config=config,member_ids=MEMBERS,checkpoint_every=1,update_seconds=600,total_seconds=600)
        if balanced:plan['evaluation_policy']='balanced_and_legacy_v1'
        controls={'source.json':source,'environment.json':environment,'inputs.json':canonical(input_record(dataset)),'plan.json':canonical(plan)}
        bindings={key:sha(controls[name]) for name,key in [('inputs.json','inputs_sha256'),('source.json','source_sha256'),('environment.json','environment_sha256'),('plan.json','plan_sha256')]}
        controls['authorization.json']=canonical(dict(bindings=bindings,allowed=True,data_mode='synthetic',operation='synthetic_executor_check',authority='D-277' if balanced else 'D-274'))
    else:
        controls=checked_request(Path(request['request']),request['request_pin'],Path(request['approval']),request['approval_pin'])
        dataset=load_dataset();plan=json.loads(controls['plan.json']);config=plan['config']
        balanced=config.get('loss_id')=='balanced_ce_dice_v1'
        if canonical(input_record(dataset))!=controls['inputs.json']:raise ValueError('Resolved cohort inputs changed')
    identity=dict(schema_version='4.0.0' if balanced else '3.0.0',run_id=dest.name,purpose='bounded-localizer-smoke',training_data='synthetic' if synthetic else 'qualified_cohort',device='mps',config=config,
        **{key:sha(controls[name]) for name,key in [('inputs.json','inputs_sha256'),('source.json','source_sha256'),('environment.json','environment_sha256'),('plan.json','plan_sha256'),('authorization.json','authorization_sha256')]})
    put(dest/'identity.json',canonical(identity))
    for name,data in controls.items():put(dest/name,data)
    primary,backup,_=stores();peak_driver=0
    def guard():
        nonlocal peak_driver
        primary.check_root();torch.mps.synchronize()
        peak_driver=max(peak_driver,torch.mps.driver_allocated_memory())
        if peak_driver>16*1024**3:raise MemoryError('MPS driver memory cap')
    def event(row):
        row=dict(row,monotonic_seconds=time.monotonic())
        with (dest/'events.jsonl').open('ab') as stream:stream.write(canonical(row));stream.flush();os.fsync(stream.fileno())
        print(json.dumps(dict(state=row['state'],step=row.get('completed_step'))),flush=True)
    result,reference=execute(MPSRun(config),dataset,identity,controls,primary,guard=guard,event=event)
    cap=json.loads((REPO/'docs/capstone/operations/LOCALIZER-RUN-CAPABILITY-2026-09-28.json').read_bytes())
    backup_ref=backup_checkpoint(primary,backup,reference,identity,source_domain=cap['primary_volume_uuid'],destination_domain=cap['backup_volume_uuid'],validator=validate_terminal)
    put(dest/'recovery-request.json',canonical(dict(identity=identity,primary=reference,backup=backup_ref)))
    put(dest/'result.json',canonical(dict(result,terminal_reference=reference,backup_reference=backup_ref,peak_boundary_mps_driver_bytes=peak_driver)))


def recover(dest):
    import torch
    from src.operations.localizer_backup import restore_backup
    from src.training.localizer_smoke import validate_terminal,checkpoint_files
    from src.training.localizer_run import restore_payload
    from scripts.diagnostics.localizer_run_bridge import stores,setup_mps
    setup_mps()
    def audit(event,args):
        if event in ('open','os.scandir','os.listdir') and args and isinstance(args[0],(str,bytes)) and os.fsdecode(args[0]).startswith('/Volumes/PROWL-Data'):raise RuntimeError('Primary access forbidden')
    sys.addaudithook(audit)
    request=json.loads((dest/'recovery-request.json').read_bytes());_,backup,restore=stores(recovery_only=True)
    files,reference=restore_backup(backup,restore,request['backup'],request['primary'],request['identity'],validator=validate_terminal)
    session=restore_payload(checkpoint_files(files),request['identity'])
    # Independently stored state dictates the same fixed probe; model loaded from backup only.
    cfg=request['identity']['config'];x=torch.full((1,*cfg['patch_size']),.25);pred=session.predict(x)
    expected=torch.load(BytesIO(files['probe.pt']),weights_only=True)
    difference=(pred-expected).abs().max().item()
    if not torch.allclose(pred,expected,rtol=0,atol=1e-5):raise ValueError('Restored model probability mismatch')
    put(dest/'recovery.json',encoded(dict(state='restore_tested',reference=reference,step=session.step,
        finite_probe=True,max_probability_difference=difference,primary_reads_forbidden=True,backup_receipt_sha256=request['backup']['receipt_sha256'])))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--balanced',action='store_true');parser.add_argument('--experiment',choices=['CAP-EXP-001','CAP-EXP-002','CAP-EXP-003','CAP-EXP-004']);parser.add_argument('--synthetic-check',action='store_true');parser.add_argument('--launch',action='store_true')
    parser.add_argument('--request',type=Path);parser.add_argument('--request-pin');parser.add_argument('--approval',type=Path);parser.add_argument('--approval-pin')
    parser.add_argument('--worker',type=Path);parser.add_argument('--recover',type=Path);parser.add_argument('--synthetic-worker',action='store_true');args=parser.parse_args()
    if sum((args.prepare,args.synthetic_check,args.launch))>1:parser.error('Choose exactly one public mode')
    if args.prepare:return prepare(args.balanced,args.experiment)
    if args.worker or args.recover:
        dest=args.worker or args.recover
        if dest.parent!=OUTPUT or dest.resolve(strict=True)!=dest:raise ValueError('Wrong output path')
        return worker(dest,args.synthetic_worker) if args.worker else recover(dest)
    if not args.synthetic_check and not args.launch:parser.error('Choose prepare, synthetic-check or explicitly authorized launch')
    if args.launch:
        if not all((args.request,args.request_pin,args.approval,args.approval_pin)):parser.error('Pinned request and approval are mandatory')
        checked_request(args.request,args.request_pin,args.approval,args.approval_pin)
    from scripts.diagnostics.localizer_resource_profile import power
    if not power()[0] or shutil.disk_usage(REPO).free<100*1024**3:raise RuntimeError('Power/free-space preflight')
    lock=os.open(OUTPUT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        dest=OUTPUT/('localizer-smoke-'+str(uuid4()));dest.mkdir()
        if args.launch:put(OUTPUT/('launch-claim-'+args.request_pin+'.json'),encoded(dict(run_id=dest.name,request_pin=args.request_pin,approval_pin=args.approval_pin)))
        put(dest/'invocation.json',encoded(dict(synthetic=args.synthetic_check,balanced=args.balanced or args.experiment in ('CAP-EXP-002','CAP-EXP-003','CAP-EXP-004'),experiment=args.experiment,request=str(args.request) if args.request else None,
            request_pin=args.request_pin,approval=str(args.approval) if args.approval else None,approval_pin=args.approval_pin)))
        print(dest,flush=True);start=time.monotonic();peak=0;limit=600 if args.synthetic_check else 1200
        for mode in ('worker','recover'):
            cmd=[sys.executable,'-m','scripts.diagnostics.localizer_smoke_run','--'+mode,str(dest)]
            if args.synthetic_check and mode=='worker':cmd.append('--synthetic-worker')
            reason=None
            with (dest/(mode+'.log')).open('xb') as log:
                proc=subprocess.Popen(cmd,cwd=REPO,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTORCH_ENABLE_MPS_FALLBACK='0'),stdout=log,stderr=subprocess.STDOUT)
                try:
                    while proc.poll() is None:
                        if time.monotonic()-start>=limit:raise RuntimeError('Total time cap')
                        if not power()[0]:raise RuntimeError('AC power lost')
                        journal=dest/'events.jsonl'
                        if mode=='worker' and journal.exists():
                            update_start=None
                            for line in journal.read_bytes().splitlines(keepends=True):
                                if not line.endswith(b'\n'):continue
                                item=json.loads(line)
                                if item['state']=='before_evaluation':update_start=item['monotonic_seconds']
                                elif item['state']=='update_phase_complete':update_start=None
                            if update_start is not None and time.monotonic()-update_start>=600:raise RuntimeError('Update phase time cap')
                        rss=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                        if rss.returncode==0 and rss.stdout.strip():peak=max(peak,int(rss.stdout.strip())*1024)
                        elif proc.poll() is None:raise RuntimeError('Memory monitor failed')
                        if peak>16*1024**3 or shutil.disk_usage(REPO).free<100*1024**3:raise RuntimeError('Memory/free-space cap')
                        if sum(p.stat().st_size for p in dest.iterdir() if p.is_file())>1024**3:raise RuntimeError('Local output cap')
                        time.sleep(.25)
                    if proc.returncode:raise RuntimeError('Child failed')
                except BaseException as error:reason=str(error);raise
                finally:
                    if proc.poll() is None:
                        proc.terminate()
                        try:proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
                    put(dest/(mode+'-supervisor.json'),encoded(dict(exit_code=proc.returncode,stop_reason=reason,peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start)))
        refs={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in dest.iterdir() if p.is_file()}
        put(dest/'receipt.json',encoded(dict(state='complete',files=refs,synthetic_only=args.synthetic_check)))
        print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()),flush=True)
    finally:os.close(lock)


if __name__=='__main__':main()
