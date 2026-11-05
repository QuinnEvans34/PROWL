from copy import deepcopy
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from tests.test_kd_error_review_preparation import make_review_fixture, write
from src.operations import mac_kd_result_report_v1 as module


@pytest.fixture
def completed(tmp_path, monkeypatch):
    root, pin = make_review_fixture(tmp_path, terminal=24000)
    receipt = json.loads((root/'ready.json').read_text())
    original_pin = receipt['original_sha256']
    receipt['control_closeout']['resources'].update(exit_code=0)
    control_root = Path(receipt['segments']['control'][-1]['root'])
    control_backup = Path(receipt['segments']['control'][-1]['backup'])
    write(control_root/'control/resources.json', receipt['control_closeout']['resources'])
    for arm, r, b in [('control', control_root, control_backup), ('treatment', root, Path(receipt['backup']))]:
        ex, backup = r/arm/'execution', b/arm
        for endpoint, step in [('selected', 2000), ('terminal', 24000)]:
            body = json.loads((ex/f'native-{step:06d}.json').read_text())
            side = json.loads((ex/f'native-{step:06d}-components.json').read_text())
            value = dict(body, endpoint=endpoint)
            side['report_sha256'] = hashlib.sha256(json.dumps(value).encode()).hexdigest()
            for base in (ex, backup):
                write(base/f'native-{endpoint}.json', value)
                write(base/f'native-{endpoint}-components.json', side)
        for name in ('best.pt', 'last.pt', 'step-002000.pt', 'step-024000.pt'):
            (ex/name).write_bytes(b'opaque synthetic checkpoint')
            (backup/name).write_bytes(b'opaque synthetic checkpoint')
        journal = ex/'history.jsonl'
        with journal.open('a') as f:f.write(json.dumps(dict(event='completed', step=24000))+'\n')
        (backup/'history.jsonl').write_bytes(journal.read_bytes())
        result = dict(status='completed', completed=True, completed_updates=24000,
                      selected_step=2000, best_development_dice=80/220)
        write(r/arm/'result.json', result);write(backup/'result.json', result)
        if arm == 'control':receipt['control_closeout']['result'] = result
        else:
            resources = dict(success=True, workers_reaped=True, exit_code=0,
                             surviving_workers=[], cleanup_error=None, supervisor_cleanup_error=None)
            write(r/arm/'resources.json', resources);write(backup/'resources.json', resources)
            write(r/'complete.json', dict(success=True, arms=['treatment']))
        run_id = ('a' if arm == 'control' else 'b')*32
        dispatch = dict(run_id=run_id, tracking_uri='sqlite:///'+str(r/'mlflow.db'))
        write(r/arm/'dispatch.json', dispatch);write(backup/'dispatch.json', dispatch)
        if arm == 'treatment':write(r/arm/'complete.json', dict(success=True, completed_updates=24000, run_id=run_id))
        with sqlite3.connect(r/'mlflow.db') as db:
            db.executescript('CREATE TABLE runs (run_uuid TEXT,status TEXT); CREATE TABLE tags(run_uuid TEXT,key TEXT,value TEXT); CREATE TABLE metrics(run_uuid TEXT,key TEXT,value REAL,step INT,is_nan INT);')
            db.execute('INSERT INTO runs VALUES(?,?)', (run_id, 'FAILED' if arm=='control' else 'FINISHED'))
            for key, value in [('arm', arm), ('comparison_sha256', original_pin)]:db.execute('INSERT INTO tags VALUES(?,?,?)',(run_id,key,value))
            db.execute('INSERT INTO metrics VALUES(?,?,?,?,?)',(run_id,'train/loss',.5,24000,0))
            for step in range(2000,24001,2000):
                db.execute('INSERT INTO metrics VALUES(?,?,?,?,?)',(run_id,'native/dev70/raw/lesion_positive_macro_dice',80/220,step,0))
    write(root/'ready.json', receipt);pin=hashlib.sha256((root/'ready.json').read_bytes()).hexdigest()
    monkeypatch.setattr(module, 'separate_filesystems', lambda a,b:True)
    monkeypatch.setattr(module, 'verify_process_cleanup', lambda *args:None)
    monkeypatch.setattr(module, 'verify_gpu_release', lambda:None)
    return root, pin


def test_live_report_is_explicitly_pending_and_does_not_observe_or_stop_workers(tmp_path, monkeypatch):
    root,pin=make_review_fixture(tmp_path)
    monkeypatch.setattr(module,'verify_process_cleanup',lambda *a:pytest.fail('must not inspect cleanup while live'))
    result=module.report(root,pin,tmp_path/'result')
    assert result['status']=='PENDING_TREATMENT_COMPLETION'
    assert not result['execution_closeout_verified'] and result['endpoints'] is None
    assert result['latest_matched']['step']==14000
    assert result['hypothesis_decision'] is result['practical_decision'] is None


def test_full_series_waits_for_terminal_receipts_not_just_last_dice(tmp_path):
    root,pin=make_review_fixture(tmp_path,terminal=24000)
    result=module.report(root,pin,tmp_path/'pending')
    assert not any(result['missing_native_steps'].values())
    assert result['status']=='PENDING_TREATMENT_COMPLETION' and result['pending_terminal_receipts']


def test_complete_report_preserves_control_failure_and_withholds_unjustified_verdict(completed,tmp_path):
    root,pin=completed
    before=(root/'mlflow.db').read_bytes()
    result=module.report(root,pin,tmp_path/'closed')
    assert result['status']=='CLOSED_DESCRIPTIVE_ONLY' and result['execution_closeout_verified']
    assert set(result['endpoints'])=={'selected','terminal'}
    assert len(result['endpoints']['selected']['cases'])==70
    assert result['closeout']['control']['tracking']['status']=='FAILED'
    assert result['closeout']['treatment']['tracking']['status']=='FINISHED'
    assert not result['historical_control_supervision_success']
    assert result['confidence_intervals'] is result['hypothesis_decision'] is result['practical_decision'] is None
    assert before==(root/'mlflow.db').read_bytes()
    with pytest.raises(ValueError,match='Fresh'):module.report(root,pin,tmp_path/'closed')


@pytest.mark.parametrize('damage', ['checkpoint','journal','selected','tracking','series_metric','cleanup','process','filesystem','completion'])
def test_closeout_fails_closed_on_broken_evidence(completed,tmp_path,monkeypatch,damage):
    root,pin=completed;arm=root/'treatment';ex=arm/'execution'
    if damage=='checkpoint':(ex/'last.pt').write_bytes(b'corrupt')
    if damage=='journal':(Path(json.loads((root/'ready.json').read_text())['backup'])/'treatment/history.jsonl').write_bytes(b'changed')
    if damage=='selected':write(ex/'native-selected.json',{})
    if damage=='tracking':
        with sqlite3.connect(root/'mlflow.db') as db:db.execute("UPDATE runs SET status='RUNNING'")
    if damage=='series_metric':
        with sqlite3.connect(root/'mlflow.db') as db:db.execute('DELETE FROM metrics WHERE step=4000')
    if damage=='cleanup':
        resources=json.loads((arm/'resources.json').read_text());resources['surviving_workers']=[123];write(arm/'resources.json',resources)
    if damage=='process':monkeypatch.setattr(module,'verify_process_cleanup',lambda *a:(_ for _ in ()).throw(ValueError('live owner')))
    if damage=='filesystem':monkeypatch.setattr(module,'separate_filesystems',lambda *a:False)
    if damage=='completion':write(arm/'complete.json',dict(success=True,completed_updates=24000,run_id='c'*32))
    with pytest.raises(ValueError):module.report(root,pin,tmp_path/'bad')
    assert not (tmp_path/'bad/report.json').exists()


def test_endpoint_comparison_allows_distinct_policy_selected_steps(completed):
    root,_=completed;receipt=json.loads((root/'ready.json').read_text())
    a=json.loads((Path(receipt['segments']['control'][-1]['root'])/'control/execution/native-002000.json').read_text())
    b=json.loads((root/'treatment/execution/native-024000.json').read_text())
    paired=module.endpoint_comparison(a,b,[x['case_id'] for x in a['cases']])
    assert paired['control_step']==2000 and paired['treatment_step']==24000
    assert paired['confidence_intervals'] is None


def test_gpu_release_observation_uses_an_isolated_lock(tmp_path):
    import fcntl
    lock=tmp_path/'test-only.lock';lock.touch()
    module.verify_gpu_release(lock)
    with lock.open('rb') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):module.verify_gpu_release(lock)
