import json
from contextlib import nullcontext
from pathlib import Path
import pytest
from src.operations import verifier_candidate_archive_v1 as a

def test_caps_and_reservations():
    values=dict(used_e=0,used_c=0,free_e=200*1024**3,free_c=200*1024**3)
    a.check_capacity(**values)
    for change in [dict(used_e=64*1024**3+1),dict(used_c=40*1024**3+1),dict(free_e=100*1024**3-1),dict(free_c=100*1024**3-1),dict(reserve_e=-1),dict(reserve_c=-1),dict(reserve_e=101*1024**3),dict(reserve_c=101*1024**3)]:
        with pytest.raises(ValueError):a.check_capacity(**(values|change))

def test_copy_success_duplicate_and_independence(tmp_path):
    source=tmp_path/'source';source.write_bytes(b'bound source')
    dest=tmp_path/'copy';reserves=[]
    with pytest.raises(ValueError):a.backup_file(source,dest)
    pin=a.backup_file(source,dest,independent=False,reserve=reserves.append)
    assert dest.read_bytes()==source.read_bytes() and pin==a.sha256(source) and reserves==[12]
    with pytest.raises(ValueError):a.backup_file(source,dest,independent=False)

def test_copy_failure_preserves_partial(tmp_path,monkeypatch):
    source=tmp_path/'source';source.write_bytes(b'a');dest=tmp_path/'copy'
    real=a.sha256
    monkeypatch.setattr(a,'sha256',lambda p:'bad' if str(p).endswith('.partial') else real(p))
    with pytest.raises(ValueError):a.backup_file(source,dest,independent=False)
    assert not dest.exists() and dest.with_suffix('.partial').exists()

def test_copy_capacity_fails_before_write(tmp_path):
    source=tmp_path/'source';source.write_bytes(b'a');dest=tmp_path/'copy'
    def fail(n):raise ValueError('cap')
    with pytest.raises(ValueError):a.backup_file(source,dest,independent=False,reserve=fail)
    assert not dest.exists() and not dest.with_suffix('.partial').exists()

def fixtures(tmp_path):
    cases=[dict(case_id='a',role='verifier_fit',reuse=True),dict(case_id='b',role='verifier_calibration',reuse=False)]
    calls=[]
    def produce(c):
        calls.append(('produce',c['case_id']))
        p=tmp_path/(c['case_id']+'.npz');p.write_bytes(c['case_id'].encode())
        return dict(case_id=c['case_id'],role=c['role'],prediction_sha256=a.sha256(p)),p
    def reuse(c):
        result=produce(c);calls[-1]=('reuse',c['case_id']);return result
    def backup(p):calls.append(('backup',p.name));return a.sha256(p)
    def record(row):
        p=tmp_path/(row['case_id']+'.json');a.write_json(p,row);return p
    return cases,calls,dict(produce=produce,reuse=reuse,backup=backup,record=record,journal=tmp_path/'progress.jsonl',tick=lambda:None)

def test_orchestration_success_and_reuse(tmp_path):
    cases,calls,kw=fixtures(tmp_path);rows=a.process_cases(cases,**kw)
    assert len(rows)==2 and ('reuse','a') in calls and ('produce','a') not in calls
    events=[json.loads(l) for l in kw['journal'].read_text().splitlines()]
    assert [e['event'] for e in events]==['case_started','case_completed']*2
    assert events[-1]['completed']==2

def test_failed_backup_never_counts_completed(tmp_path):
    cases,calls,kw=fixtures(tmp_path)
    def fail(p):raise OSError('backup disk error')
    kw['backup']=fail
    with pytest.raises(OSError):a.process_cases(cases,**kw)
    events=[json.loads(l) for l in kw['journal'].read_text().splitlines()]
    assert [e['event'] for e in events]==['case_started'] and not (tmp_path/'a.json').exists()

def test_duplicate_schedule_refused(tmp_path):
    cases,calls,kw=fixtures(tmp_path)
    with pytest.raises(ValueError):a.process_cases(cases+cases,**kw)
    assert not kw['journal'].exists()

def test_wrong_identity_refused(tmp_path):
    cases,calls,kw=fixtures(tmp_path)
    kw['reuse']=lambda c:(dict(case_id='wrong',role=c['role']),tmp_path/'x')
    with pytest.raises(ValueError):a.process_cases(cases,**kw)

def test_admission_refuses_existing_outputs(tmp_path,monkeypatch):
    from scripts.diagnostics import export_verifier_candidates_20261027 as full
    monkeypatch.setattr(full,'OUT',tmp_path/'out');monkeypatch.setattr(full,'BACKUP',tmp_path/'backup');monkeypatch.setattr(full,'SETUP',tmp_path/'setup')
    full.OUT.mkdir()
    with pytest.raises(ValueError,match='duplicate'):full.admission('unused')

def test_receipt_hash_refused(tmp_path,monkeypatch):
    from scripts.diagnostics import export_verifier_candidates_20261027 as full
    monkeypatch.setattr(full,'SETUP',tmp_path);(tmp_path/'request.json').write_text('{}')
    with pytest.raises(ValueError,match='hash'):full.check('0'*64)

@pytest.mark.parametrize('success',[True,False])
def test_supervisor_limits_and_failure(tmp_path,monkeypatch,success):
    from scripts.diagnostics import export_verifier_candidates_20261027 as full
    monkeypatch.setattr(full,'SETUP',tmp_path)
    monkeypatch.setattr(full,'admission',lambda pin:dict(seconds=57600,rss_bytes=12*1024**3))
    monkeypatch.setattr(full,'training_guard',lambda p:nullcontext())
    class Process:
        returncode=0 if success else 1
        duration_resources=dict(workers_reaped=True)
    monkeypatch.setattr(full.subprocess,'Popen',lambda *args,**kwargs:Process())
    def watch(p,**kw):
        assert kw['seconds']==57600 and kw['rss_bytes']==12*1024**3
        if not success:raise RuntimeError('worker failed')
    monkeypatch.setattr(full,'watch_windows',watch)
    if success:full.run('pin')
    else:
        with pytest.raises(RuntimeError):full.run('pin')
    r=json.loads((tmp_path/'resources.json').read_text());assert r['success']==success and r['workers_reaped']
    assert (tmp_path/'dispatch.json').exists()
