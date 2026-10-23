"""Receipt-gated ordinary PanTS augmentation run; one dispatch, no automatic retry."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src.training import experiment_config as E
from src.data.manifest_records import canonical
from src.data.source_inventory_records import require
from src.operations.full_training_platform import durable_replace, training_guard, require_ac, watch_windows
from scripts.train_full_segmenter import preflight, session_config, tree_bytes


def worker(cfg, report, run_id, receipt):
    import torch
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_augmentation_v1 import AugmentedSession
    from src.training.segmenter_augmented_executor_v1 import execute
    from src.training.segmenter_native_case_v1 import native_case
    from src.training.segmenter_live_tracking_v1 import Tracker
    from mlflow import MlflowClient
    from scripts.diagnostics.backfill_full_runs_mlflow import URI
    E.prepare_run(cfg, report); output = Path(cfg['paths']['output_dir']); full = cfg['full_segmenter']
    cfg['_experiment']['cohort']['review'] = str(output/'cohort-review.json')
    backup_root = Path(full['backup_dir']); backup = backup_root/cfg['_experiment']['name']
    backup.mkdir(parents=True, exist_ok=False); started = time.monotonic(); torch.set_num_threads(2)

    def tick():
        E.check_resources(cfg, elapsed=time.monotonic()-started)
        for drive in (backup_root, Path(full['cache_dir'])):
            require(shutil.disk_usage(drive).free >= cfg['_experiment']['run']['min_free_bytes'], 'Free-space floor')

    def copy(path):
        tick(); require(tree_bytes(backup_root)+path.stat().st_size <= full['backup_cap_bytes'], 'Backup budget')
        temp = backup/(path.name+'.partial')
        with path.open('rb') as src, temp.open('xb') as dest:
            shutil.copyfileobj(src, dest); dest.flush(); os.fsync(dest.fileno())
        require(E.sha256(temp) == E.sha256(path), 'Independent backup mismatch')
        durable_replace(temp, backup/path.name)

    def checkpoint(path): copy(path); copy(path.parent/'history.jsonl')

    (output/'launch-receipt.json').write_bytes(canonical(receipt))
    (output/'tracking.json').write_bytes(canonical(dict(run_id=run_id, tracking_uri=URI)))
    for path in sorted(output.rglob('*')):
        if path.is_file(): copy(path)
    provider = PreparedInputs(cfg, full['geometry'])
    require(provider.pin == receipt['control_sha256'], 'Launch cohort changed')
    (output/'input-control.json').write_bytes(canonical(provider.control)); copy(output/'input-control.json')
    client = MlflowClient(tracking_uri=URI)
    for path in (output/'resolved.yaml', output/'cohort-review.json', output/'source-review.json', output/'launch-receipt.json'):
        client.log_artifact(run_id, str(path), 'provenance')
    session = AugmentedSession(Session(session_config(cfg), provider.control, device='cuda',
                                      initialization=cfg['_experiment']['initialization']))
    result = execute(session, provider, output/'execution', validate_every=cfg['_experiment']['run']['validate_every'],
        checkpoint_every=cfg['_experiment']['run']['checkpoint_every'], retain_steps=cfg['_experiment']['run']['retain_steps'],
        tick=tick, checkpoint_hook=checkpoint, track=Tracker(run_id, output), native=native_case)
    copy(output/'execution/history.jsonl')
    (output/'result.json').write_bytes(canonical(result)); copy(output/'result.json')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt', type=Path, required=True); p.add_argument('--sha256', required=True)
    p.add_argument('--launch', action='store_true'); p.add_argument('--worker', action='store_true'); p.add_argument('--mlflow-run')
    a = p.parse_args()
    require(E.sha256(a.receipt) == a.sha256, 'Receipt changed'); receipt = json.loads(a.receipt.read_text())
    for path, pin in receipt['file_sha256'].items(): require(E.sha256(path) == pin, 'Pinned producing file changed: '+path)
    from scripts.diagnostics.setup_pants_augmentation import environment
    require(environment() == receipt['environment'], 'Runtime environment changed after qualification')
    cfg = E.load_experiment(receipt['configuration']); cfg['paths']['output_dir'] = cfg['full_segmenter']['output_dir']
    report = preflight(cfg, inspect=True); require(report['ready'], str(report))
    if not a.launch: print(json.dumps(report)); return
    if a.worker:
        require(os.environ.get('PROWL_AUGMENTATION_SUPERVISED') == '1' and a.mlflow_run, 'Use supervised entry point')
        return worker(cfg, report, a.mlflow_run, receipt)
    from mlflow import MlflowClient
    from mlflow.entities import Param
    from scripts.diagnostics.backfill_full_runs_mlflow import URI
    full = cfg['full_segmenter']; output = Path(full['output_dir']); tracking = a.receipt.parent/'live-tracking.json'
    require(not output.exists() and not (Path(full['backup_dir'])/cfg['_experiment']['name']).exists(), 'Run output already exists')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        # Exclusive durable marker prevents another dispatch even if initial tracking fails.
        with tracking.open('xb') as stream:
            stream.write(canonical(dict(status='dispatch_claimed', receipt_sha256=a.sha256)))
            stream.flush(); os.fsync(stream.fileno())
        client = MlflowClient(tracking_uri=URI); experiment = client.get_experiment_by_name('PROWL capstone lesion outlining')
        require(experiment is not None, 'Expected local MLflow experiment missing')
        run = client.create_run(experiment.experiment_id, tags={'mlflow.runName':receipt['title'],
            'experiment_id':'CAP-EXP-019', 'scope':'exploratory_development_provided_ROI',
            'receipt_sha256':a.sha256, 'tracking':'live_local_journal_authoritative',
            'control_run_id':'67d11609cc78406b86145f13e24ec61b'})
        run_id = run.info.run_id
        tracking.write_bytes(canonical(dict(status='dispatched', run_id=run_id, tracking_uri=URI)))
        process = None; last_scan = [0.]

        def tick():
            if time.monotonic()-last_scan[0] < 30: return
            require_ac()
            for drive in (Path('C:/'), Path('E:/')):
                require(shutil.disk_usage(drive).free >= cfg['_experiment']['run']['min_free_bytes'], 'Free-space floor')
            require(tree_bytes(full['cache_dir']) <= full['cache_max_bytes'], 'Cache budget')
            require(tree_bytes(full['backup_dir']) <= full['backup_cap_bytes'], 'Backup budget')
            last_scan[0] = time.monotonic()

        try:
            params = dict(session_config(cfg), augmentation_policy=receipt['augmentation']['policy'],
                train_cases=1333, development_cases=70, control_sha256=receipt['control_sha256'],
                initialization_sha256=cfg['_experiment']['initialization']['sha256'], ema=False)
            client.log_batch(run_id, params=[Param(k, str(v)) for k, v in params.items()], synchronous=True)
            client.log_artifact(run_id, str(a.receipt), 'provenance'); tick()
            with (a.receipt.parent/'training-worker.log').open('x') as log:
                process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--receipt', str(a.receipt),
                    '--sha256', a.sha256, '--launch', '--worker', '--mlflow-run', run_id], cwd=ROOT,
                    env=dict(os.environ, PROWL_AUGMENTATION_SUPERVISED='1'), stdout=log, stderr=subprocess.STDOUT)
                resources = watch_windows(process, seconds=cfg['_experiment']['run']['max_seconds'], rss_bytes=full['rss_bytes'], tick=tick)
            client.set_tag(run_id, 'tracking_health', 'degraded_requires_backfill' if (output/'tracking-warning.json').exists() else 'healthy')
            for path in [output/'result.json', output/'execution/history.jsonl', *sorted((output/'execution').glob('native-*.json'))]:
                client.log_artifact(run_id, str(path), 'results')
            client.set_terminated(run_id, 'FINISHED'); print(json.dumps(resources), flush=True)
        except BaseException:
            client.set_terminated(run_id, 'FAILED'); raise
        finally:
            (a.receipt.parent/'training-resources.json').write_bytes(canonical(getattr(process, 'duration_resources', {})))


if __name__ == '__main__': main()
