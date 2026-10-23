"""One bounded CPU-only inert-record conversion; preserves original rejected inspection."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from scripts.diagnostics.inspect_distillation_teacher import BASE, CHECKPOINT, SHA, write
from src.operations.full_training_platform import watch_windows

OUT = Path('E:/PROWL/readiness/distillation-teacher-conversion-20261023-a01')


def worker():
    if os.environ.get('PROWL_TEACHER_CONVERT') != '1': raise ValueError('Supervisor required')
    import torch
    import yaml
    from src.training.teacher_checkpoint_v1 import read_legacy_release, tensor_state
    torch.set_num_threads(1)
    with CHECKPOINT.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != SHA: raise ValueError('Source pin')
    data, globals_used = read_legacy_release(CHECKPOINT)
    labels = sorted(yaml.safe_load((BASE/'release/labels_pants.yaml').read_text()))
    states = {}
    for label, key in (('raw', 'model_state_dict'), ('ema', 'ema_model_state_dict')):
        state = tensor_state(data[key])
        if not all(torch.isfinite(v).all().item() for v in state.values()): raise ValueError('Nonfinite tensor')
        heads = {k: list(v.shape) for k,v in state.items() if k.startswith(('outc.', 'aux_out.'))}
        if state['outc.weight'].shape[0] != len(labels) or state['aux_out.weight'].shape[0] != len(labels):
            raise ValueError('Actual head differs from published labels')
        target = OUT/('teacher-' + label + '.pt')
        with target.open('xb') as stream: torch.save(state, stream)
        restored = torch.load(target, weights_only=True, map_location='cpu', mmap=True)
        if set(restored) != set(state) or not all(torch.equal(restored[k], v) for k,v in state.items()):
            raise ValueError('Exported tensor state differs')
        with target.open('rb') as stream: pin = hashlib.file_digest(stream, 'sha256').hexdigest()
        states[label] = dict(path=str(target), sha256=pin, keys=len(state),
            elements=sum(v.numel() for v in state.values()), heads=heads, exact_export_reload=True)
    if torch.cuda.is_initialized(): raise RuntimeError('CPU-only violation')
    epoch = data.get('epoch')
    if epoch is not None and type(epoch) not in (int, float): epoch = str(type(epoch))
    write(OUT/'conversion.json', dict(success=True, source_sha256=SHA,
        restricted_weights_only=True, original_class_code_executed=False,
        inert_global_mappings=globals_used, top_level_keys=sorted(data), epoch=epoch,
        states=states, labels=labels, lesion_channel_zero_based=labels.index('pancreatic_lesion'),
        activation='independent_sigmoid', cuda_initialized=False, model_forward=False,
        ct_reads=0, membership='not established by weights', ready_for_training=False))


def main():
    OUT.mkdir(exist_ok=False)
    files = [Path(__file__), ROOT/'src/training/teacher_checkpoint_v1.py']
    write(OUT/'request.json', dict(seconds=180, rss_bytes=4*1024**3,
        source_sha256=SHA, pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        prior_inspection_preserved='distillation-teacher-inspection-20261023-a01',
        distinction='Explicit inert record extraction, not unsafe pickle fallback', scientific=False))
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
        PYTHONDONTWRITEBYTECODE='1', PROWL_TEACHER_CONVERT='1')
    success = False; error = None
    with (OUT/'worker.log').open('x', encoding='utf-8') as stream:
        p = subprocess.Popen([sys.executable, __file__, '--worker'], cwd=ROOT, env=env,
            stdout=stream, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        try: watch_windows(p, seconds=180, rss_bytes=4*1024**3); success = True
        except Exception as exc: error = f'{type(exc).__name__}: {exc}'
        finally:
            result = dict(getattr(p,'duration_resources',{}), success=success, exit_code=p.returncode, error=error)
            write(OUT/'resources.json', result); print(json.dumps(result))
    if not success: raise SystemExit(1)


if __name__ == '__main__':
    if sys.argv[1:] == ['--worker']: worker()
    elif not sys.argv[1:]: main()
    else: raise ValueError('Unsupported command')
