"""Bounded CUDA fit and fresh-process continuation check using invented arrays only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def worker(output, size, cold):
    import numpy as np
    import torch
    from src.data.manifest_records import canonical, digest
    from src.data.segmenter_full_batch_v1 import Batch, _TOKEN
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_full_executor_v1 import atomic_checkpoint
    torch.set_num_threads(2)
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    class Provider:
        def __init__(self):
            self.control = dict(train=['invented-0', 'invented-1', 'invented-2'], validation=['invented-dev'])
            self.target = np.zeros((size,)*3, dtype=np.uint8)
            self.target[size//4:3*size//4, size//4:3*size//4, size//4:3*size//4] = 1
            self.target[size//2:size//2+3, size//2:size//2+3, size//2:size//2+3] = 2
            self.image = self.target[None].astype(np.float32)/2
        def get(self, name, *, role, operation):
            return Batch(_TOKEN, study_id=name, role=role, operation=operation,
                image=self.image, target=self.target, control_sha256=digest(canonical(self.control)))
    provider = Provider()
    config = dict(max_steps=24000, tensor_shape=[size]*3, seed=42, learning_rate=.0001,
        weight_decay=.00001, warmup_steps=500, lr_schedule='warmup_cosine')
    if cold:
        checkpoint = torch.load(output/'saved.pt', map_location='cpu', weights_only=True)
        expected = torch.load(output/'expected.pt', map_location='cpu', weights_only=True)
        saved = checkpoint['session']
        session = Session.restore(saved, saved['identity'])
        maxima = []
        def compare(left, right, exact=False):
            if isinstance(left, torch.Tensor):
                assert left.shape == right.shape and left.dtype == right.dtype
                if exact or not left.is_floating_point():
                    assert torch.equal(left, right)
                else:
                    torch.testing.assert_close(left, right, rtol=1.3e-6, atol=1e-5)
                    maxima.append(float((left-right).abs().max()))
            elif isinstance(left, dict):
                assert left.keys() == right.keys()
                for key in left: compare(left[key], right[key], exact)
            elif isinstance(left, (list, tuple)):
                assert len(left) == len(right)
                for a, b in zip(left, right): compare(a, b, exact)
            else:
                assert left == right
        compare(session.state(), saved, exact=True)
        row = session.update(provider)
        compare(session.state(), expected['session'])
        report = dict(stage='cold', optimizer_updates=1, full_state_restore_exact=True,
            next_update_state_close=True, rtol=1.3e-6, atol=1e-5,
            maximum_absolute_tensor_difference=max(maxima, default=0), update=row)
    else:
        session = Session(config, provider.control, device='cuda', initialization={'kind':'scratch'})
        rows = [session.update(provider), session.update(provider)]
        atomic_checkpoint(output/'saved.pt', session, best_score=None, history_bytes=0)
        rows.append(session.update(provider))
        evaluation = session.evaluate_case(provider, 'invented-dev')
        atomic_checkpoint(output/'expected.pt', session, best_score=None, history_bytes=0)
        report = dict(stage='producer', optimizer_updates=3, forwards=4, updates=rows, evaluation=evaluation)
    torch.cuda.synchronize()
    report.update(domain='invented_arrays_only', tensor_shape=[size]*3, precision='float32_tf32_disabled',
        seconds=time.monotonic()-started, peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        peak_reserved_bytes=torch.cuda.max_memory_reserved(), gpu=torch.cuda.get_device_name(0),
        torch=str(torch.__version__), cuda=torch.version.cuda, real_data_qualified=False)
    (output/('cold.json' if cold else 'producer.json')).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--size', type=int, choices=(96, 128, 144), default=144)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--cold', action='store_true')
    args = parser.parse_args(); output = Path(args.output).resolve()
    if args.worker:
        worker(output, args.size, args.cold); return
    if os.name != 'nt': raise RuntimeError('This profile uses the Windows supervisor')
    from src.operations.full_training_platform import training_guard, watch_windows, require_ac
    output.mkdir(parents=True, exist_ok=False)
    producing_paths = ['scripts/diagnostics/profile_windows_full_segmenter.py',
        'src/data/segmenter_full_batch_v1.py',
        'src/training/segmenter_full_session_v1.py', 'src/training/segmenter_full_executor_v1.py',
        'src/training/segmenter_normalized_loss_v1.py', 'src/models/segresnet.py',
        'src/operations/full_training_platform.py']
    (output/'code-pins.json').write_text(json.dumps({name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        for name in producing_paths}, indent=2)+'\n')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        for stage in ('producer', 'cold'):
            command = [sys.executable, str(Path(__file__).resolve()), '--output', str(output),
                '--size', str(args.size), '--worker'] + (['--cold'] if stage == 'cold' else [])
            with (output/f'{stage}.log').open('x') as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
                try:
                    resources = watch_windows(process, seconds=600, rss_bytes=12*1024**3, tick=require_ac)
                finally:
                    resources = getattr(process, 'duration_resources', {})
                    (output/f'{stage}-resources.json').write_text(json.dumps(resources, indent=2)+'\n')
            print((output/f'{stage}.json').read_text(), flush=True)


if __name__ == '__main__':
    main()
