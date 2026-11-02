"""Explicit, receipt-bound continuation; original comparison files stay frozen."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import train_mac_kd_comparison as original
from src.operations.mac_kd_resume_controller_v1 import completed
from src.operations.mac_kd_control_closeout_v1 import inspect as inspect_control
from src.operations.kd_gpu_qualification_v1 import write,check_pins,runtime
from src.data.teacher_target_publication_v1 import read_bound
from src.data.segmenter_teacher_cache_v1 import sha


def stopped(parent):
    """No matching registered owner or worker may remain; reused PIDs are not signalled."""
    parent=Path(parent)
    job=json.loads((parent/'dispatch.json').read_text())
    found=subprocess.run(['launchctl','print',job['target']],capture_output=True,text=True)
    if found.returncode==0:
        import re
        if re.search(r'^\s*pid = \d+\s*$',found.stdout,re.M):raise ValueError('Parent supervisor still running')
    elif 'Could not find service' not in found.stderr:
        raise ValueError('Cannot establish parent launchd state')
    for arm in ('control','treatment'):
        p=parent/arm/'process.json'
        if not p.exists():continue
        proc=json.loads(p.read_text())
        from src.operations.mac_worker_cleanup_v3 import snapshot
        if any(row['group']==proc['worker'] for row in snapshot().values()):
            raise ValueError('Parent process group still present')
        result=subprocess.run(['ps','-p',str(proc['worker']),'-o','lstart='],capture_output=True,text=True)
        if result.returncode==0 and result.stdout.strip()==proc['worker_start']:
            raise ValueError('Parent worker still running')


def safety(r, additional_backup_bytes=0):
    original.safety(r['scientific'])
    # Count the entire retained lineage, not a fresh allowance for each continuation.
    roots={r['scientific']['output'],r['output']};backups={r['scientific']['backup'],r['backup']}
    if r.get('parent'):
        roots.add(r['parent'])
        backups.add(r['parent_backup'])
    for rows in r['segments'].values():
        roots.update(x['root'] for x in rows);backups.update(x['backup'] for x in rows)
    if sum(original.usage(p) for p in roots)>original.LIMITS['output_bytes']:
        raise ValueError('Cumulative comparison output cap')
    if sum(original.usage(p) for p in backups)+additional_backup_bytes>original.LIMITS['backup_bytes']:
        raise ValueError('Cumulative comparison backup cap')
    if Path(r['output']).parent.stat().st_dev==Path(r['backup']).parent.stat().st_dev:
        raise ValueError('Independent backup filesystem required')


def prepare(source,source_pin,parent,parent_pin,arm,checkpoint,out,backup):
    from src.operations.full_training_platform import training_guard
    from src.operations.kd_continuation_v1 import inspect_checkpoint,remaining_budget
    out,backup=Path(out).absolute(),Path(backup).absolute()
    if out.exists() or backup.exists():raise FileExistsError('Fresh continuation destinations required')
    if (Path.home()/'PROWL-Backups').resolve() not in backup.parents:raise ValueError('Internal independent backup required')
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        if arm!='treatment':raise ValueError('Treatment continuation only')
        parent=Path(parent).resolve();stopped(parent)
        prior=read_bound(parent/'ready.json',parent_pin)
        if prior['version']=='mac-kd-reviewed-treatment-launch-2':
            from scripts import resume_mac_kd_treatment_v2 as previous
        elif prior['version']=='mac-kd-treatment-resume-3':
            previous=sys.modules[__name__]
        else:raise ValueError('Unsupported treatment parent')
        prior=previous.check(parent,parent_pin)
        if prior['original']!=str(Path(source).resolve()) or prior['original_sha256']!=source_pin:
            raise ValueError('Wrong original comparison')
        scientific=original.check(source,source_pin)
        if (parent/'treatment/complete.json').exists():raise ValueError('Treatment already complete')
        resources=json.loads((parent/'treatment/resources.json').read_text())
        if resources.get('workers_reaped') is not True or resources.get('surviving_workers') or resources.get('cleanup_error'):
            raise ValueError('Verified clean parent required')
        context=inspect_checkpoint(parent/'treatment/execution',Path(prior['backup'])/'treatment',checkpoint)
        dispatch=json.loads((parent/'treatment/dispatch.json').read_text())
        if dispatch['receipt_sha256']!=parent_pin:raise ValueError('Parent dispatch mismatch')
        segments=deepcopy(prior['segments'])
        if any(x['root']==str(parent) for x in segments['treatment']):raise ValueError('Duplicate parent charge')
        files=[parent/'treatment'/n for n in ('resources.json','process.json','dispatch.json')]
        files.append(parent/'treatment/execution/history.jsonl')
        segments['treatment'].append(dict(root=str(parent),backup=prior['backup'],run_id=dispatch['run_id'],
            resources=resources,pins={str(f):sha(f) for f in files},checkpoint_step=context['step']))
        budget=remaining_budget(scientific['limits']['seconds_per_arm'],[x['resources'] for x in segments['treatment']])
        files=[Path(__file__).resolve(),ROOT/'scripts/diagnostics/qualify_mac_kd_resume_v3.py',
               ROOT/'scripts/diagnostics/pause_mac_kd_resume_v3.py']
        pins={**prior['pins'],str(parent/'ready.json'):parent_pin,**context['pins'],**{str(f):sha(f) for f in files}}
        for rows in segments.values():
            for row in rows:check_pins(row['pins']);pins.update(row['pins'])
        r=dict(version='mac-kd-treatment-resume-3',original=str(Path(source).resolve()),original_sha256=source_pin,
               parent=str(parent),parent_sha256=parent_pin,output=str(out),backup=str(backup),runtime=runtime(),
               scientific=scientific,segments=segments,context=context,order=['treatment'],budget=budget,parent_backup=prior['backup'],
               pins=pins,control_closeout=prior['control_closeout'],operator_resume_authorized=True,
               scientific_ready=False,requires_gpu_continuation_qualification=True,automatic_retry=False)
        safety(r);out.mkdir();write(out/'ready.json',r);return r


def check(root,pin):
    r=read_bound(Path(root)/'ready.json',pin)
    if r['version']!='mac-kd-treatment-resume-3' or r['runtime']!=runtime():raise ValueError('Continuation identity changed')
    if r['order']!=['treatment'] or not r['context']:raise ValueError('Checkpoint treatment required')
    check_pins(r['pins']);original.check(Path(r['original']),r['original_sha256']);stopped(r['parent']);safety(r)
    from src.operations.kd_continuation_v1 import remaining_budget,inspect_checkpoint
    budget=remaining_budget(r['scientific']['limits']['seconds_per_arm'],[x['resources'] for x in r['segments']['treatment']])
    if budget!=r['budget']:raise ValueError('Budget changed')
    actual=inspect_checkpoint(Path(r['parent'])/'treatment/execution',Path(r['parent_backup'])/'treatment',Path(r['context']['checkpoint']).name)
    if actual!=r['context']:raise ValueError('Checkpoint context changed')
    return r


def pause_requested(root,pin):
    path=Path(root)/'pause-request.json'
    if not path.exists():return False
    request=json.loads(path.read_text())
    if request.get('receipt_sha256')!=pin or request.get('action')!='operator_pause':
        raise ValueError('Invalid pause request')
    return True


def worker(root,pin,arm,rid):
    if os.environ.get('PROWL_MAC_KD_CONTINUATION')!='1':raise ValueError('Owned supervisor required')
    r=check(root,pin);dispatch=json.loads((root/arm/'dispatch.json').read_text())
    if dispatch['run_id']!=rid or dispatch['receipt_sha256']!=pin:raise ValueError('Dispatch mismatch')
    import torch
    from mlflow import MlflowClient
    from scripts.diagnostics.prepare_rsuper_full_provider import provider
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_errata_kd_session_v1 import OnDemandStudent,ErrataKDSession
    from src.training.segmenter_distillation_v1 import DistillationConfig
    from src.training.segmenter_distillation_session_v1 import BoundDistillationSession
    from src.training.segmenter_distillation_tracking_v1 import DistillationTracker
    from src.training.segmenter_kd_continuation_executor_v1 import execute
    from src.data.segmenter_teacher_cache_v1 import TeacherTargetStore
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')!='0' or not torch.backends.mps.is_available():raise ValueError('Actual MPS required')
    torch.set_num_threads(1);p,_,_=provider();sci=r['scientific'];design=sci['designs'][sci['order'].index(arm)]
    if p.pin!=design['provider_sha256']:raise ValueError('Provider differs')
    target=Path(sci['preparation']['admitted_targets'])
    targets=TeacherTargetStore(target,design['target_manifest_sha256'],control=p.control,
            common_identity=json.loads((target/'common-identity.json').read_text()))
    cfg=deepcopy(design['student_configuration']);loss={k:v for k,v in design['distillation'].items() if k!='policy'}
    context=r['context'] if arm==r['order'][0] else None
    if context:
        saved=torch.load(context['checkpoint'],weights_only=True,map_location='cpu')
        session=ErrataKDSession.restore(saved['session'],context['identity'])
        if (session.config!=cfg['session'] or session.control!=p.control or session.loss_config!=DistillationConfig(**loss)
                or session.identity['teacher']!=sci['preparation']['teacher']
                or session.identity['target_manifest_sha256']!=targets.pin):raise ValueError('Restored scientific identity differs')
    else:
        init=cfg['initialization'];init['checkpoint']=str((ROOT/init['checkpoint']).resolve())
        if sha(init['checkpoint'])!=init['sha256']:raise ValueError('Initialization differs')
        session=ErrataKDSession(OnDemandStudent(Session(cfg['session'],p.control,device='mps',initialization=init)),
            teacher_identity=sci['preparation']['teacher'],loss_config=DistillationConfig(**loss),target_manifest_sha256=targets.pin)
    backup=Path(r['backup'])/arm;backup.mkdir(parents=True,exist_ok=False)
    bound=dict(sci,output=r['output'],backup=r['backup'])
    def preserve(path):
        safety(r,Path(path).stat().st_size);original.preserve(path,backup,bound);safety(r)
    preserve(root/'ready.json')
    def tick():
        safety(r)
        if torch.mps.driver_allocated_memory()>original.LIMITS['mps_bytes']:raise ValueError('MPS allocation cap')
    def hook(path):preserve(path);preserve(path.parent/'history.jsonl')
    tracker=DistillationTracker(rid,root/arm,client=MlflowClient(tracking_uri=dispatch['tracking_uri']))
    result=execute(BoundDistillationSession(session,targets),p,root/arm/'execution',checkpoint_hook=hook,
                   continuation=context,pause_requested=lambda:pause_requested(root,pin),tick=tick,track=tracker)
    write(root/arm/'result.json',result);preserve(root/arm/'result.json');preserve(root/arm/'execution/history.jsonl')


def launch(root,pin,qualification,qualification_pin):
    """Activation stays gated on a separately bound actual-GPU continuation receipt."""
    from mlflow import MlflowClient
    from src.operations.full_training_platform import training_guard
    from src.operations.mac_teacher_supervision_v3 import run
    r=check(root,pin)
    from scripts.diagnostics.qualify_mac_kd_resume_v3 import validate_qualification
    validate_qualification(qualification,qualification_pin,pin)
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        stopped(r['parent']);write(root/'launch.json',dict(receipt_sha256=pin,qualification_sha256=qualification_pin))
        uri='sqlite:///'+str(root/'mlflow.db');client=MlflowClient(tracking_uri=uri)
        exp=client.create_experiment('PROWL Mac KD continuation',artifact_location=(root/'mlflow-artifacts').as_uri())
        for arm in r['order']:
            if pause_requested(root,pin):
                write(root/'paused.json',dict(paused=True,next_arm=arm,between_arms=True));return
            if arm!=r['order'][0]:completed(root,r['backup'],r['order'][0])
            dest=root/arm;dest.mkdir()
            parent_runs=[s['run_id'] for s in r['segments'][arm]]
            rid=client.create_run(exp,tags={'mlflow.runName':arm+' continuation','arm':arm,
                 'comparison_sha256':r['original_sha256'],'continuation_sha256':pin,
                 'parent_run_ids':json.dumps(parent_runs),'scope':r['scientific']['scope']}).info.run_id
            write(dest/'dispatch.json',dict(run_id=rid,tracking_uri=uri,receipt_sha256=pin,parent_run_ids=parent_runs))
            seconds=r['budget']['remaining_seconds'] if arm==r['order'][0] else original.LIMITS['seconds_per_arm']
            try:
                client.log_dict(rid,r['scientific']['designs'][r['scientific']['order'].index(arm)],'recipe.json')
                env=dict(os.environ,PROWL_MAC_KD_CONTINUATION='1',PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='1')
                ok=run(['caffeinate','-i',sys.executable,str(Path(__file__).resolve()),'--root',str(root),
                        '--receipt-sha256',pin,'--worker',arm,'--run-id',rid],dest,
                        seconds=seconds,rss_bytes=original.LIMITS['rss_bytes'],tick=lambda:safety(r),env=env)
                resources=json.loads((dest/'resources.json').read_text());result=json.loads((dest/'result.json').read_text()) if ok else {}
                if not ok or resources.get('success') is not True or resources.get('workers_reaped') is not True or resources.get('exit_code')!=0:
                    raise ValueError('Continuation failed; no successor')
                bound=dict(r['scientific'],output=r['output'],backup=r['backup'])
                for name in ('resources.json','dispatch.json'):
                    safety(r,(dest/name).stat().st_size)
                    original.preserve(dest/name,Path(r['backup'])/arm,bound)
                safety(r)
                for path in (dest/'execution').glob('*'):
                    if path.is_file() and sha(path)!=sha(Path(r['backup'])/arm/path.name):raise ValueError('Final backup mismatch')
                if (dest/'tracking-warning.json').exists():raise ValueError('Tracking degraded; no successor')
                if result.get('status')=='paused':
                    client.set_tag(rid,'operator_paused','true');client.set_terminated(rid,'KILLED')
                    write(root/'paused.json',dict(paused=True,arm=arm,step=result['completed_updates']));return
                if result.get('completed') is not True or result.get('completed_updates')!=24000:
                    raise ValueError('Incomplete arm; no successor')
                client.set_terminated(rid,'FINISHED');write(dest/'complete.json',dict(success=True,run_id=rid,completed_updates=24000))
            except BaseException:client.set_terminated(rid,'FAILED');raise
        write(root/'complete.json',dict(success=True,arms=r['order']))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    m=p.add_mutually_exclusive_group(required=True);m.add_argument('--prepare',action='store_true');m.add_argument('--launch',action='store_true');m.add_argument('--worker',choices=('control','treatment'))
    for name in ('original','parent','backup','qualification'):p.add_argument('--'+name,type=Path)
    for name in ('original-sha256','parent-sha256','receipt-sha256','qualification-sha256','run-id'):p.add_argument('--'+name)
    p.add_argument('--arm',choices=('control','treatment'));p.add_argument('--checkpoint',default='last.pt')
    a=p.parse_args()
    if a.prepare:
        prepare(a.original,a.original_sha256,a.parent,a.parent_sha256,a.arm,a.checkpoint,a.root,a.backup);print(sha(a.root/'ready.json'))
    elif a.launch:launch(a.root,a.receipt_sha256,a.qualification,a.qualification_sha256)
    else:worker(a.root,a.receipt_sha256,a.worker,a.run_id)

if __name__=='__main__':main()
