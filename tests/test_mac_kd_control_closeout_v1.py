import json
from pathlib import Path
import pytest
from src.operations.mac_kd_control_closeout_v1 import inspect


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def completed(tmp_path):
    root=tmp_path/'run';backup=tmp_path/'backup';arm=root/'control';ex=arm/'execution'
    result=dict(completed=True,status='completed',completed_updates=24000,selected_step=20000)
    put(arm/'result.json',result);put(backup/'control/result.json',result)
    put(arm/'resources.json',dict(exit_code=0,success=False,workers_reaped=False,seconds=100,
        error="ValueError('Owned worker descendant was not reaped')"))
    for name in ('process.json','dispatch.json'):put(arm/name,{})
    for name,step in [('native-terminal.json',24000),('native-selected.json',20000)]:
        report=dict(step=step,scope='native_provided_pancreas_region_development',
                    cases=[dict(case_id='V',reconstruction=dict(gap_voxels=0))])
        put(ex/name,report);put(backup/'control'/name,report)
    for p in (ex/'history.jsonl',backup/'control/history.jsonl'):put(p,dict(event='completed',step=24000))
    return root,backup


def test_preserves_failed_record_and_binds_backups(completed):
    root,backup=completed;before=(root/'control/resources.json').read_bytes()
    proof=inspect(root,backup,['V'])
    assert proof['optimization_complete'] and not proof['historical_supervision_success']
    assert (root/'control/resources.json').read_bytes()==before
    assert str(backup/'control/native-terminal.json') in proof['pins']


@pytest.mark.parametrize('change', ['incomplete','failure','backup','coverage','tracking','duplicate'])
def test_rejects_ineligible_closeout(completed,change):
    root,backup=completed
    if change=='incomplete':put(root/'control/result.json',dict(completed=False))
    elif change=='failure':put(root/'control/resources.json',dict(exit_code=1))
    elif change=='backup':(backup/'control/native-terminal.json').write_text('{}')
    elif change=='coverage':
        path=root/'control/execution/native-terminal.json';v=json.loads(path.read_text());v['cases']=[];put(path,v)
    elif change=='tracking':put(root/'control/tracking-warning.json',{})
    else:(root/'treatment').mkdir()
    with pytest.raises(ValueError):inspect(root,backup,['V'])


def test_new_pause_protocol_preserves_old_request(tmp_path):
    from scripts.diagnostics.pause_mac_kd_treatment_v2 import request
    from src.data.segmenter_teacher_cache_v1 import sha
    put(tmp_path/'ready.json',dict(version='mac-kd-reviewed-treatment-launch-2'))
    pin=sha(tmp_path/'ready.json');request(tmp_path,pin);request(tmp_path,pin)
    assert json.loads((tmp_path/'pause-request.json').read_text())['receipt_sha256']==pin


def test_cleanup_failure_time_is_charged_without_rewriting():
    from src.operations.mac_kd_control_closeout_v1 import charge_control
    rows=[dict(resources=dict(workers_reaped=True,seconds=10.2)),
          dict(resources=dict(workers_reaped=False,seconds=20.1))]
    assert charge_control(100,rows)['charged_seconds']==32
    assert rows[-1]['resources']['workers_reaped'] is False
    with pytest.raises(ValueError,match='exhausted'):charge_control(32,rows)
