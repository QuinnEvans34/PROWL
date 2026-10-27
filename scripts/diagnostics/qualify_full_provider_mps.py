"""Bounded full-provider MPS engineering stages. Never starts scientific training."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.operations.kd_gpu_qualification_v1 import (
    STAGES, LIMITS, prepare, validate_request, dispatch, write,
)
from src.data.segmenter_teacher_cache_v1 import sha


def usage(path):
    return sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file())


def safety(request, root):
    from src.operations.full_training_platform import require_ac
    from scripts.diagnostics.qualify_distillation_mac import storage_preflight
    require_ac(); storage_preflight()
    backup = Path(request['backup'])
    allowed = (Path.home()/'PROWL-Backups').resolve()
    if allowed not in backup.parents or not backup.parent.is_dir():
        raise ValueError('Independent internal backup under PROWL-Backups required')
    if Path(root).stat().st_dev == backup.parent.stat().st_dev:
        raise ValueError('Backup must use a separate filesystem')
    if usage(root) > LIMITS['output_bytes'] or usage(backup) > LIMITS['backup_bytes']:
        raise ValueError('Qualification output/backup cap exceeded')


def worker(root, stage, request_sha256):
    if os.environ.get('PROWL_FULL_KD_ENGINEERING') != '1':
        raise ValueError('Owned supervisor required')
    request, prepared = validate_request(root, request_sha256)
    # Confirm dispatch identity before any model allocation.
    destination = root/stage
    dispatched = json.loads((destination/'dispatch.json').read_text())
    if dispatched['stage'] != stage or dispatched['request_sha256'] != request_sha256:
        raise ValueError('Dispatch identity mismatch')
    import torch
    from scripts.diagnostics.prepare_rsuper_full_provider import provider
    from scripts.diagnostics.mac_kd_synthetic import compare
    from src.data.segmenter_teacher_cache_v1 import TeacherTargetStore
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_errata_kd_session_v1 import OnDemandStudent, ErrataKDSession
    from src.training.segmenter_distillation_v1 import DistillationConfig
    from src.training.segmenter_kd_native_evaluation_v1 import evaluate
    from scripts.diagnostics.qualify_distillation_mac import check_storage_budget, storage_preflight
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') != '0' or not torch.backends.mps.is_available():
        raise ValueError('Actual MPS without fallback required')
    torch.set_num_threads(1)
    inputs, _, _ = provider()
    design = prepared['operational_designs'][1]
    if inputs.pin != design['provider_sha256']:
        raise ValueError('Full provider changed')
    target_root = Path(prepared['admitted_targets'])
    targets = TeacherTargetStore(target_root, design['target_manifest_sha256'], control=inputs.control,
                  common_identity=json.loads((target_root/'common-identity.json').read_text()))
    cfg = deepcopy(design['student_configuration'])
    init = cfg['initialization']; init['checkpoint'] = str((ROOT/init['checkpoint']).resolve())
    if sha(init['checkpoint']) != init['sha256']:
        raise ValueError('Initialization changed')
    def student():
        return OnDemandStudent(Session(cfg['session'], inputs.control, device='mps', initialization=init))
    def kd(weight):
        loss = {k:v for k,v in design['distillation'].items() if k != 'policy'}
        loss['max_weight'] = weight
        return ErrataKDSession(student(), teacher_identity=prepared['teacher'],
                loss_config=DistillationConfig(**loss), target_manifest_sha256=targets.pin)
    memory_samples = []
    def tick():
        safety(request, root); torch.mps.synchronize()
        memory_samples.append(torch.mps.driver_allocated_memory())
        if memory_samples[-1] > LIMITS['mps_bytes']:
            raise ValueError('MPS allocation cap exceeded')
    def backup_admission(size):
        storage = storage_preflight()
        check_storage_budget(storage['internal_free_bytes'],storage['external_free_bytes'],
                             storage['existing_backup_bytes'],new_backup_bytes=size)
    from src.training.kd_executor_qualification_v1 import exercise
    exercise(root,stage,request,inputs=inputs,targets=targets,student=student,kd=kd,tick=tick,
             compare=compare,evaluate=evaluate,backup_admission=backup_admission)
    write(destination/'device.json',dict(device='mps',fallback=False,
          max_observed_driver_bytes=max(memory_samples),samples=len(memory_samples),
          note='Sampled at updates/evaluation callbacks, not a continuous device peak'))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--stage',choices=STAGES)
    mode.add_argument('--worker',choices=STAGES,help=argparse.SUPPRESS)
    parser.add_argument('--preparation',type=Path)
    parser.add_argument('--preparation-sha256')
    parser.add_argument('--request-sha256')
    parser.add_argument('--backup',type=Path)
    parser.add_argument('--positive-dev')
    parser.add_argument('--empty-dev')
    parser.add_argument('--explicit-run',action='store_true')
    args=parser.parse_args(argv)
    if args.prepare:
        if not all((args.preparation,args.preparation_sha256,args.backup,args.positive_dev,args.empty_dev)):
            parser.error('Preparation, backup and two development identities required')
        files=[Path(__file__),ROOT/'src/training/kd_executor_qualification_v1.py',ROOT/'src/operations/kd_gpu_qualification_v1.py',
               ROOT/'scripts/diagnostics/prepare_rsuper_full_provider.py',
               ROOT/'scripts/diagnostics/bind_mac_distillation_metadata.py',
               ROOT/'scripts/diagnostics/qualify_distillation_mac.py',ROOT/'scripts/diagnostics/mac_kd_synthetic.py']
        prepare(args.preparation,args.preparation_sha256,args.root,args.backup,
                args.positive_dev,args.empty_dev,{str(p.resolve()):sha(p) for p in files})
        return
    if not args.request_sha256: parser.error('Exact request hash required')
    if args.worker:
        worker(args.root,args.worker,args.request_sha256);return
    if not args.explicit_run: parser.error('Explicit engineering run selection required')
    from src.operations.full_training_platform import training_guard
    from src.operations.mac_teacher_supervision_v2 import run
    environment=dict(os.environ,PROWL_FULL_KD_ENGINEERING='1',PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='1')
    dispatch(args.root,args.stage,args.request_sha256,
        guard=lambda:training_guard(ROOT/'outputs/prowl/.mps-profile.lock'),
        preflight=lambda r:safety(r,args.root),supervise=run,env=environment,
        command=lambda stage:['caffeinate','-i',sys.executable,str(Path(__file__).resolve()),
                             '--root',str(args.root),'--worker',stage,'--request-sha256',args.request_sha256])


if __name__=='__main__': main()
