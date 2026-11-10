"""Explicit operator stop of this owned experiment; never launches/resumes work."""
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.append('/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies')
from scripts.diagnostics.run_stunet_margin_mac_20261110 import BASE, OUT, sha, write, backup

LABEL = 'com.prowl.stunet-margin-mac-20261110-01c'
PAUSE = BASE/'operator-pause-01'
EXPECTED = '8cff4e3bcb0142ea12bb9c5ee1c1efff4401dbca4755c3fccbe51677e26deb75'


def process(pid):
    p = subprocess.run(['ps','-p',str(pid),'-o','lstart='],capture_output=True,text=True)
    if p.returncode:
        return None
    command = subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip()
    return dict(pid=pid, start=p.stdout.strip(), command=command)


def owner():
    p = json.loads((OUT/'process.json').read_text())
    job = subprocess.check_output(['launchctl','print',f'gui/{os.getuid()}/{LABEL}'],text=True)
    matched = re.search(r'^\s*pid = (\d+)\s*$',job,re.M)
    worker = process(p['worker']); supervisor = process(p['supervisor'])
    if (matched is None or int(matched[1]) != p['supervisor'] or worker is None
            or worker['start'] != p['worker_start'] or supervisor is None
            or 'run_stunet_margin_mac_20261110.py --worker' not in worker['command']
            or 'run_stunet_margin_mac_20261110.py --launch-sha256 '+EXPECTED not in supervisor['command']
            or int(subprocess.check_output(['ps','-p',str(p['worker']),'-o','ppid='],text=True)) != p['supervisor']):
        raise ValueError('Owned process identity changed; refusing signal')
    return dict(process=p, supervisor=supervisor, worker=worker)


def completed():
    root = Path.home()/'PROWL-Backups/stunet-margin-mac-20261110-01'
    rows = []
    for path in sorted(OUT.glob('PanTS_*.json')):
        other = root/path.name
        if not other.is_file() or sha(path) != sha(other):
            continue  # A case is reusable only after its full independent commit.
        row = json.loads(path.read_text())
        if not row['independent_policy_replay'] or len(row['policies']) != 54 or row['gaps'] != 0:
            raise ValueError('Invalid completed case evidence')
        a = row['artifact']
        if sha(a['path']) != a['sha256'] or sha(a['backup']) != a['sha256']:
            raise ValueError('Completed native code backup mismatch')
        rows.append(row)
    return rows


def main():
    if sha(OUT/'request.json') != EXPECTED or (OUT/'resources.json').exists():
        raise ValueError('Unexpected scope/already stopped; inspect evidence, no repeat stop')
    if (PAUSE/'request.json').exists():
        raise FileExistsError('Operator-stop attempt already recorded')
    initial = owner(); initial_rows = completed()
    write(PAUSE/'request.json',dict(action='EXPLICIT_USER_PAUSE',requested_unix=time.time(),
        user_instruction='Pause it before leaving for school; later continuation at school needs readiness checks',
        primary_request_sha256=EXPECTED, ownership=initial,
        completed_initial=[r['case_id'] for r in initial_rows],automatic_resume=False))
    # Disable only the two identified idle CPU waiters before stopping their parent study.
    stopped = []
    for label, filename in (
            ('com.prowl.stunet-margin-closeout-20261110-02','close_stunet_margin_20261110_v2.py --publish-report'),
            ('com.prowl.stunet-voxel-clip-20261110-01','run_stunet_voxel_clip_20261110.py')):
        job = subprocess.check_output(['launchctl','print',f'gui/{os.getuid()}/{label}'],text=True)
        match = re.search(r'^\s*pid = (\d+)\s*$',job,re.M)
        if match is None:
            raise ValueError('Queued owner not in expected waiting state')
        identity = process(int(match[1]))
        if filename not in identity['command']:
            raise ValueError('Queued process identity differs')
        if (OUT/'voxel-clip-01/process.json').exists():
            raise ValueError('Secondary stage unexpectedly started; inspect rather than blind stop')
        subprocess.run(['launchctl','bootout',f'gui/{os.getuid()}/{label}'],check=True)
        stopped.append(dict(label=label,identity=identity))
    write(PAUSE/'queued-stages-stopped.json',dict(stopped=stopped))
    # Give the current short case up to45s to commit; preserve partial work if not.
    until = time.monotonic()+45
    while len(completed()) <= len(initial_rows) and time.monotonic() < until:
        time.sleep(.5)
    current = owner()
    if current != initial:
        raise ValueError('Owner changed immediately before signal')
    write(PAUSE/'signal.json',dict(signal='SIGTERM',label=LABEL,identity=current,time_unix=time.time()))
    subprocess.run(['launchctl','kill','SIGTERM',f'gui/{os.getuid()}/{LABEL}'],check=True)
    deadline = time.monotonic()+30
    while process(initial['process']['supervisor']) is not None:
        if time.monotonic() >= deadline:
            raise TimeoutError('Supervisor cleanup not confirmed; do not disconnect')
        time.sleep(.1)
    resources = json.loads((OUT/'resources.json').read_text())
    if not resources['workers_reaped']:
        raise ValueError('Owned worker reaping not verified; do not disconnect')
    live = process(initial['process']['worker'])
    if live is not None and live['start'] == initial['process']['worker_start']:
        raise ValueError('Original worker remains live')
    with (ROOT/'outputs/prowl/.mps-profile.lock').open('a+b') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
    for stage in stopped:
        observed = process(stage['identity']['pid'])
        if observed is not None and observed['start'] == stage['identity']['start']:
            raise ValueError('Queued CPU waiter remains live')
    subprocess.run(['launchctl','bootout',f'gui/{os.getuid()}/{LABEL}'],check=True)
    rows = completed()
    request = json.loads((OUT/'request.json').read_text())
    if any(sha(path) != h for path,h in request['pins'].items()):
        raise ValueError('Producing hash mismatch after stop')
    from mlflow import MlflowClient
    import sqlite3
    tracking = json.loads((OUT/'tracking.json').read_text())
    client = MlflowClient(tracking_uri=tracking['tracking_uri'])
    previous_status = client.get_run(tracking['run_id']).info.status
    client.set_tag(tracking['run_id'],'prowl.operator_status','PAUSED_BY_USER')
    client.set_tag(tracking['run_id'],'prowl.pause_evidence',str(PAUSE/'receipt.json'))
    client.set_terminated(tracking['run_id'],status='KILLED')
    if client.get_run(tracking['run_id']).info.status != 'KILLED':
        raise ValueError('Operator interruption tracking readback failed')
    with sqlite3.connect(BASE/'mlflow.db') as source, sqlite3.connect(OUT/'mlflow-after-operator-pause.db') as target:
        source.backup(target)
    backup(OUT/'mlflow-after-operator-pause.db')
    receipt = dict(status='USER_PAUSED_VERIFIED',observed_unix=time.time(),
        completed_cases=len(rows), completed_tiles=sum(r['tiles'] for r in rows),
        reusable_case_ids=[r['case_id'] for r in rows],
        remaining_case_ids=sorted({r['case_id'] for r in request['cases']}-{r['case_id'] for r in rows}),
        all_completed_case_backups_hash_match=True,all54_policy_replays_previously_verified=True,
        producing_pins_match=True,gpu_lock_acquired_after_stop=True,owned_workers_reaped=True,
        cpu_waiters_stopped=True,all_three_launchd_registrations_removed=True,
        checkpoint_sha256=request['checkpoint']['sha256'],primary_request_sha256=EXPECTED,
        resources=resources,mlflow=dict(**tracking,status='KILLED',operator_status='PAUSED_BY_USER',
            prior_interrupted_status_preserved=previous_status),
        original_deadline_unix=request['deadline_unix'],budget_reset=False,
        automatic_resume=False,continuation_requires_new_additive_runner_and_budget_check=True,
        incomplete_case_artifacts_preserved=[p.name for p in OUT.glob('PanTS_*')
            if p.stem not in {r['case_id'] for r in rows}])
    write(PAUSE/'receipt.json',receipt)
    dest=Path.home()/'PROWL-Backups/stunet-margin-mac-20261110-01/operator-pause-01'
    dest.mkdir()
    for path in PAUSE.glob('*.json'):
        import shutil
        with path.open('rb') as source,(dest/path.name).open('xb') as target:
            shutil.copyfileobj(source,target);target.flush();os.fsync(target.fileno())
        if sha(path) != sha(dest/path.name):
            raise ValueError('Operator evidence backup mismatch')
    print(json.dumps(receipt),flush=True)


if __name__ == '__main__':
    main()
