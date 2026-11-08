import importlib.util,sys,types
from pathlib import Path


def load(monkeypatch):
    fake=types.SimpleNamespace(experiment=lambda *args:None,dashboard=lambda:None)
    monkeypatch.setitem(sys.modules,'experiments_legacy_20261108',fake)
    spec=importlib.util.spec_from_file_location('stunet_dashboard',Path(__file__).parents[1]/'scripts/monitoring/stunet_dashboard_20261108.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_new_updates_and_hours_not_double_counted(monkeypatch):
    m=load(monkeypatch);row=dict(step=14000,dice=.4)
    r=dict(steps=14001,target_steps=24000,seconds=1234,next_validation=16000,latest=row,best=row,history=[row],native=[row])
    out=m.adjust_continuation(r,12000)
    assert out['steps']==2001 and out['target_steps']==12000 and out['global_steps']==14001
    assert out['seconds']==1234 and out['next_validation']==4000
    assert out['history'][0]['step']==2000 and out['history'][0]['global_step']==14000
    assert r['history'][0]['step']==14000


def test_before_first_update_and_legacy(monkeypatch):
    m=load(monkeypatch)
    r=dict(steps=0,target_steps=24000,seconds=10,next_validation=2000,history=[],native=[])
    out=m.adjust_continuation(r,12000)
    assert out['steps']==0 and out['global_steps']==12000 and out['seconds']==10
    assert m.adjust_continuation(r,0) is r
