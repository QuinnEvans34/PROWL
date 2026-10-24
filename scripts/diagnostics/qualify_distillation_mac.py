"""Bounded Mac-only engineering checks. Synthetic inputs; never a scientific launcher."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data.manifest_records import canonical, digest
from src.operations.segmenter_duration_dispatch_v1 import watch
from src.operations.full_training_platform import training_guard

BASE = Path('/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023')


def write(path, value):
    import numpy as np
    def scalar(value):
        if isinstance(value, np.generic): return value.item()
        raise TypeError(type(value).__name__)
    value = json.loads(json.dumps(value, default=scalar, allow_nan=False))
    payload = canonical(value)
    with path.open('xb') as f:
        f.write(payload); f.flush(); os.fsync(f.fileno())


def worker(stage, destination):
    if os.environ.get('PROWL_MAC_KD_ENGINEERING') != '1':
        raise ValueError('Supervisor required')
    import torch
    torch.set_num_threads(1)
    if stage == 'convert':
        from scripts.diagnostics import convert_distillation_teacher as convert
        convert.BASE = BASE/'teacher'
        convert.CHECKPOINT = convert.BASE/'release/pants_pancreas_release/fold_0_latest.pth'
        convert.OUT = destination
        os.environ['PROWL_TEACHER_CONVERT'] = '1'
        convert.worker()
        return
    if stage in ('student', 'student-cold'):
        from scripts.diagnostics.mac_kd_synthetic import run
        run(stage, destination, BASE)
        return
    from src.training.teacher_medformer_v1 import bundle_identity, FrozenTeacher
    identity = bundle_identity(BASE/'teacher', BASE/'convert-01/conversion.json')
    write(destination/'teacher-bundle.json', identity)
    device = 'cpu' if stage == 'cpu' else 'mps'
    if device == 'mps' and not torch.backends.mps.is_available():
        raise ValueError('MPS unavailable')
    teacher = FrozenTeacher(identity, digest(canonical(identity)), device=device)
    size = 128 if stage == 'mps128' else 32
    x = torch.randn((1,1,size,size,size), generator=torch.Generator().manual_seed(42))
    before = {k: v.detach().cpu().clone() for k,v in teacher.model.state_dict().items()}
    a = teacher.lesion_probability(x); b = teacher.lesion_probability(x)
    if device == 'mps': torch.mps.synchronize()
    if not torch.equal(a,b): raise ValueError('Teacher repeated output differs')
    if not all(torch.equal(before[k],v.detach().cpu()) for k,v in teacher.model.state_dict().items()):
        raise ValueError('Frozen teacher changed')
    if device == 'mps' and torch.mps.driver_allocated_memory() > 12*1024**3:
        raise ValueError('MPS allocation exceeded engineering budget')
    write(destination/'result.json', dict(success=True, stage=stage, device=device,
        shape=list(x.shape), output_shape=list(a.shape), min=float(a.min()), max=float(a.max()),
        exact_repeated_forward=True, frozen_state_unchanged=True, source_patient_reads=0,
        scientific_updates=0, training_ready=False,
        mps_driver_bytes=torch.mps.driver_allocated_memory() if device=='mps' else 0))


def launch(stage):
    import shutil
    if sys.platform != 'darwin': raise ValueError('Mac-only supervisor')
    if not Path('/Volumes/PROWL-Data').is_mount(): raise ValueError('External drive missing')
    if shutil.disk_usage('/Volumes/PROWL-Data').free < 100*1024**3:
        raise ValueError('External reserve')
    destination = BASE/(stage+'-01')
    destination.mkdir(exist_ok=False)
    paths = [Path(__file__), ROOT/'src/training/teacher_medformer_v1.py', ROOT/'src/training/teacher_checkpoint_v1.py', ROOT/'scripts/diagnostics/mac_kd_synthetic.py']
    write(destination/'request.json', dict(stage=stage, seconds=240, rss_bytes=12*1024**3,
        mps_bytes=12*1024**3, scientific=False, inputs='synthetic only',
        pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}))
    source_dir = destination/'source'
    source_dir.mkdir()
    for path in paths:
        (source_dir/path.name).write_bytes(path.read_bytes())
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PROWL_MAC_KD_ENGINEERING='1',
        OMP_NUM_THREADS='1', PYTORCH_ENABLE_MPS_FALLBACK='0')
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        with (destination/'worker.log').open('x') as log:
            process = subprocess.Popen(['caffeinate','-i',sys.executable,__file__,'--worker',stage,str(destination)],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            success=False;error=None
            try:
                watch(process,seconds=240,rss_bytes=12*1024**3);success=True
            except Exception as exc: error=str(exc)
            finally:
                receipt=dict(getattr(process,'duration_resources',{}),success=success,error=error,exit_code=process.returncode)
                write(destination/'resources.json',receipt);print(json.dumps(receipt))
    if not success: raise SystemExit(1)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['convert','cpu','mps32','mps128','student','student-cold'])
    p.add_argument('--worker',nargs=2);args=p.parse_args()
    if args.worker: worker(args.worker[0],Path(args.worker[1]))
    elif args.stage: launch(args.stage)
    else: p.error('stage required')
