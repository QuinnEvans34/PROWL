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
from src.operations.mac_kd_resume_controller_v1 import plans,completed
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
        result=subprocess.run(['ps','-p',str(proc['worker']),'-o','lstart='],capture_output=True,text=True)
        if result.returncode==0 and result.stdout.strip()==proc['worker_start']:
            raise ValueError('Parent worker still running')


def safety(r, additional_backup_bytes=0):
    original.safety(r['scientific'])
    # Count the entire retained lineage, not a fresh allowance for each continuation.
    roots={r['scientific']['output'],r['output']};backups={r['scientific']['backup'],r['backup']}
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
    out,backup=Path(out).absolute(),Path(backup).absolute()
    if out.exists() or backup.exists():raise FileExistsError('Fresh continuation destinations required')
    if (Path.home()/'PROWL-Backups').resolve() not in backup.parents:raise ValueError('Internal independent backup required')
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        stopped(parent)
        p=plans(source,source_pin,parent,parent_pin,arm,checkpoint)
        original.check(source,source_pin)
        files=[Path(__file__).resolve(),ROOT/'src/operations/mac_kd_resume_controller_v1.py',
               ROOT/'src/operations/kd_continuation_v1.py',ROOT/'src/training/segmenter_kd_continuation_executor_v1.py',
               ROOT/'scripts/diagnostics/pause_mac_kd_comparison.py']
        r=dict(version='mac-kd-continuation-launch-1',original=str(Path(source).resolve()),original_sha256=source_pin,
               parent=str(Path(parent).resolve()),parent_sha256=parent_pin,output=str(out),backup=str(backup),runtime=runtime(),
               scientific=p['scientific'],segments=p['segments'],context=p['context'],order=p['order'],budget=p['budget'],
               pins={**p['inherited_pins'],**{str(f):sha(f) for f in files}},
               scientific_ready=False,requires_gpu_continuation_qualification=True,automatic_retry=False)
        safety(r);out.mkdir();write(out/'ready.json',r)
        return r


def check(root,pin):
    r=read_bound(Path(root)/'ready.json',pin)
    if r['version']!='mac-kd-continuation-launch-1' or r['runtime']!=runtime():raise ValueError('Continuation identity changed')
    check_pins(r['pins']);original.check(Path(r['original']),r['original_sha256']);stopped(r['parent']);safety(r)
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
    from src.operations.mac_teacher_supervision_v2 import run
    r=check(root,pin)
    q=read_bound(qualification,qualification_pin)
    if (q.get('version')!='mac-kd-continuation-gpu-1' or q.get('success') is not True
            or q.get('continuation_sha256')!=pin or q.get('workers_reaped') is not True):
        raise ValueError('Bound real GPU continuation qualification required')
    check_pins(q['evidence'])
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
