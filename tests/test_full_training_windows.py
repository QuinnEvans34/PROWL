"""Windows process ownership/durability and CUDA state tests on invented inputs."""
from copy import deepcopy
import os
import subprocess
import sys

import pytest
import torch

from src.operations.full_training_platform import durable_replace, training_guard, watch_windows
from src.training.segmenter_full_session_v1 import Session
from test_segmenter_full import Invented, config


def test_portable_batch_matches_frozen_boundary():
    # Compare the exact historical class/encoder without importing its OS-specific resolver.
    import ast
    from io import BytesIO
    from pathlib import Path
    from types import SimpleNamespace
    import numpy as np
    from src.data import segmenter_full_batch_v1 as portable
    from src.data.manifest_records import digest
    from src.data.source_inventory_records import require
    root = Path(__file__).resolve().parents[1]
    namespace = dict(np=np, BytesIO=BytesIO, digest=digest, require=require, _TOKEN=object())
    for filename, name in [('src/data/segmenter_cache_v1.py', 'encode'),
                           ('src/data/segmenter_training_inputs_v1.py', 'Batch')]:
        tree = ast.parse((root/filename).read_text())
        node = next(n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), filename, 'exec'), namespace)
        if name == 'encode': namespace['cache'] = SimpleNamespace(encode=namespace['encode'])
    arrays = Invented()
    args = dict(study_id='t0', role='train', operation='optimizer', image=arrays.x,
                target=arrays.y, control_sha256='a'*64)
    original = namespace['Batch'](namespace['_TOKEN'], **args)
    new = portable.Batch(portable._TOKEN, **args)
    assert original.hashes() == new.hashes()
    for batch in (original, new):
        batch.checked('a'*64, 'optimizer', 't0')
        batch.target[0, 0, 0] = 2
        with pytest.raises(ValueError, match='provenance'):
            batch.checked('a'*64, 'optimizer', 't0')
    args.update(role='validation')
    with pytest.raises(ValueError, match='Evaluator batch'):
        portable.Batch(portable._TOKEN, **args).checked('a'*64, 'optimizer', 't0')


def test_durable_replace_existing(tmp_path):
    source, target = tmp_path/'new.partial', tmp_path/'last.pt'
    source.write_bytes(b'new'); target.write_bytes(b'old')
    durable_replace(source, target)
    assert target.read_bytes() == b'new' and not source.exists()


@pytest.mark.skipif(os.name != 'nt', reason='Windows process supervisor')
@pytest.mark.parametrize('failure', [False, True])
def test_windows_watchdog_reaps(failure):
    command = 'import time; time.sleep(30)' if failure else 'import time; time.sleep(.5)'
    process = subprocess.Popen([sys.executable, '-c', command])
    if failure:
        with pytest.raises(RuntimeError, match='resource stop'):
            watch_windows(process, seconds=.3, rss_bytes=1024**3)
    else:
        result = watch_windows(process, seconds=10, rss_bytes=1024**3)
        assert result['samples'] > 0
    assert process.poll() is not None and process.duration_resources['workers_reaped']


@pytest.mark.skipif(os.name != 'nt', reason='Windows locking and power guard')
def test_exclusive_training_guard(tmp_path):
    with training_guard(tmp_path/'gpu.lock'):
        with pytest.raises(OSError):
            with training_guard(tmp_path/'gpu.lock'):
                pytest.fail('Lock admitted second owner')
    with training_guard(tmp_path/'gpu.lock'):
        pass


@pytest.mark.skipif(os.name != 'nt', reason='Windows job descendants')
def test_watchdog_closes_surviving_descendant(tmp_path):
    import psutil
    record = tmp_path/'child.txt'
    command = ('import subprocess,sys,time; from pathlib import Path; '
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
        f'Path({str(record)!r}).write_text(str(p.pid)); time.sleep(.7)')
    process = subprocess.Popen([sys.executable, '-c', command])
    result = watch_windows(process, seconds=10, rss_bytes=1024**3)
    assert result['workers_reaped'] and not psutil.pid_exists(int(record.read_text()))


@pytest.mark.skipif(not torch.cuda.is_available(), reason='CUDA required')
def test_cuda_rng_and_continuation():
    torch.set_num_threads(2)
    torch.cuda.init()
    old_cpu, old_cuda = torch.get_rng_state().clone(), torch.cuda.get_rng_state().clone()
    provider = Invented()
    session = Session(config(), provider.control, device='cuda', initialization={'kind':'scratch'})
    assert torch.equal(old_cpu, torch.get_rng_state()) and torch.equal(old_cuda, torch.cuda.get_rng_state())
    session.update(provider)
    state = session.state()
    restored = Session.restore(deepcopy(state), session.identity)
    left, right = session.update(provider), restored.update(provider)
    assert left['member_id'] == right['member_id'] and left['loss'] == pytest.approx(right['loss'], rel=1e-6)
    for key, value in session.state()['model'].items():
        torch.testing.assert_close(value, restored.state()['model'][key], rtol=1.3e-6, atol=1e-5)
    assert torch.equal(old_cpu, torch.get_rng_state()) and torch.equal(old_cuda, torch.cuda.get_rng_state())
    state['cuda_rng'] = torch.zeros(3)
    with pytest.raises(ValueError, match='CUDA RNG'):
        Session.restore(state, session.identity)
