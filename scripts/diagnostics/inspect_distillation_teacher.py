"""Bounded CPU checkpoint inspection. No CT reads, GPU context or pickle fallback."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.operations.full_training_platform import watch_windows

BASE = Path('E:/PROWL/teachers/medformer-pants-b854c824')
OUT = Path('E:/PROWL/readiness/distillation-teacher-inspection-20261023-a01')
CHECKPOINT = BASE/'release/pants_pancreas_release/fold_0_latest.pth'
SHA = 'ff0f0868db15f99285e218e0468a2717c1a79a421357eb37171ecd5f3bb75d1f'


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def worker():
    if os.environ.get('PROWL_TEACHER_INSPECT') != '1': raise ValueError('Bounded supervisor required')
    import torch
    import yaml
    torch.set_num_threads(1)
    with CHECKPOINT.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != SHA: raise ValueError('Checkpoint pin')
    unsafe = torch.serialization.get_unsafe_globals_in_checkpoint(CHECKPOINT)
    write(OUT/'pickle-inspection.json', dict(unsupported_globals=unsafe, unsafe_fallback=False))
    if unsafe: raise ValueError('Checkpoint needs separately reviewed globals; do not unsafe-load')
    data = torch.load(CHECKPOINT, weights_only=True, map_location='cpu', mmap=True)
    labels = sorted(yaml.safe_load((BASE/'release/labels_pants.yaml').read_text()))
    states = {}
    for key in ('model_state_dict', 'ema_model_state_dict'):
        state = data[key]
        if not isinstance(state, dict) or not all(isinstance(v, torch.Tensor) for v in state.values()):
            raise ValueError('Expected tensor-only state dictionary')
        if not all(torch.isfinite(v).all().item() for v in state.values()): raise ValueError('Nonfinite weights')
        heads = {k: list(v.shape) for k, v in state.items() if k.startswith(('outc.', 'aux_out.'))}
        if state['outc.weight'].shape[0] != len(labels) or state['aux_out.weight'].shape[0] != len(labels):
            raise ValueError('Actual model head and published class list disagree')
        states[key] = dict(keys=len(state), elements=sum(v.numel() for v in state.values()), heads=heads)
    if torch.cuda.is_initialized(): raise RuntimeError('CPU-only inspection violated')
    write(OUT/'inspection.json', dict(success=True, checkpoint_sha256=SHA, weights_only=True,
        top_level_keys=sorted(data), epoch=data.get('epoch'), states=states, labels=labels,
        lesion_channel_zero_based=labels.index('pancreatic_lesion'), activation='independent_sigmoid',
        cpu_only=True, cuda_initialized=False, model_forward=False, ct_reads=0,
        training_membership='not established by checkpoint tensor inspection'))


def main():
    OUT.mkdir(exist_ok=False)
    write(OUT/'request.json', dict(seconds=180, rss_bytes=4*1024**3,
        checkpoint_sha256=SHA, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        cpu_only=True, scientific=False, no_unsafe_deserialization=True))
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
        PYTHONDONTWRITEBYTECODE='1', PROWL_TEACHER_INSPECT='1')
    success = False; error = None
    with (OUT/'worker.log').open('x', encoding='utf-8') as stream:
        process = subprocess.Popen([sys.executable, __file__, '--worker'], cwd=ROOT,
            env=env, stdout=stream, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            watch_windows(process, seconds=180, rss_bytes=4*1024**3); success = True
        except Exception as exc: error = f'{type(exc).__name__}: {exc}'
        finally:
            record = dict(getattr(process, 'duration_resources', {}), success=success,
                exit_code=process.returncode, error=error)
            write(OUT/'resources.json', record); print(json.dumps(record))
    if not success: raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--worker', action='store_true')
    if parser.parse_args().worker: worker()
    else: main()
