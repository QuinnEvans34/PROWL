#!/usr/bin/env python3
"""Supervised full-cohort capstone session/executor entry point; no legacy training loop."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.training import experiment_config as E
from src.data.manifest_records import canonical
from src.data.source_inventory_records import require


def session_config(cfg):
    require('max_steps' not in cfg['full_segmenter']['session'], 'Set duration only in run.max_updates')
    return dict(cfg['full_segmenter']['session'], max_steps=cfg['_experiment']['run']['max_updates'])


def preflight(cfg, inspect=False):
    from src.data.segmenter_geometry_v2 import validate_recipe
    from src.training.segmenter_full_session_v1 import validate_config
    report = E.preflight(cfg, inspect_payload_paths=inspect, source_review_mode='development_use')
    full = cfg.get('full_segmenter', {})
    try:
        require(set(full) == {'session', 'geometry', 'output_dir', 'cache_dir', 'cache_max_bytes', 'backup_dir',
            'backup_cap_bytes', 'rss_bytes'}, 'Full segmenter configuration required')
        validate_config(session_config(cfg)); validate_recipe(full['geometry'])
        require(full['session']['tensor_shape'] == full['geometry']['tensor_shape'], 'Conflicting geometry')
        for k in ('cache_max_bytes', 'backup_cap_bytes', 'rss_bytes'):
            require(type(full[k]) is int and full[k] > 0, f'Invalid {k}')
        for k in ('output_dir', 'cache_dir', 'backup_dir'): require(Path(full[k]).is_absolute(), f'Absolute {k} required')
        if inspect:
            def ancestor(path):
                path = Path(path)
                while not path.exists(): path = path.parent
                return path
            require(ancestor(full['output_dir']).stat().st_dev != ancestor(full['backup_dir']).stat().st_dev,
                    'Primary checkpoints and backup must be on separate volumes')
            require(tree_bytes(full['backup_dir']) + 512*1024**2 <= full['backup_cap_bytes'],
                    'Insufficient backup allocation for checkpoints/history')
        review_path = cfg['_experiment']['cohort']['review']
        if review_path:
            review = json.loads(E.resolve(review_path).read_text())
            names = set(E.ids(E.resolve(cfg['_experiment']['cohort']['train_ids']))) | set(
                E.ids(E.resolve(cfg['_experiment']['cohort']['development_ids'])))
            require(set(review.get('target_states', {})) == names and
                all(v in ('positive', 'verified_negative') or (v=='reference_empty' and
                    review.get('empty_reference_policy')=='annotation_background_not_verified_healthy')
                    for v in review['target_states'].values()),
                'Explicit reviewed target state for every selected case required')
            require('prepared_cache' in review, 'Completed, reviewed content cache required')
    except (OSError, ValueError, KeyError) as exc: report['errors'].append(str(exc))
    report['ready'] = not report['errors']; report['engine'] = 'segmenter_full_session_v1 / segmenter_full_executor_v1'
    return report


def tree_bytes(root):
    return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file()) if Path(root).exists() else 0


def worker(cfg, report):
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_full_executor_v1 import execute
    E.prepare_run(cfg, report)
    output = Path(cfg['paths']['output_dir']); full = cfg['full_segmenter']
    # Use the exact reviewed snapshot, including target-state findings.
    cfg['_experiment']['cohort']['review'] = str(output / 'cohort-review.json')
    backup_root = Path(full['backup_dir']); backup = backup_root / cfg['_experiment']['name']
    require(not backup.exists(), 'Backup run already exists')
    backup.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    def tick():
        E.check_resources(cfg, elapsed=time.monotonic()-started)
        require(shutil.disk_usage(full['cache_dir']).free >= cfg['_experiment']['run']['min_free_bytes'],
                'External free-space floor reached')
        require(shutil.disk_usage(backup_root).free >= cfg['_experiment']['run']['min_free_bytes'],
                'Internal backup free-space floor reached')
    def copy_backup(path):
        size = path.stat().st_size
        require(tree_bytes(backup_root) + size <= full['backup_cap_bytes'], 'Registered backup budget exceeded')
        temp = backup / (path.name + '.partial')
        with path.open('rb') as src, temp.open('xb') as dest:
            shutil.copyfileobj(src, dest); dest.flush(); os.fsync(dest.fileno())
        require(E.sha256(temp) == E.sha256(path), 'Backup verification failed')
        os.replace(temp, backup / path.name)
        fd = os.open(backup, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    def backup_checkpoint(path):
        copy_backup(path)
        copy_backup(path.parent / 'history.jsonl')
    for path in sorted(output.rglob('*')):
        if path.is_file():
            # Metadata snapshots have unique filenames, including original protected split files.
            copy_backup(path)
    Path(full['cache_dir']).mkdir(parents=True, exist_ok=True)
    provider = PreparedInputs(cfg, full['geometry'])
    (output / 'input-control.json').write_bytes(canonical(provider.control))
    copy_backup(output / 'input-control.json')
    session = Session(session_config(cfg), provider.control, device=cfg['device'],
                      initialization=cfg['_experiment']['initialization'])
    result = execute(session, provider, output / 'execution',
        validate_every=cfg['_experiment']['run']['validate_every'],
        checkpoint_every=cfg['_experiment']['run']['checkpoint_every'], tick=tick,
        checkpoint_hook=backup_checkpoint)
    copy_backup(output / 'execution' / 'history.jsonl')
    (output / 'result.json').write_bytes(canonical(result))
    copy_backup(output / 'result.json')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', required=True)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--inspect-input-paths', action='store_true')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(); cfg = E.load_experiment(args.experiment)
    if 'full_segmenter' in cfg:
        cfg['paths']['output_dir'] = cfg['full_segmenter']['output_dir']
    report = preflight(cfg, inspect=args.inspect_input_paths or not args.preflight)
    if args.preflight or not report['ready']:
        print(json.dumps(report, indent=2)); return 0 if report['ready'] else 2
    if args.worker:
        require(os.environ.get('PROWL_FULL_SUPERVISED') == '1', 'Use the supervised entry point')
        print(json.dumps(worker(cfg, report))); return 0
    from src.operations.segmenter_duration_dispatch_v1 import watch
    lock_path = ROOT / 'outputs/prowl/.mps-profile.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require('AC Power' in subprocess.check_output(['pmset', '-g', 'batt'], text=True), 'AC power required')
        env = dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK='0', PROWL_FULL_SUPERVISED='1')
        command = ['/usr/bin/caffeinate', '-dimsu', sys.executable, str(Path(__file__).resolve()),
                   '--experiment', str(Path(args.experiment).resolve()), '--worker']
        full = cfg['full_segmenter']; last_scan = [0.]
        def tick():
            E.check_resources(cfg, elapsed=0)
            # The inherited watchdog also bounds stalled kernels and owned process memory.
            if time.monotonic() - last_scan[0] >= 30:
                require(tree_bytes(full['cache_dir']) <= full['cache_max_bytes'], 'Derived cache budget exceeded')
                require(tree_bytes(full['backup_dir']) <= full['backup_cap_bytes'], 'Backup budget exceeded')
                last_scan[0] = time.monotonic()
        tick()
        process = subprocess.Popen(command, cwd=ROOT, env=env, start_new_session=True)
        resources = watch(process, seconds=cfg['_experiment']['run']['max_seconds'],
                          rss_bytes=full['rss_bytes'], tick=tick)
        print(json.dumps(resources)); return 0


if __name__ == '__main__':
    sys.exit(main())
