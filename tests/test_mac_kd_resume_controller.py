"""Invented controller evidence only; no GPU or live run mutation."""
import json
from types import SimpleNamespace
import contextlib
import pytest
from scripts import resume_mac_kd_comparison as m
from scripts.diagnostics.pause_mac_kd_comparison import request
from src.operations import mac_kd_resume_controller_v1 as rules
from src.data.segmenter_teacher_cache_v1 import sha


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


def test_pause_is_bound_idempotent_and_not_cleanup(tmp_path):
    put(tmp_path/'ready.json',{'version':'mac-kd-continuation-launch-1'})
    pin=sha(tmp_path/'ready.json')
    assert request(tmp_path,pin)['cleanup_verified'] is False
    assert request(tmp_path,pin)['requested']
    assert m.pause_requested(tmp_path,pin)
    with pytest.raises(ValueError):m.pause_requested(tmp_path,'wrong')


def test_legacy_pause_rejected(tmp_path):
    put(tmp_path/'ready.json',{'version':'mac-matched-kd-launch-1'})
    with pytest.raises(ValueError,match='Original launcher'):request(tmp_path,sha(tmp_path/'ready.json'))
    assert not (tmp_path/'pause-request.json').exists()


@pytest.mark.parametrize('returncode,stdout,stderr',[(0,' pid = 123\n',''),(1,'','permission denied')])
def test_parent_unknown_or_live_rejected(tmp_path,monkeypatch,returncode,stdout,stderr):
    put(tmp_path/'dispatch.json',{'target':'gui/501/invented'})
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=returncode,stdout=stdout,stderr=stderr))
    with pytest.raises(ValueError):m.stopped(tmp_path)


def test_lineage_charges_parent_and_rejects_unreaped(tmp_path,monkeypatch):
    root=tmp_path/'original';backup=tmp_path/'backup'
    put(root/'ready.json',dict(version='mac-matched-kd-launch-1',order=['control','treatment'],pins={},backup=str(backup),limits={'seconds_per_arm':100}))
    pin=sha(root/'ready.json')
    put(root/'control/process.json',{})
    put(root/'control/dispatch.json',dict(receipt_sha256=pin,run_id='parent'))
    put(root/'control/resources.json',dict(seconds=10.1,workers_reaped=True))
    put(root/'control/execution/history.jsonl',{})
    monkeypatch.setattr(rules,'inspect_checkpoint',lambda *a:dict(step=500))
    plan=rules.plans(root,pin,root,pin,'control','last.pt')
    assert plan['budget']['remaining_seconds']==89
    assert plan['segments']['control'][0]['run_id']=='parent'
    put(root/'control/resources.json',dict(seconds=10.1,workers_reaped=False))
    with pytest.raises(ValueError,match='Reaped'):rules.plans(root,pin,root,pin,'control','last.pt')
    with pytest.raises(ValueError,match='completed control'):rules.plans(root,pin,root,pin,'treatment','last.pt')


@pytest.mark.parametrize('outcome',['failed','paused','completed'])
def test_launch_successor_and_tracking_rules(tmp_path,monkeypatch,outcome):
    import mlflow
    from src.operations import full_training_platform,mac_teacher_supervision_v2
    calls=[]
    class Client:
        def __init__(self,**kw):pass
        def create_experiment(self,*a,**k):return 'experiment'
        def create_run(self,*a,**k):
            calls.append(k['tags']['arm']);return SimpleNamespace(info=SimpleNamespace(run_id='segment'))
        def log_dict(self,*a):pass
        def set_tag(self,*a):pass
        def set_terminated(self,rid,status):calls.append(status)
    r=dict(original_sha256='original',parent=str(tmp_path/'parent'),backup=str(tmp_path/'backup'),output=str(tmp_path),
           order=['control','treatment'],segments={'control':[{'run_id':'old'}],'treatment':[]},budget={'remaining_seconds':89},
           scientific={'scope':'invented','order':['control','treatment'],'designs':[{},{}]})
    monkeypatch.setattr(mlflow,'MlflowClient',Client)
    monkeypatch.setattr(m,'check',lambda *a:r)
    monkeypatch.setattr(m,'stopped',lambda *a:None)
    monkeypatch.setattr(m,'safety',lambda *a:None)
    monkeypatch.setattr(m,'completed',lambda *a:{})
    monkeypatch.setattr(m.original,'preserve',lambda *a:None)
    monkeypatch.setattr(full_training_platform,'training_guard',lambda *a:contextlib.nullcontext())
    q=tmp_path/'qualification.json';put(q,dict(version='mac-kd-continuation-gpu-1',success=True,workers_reaped=True,continuation_sha256='pin',evidence={}))
    def run(command,dest,**kw):
        assert kw['seconds']==(89 if dest.name=='control' else m.original.LIMITS['seconds_per_arm'])
        put(dest/'resources.json',dict(success=outcome!='failed',workers_reaped=True,exit_code=0 if outcome!='failed' else 1))
        put(dest/'result.json',dict(status=outcome,completed=outcome=='completed',completed_updates=24000 if outcome=='completed' else 500))
        (dest/'execution').mkdir()
        return outcome!='failed'
    monkeypatch.setattr(mac_teacher_supervision_v2,'run',run)
    if outcome=='failed':
        with pytest.raises(ValueError,match='no successor'):m.launch(tmp_path,'pin',q,sha(q))
        assert calls==['control','FAILED']
    else:
        m.launch(tmp_path,'pin',q,sha(q))
        assert calls==(['control','KILLED'] if outcome=='paused' else ['control','FINISHED','treatment','FINISHED'])
    with pytest.raises(FileExistsError):m.launch(tmp_path,'pin',q,sha(q))


def test_original_completion_uses_legacy_journal_not_new_result_field(tmp_path):
    root=tmp_path/'run';backup=tmp_path/'backup'
    put(root/'control/result.json',{'completed_updates':24000})
    put(root/'control/resources.json',dict(success=True,workers_reaped=True,exit_code=0))
    put(root/'control/complete.json',{'success':True})
    event=dict(event='completed',step=24000)
    put(root/'control/execution/history.jsonl',event)
    put(backup/'control/history.jsonl',event)
    assert rules.completed(root,backup,'control')
    put(root/'control/execution/history.jsonl',dict(event='paused',step=24000))
    with pytest.raises(ValueError,match='journal'):rules.completed(root,backup,'control')
