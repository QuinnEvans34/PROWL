"""Launch/backup gates with invented files; no clinical data or GPU."""
import json
from pathlib import Path
import pytest
from scripts import train_mac_kd_comparison as m


def test_backup_rotates_only_after_verified_copy(tmp_path, monkeypatch):
    monkeypatch.setattr(m,'safety',lambda r:None)
    monkeypatch.setattr(m,'storage_preflight',lambda:dict(internal_free_bytes=10**12,external_free_bytes=10**12,existing_backup_bytes=0))
    backup=tmp_path/'backup';backup.mkdir();source=tmp_path/'last.pt'
    r={'backup':str(backup)}
    source.write_bytes(b'first');m.preserve(source,backup,r)
    source.write_bytes(b'second');m.preserve(source,backup,r)
    assert (backup/'last.pt').read_bytes()==b'second'
    assert (backup/'previous-last.pt').read_bytes()==b'first'
    source.write_bytes(b'third')
    monkeypatch.setattr(m.shutil,'copyfileobj',lambda *args: (_ for _ in ()).throw(OSError('injected I/O failure')))
    with pytest.raises(OSError):m.preserve(source,backup,r)
    assert (backup/'last.pt').read_bytes()==b'second'
    assert (backup/'previous-last.pt').read_bytes()==b'first'
    assert (backup/'last.pt.partial').exists()


def test_backup_corruption_preserves_previous(tmp_path, monkeypatch):
    monkeypatch.setattr(m,'safety',lambda r:None)
    monkeypatch.setattr(m,'storage_preflight',lambda:dict(internal_free_bytes=10**12,external_free_bytes=10**12,existing_backup_bytes=0))
    backup=tmp_path/'backup';backup.mkdir();(backup/'last.pt').write_bytes(b'old')
    source=tmp_path/'last.pt';source.write_bytes(b'new')
    monkeypatch.setattr(m.shutil,'copyfileobj',lambda a,b:b.write(b'corrupt'))
    with pytest.raises(ValueError,match='hash mismatch'):m.preserve(source,backup,{'backup':str(backup)})
    assert (backup/'last.pt').read_bytes()==b'old'


def test_qualification_rejects_cold_parent_change(tmp_path,monkeypatch):
    monkeypatch.setattr(m,'validate_request',lambda *a:({},{}))
    monkeypatch.setattr(m,'prerequisites',lambda *a:{'producer':'correct'})
    p=tmp_path/'cold';p.mkdir()
    (p/'receipt.json').write_text(json.dumps(dict(success=True,stage='cold',request_sha256='pin',parents={'producer':'wrong'})))
    with pytest.raises(ValueError,match='cold recovery'):m.qualified(tmp_path,'pin')


def test_scientific_failure_never_starts_treatment(tmp_path,monkeypatch):
    import mlflow
    import contextlib
    from src.operations import full_training_platform, mac_teacher_supervision_v2
    calls=[]
    class Client:
        def __init__(self,**kw): pass
        def create_experiment(self,*a,**kw): return 'experiment'
        def create_run(self,*a,**kw):
            calls.append(kw['tags']['arm'])
            from types import SimpleNamespace
            return SimpleNamespace(info=SimpleNamespace(run_id='run'))
        def log_dict(self,*a): pass
        def set_terminated(self,*a): calls.append(a[-1])
    monkeypatch.setattr(mlflow,'MlflowClient',Client)
    monkeypatch.setattr(full_training_platform,'training_guard',lambda *a:contextlib.nullcontext())
    monkeypatch.setattr(m,'check',lambda *a:dict(order=['control','treatment'],scope='invented',designs=[{},{}]))
    def fail(command,dest,**kw):
        (dest/'resources.json').write_text(json.dumps(dict(success=False,workers_reaped=True,exit_code=1)))
        return False
    monkeypatch.setattr(mac_teacher_supervision_v2,'run',fail)
    with pytest.raises(ValueError,match='Arm failed'):m.launch(tmp_path,'pin')
    assert calls==['control','FAILED']
    assert not (tmp_path/'treatment').exists()
    with pytest.raises(FileExistsError):m.launch(tmp_path,'pin')
    assert calls==['control','FAILED']


def test_successful_pair_runs_in_order_with_distinct_records(tmp_path,monkeypatch):
    import mlflow
    import contextlib
    from types import SimpleNamespace
    from src.operations import full_training_platform, mac_teacher_supervision_v2
    calls=[];recipes=[]
    class Client:
        def __init__(self,**kw): pass
        def create_experiment(self,*a,**kw): return 'experiment'
        def create_run(self,*a,**kw):
            arm=kw['tags']['arm'];calls.append(arm)
            return SimpleNamespace(info=SimpleNamespace(run_id=arm+'-run'))
        def log_dict(self,rid,recipe,name): recipes.append((rid,recipe))
        def set_terminated(self,rid,state):calls.append(state)
    monkeypatch.setattr(mlflow,'MlflowClient',Client)
    monkeypatch.setattr(full_training_platform,'training_guard',lambda *a:contextlib.nullcontext())
    r=dict(order=['control','treatment'],scope='invented',designs=[{'kd':0},{'kd':.1}],backup=str(tmp_path/'backups'))
    monkeypatch.setattr(m,'check',lambda *a:r)
    monkeypatch.setattr(m,'preserve',lambda *a:None)
    def success(command,dest,**kw):
        assert kw['seconds']==96*3600
        (dest/'resources.json').write_text(json.dumps(dict(success=True,workers_reaped=True,exit_code=0)))
        (dest/'result.json').write_text(json.dumps(dict(completed_updates=24000)))
        (dest/'execution').mkdir()
        return True
    monkeypatch.setattr(mac_teacher_supervision_v2,'run',success)
    m.launch(tmp_path,'pin')
    assert calls==['control','FINISHED','treatment','FINISHED']
    assert recipes==[('control-run',{'kd':0}),('treatment-run',{'kd':.1})]
    assert json.loads((tmp_path/'complete.json').read_text())['success']
