"""Additive v2 closeout: exact producer reduction order; never retries inference."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.append('/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies')
BASE = Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-margin-mac-20261110')
OUT = BASE/'screen-01'
LABEL = 'com.prowl.stunet-margin-mac-20261110-01c'
REPORT = ROOT/'docs/capstone/evaluation/STUNET-24K-MARGIN-RESULTS-20261110.md'
EVIDENCE = ROOT/'docs/capstone/evaluation/STUNET-24K-MARGIN-CLOSEOUT-20261110.json'


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def alive(pid, expected=None, command_contains=None):
    p = subprocess.run(['ps','-p',str(pid),'-o','lstart='], capture_output=True, text=True)
    if p.returncode != 0 or (expected is not None and p.stdout.strip() != expected):
        return False
    if command_contains is not None:
        command = subprocess.check_output(['ps','-p',str(pid),'-o','command='], text=True)
        return command_contains in command
    return True


def summarize_saved():
    from src.inference.stunet_margin_screen_20261110 import summarize
    request = json.loads((OUT/'request.json').read_text())
    by_id = {r['case_id']:r for r in request['cases']}
    order = request['pilot']+[r['case_id'] for r in request['cases'] if r['case_id'] not in request['pilot']]
    # Preserve the producer's summation order for exact floating-point reduction.
    rows = [json.loads((OUT/(name+'.json')).read_text()) for name in order]
    scored = summarize(rows)
    final = json.loads((OUT/'result.json').read_text())
    if any(scored[k] != final[k] for k in scored):
        raise ValueError('Final result differs from independently reduced70 case records')
    for row in rows:
        if row['gaps'] != 0 or not row['independent_policy_replay']:
            raise ValueError('Incomplete geometry/independent policy replay')
        for path in (OUT/(row['case_id']+'.npz'), OUT/(row['case_id']+'.json')):
            backup = Path.home()/'PROWL-Backups/stunet-margin-mac-20261110-01'/path.name
            if sha(path) != sha(backup):
                raise ValueError('Case independent backup hash mismatch')
    for path, expected in request['pins'].items():
        if sha(path) != expected:
            raise ValueError('Producing pin changed before closeout')
    return final, rows


def render(final, proof):
    raw = final['policies']['raw']; fixed = final['policies']['bias0_near5_min0']
    selected = final['selected_exploratory_policy']
    best = final['best_dice_ignoring_guards']
    top = sorted(final['policies'], key=lambda k:(-final['policies'][k]['positive_macro_dice'], k))[:10]
    selected_metrics = final['policies'][selected]
    text = [
        '# Terminal 24k: measured inference-policy results — November 10', '',
        f"Raw Dice: **{raw['positive_macro_dice']:.6f}**. Fixed 5 mm: **{fixed['positive_macro_dice']:.6f}**. "
        f"Guard-qualified exploratory selection: **{selected}**, Dice **{selected_metrics['positive_macro_dice']:.6f}**.", '',
        f"Highest Dice ignoring safeguards: **{best}** ({final['policies'][best]['positive_macro_dice']:.6f}); "
        f"guard status: {final['guards'].get(best, {}).get('passes', 'raw control')}. "
        'An ineligible maximum is not a recommended improvement.', '',
        'All 70 exposed development cases, 36 positive / 34 empty, 45 reference components and five small positive cases retained. '
        'One terminal24k MPS inference pass, 54 fixed reference-free decisions, zero training updates. '
        'Provided-pancreas-region evaluation; no independent or leakage-free performance claim. No policy deployed.', '',
        '| Policy | Dice | Recall | Small recall | Cases / components hit | Empty alarms | FP mL | Guards |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    order = list(dict.fromkeys(['raw','bias0_near5_min0',selected]+top))
    for key in order:
        m = final['policies'][key]
        text.append(f"| {key} | {m['positive_macro_dice']:.6f} | {m['positive_macro_recall']:.6f} | "
            f"{m['small_case_macro_recall']:.6f} | {m['detected_cases']}/36; {m['detected_components']}/45 | "
            f"{m['empty_alarm_cases']}/34 | {m['false_positive_mL']:.3f} | "
            f"{final['guards'].get(key, {}).get('passes', 'control')} |")
    text += ['', '## Interpretation', '',
        f"Selected gain versus raw: {selected_metrics['positive_macro_dice']-raw['positive_macro_dice']:+.6f}; "
        f"versus standing 5 mm: {selected_metrics['positive_macro_dice']-fixed['positive_macro_dice']:+.6f}. "
        'These comparisons share the newly generated MPS raw control. Original CUDA differences are retained per case; '
        'they are not attributed to the decision policy.', '',
        'A failed recall, small-lesion, case/component identity, pancreas, empty-alarm or false-positive-volume guard '
        'disqualifies a setting even if its Dice is higher. Selection on these already exposed cases is optimistic. '
        'Confirmation on a prospectively fixed later checkpoint and, ultimately, a verified independent cohort remains necessary.', '',
        'This finite search tunes inference decisions, not learning rate or the training loss. '
        'Any later training ablation must preserve a matched control and wait for Lenovo GPU availability.', '',
        '## Integrity and execution', '',
        f"Checkpoint SHA256: `{final['checkpoint_sha256']}`. Request SHA256: `{final['request_sha256']}`.", '',
        f"Elapsed worker seconds: {final['seconds']:.1f}; resource and cleanup verification: {proof['status']}. "
        'All 54 policies were independently replayed from each reopened case backup. '
        'Final summaries were independently rebuilt from saved case records; all producing pins matched. '
        'MLflow stores this as inference-policy work, excluded from training hours.', '',
        '[Protocol](../operations/STUNET-24K-MARGIN-SCREEN-20261110.md). '
        '[Closeout evidence](STUNET-24K-MARGIN-CLOSEOUT-20261110.json).', '',
        'Method context: [nnU-Net validates component-removal postprocessing](https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/how-to/find-best-configuration.md); '
        '[Optuna documents exhaustive finite-grid search](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.GridSampler.html). '
        'Those sources motivate evaluating decisions rather than assuming that a filter helps; they do not establish a gain for PROWL.', '']
    return '\n'.join(text)


def close(publish=False):
    request = json.loads((OUT/'request.json').read_text())
    deadline = request['deadline_unix']+180  # CPU verification only; never extends GPU budget.
    process = json.loads((OUT/'process.json').read_text())
    while alive(process['supervisor'], command_contains='run_stunet_margin_mac_20261110.py --launch-sha256 '+sha(OUT/'request.json')):
        if time.time() > deadline:
            raise TimeoutError('Bounded closeout waiting exhausted; no GPU restart')
        time.sleep(2)
    resources = json.loads((OUT/'resources.json').read_text())
    if not resources['success'] or not resources['workers_reaped'] or resources['exit_code'] != 0:
        raise ValueError('Scientific screen did not finish successfully; retain evidence, no retry')
    if alive(process['worker'], process['worker_start']):
        raise ValueError('Owned worker identity remains live')
    with (ROOT/'outputs/prowl/.mps-profile.lock').open('a+b') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(f, fcntl.LOCK_UN)
    final, rows = summarize_saved()
    from mlflow import MlflowClient
    tracking = json.loads((OUT/'tracking.json').read_text())
    run = MlflowClient(tracking_uri=tracking['tracking_uri']).get_run(tracking['run_id'])
    if run.info.status != 'FINISHED':
        raise ValueError('MLflow not FINISHED')
    for key, metrics in final['policies'].items():
        for name, value in metrics.items():
            if value is not None and run.data.metrics.get(key+'/'+name) != float(value):
                raise ValueError('MLflow complete metric readback mismatch')
    snapshot = OUT/'mlflow-snapshot.db'
    backup_root = Path.home()/'PROWL-Backups/stunet-margin-mac-20261110-01'
    for path in (snapshot, OUT/'resources.json', OUT/'result.json', OUT/'request.json'):
        if sha(path) != sha(backup_root/path.name):
            raise ValueError('Final independent backup mismatch')
    with sqlite3.connect('file:'+str(snapshot)+'?mode=ro', uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Saved tracking database integrity failed')
    description = subprocess.check_output(['launchctl','print',f'gui/{os.getuid()}/{LABEL}'], text=True)
    if 'state = not running' not in description or 'last exit code = 0' not in description:
        raise ValueError('One-shot launch owner has not exited normally')
    subprocess.run(['launchctl','bootout',f'gui/{os.getuid()}/{LABEL}'], check=True)
    proof = dict(status='VERIFIED_COMPLETE', cases=len(rows), policies=54,
        source_checkpoint_sha256=final['checkpoint_sha256'], request_sha256=sha(OUT/'request.json'),
        result_sha256=sha(OUT/'result.json'), mlflow=tracking, mlflow_status='FINISHED',
        source_pins_match=True, all_case_backups_match=True, all_policy_replays_match=True,
        independent_final_backups_match=True, database_integrity='ok', resources=resources,
        gpu_lock_acquired_after_exit=True, owned_processes_absent=True,
        one_shot_launch_registration_removed=True, producing_attempts_preserved=True,
        policy_deployed=False, training_updates=0)
    with EVIDENCE.open('x') as f:
        json.dump(proof, f, indent=2); f.write('\n')
    with REPORT.open('x') as f:
        f.write(render(final, proof))
    if publish:
        if subprocess.check_output(['git','branch','--show-current'], cwd=ROOT, text=True).strip() != 'main':
            raise ValueError('Report prepared, but autonomous commit requires the unchanged main branch')
        paths = [str(REPORT.relative_to(ROOT)), str(EVIDENCE.relative_to(ROOT))]
        subprocess.run(['git','add','--']+paths, cwd=ROOT, check=True, timeout=60)
        subprocess.run(['git','commit','--only','-m','Report verified terminal24k postprocessing tuning results','--']+paths, cwd=ROOT, check=True, timeout=60)
        subprocess.run(['git','push','origin','main'], cwd=ROOT, check=True, timeout=60)
    print(json.dumps(dict(status=proof['status'], report=str(REPORT), selected=final['selected_exploratory_policy'])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--publish-report', action='store_true')
    a = p.parse_args()
    try:
        close(a.publish_report)
    except Exception as exc:
        with (BASE/'closeout-failure.json').open('x') as f:
            json.dump(dict(status='CLOSEOUT_BLOCKED_NO_RETRY', reason=repr(exc), inference_restarted=False), f, indent=2)
        raise
