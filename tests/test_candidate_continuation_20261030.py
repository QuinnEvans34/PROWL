import copy
import pytest
from scripts.diagnostics import continue_candidate_export_20261030 as run
from scripts.diagnostics import recover_candidate_export_20261030 as recovery

def membership():
    a=dict(rows=[dict(case_id=f'old{i}') for i in range(355)],remaining=[dict(case_id=f'new{i}',role='verifier_fit',reuse=False) for i in range(178)])
    r=dict(status='BYTE_IDENTICAL_CT_RESTORATION_ONLY',cases={c['case_id']:dict(role=c['role']) for c in a['remaining']})
    return a,r

def test_exact_partition():
    run.verify_membership(*membership())

@pytest.mark.parametrize('change',['missing','extra','overlap','role','reuse','status'])
def test_membership_fail_closed(change):
    a,r=membership()
    if change=='missing':r['cases'].pop('new0')
    if change=='extra':r['cases']['dev']=dict(role='verifier_fit')
    if change=='overlap':a['rows'][0]['case_id']='new0'
    if change=='role':r['cases']['new0']['role']='verifier_calibration'
    if change=='reuse':a['remaining'][0]['reuse']=True
    if change=='status':r['status']='incomplete'
    with pytest.raises(ValueError):run.verify_membership(a,r)

@pytest.mark.parametrize('marker',['output','backup','dispatch','log'])
def test_duplicate_admission_refused(tmp_path,monkeypatch,marker):
    setup=tmp_path/'setup';setup.mkdir()
    monkeypatch.setattr(run,'SETUP',setup);monkeypatch.setattr(run,'OUT',tmp_path/'output');monkeypatch.setattr(run,'BACKUP',tmp_path/'backup')
    path={'output':run.OUT,'backup':run.BACKUP,'dispatch':setup/'dispatch.json','log':setup/'worker.log'}[marker];path.touch()
    monkeypatch.setattr(run,'check',lambda *a:pytest.fail('Gate must reject before hashing or GPU'))
    with pytest.raises(ValueError,match='duplicate'):run.admission('hash')

def test_split_starts_at_failed_patient():
    old=[dict(case_id=f'old{i}',role='verifier_fit') for i in range(355)]
    new=[dict(case_id='PanTS_00005914',role='verifier_calibration')]+[dict(case_id=f'new{i}',role='verifier_fit') for i in range(177)]
    events=[dict(c,event='case_completed') for c in old]
    done,left=recovery.completion_split(dict(cases=old+new),events)
    assert len(done)==355 and len(left)==178 and left[0]['case_id']=='PanTS_00005914'
    with pytest.raises(ValueError):recovery.completion_split(dict(cases=old+new),events+[events[0]])

@pytest.mark.parametrize('event,expected',[('started',False),('failed','error'),('completed',True)])
def test_handoff_restoration_gate(tmp_path,monkeypatch,event,expected):
    import json
    from scripts.diagnostics import handoff_candidate_recovery_20261030 as handoff
    a,r=membership()
    (tmp_path/'progress.jsonl').write_text(json.dumps(dict(event=event))+'\n')
    (tmp_path/'restoration.json').write_text(json.dumps(r))
    (tmp_path/'audit.json').write_text(json.dumps(a))
    monkeypatch.setattr(handoff.restore,'OUT',tmp_path);monkeypatch.setattr(handoff.stage.recovery,'OUT',tmp_path)
    if expected=='error':
        with pytest.raises(ValueError):handoff.restored_gate()
    else:assert handoff.restored_gate() is expected

def test_handoff_wont_start_twice(tmp_path,monkeypatch):
    from scripts.diagnostics import handoff_candidate_recovery_20261030 as handoff
    monkeypatch.setattr(handoff.stage,'SETUP',tmp_path)
    (tmp_path/'handoff-started.json').touch()
    with pytest.raises(ValueError,match='already started'):handoff.main(-1)
