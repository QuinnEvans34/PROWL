"""Freeze and explicitly launch the qualified Mac control/KD pair, once each."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.segmenter_teacher_cache_v1 import sha
from src.data.teacher_target_publication_v1 import read_bound
from src.operations.kd_gpu_qualification_v1 import validate_request, prerequisites, write, check_pins, runtime
from scripts.diagnostics.qualify_distillation_mac import storage_preflight, check_storage_budget

LIMITS = dict(seconds_per_arm=96*3600, rss_bytes=12*1024**3, mps_bytes=12*1024**3,
              output_bytes=8*1024**3, backup_bytes=4*1024**3)


def usage(root):
    return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())


def qualified(root, pin):
    request, prepared = validate_request(root, pin)
    parents = prerequisites(root, 'cold', pin)
    cold = json.loads((Path(root)/'cold/receipt.json').read_text())
    if cold['success'] is not True or cold['stage'] != 'cold' or cold['request_sha256'] != pin or cold['parents'] != parents:
        raise ValueError('Qualified cold recovery required')
    check_pins(cold['artifacts'])
    return request, prepared


def safety(receipt):
    from src.operations.full_training_platform import require_ac
    require_ac()
    space = storage_preflight()
    out, backup = Path(receipt['output']), Path(receipt['backup'])
    if out.parent.stat().st_dev == backup.parent.stat().st_dev:
        raise ValueError('Independent backup filesystem required')
    if usage(out) > LIMITS['output_bytes'] or usage(backup) > LIMITS['backup_bytes']:
        raise ValueError('Comparison storage budget exceeded')
    return space


def freeze(qualification, pin, output, backup):
    request, prepared = qualified(qualification, pin)
    output, backup = Path(output).absolute(), Path(backup).absolute()
    if output.exists() or backup.exists():
        raise FileExistsError('Fresh comparison and backup required')
    if (Path.home()/'PROWL-Backups').resolve() not in backup.parents:
        raise ValueError('Internal PROWL backup location required')
    designs = deepcopy(prepared['operational_designs'])
    paired = deepcopy(designs[0]); paired['distillation']['max_weight'] = .1
    if paired != designs[1]:
        raise ValueError('Unmatched recipes')
    maximum = max(p.stat().st_size for p in Path(qualification).rglob('*.pt'))
    # 15 unique states/arm plus physical best alias and atomic replacement headroom.
    planned = 34*maximum + 256*1024**2
    space = storage_preflight()
    check_storage_budget(space['internal_free_bytes'], space['external_free_bytes'],
                         space['existing_backup_bytes'], new_backup_bytes=planned,
                         planned_external_bytes=planned)
    files = [Path(__file__).resolve(), ROOT/'scripts/diagnostics/launch_mac_owned_job.py']
    files += sorted(Path(qualification).glob('*/receipt.json'))
    files += [ROOT/'tests/test_mac_kd_comparison_launch.py']
    value = dict(version='mac-matched-kd-launch-1', qualification=str(Path(qualification).resolve()),
        qualification_sha256=pin, output=str(output), backup=str(backup), limits=LIMITS,
        runtime=runtime(), pins={str(p.resolve()):sha(p) for p in files},
        designs=designs, preparation=prepared, maximum_checkpoint_bytes=maximum,
        projected_backup_bytes=planned, scope='teacher-assisted exploratory; teacher membership unknown',
        order=['control','treatment'], explicit_user_authorization=True, automatic_retry=False)
    safety(value)
    output.mkdir(); write(output/'ready.json', value)
    return value


def check(root, pin):
    r = read_bound(Path(root)/'ready.json', pin)
    if r['version'] != 'mac-matched-kd-launch-1' or r['limits'] != LIMITS or r['runtime'] != runtime():
        raise ValueError('Launch identity changed')
    check_pins(r['pins']); qualified(r['qualification'], r['qualification_sha256']); safety(r)
    return r


def preserve(path, backup, receipt):
    """Retain the previous recovery state only after the new copy verifies."""
    path, backup = Path(path), Path(backup)
    safety(receipt)
    space = storage_preflight()
    check_storage_budget(space['internal_free_bytes'], space['external_free_bytes'],
                         space['existing_backup_bytes'], new_backup_bytes=path.stat().st_size)
    temporary = backup/(path.name+'.partial')
    if usage(receipt['backup'])+path.stat().st_size > LIMITS['backup_bytes']:
        raise ValueError('Backup write would exceed budget')
    with path.open('rb') as source, temporary.open('xb') as target:
        shutil.copyfileobj(source,target); target.flush(); os.fsync(target.fileno())
    if sha(path) != sha(temporary):
        raise ValueError('Backup hash mismatch')
    destination = backup/path.name
    if path.name == 'last.pt' and destination.exists():
        os.replace(destination,backup/'previous-last.pt')
    os.replace(temporary,destination)
    fd=os.open(backup,os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def worker(root, pin, arm, run_id):
    if os.environ.get('PROWL_MAC_KD_SCIENCE') != '1':
        raise ValueError('Owned supervisor required')
    r=check(root,pin)
    dispatch=json.loads((root/arm/'dispatch.json').read_text())
    if dispatch['receipt_sha256'] != pin or dispatch['run_id'] != run_id:
        raise ValueError('Worker dispatch mismatch')
    import torch
    from mlflow import MlflowClient
    from scripts.diagnostics.prepare_rsuper_full_provider import provider
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_errata_kd_session_v1 import OnDemandStudent, ErrataKDSession
    from src.training.segmenter_distillation_v1 import DistillationConfig
    from src.training.segmenter_distillation_session_v1 import BoundDistillationSession
    from src.training.segmenter_distillation_tracking_v1 import DistillationTracker
    from src.training.segmenter_kd_evidence_executor_v1 import execute
    from src.data.segmenter_teacher_cache_v1 import TeacherTargetStore
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') != '0' or not torch.backends.mps.is_available():
        raise ValueError('Actual MPS required without fallback')
    torch.set_num_threads(1)
    p,_,_=provider(); design=r['designs'][r['order'].index(arm)]
    if p.pin != design['provider_sha256']: raise ValueError('Provider changed')
    target=Path(r['preparation']['admitted_targets'])
    targets=TeacherTargetStore(target,design['target_manifest_sha256'],control=p.control,
                              common_identity=json.loads((target/'common-identity.json').read_text()))
    cfg=deepcopy(design['student_configuration']); init=cfg['initialization']
    init['checkpoint']=str((ROOT/init['checkpoint']).resolve())
    if sha(init['checkpoint']) != init['sha256']: raise ValueError('Initialization changed')
    loss={k:v for k,v in design['distillation'].items() if k!='policy'}
    s=ErrataKDSession(OnDemandStudent(Session(cfg['session'],p.control,device='mps',initialization=init)),
        teacher_identity=r['preparation']['teacher'],loss_config=DistillationConfig(**loss),
        target_manifest_sha256=targets.pin)
    backup=Path(r['backup'])/arm; backup.mkdir(parents=True,exist_ok=False)
    preserve(root/'ready.json',backup,r)
    def tick():
        safety(r)
        if torch.mps.driver_allocated_memory()>LIMITS['mps_bytes']:
            raise ValueError('MPS allocation cap exceeded')
    destination=root/arm
    def hook(path):
        preserve(path,backup,r); preserve(path.parent/'history.jsonl',backup,r)
    client=MlflowClient(tracking_uri=dispatch['tracking_uri'])
    tracker=DistillationTracker(run_id,destination,client=client)
    result=execute(BoundDistillationSession(s,targets),p,destination/'execution',
        checkpoint_hook=hook,tick=tick,track=tracker,checkpoint_every=500,validate_every=2000)
    write(destination/'result.json',result)
    preserve(destination/'result.json',backup,r)
    preserve(destination/'execution/history.jsonl',backup,r)


def launch(root, pin):
    from mlflow import MlflowClient
    from src.operations.full_training_platform import training_guard
    from src.operations.mac_teacher_supervision_v2 import run
    r=check(root,pin)
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        # Claim the pair once. No restart/retry is implicit in this entry point.
        write(root/'launch.json',dict(receipt_sha256=pin,supervisor=os.getpid(),utc_ms=int(time.time()*1000)))
        uri='sqlite:///'+str(root/'mlflow.db')
        client=MlflowClient(tracking_uri=uri)
        experiment=client.create_experiment('PROWL Mac matched KD',artifact_location=(root/'mlflow-artifacts').as_uri())
        for arm in r['order']:
            check(root,pin)
            dest=root/arm; dest.mkdir()
            rid=client.create_run(experiment,tags={'mlflow.runName':arm,'comparison_sha256':pin,
                    'scope':r['scope'],'arm':arm}).info.run_id
            write(dest/'dispatch.json',dict(run_id=rid,tracking_uri=uri,receipt_sha256=pin))
            try:
                client.log_dict(rid,r['designs'][r['order'].index(arm)],'recipe.json')
                env=dict(os.environ,PROWL_MAC_KD_SCIENCE='1',PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='1')
                ok=run(['caffeinate','-i',sys.executable,str(Path(__file__).resolve()),'--root',str(root),
                        '--receipt-sha256',pin,'--worker',arm,'--run-id',rid],dest,
                        seconds=LIMITS['seconds_per_arm'],rss_bytes=LIMITS['rss_bytes'],tick=lambda:safety(r),env=env)
                resources=json.loads((dest/'resources.json').read_text())
                result=json.loads((dest/'result.json').read_text()) if ok else {}
                if (not ok or resources.get('success') is not True or resources.get('exit_code') != 0
                        or resources.get('workers_reaped') is not True or result.get('completed_updates')!=24000):
                    raise ValueError('Arm failed; preserve attempt and do not launch successor')
                backup=Path(r['backup'])/arm
                preserve(dest/'resources.json',backup,r)
                preserve(dest/'dispatch.json',backup,r)
                for path in (dest/'execution').glob('*'):
                    if path.is_file() and sha(path)!=sha(backup/path.name):
                        raise ValueError('Final independent backup mismatch')
                if (dest/'tracking-warning.json').exists():
                    raise ValueError('Tracking degraded; reconcile before successor')
                client.set_terminated(rid,'FINISHED')
                write(dest/'complete.json',dict(success=True,run_id=rid,completed_updates=24000))
            except BaseException:
                client.set_terminated(rid,'FAILED'); raise
        write(root/'complete.json',dict(success=True,arms=r['order']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze',action='store_true'); mode.add_argument('--launch',action='store_true')
    mode.add_argument('--worker',choices=('control','treatment'))
    parser.add_argument('--qualification',type=Path); parser.add_argument('--qualification-sha256')
    parser.add_argument('--backup',type=Path); parser.add_argument('--receipt-sha256'); parser.add_argument('--run-id')
    args=parser.parse_args()
    if args.freeze:
        freeze(args.qualification,args.qualification_sha256,args.root,args.backup)
        print(sha(args.root/'ready.json'))
    elif args.launch: launch(args.root,args.receipt_sha256)
    else: worker(args.root,args.receipt_sha256,args.worker,args.run_id)

if __name__=='__main__':main()
