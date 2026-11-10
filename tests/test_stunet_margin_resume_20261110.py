"""Case reuse and scientific-producer identity; no private arrays or GPU calls."""
from pathlib import Path
from copy import deepcopy
import pytest

from scripts.diagnostics import resume_stunet_margin_mac_20261110 as resume


def fixture():
    parent = dict(cases=[dict(case_id=str(i)) for i in range(70)],pilot=['68','69'])
    pause = dict(reusable_case_ids=['0','1','68','69'],status='USER_PAUSED_VERIFIED',
        owned_workers_reaped=True,gpu_lock_acquired_after_stop=True,
        primary_request_sha256=resume.PARENT_REQUEST_SHA,completed_cases=4,
        remaining_case_ids=[str(i) for i in range(2,68)])
    return parent,pause


def test_partition_reuses_complete_cases_and_preserves_producer_order():
    parent,pause=fixture()
    old,new=resume.partition(parent,pause)
    assert old==['68','69','0','1']
    assert new==[str(i) for i in range(2,68)]
    assert not set(old)&set(new)
    assert set(old)|set(new)=={str(i) for i in range(70)}


@pytest.mark.parametrize('change',[
    lambda p:p['reusable_case_ids'].append('0'),
    lambda p:p['reusable_case_ids'].append('not-in-cohort'),
    lambda p:p.update(owned_workers_reaped=False),
    lambda p:p.update(gpu_lock_acquired_after_stop=False),
    lambda p:p.update(status='FAILED'),
    lambda p:p.update(primary_request_sha256='bad'),
    lambda p:p['remaining_case_ids'].pop(),
    lambda p:p.update(completed_cases=5),
])
def test_invalid_pause_or_duplicate_cannot_authorize_reuse(change):
    parent,pause=fixture();change(pause)
    with pytest.raises(ValueError):resume.partition(parent,pause)


def test_model_forward_reconstruction_and_scoring_body_unchanged():
    root=Path(__file__).resolve().parents[1]
    old=(root/'scripts/diagnostics/run_stunet_margin_mac_20261110.py').read_text()
    new=(root/'scripts/diagnostics/resume_stunet_margin_mac_20261110.py').read_text()
    def body(s):
        return s[s.index('        before = time.monotonic(); case = load_case'):s.index('        if len(rows) ==')]
    assert body(new).replace('; fresh_tiles_done += 1','')==body(old)


def test_pause_aware_budget_requires_approval_and_never_resets_total(tmp_path,monkeypatch):
    import json
    def save(name,value):
        p=tmp_path/name;p.write_text(json.dumps(value));return p
    save('budget-origin.json',dict(unix=100.,seconds=14400,deadline_unix=14500.))
    pause=save('pause.json',dict(observed_unix=2100.))
    origin=save('resume.json',dict(unix=10000.))
    approval=save('approval.json',dict(approved=True,cumulative_active_seconds=14400,deadline_unix=99999.))
    monkeypatch.setattr(resume,'BASE',tmp_path);monkeypatch.setattr(resume,'PAUSE_RECEIPT',pause)
    monkeypatch.setattr(resume,'RESUME_ORIGIN',origin);monkeypatch.setattr(resume,'APPROVAL',approval)
    monkeypatch.setattr(resume.time,'time',lambda:11000.)
    b=resume.budget()
    assert b['deadline_unix']==22400.
    assert b['remaining_seconds']==11400.
    assert b['prior_charged_seconds']==2000.
    approval.write_text(json.dumps(dict(approved=False,cumulative_active_seconds=14400,deadline_unix=99999.)))
    with pytest.raises(ValueError,match='approval'):resume.budget()


def test_corrupt_reused_native_backup_is_rejected(tmp_path,monkeypatch):
    import json
    import shutil
    parent,pause=fixture();parent['policies']={'raw':{}};pause['completed_tiles']=4
    primary=tmp_path/'primary';backup=tmp_path/'backup';primary.mkdir();backup.mkdir()
    monkeypatch.setattr(resume,'PARENT_OUT',primary);monkeypatch.setattr(resume,'PARENT_BACKUP',backup)
    for name in pause['reusable_case_ids']:
        code=primary/(name+'.npz');code.write_bytes(b'synthetic-not-clinical')
        other=backup/code.name;shutil.copyfile(code,other)
        row=dict(case_id=name,gaps=0,independent_policy_replay=True,policies={'raw':{}},tiles=1,
                 artifact=dict(path=str(code),backup=str(other),sha256=resume.sha(code)))
        path=primary/(name+'.json');path.write_text(json.dumps(row));shutil.copyfile(path,backup/path.name)
    rows,new=resume.reused_rows(parent,pause)
    assert len(rows)==4 and len(new)==66
    (backup/'0.npz').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='native-code'):resume.reused_rows(parent,pause)
