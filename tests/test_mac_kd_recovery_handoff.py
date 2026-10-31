import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.diagnostics import stop_original_mac_kd as stop
from scripts.diagnostics import qualify_mac_kd_continuation as q


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


def test_owner_mismatch_never_signals(tmp_path,monkeypatch):
    monkeypatch.setattr(stop,'audit',lambda *a:{})
    put(tmp_path/'dispatch.json',dict(target=f'gui/{stop.os.getuid()}/com.prowl.mac-kd-comparison-test'))
    put(tmp_path/'control/process.json',dict(supervisor=123,worker=456,worker_start='born'))
    monkeypatch.setattr(stop.subprocess,'check_output',lambda *a,**k:' pid = 999\n')
    monkeypatch.setattr(stop.subprocess,'run',lambda *a,**k:pytest.fail('No signal'))
    with pytest.raises(ValueError,match='Supervisor'):stop.stop(tmp_path,'pin','control','last.pt',tmp_path/'receipt')
    assert not (tmp_path/'receipt').exists()


def test_changed_owner_after_receipt_never_signals(tmp_path,monkeypatch):
    values=iter([dict(target='job',process={'worker':1}),dict(target='job',process={'worker':2})])
    monkeypatch.setattr(stop,'owner',lambda *a:next(values))
    monkeypatch.setattr(stop.subprocess,'run',lambda *a,**k:pytest.fail('No signal'))
    with pytest.raises(ValueError,match='Owner changed'):stop.stop(tmp_path,'pin','control','last.pt',tmp_path/'receipt')
    assert (tmp_path/'receipt/request.json').exists()


def test_stop_only_requests_verified_launchd_signal(tmp_path,monkeypatch):
    monkeypatch.setattr(stop,'owner',lambda *a:dict(target='verified-job',process={'worker':1}))
    calls=[];monkeypatch.setattr(stop.subprocess,'run',lambda command,**kw:calls.append(command))
    result=stop.stop(tmp_path,'pin','control','last.pt',tmp_path/'receipt')
    assert calls==[['launchctl','kill','SIGTERM','verified-job']]
    assert result['cleanup_verified'] is False


def test_stage_rejects_unreaped_or_cpu(tmp_path):
    for reaped,device in [(False,'mps'),(True,'cpu')]:
        p=tmp_path/str(reaped)
        put(p/'producer/result.json',dict(success=True,stage='producer',scientific_updates=0,engineering_updates=2,evidence={}))
        put(p/'producer/resources.json',dict(success=True,workers_reaped=reaped,exit_code=0))
        put(p/'producer/device.json',dict(device=device,fallback=False))
        with pytest.raises(ValueError,match='Actual GPU'):q.verify_stage(p,'producer','pin')


def test_engine_cold_restore_uses_independent_backup(tmp_path):
    import torch
    class Session:
        identity={'fixture':True}
        def __init__(self,value):self.value=value
        def state(self):return dict(value=self.value)
    def restore(state,identity):
        assert identity==Session.identity
        return Session(state['value'])
    def update(s):
        s.value+=1
        return dict(step=s.value,batch_sha256={'image':str(s.value)},member_id='invented',learning_rate=.1,kd_weight=0,teacher_accessed=False)
    def compare(a,b):assert a==b
    (tmp_path/'producer').mkdir();(tmp_path/'cold').mkdir()
    checkpoint=tmp_path/'original.pt';torch.save(dict(session={'value':10}),checkpoint)
    request={'backup':str(tmp_path/'backup')};context={'checkpoint':str(checkpoint),'identity':Session.identity}
    args=(request,context,restore,update,compare,lambda:None,lambda size:None)
    q.exercise(tmp_path,'producer',*args);q.exercise(tmp_path,'cold',*args)
    assert json.loads((tmp_path/'cold/updates.json').read_text())[0]['step']==12
    (tmp_path/'backup/saved.pt').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='backup changed'):q.exercise(tmp_path,'cold',*args)


def test_bare_success_receipt_does_not_authorize_launch(tmp_path):
    from src.data.segmenter_teacher_cache_v1 import sha
    proof=tmp_path/'qualified.json'
    put(proof,dict(version='mac-kd-continuation-gpu-1',success=True,workers_reaped=True,
                   continuation_sha256='pin',scientific_updates=0,evidence={}))
    with pytest.raises(ValueError,match='request required'):q.validate_qualification(proof,sha(proof),'pin')
