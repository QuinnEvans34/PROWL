"""Prepare then separately dispatch bounded nonpromotable CUDA/cold checks.

No scientific launcher, scheduler, retries or parent interruption.
"""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.diagnostics.qualify_generator_input_pilot import BASE, provider, read, sha, write

OUT = BASE / 'cuda-qualification-01'
PILOT = BASE / 'cpu-pilot-01'
BACKUP = Path('C:/Users/quinn/PROWL-Backups/verifier-generator-qualification-20261023-a01')
PARENT_SETUP = Path('E:/PROWL/readiness/varied-deterministic-20261022-a02')
SECONDS = 1200
RSS_BYTES = 12 * 1024**3


def qualification_config(source):
    config = deepcopy(source)
    # Session requires its warmup/horizon to fit its bounded max_steps.
    # This diagnostic schedule is nonpromotable, not the scientific 24k recipe.
    config['session'].update(max_steps=5, warmup_steps=1, lr_horizon_steps=5)
    return config


def pilot_gate():
    result = read(PILOT / 'result.json')
    review = read(PILOT / 'visual-review.json')
    resources = read(PILOT / 'resources.json')
    names = read(PILOT / 'request.json')['cases']
    if (not result['passed'] or not resources['workers_reaped'] or not review['passed']
            or review['result_sha256'] != sha(PILOT / 'result.json')
            or len(names) != 12 or len(set(names)) != 12
            or [r['case_id'] for r in result['cases']] != names
            or [r['case_id'] for r in review['cases']] != names):
        raise ValueError('Real pilot/review binding failed')
    for row in result['cases']:
        if not row['roundtrip_exact'] or sha(PILOT / row['figure']) != row['figure_sha256']:
            raise ValueError('Pilot coverage/figure changed')


def prepare():
    if OUT.exists():
        raise ValueError('Qualification already prepared; no overwrite')
    pilot_gate()
    files = list((ROOT / 'src').rglob('*.py')) + list((ROOT / 'scripts').rglob('*.py'))
    files += [BASE / 'partitions.json', BASE / 'restricted-inputs-01/setup.json',
              PARENT_SETUP / 'configuration.json', PARENT_SETUP / 'ready.json']
    files += list(PILOT.glob('*.json')) + list(PILOT.glob('*.png'))
    files += [ROOT / 'tests/test_restricted_generator_qualification.py',
              ROOT / 'tests/test_verifier_generator_executor_v1.py']
    config = qualification_config(read(PARENT_SETUP / 'configuration.json'))
    OUT.mkdir()
    write(OUT / 'request.json', dict(pins={str(p): sha(p) for p in files},
        configuration=config, producer_updates=5, cold_updates=1,
        seconds_per_stage=SECONDS, rss_bytes=RSS_BYTES, scientific=False,
        automatic_dispatch=False, status='CPU_PREPARED_GPU_PENDING'))


def check():
    request = read(OUT / 'request.json')
    for name, pin in request['pins'].items():
        if sha(name) != pin:
            raise ValueError('Qualification pin changed: ' + name)
    pilot_gate()
    return request


def parent_gate():
    from scripts.diagnostics.prepare_distillation import normal_parent_gate
    names = read(BASE / 'restricted-inputs-01/setup.json')['control']['validation']
    return normal_parent_gate(names)


def stage_admission(name):
    if name not in ('producer', 'cold'):
        raise ValueError('Unknown stage')
    if (OUT / (name + '.log')).exists():
        raise ValueError('Stage already started; never retry or duplicate')
    check()
    parent_gate()  # No stage/process/output side effects until normal completion.
    if name == 'cold':
        resource = read(OUT / 'producer-resources.json')
        if not resource.get('success') or resource.get('exit_code') != 0 or not resource.get('workers_reaped'):
            raise ValueError('Producer not successful and reaped')
        if not read(OUT / 'producer.json')['passed']:
            raise ValueError('Producer failed')


def worker(name):
    import torch
    from scripts.diagnostics import setup_fast_varied as shared
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    from scripts.diagnostics.control_original_repeatability import compare_states
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from src.training.verifier_generator_executor_v1 import execute
    request = check()
    parent_gate()
    torch.set_num_threads(2)
    if not torch.cuda.is_available():
        raise ValueError('Actual CUDA required')
    p = provider()
    try:
        p.enable_prefetch()
        if name == 'producer':
            config = request['configuration']
            s = FastVariedSession(Session(config['session'], p.control,
                device='cuda', initialization=config['initialization']))
            def backup(path):
                shared.resources()
                destination = BACKUP / ('saved-four.pt' if s.step == 4 else path.name)
                if destination.exists():
                    raise ValueError('Backup destination already exists')
                if path.stat().st_dev == BACKUP.stat().st_dev:
                    raise ValueError('Backup must be on independent device')
                if shared.parent.tree_bytes(shared.parent.BACKUP_ROOT) + path.stat().st_size > 27917287424:
                    raise ValueError('Backup cap')
                with path.open('rb') as source, destination.open('xb') as target:
                    shutil.copyfileobj(source, target)
                    target.flush(); os.fsync(target.fileno())
                if sha(path) != sha(destination):
                    raise ValueError('Independent backup mismatch')
            result = execute(s, p, OUT / 'execution', checkpoint_every=4,
                             tick=shared.resources, checkpoint_hook=backup)
            write(OUT / 'producer.json', dict(passed=True, nonpromotable=True, result=result,
                saved_four_sha256=sha(BACKUP / 'saved-four.pt'),
                expected_terminal_sha256=sha(OUT / 'execution/terminal.pt')))
        else:
            saved_path = BACKUP / 'saved-four.pt'
            evidence = read(OUT / 'producer.json')
            if (sha(saved_path) != evidence['saved_four_sha256']
                    or sha(OUT / 'execution/terminal.pt') != evidence['expected_terminal_sha256']):
                raise ValueError('Cold checkpoint bytes changed')
            saved = torch.load(saved_path, map_location='cpu', weights_only=True)['session']
            expected = torch.load(OUT / 'execution/terminal.pt', map_location='cpu', weights_only=True)['session']
            s = FastVariedSession.restore(saved, saved['identity'])
            if s.step != 4 or s.control_pin != p.pin:
                raise ValueError('Cold checkpoint/control identity')
            compare(s.state(), saved, exact=True)
            row = s.update(p)
            rows = [json.loads(line) for line in (OUT / 'execution/history.jsonl').read_text().splitlines()]
            reference = [r for r in rows if r['event'] == 'update'][-1]
            if any(row[key] != reference[key] for key in ('step','member_id','batch_sha256','input_view','learning_rate')):
                raise ValueError('Cold replay input mismatch')
            comparison = compare_states(expected, s.state())
            if not comparison['passes_original_bound']:
                raise ValueError('Cold replay numerical gate failed')
            p.close()
            write(OUT / 'cold.json', dict(passed=True, nonpromotable=True,
                exact_restore=True, exact_next_input=True, comparison=comparison,
                independent_backup_sha256=sha(saved_path)))
    finally:
        p.close()


def stage(name):
    from scripts.diagnostics.setup_fast_varied import resources
    from src.operations.full_training_platform import training_guard, watch_windows
    stage_admission(name)
    resources()
    with training_guard(ROOT / 'outputs/prowl/.cuda-training.lock'):
        parent_gate()
        if name == 'producer':
            BACKUP.mkdir(exist_ok=False)
        with (OUT / (name + '.log')).open('x') as log:
            env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PROWL_GENERATOR_QUAL='1')
            env.pop('CUDA_VISIBLE_DEVICES', None)
            process = subprocess.Popen([sys.executable, __file__, '--worker', name], cwd=ROOT,
                                       env=env, stdout=log, stderr=subprocess.STDOUT)
            success = False
            try:
                watch_windows(process, seconds=SECONDS, rss_bytes=RSS_BYTES, tick=resources)
                success = True
            finally:
                write(OUT / (name + '-resources.json'), dict(getattr(process,'duration_resources',{}),
                      success=success, exit_code=process.returncode))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--stage', choices=('producer','cold'))
    group.add_argument('--worker', choices=('producer','cold'))
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.stage:
        stage(args.stage)
    else:
        if os.environ.get('PROWL_GENERATOR_QUAL') != '1':
            raise ValueError('Supervisor required')
        worker(args.worker)
