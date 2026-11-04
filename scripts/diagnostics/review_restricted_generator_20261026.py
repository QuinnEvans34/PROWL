"""Read-only source review; writes a new closeout receipt, never trains/infers."""
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics

RUN = Path('E:/PROWL/artifacts/pants_reserved_verifier_generator_24k_20261025')
BACKUP = Path('C:/Users/quinn/PROWL-Backups/pants_reserved_verifier_generator_24k_20261025')
SETUP = Path('E:/PROWL/readiness/verifier-generator-launch-20261025-a01')
DEST = Path('E:/PROWL/readiness/verifier-generator-review-20261026-a01')
READY = 'b3e49f3d96e1694252fc29b9776d7969ba139a29b245b23bbc4b27bcb5f46d89'

def read(p):
    return json.loads(p.read_text())

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def review():
    require(not DEST.exists(), 'Review already exists; inspect, do not overwrite')
    require(sha(SETUP/'ready.json') == READY, 'Ready identity changed')
    receipt = read(SETUP/'ready.json')
    bad = [p for p, h in receipt['pins'].items() if sha(Path(p)) != h]
    require(not bad, 'Producing pins changed: ' + repr(bad))
    result = read(RUN/'result.json')
    resources = read(SETUP/'scientific-resources.json')
    require(resources['success'] and resources['exit_code'] == 0 and resources['workers_reaped'], 'Unclean closeout')
    require(result['completed_updates'] == result['selected_step'] == 24000 and result['selected_checkpoint'] == 'terminal.pt' and result['development_cases_evaluated'] == 0, 'Completion/selection mismatch')
    rows = [json.loads(line) for line in (RUN/'execution/history.jsonl').read_text().splitlines()]
    updates = [r for r in rows if r['event'] == 'update']
    require([r['step'] for r in updates] == list(range(1, 24001)), 'Noncontiguous steps')
    require(rows[-1]['event'] == 'completed' and not any(r['event'] == 'failed' or 'validat' in r['event'] for r in rows), 'Unexpected failure/evaluation')
    require(all(math.isfinite(r['loss']) for r in updates), 'Nonfinite losses')
    control = read(RUN/'input-control.json')
    partition = read(Path('E:/PROWL/readiness/verifier-generator-20261023-a01/partitions.json'))
    members = collections.Counter(r['member_id'] for r in updates)
    require(set(members) == set(control['train']) == set(partition['roles']['generator_train']) and len(members) == 800, 'Optimizer membership mismatch')
    require(set(members.values()) == {30}, 'Expected 30 visits per generator patient')
    require(not set(members) & set(partition['development']), 'Development exposure')
    backups = {}
    for p in BACKUP.iterdir():
        if p.name in ('initial.pt', 'last.pt', 'terminal.pt', 'history.jsonl'):
            source = RUN/'execution'/p.name
        elif p.name == 'train_ids.txt':
            source = RUN/'splits'/p.name
        else:
            source = RUN/p.name
        require(source.is_file() and sha(source) == sha(p), 'Backup mismatch: ' + p.name)
        backups[p.name] = sha(p)
    require({'initial.pt','last.pt','terminal.pt','history.jsonl','result.json'} <= set(backups), 'Missing backups')
    from mlflow import MlflowClient
    tracking = read(RUN/'tracking.json')
    client = MlflowClient(tracking_uri=tracking['tracking_uri'])
    run = client.get_run(tracking['run_id'])
    metrics = client.get_metric_history(tracking['run_id'], 'train/loss')
    require(run.info.status == 'FINISHED', 'MLflow not finished')
    require({m.step for m in metrics} == {1, *range(25, 24001, 25)}, 'Missing stored losses')
    require(all(m.value == updates[m.step-1]['loss'] for m in metrics), 'MLflow/journal loss mismatch')
    require(not (RUN/'tracking-warning.json').exists(), 'Tracking warning')
    kinds = collections.Counter(r['input_view']['window']['kind'] for r in updates)
    evidence = dict(status='CLOSEOUT_PASS_NOT_VERIFIER_EFFICACY', ready_sha256=READY,
        producing_pins_verified=len(receipt['pins']), result=result, resources=resources,
        journal_sha256=sha(RUN/'execution/history.jsonl'), terminal_sha256=backups['terminal.pt'],
        backup_sha256=backups, optimizer_patients=len(members), visits_per_patient=30,
        update_kinds=dict(kinds), loss_first500=statistics.mean(r['loss'] for r in updates[:500]),
        loss_last500=statistics.mean(r['loss'] for r in updates[-500:]),
        loss_last_update=updates[-1]['loss'], mlflow_run_id=tracking['run_id'],
        mlflow_status=run.info.status, stored_loss_points=len(metrics),
        h0_verdict='NOT_TESTED: no candidate-verifier evaluation performed',
        scope='Design-informed/exploratory; inherited annotation-informed margins; unknown SuPreM pretraining membership')
    DEST.mkdir()
    with (DEST/'results.json').open('x') as f:
        json.dump(evidence, f, indent=2, allow_nan=False)
    print(json.dumps(evidence, indent=2))

if __name__ == '__main__':
    review()
