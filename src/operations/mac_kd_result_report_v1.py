"""Read-only Mac KD closeout. Live runs yield pending evidence, never acceptance.

Reuses the full-series/native component reader. Checkpoints are byte-hashed, not
deserialized or restored. Patient independence remains unresolved, so completed
reports contain descriptive selected/terminal comparisons without bootstrap CIs.
"""
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess

from src.operations.kd_error_review_preparation_v1 import MetadataReader, prepare
from src.training.native_error_review_v1 import case_error, check_pair, close, require, summarize, validate_report


def endpoint_comparison(control, treatment, cohort):
    a, b = validate_report(control, cohort), validate_report(treatment, cohort)
    check_pair(a, b)
    rows = []
    for name in cohort:
        old, new = case_error(a[name]), case_error(b[name])
        rows.append(dict(case_id=name, control=old, treatment=new,
                         dice_delta=None if not old['target_voxels'] else new['dice'] - old['dice'],
                         missed_component_delta=(new['components'] - new['components_detected']) -
                                                (old['components'] - old['components_detected']),
                         false_positive_voxel_delta=new['false_positive'] - old['false_positive']))
    return dict(control=summarize(control, cohort), treatment=summarize(treatment, cohort), cases=rows,
                control_step=control['step'], treatment_step=treatment['step'],
                confidence_intervals=None, hypothesis_decision=None, practical_decision=None)


def separate_filesystems(execution, backup):
    return execution.stat().st_dev != backup.stat().st_dev


def verify_gpu_release(lock=None):
    lock = lock or Path(__file__).resolve().parents[2] / 'outputs/prowl/.mps-profile.lock'
    with Path(lock).open('rb') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(stream, fcntl.LOCK_UN)


def verify_series_tracking(reader, preparation, original_pin):
    verified = {}
    for arm, sources in preparation['series_sources'].items():
        verified[arm] = []
        for step, source in sources.items():
            root = Path(source['report_path']).parents[2]
            dispatch, _ = reader.read(root / arm / 'dispatch.json')
            database = root / 'mlflow.db'
            require(dispatch['tracking_uri'] == 'sqlite:///' + str(database), 'Series tracking identity differs')
            report, _ = reader.read(source['report_path'], source['report_sha256'])
            with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=5) as db:
                tags = dict(db.execute('SELECT key,value FROM tags WHERE run_uuid=?', (dispatch['run_id'],)))
                require(tags.get('arm') == arm and tags.get('comparison_sha256') == original_pin,
                        'Series tracking comparison differs')
                values = db.execute('SELECT value,is_nan FROM metrics WHERE run_uuid=? AND key=? AND step=?',
                                    (dispatch['run_id'], 'native/dev70/raw/lesion_positive_macro_dice', step)).fetchall()
                require(len(values) == 1 and not values[0][1]
                        and close(values[0][0], report['lesion_positive_macro_dice']), 'Stored series metric differs')
            verified[arm].append(dict(step=step, run_id=dispatch['run_id'], value=values[0][0]))
    return verified


def verify_process_cleanup(root, arm, reader):
    """Observe ownership only; never signal, stop, repair or restart anything."""
    from src.operations.mac_worker_cleanup_v3 import snapshot
    process, _ = reader.read(root / arm / 'process.json')
    current = snapshot()
    require(not any(r['group'] == process['worker'] for r in current.values()), 'Worker group remains live')
    worker = current.get(process['worker'])
    require(worker is None or worker['born'] != process['worker_start'], 'Worker identity remains live')
    dispatch, _ = reader.read(root / 'dispatch.json')
    target = dispatch['target']
    require(re.fullmatch(r'gui/[0-9]+/com\.prowl\.[a-z0-9.-]+', target), 'Owned launchd target required')
    found = subprocess.run(['launchctl', 'print', target], capture_output=True, text=True, timeout=5)
    if found.returncode == 0:
        require(not re.search(r'^\s*pid = [0-9]+\s*$', found.stdout, re.M), 'Supervisor remains live')
    else:
        require('Could not find service' in found.stderr, 'Unknown launchd ownership state')


def tracking(root, arm, reader, original_pin, selected, terminal, *, historical_failure=False):
    dispatch, _ = reader.read(root / arm / 'dispatch.json')
    database = root / 'mlflow.db'
    require(dispatch['tracking_uri'] == 'sqlite:///' + str(database), 'Tracking database identity differs')
    run = dispatch['run_id']
    require(re.fullmatch('[a-f0-9]{32}', run), 'MLflow run identity required')
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=5) as db:
        status = db.execute('SELECT status FROM runs WHERE run_uuid=?', (run,)).fetchall()
        expected = 'FAILED' if historical_failure else 'FINISHED'
        require(status == [(expected,)], 'Terminal MLflow status differs')
        tags = dict(db.execute('SELECT key,value FROM tags WHERE run_uuid=?', (run,)))
        require(tags.get('arm') == arm and tags.get('comparison_sha256') == original_pin,
                'Tracking arm/comparison differs')
        loss = db.execute('SELECT value,is_nan FROM metrics WHERE run_uuid=? AND key=? AND step=24000',
                          (run, 'train/loss')).fetchall()
        require(len(loss) == 1 and not loss[0][1] and close(loss[0][0], loss[0][0]), 'Stored terminal loss required')
        # The selected report may be inherited from an earlier continuation. Its
        # owning dispatch is checked separately through series_sources below.
        values = db.execute('SELECT value,is_nan FROM metrics WHERE run_uuid=? AND key=? AND step=?',
                            (run, 'native/dev70/raw/lesion_positive_macro_dice', terminal['step'])).fetchall()
        require(len(values) == 1 and not values[0][1] and close(values[0][0], terminal['lesion_positive_macro_dice']),
                'Stored terminal native metric differs')
    require(not (root / arm / 'tracking-warning.json').exists(), 'Tracking warning retained')
    return dict(run_id=run, status=expected, terminal_loss=loss[0][0], read_only=True)


def close_arm(reader, root, backup, arm, preparation, original_pin, *, historical_failure=False):
    ex, peer = root / arm / 'execution', backup / arm
    require(separate_filesystems(ex, peer), 'Independent backup filesystem required')
    result, pin = reader.read(root / arm / 'result.json')
    reader.read(peer / 'result.json', pin)
    resources, _ = reader.read(root / arm / 'resources.json')
    require(result.get('completed') is True and result.get('status') == 'completed'
            and result.get('completed_updates') == 24000, 'Terminal optimization required')
    if not historical_failure:
        require(resources.get('success') is True and resources.get('workers_reaped') is True
                and resources.get('exit_code') == 0 and not resources.get('surviving_workers')
                and not resources.get('cleanup_error') and not resources.get('supervisor_cleanup_error'),
                'Clean terminal supervision required')
        _, resource_pin = reader.read(root / arm / 'resources.json')
        reader.read(peer / 'resources.json', resource_pin)
        complete, _ = reader.read(root / arm / 'complete.json')
        overall, _ = reader.read(root / 'complete.json')
        require(complete.get('success') is True and complete.get('completed_updates') == 24000
                and overall == dict(success=True, arms=['treatment']), 'Completion receipts required')
        dispatch, dispatch_pin = reader.read(root / arm / 'dispatch.json')
        reader.read(peer / 'dispatch.json', dispatch_pin)
        require(complete['run_id'] == dispatch['run_id'], 'Completion/tracking identity differs')
    else:
        require(resources == preparation['historical_control_resources'], 'Historical failure changed')
    snapshot = reader.journal(ex / 'history.jsonl')
    require(snapshot['last'] == dict(event='completed', step=24000) and snapshot['last_update'] == 24000,
            'Completed terminal journal required')
    journal = (ex / 'history.jsonl').read_bytes()
    require(journal == (peer / 'history.jsonl').read_bytes(), 'Final journal backup differs')
    endpoints, checkpoints = {}, {}
    selection = preparation['endpoints_if_full_series'][arm]
    for endpoint, step in [('selected', selection['selected_step']), ('terminal', 24000)]:
        path = ex / f'native-{endpoint}.json'
        report, digest = reader.read(path)
        reader.read(peer / path.name, digest)
        side, side_pin = reader.read(ex / f'native-{endpoint}-components.json')
        reader.read(peer / f'native-{endpoint}-components.json', side_pin)
        from src.operations.kd_error_review_preparation_v1 import reference_signature
        reference_signature(report, side, digest, preparation['cohort'], 36)
        source, _ = reader.read(preparation['series_sources'][arm][step]['report_path'])
        require(report == dict(source, endpoint=endpoint), 'Endpoint differs from selected/terminal series report')
        require(report['step'] == step, 'Endpoint step differs')
        endpoints[endpoint] = report
        name = 'best.pt' if endpoint == 'selected' else 'last.pt'
        # Hash opaque checkpoint bytes; do not load tensors alongside the trainer.
        for filename in (name, f'step-{step:06d}.pt'):
            require((ex / filename).stat().st_size <= 256 * 1024**2, 'Checkpoint hash-read limit')
            with (ex / filename).open('rb') as stream:
                value = hashlib.file_digest(stream, 'sha256').hexdigest()
            with (peer / filename).open('rb') as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == value, 'Checkpoint backup differs')
            checkpoints[filename] = value
    require(result['selected_step'] == selection['selected_step']
            and close(result['best_development_dice'], endpoints['selected']['lesion_positive_macro_dice']),
            'Result selection differs from full series')
    verify_process_cleanup(root, arm, reader)
    tracked = tracking(root, arm, reader, original_pin, endpoints['selected'], endpoints['terminal'],
                       historical_failure=historical_failure)
    return dict(endpoints=endpoints, checkpoint_sha256=checkpoints, checkpoint_scope='byte_hash_and_independent_backup_not_restore',
                tracking=tracked, current_process_absence_verified=True,
                historical_supervision_success=not historical_failure)


def report(root, ready_sha256, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    require(not output.exists(), 'Fresh report destination required')
    guard = MetadataReader()
    receipt, _ = guard.read(root / 'ready.json', ready_sha256)
    producing = [root, Path(receipt['original']), Path(receipt['backup'])]
    for segments in receipt['segments'].values():
        for segment in segments:
            producing.extend([Path(segment['root']), Path(segment['backup'])])
    require(not any(p.resolve() == output or p.resolve() in output.parents for p in producing),
            'Report must be outside producing and backup directories')
    # An interrupted report remains in its own directory and is never reused.
    output.mkdir(parents=True)
    preparation = prepare(root, ready_sha256, output / 'preparation')
    guard.verify()
    result = dict(schema='prowl.mac-kd.result-report.v1', status='PENDING_TREATMENT_COMPLETION',
                  completed_native_steps=preparation['completed_native_steps'],
                  missing_native_steps=preparation['missing_native_steps'],
                  latest_matched=preparation['latest_matched'], endpoints=None,
                  execution_closeout_verified=False, hypothesis_decision=None, practical_decision=None,
                  confidence_intervals=None, patient_independence='unresolved',
                  scope=preparation['scope'], historical_control_supervision_success=False,
                  model_calls=0, optimizer_updates=0)
    final_receipts = ['complete.json', 'treatment/complete.json', 'treatment/result.json', 'treatment/resources.json']
    result['pending_terminal_receipts'] = [name for name in final_receipts if not (root / name).exists()]
    if (root / 'treatment/resources.json').exists():
        resources, _ = guard.read(root / 'treatment/resources.json')
        result['observed_supervision'] = resources
        if (resources.get('success') is not True or resources.get('workers_reaped') is not True
                or resources.get('exit_code') != 0 or resources.get('surviving_workers')
                or resources.get('cleanup_error') or resources.get('supervisor_cleanup_error')):
            result['status'] = 'FAILED_EXECUTION_REVIEW_REQUIRED'
        elif (root / 'treatment/result.json').exists():
            terminal_result, _ = guard.read(root / 'treatment/result.json')
            if terminal_result.get('status') == 'paused':
                result['status'] = 'PAUSED_OPERATOR'
            elif terminal_result.get('completed') is True:
                result['status'] = 'PENDING_CLOSEOUT'
    if not any(preparation['missing_native_steps'].values()) and not result['pending_terminal_receipts']:
        reader = MetadataReader()
        receipt, _ = reader.read(root / 'ready.json', ready_sha256)
        last_control = receipt['segments']['control'][-1]
        preparation['historical_control_resources'] = receipt['control_closeout']['resources']
        arms = dict(control=close_arm(reader, Path(last_control['root']), Path(last_control['backup']), 'control',
                                     preparation, receipt['original_sha256'], historical_failure=True),
                    treatment=close_arm(reader, root, Path(receipt['backup']), 'treatment', preparation,
                                       receipt['original_sha256']))
        # Process absence and an available exclusive GPU lock are separate checks.
        verify_gpu_release()
        series_tracking = verify_series_tracking(reader, preparation, receipt['original_sha256'])
        reader.verify()
        result.update(status='CLOSED_DESCRIPTIVE_ONLY', execution_closeout_verified=True,
                      endpoints={name: endpoint_comparison(arms['control']['endpoints'][name],
                                  arms['treatment']['endpoints'][name], preparation['cohort'])
                                 for name in ('selected', 'terminal')}, closeout=arms,
                      metadata_pins=reader.pins, journal_prefixes=reader.prefixes)
        result['series_tracking'] = series_tracking
    result['remaining_limits'] = ['No independent-patient uncertainty or scientific acceptance verdict.',
                                 'Aggregate errors do not locate false-positive regions or boundary errors.',
                                 'Checkpoint hashes are not a new numerical restore qualification.']
    guard.verify()
    (output / 'report.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result
