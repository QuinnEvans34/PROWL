"""Read-only completed-screen audit; no CT, reference-mask or model loading."""
import datetime
import fcntl
import gc
import hashlib
import json
from pathlib import Path
import resource
import sqlite3
import subprocess
import time

import numpy as np

from scripts.diagnostics.summarize_stunet_confidence_20261108 import summarize
from src.inference.lesion_confidence_screen_v2 import decode, unpack

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108/screen-03')
BACKUP = Path.home()/'PROWL-Backups/stunet-confidence-mac-20261108-03'
REQUEST_SHA = '57fb08fed8f05d89021a889fb15355f764ed87a51b8cc4baf87cd6b504cb0ebc'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024**2), b''):
            h.update(block)
    return h.hexdigest()


def main():
    started = time.monotonic()
    assert sha(OUT/'request.json') == REQUEST_SHA
    request = json.loads((OUT/'request.json').read_text())
    result = json.loads((OUT/'result.json').read_text())
    resources = json.loads((OUT/'resources.json').read_text())
    assert result['status'] == 'COMPLETE_DESCRIPTIVE_ONLY'
    assert result['request_sha256'] == REQUEST_SHA
    assert result['optimizer_updates'] == 0
    assert resources['success'] and resources['exit_code'] == 0 and resources['workers_reaped']
    assert not resources['surviving_workers']
    for key in ('error', 'cleanup_error', 'supervisor_cleanup_error'):
        assert resources[key] is None
    assert resources['peak_owned_rss_bytes'] <= request['rss_bytes']
    assert result['peak_observed_driver_bytes'] <= request['mps_bytes']
    assert resources['seconds'] <= request['seconds']
    assert (OUT/'resources.json').stat().st_mtime < request['cumulative_budget_origin_unix'] + request['cumulative_budget_seconds']
    for path, expected in request['pins'].items():
        assert sha(path) == expected, path
    parent = json.loads((OUT/'parent-reference.json').read_text())
    for path in (request['checkpoint']['path'], parent['path'], parent['backup']):
        assert sha(path) == request['checkpoint']['sha256'], path
    assert OUT.stat().st_dev != BACKUP.stat().st_dev
    expected_cases = {r['case_id'] for r in request['cases']}
    assert {p.stem for p in OUT.glob('PanTS_*.json')} == expected_cases
    assert {p.stem for p in BACKUP.glob('PanTS_*.npz')} == expected_cases
    rows = [json.loads((OUT/(r['case_id']+'.json')).read_text()) for r in result['cases']]
    derived = summarize(rows)
    for key, value in derived.items():
        assert result[key] == value, key
    checked_backups = 0
    for path in sorted(OUT.iterdir()):
        if path.name not in {'worker.log', 'guardian-ready.json', 'process.json'} and path.is_file():
            assert (BACKUP/path.name).is_file(), path
            assert sha(path) == sha(BACKUP/path.name), path
            checked_backups += 1
    mask_checks = 0
    for row in rows:
        path = BACKUP/(row['case_id']+'.npz')
        assert sha(path) == row['artifact']['sha256']
        with np.load(path, allow_pickle=False) as f:
            code = unpack(f['packed'], [int(n) for n in f['shape']])
        expected_shape = next(r['native_shape'] for r in request['cases'] if r['case_id'] == row['case_id'])
        assert list(code.shape) == expected_shape
        for threshold in (0., .4, .5, .6):
            mask = decode(code, threshold)
            assert hashlib.sha256(mask.tobytes()).hexdigest() == row['mask_sha256'][str(threshold)]
            mask_checks += 1
            del mask
        del code
        gc.collect()
    tracking = json.loads((OUT/'tracking.json').read_text())
    metric_checks = 0
    for db in (OUT.parent/'mlflow.db', OUT/'mlflow-snapshot.db', BACKUP/'mlflow-snapshot.db'):
        with sqlite3.connect('file:'+str(db)+'?mode=ro', uri=True) as c:
            assert c.execute('pragma integrity_check').fetchone()[0] == 'ok'
            assert c.execute('select status from runs where run_uuid=?', (tracking['run_id'],)).fetchone()[0] == 'FINISHED'
            metrics = dict(c.execute('select key,value from latest_metrics where run_uuid=?', (tracking['run_id'],)))
            for key, values in result['policies'].items():
                for name, value in values.items():
                    if value is not None:
                        assert metrics['policy_'+key.replace('.', '')+'/'+name] == float(value)
                        metric_checks += 1
    with (ROOT/'outputs/prowl/.mps-profile.lock').open('a+b') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(f, fcntl.LOCK_UN)
    processes = subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True)
    assert not any('run_stunet_confidence_mac_20261108_v3.py' in line for line in processes.splitlines())
    report = dict(schema='prowl.confidence-closeout.20261108.v1', status='PASS',
        observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        root=str(OUT), result_sha256=sha(OUT/'result.json'), request_sha256=REQUEST_SHA,
        producing_pins_verified=len(request['pins']), cases=len(rows), tiles=sum(r['tiles'] for r in rows),
        independent_backup_files_verified=checked_backups, reopened_policy_mask_hashes_verified=mask_checks,
        summary_reproduced_exactly=True, mlflow_run=tracking['run_id'], mlflow_status='FINISHED',
        sqlite_integrity_checks=3, metric_readbacks=metric_checks, workers_reaped=True, exclusive_lock_released=True,
        resources=resources, peak_observed_driver_bytes=result['peak_observed_driver_bytes'],
        max_raw_dice_difference_from_cuda=max(r['raw_dice_difference_from_cuda'] for r in rows
                                              if r['raw_dice_difference_from_cuda'] is not None),
        undefined_cuda_dice_comparisons=sum(r['raw_dice_difference_from_cuda'] is None for r in rows),
        selected_policy=result['selected_policy'], policies=result['policies'], guards=result['guards'],
        confidence_ranking_auc=result['correlation']['quantized_auc_correct_vs_incorrect_raw_lesion_winners'],
        verification_seconds=time.monotonic()-started,
        verification_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scope='Exposed-development inference-policy screen; zero optimizer updates; no automatic deployment')
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
