import json
from pathlib import Path
import subprocess
import pytest
from scripts.retrieval import prepare_local_expert as expert


def test_gpu_lock_is_respected(tmp_path, monkeypatch):
    import fcntl
    monkeypatch.setattr(expert, 'LOCK', tmp_path/'gpu.lock')
    assert not expert.gpu_busy()
    with expert.LOCK.open('a+b') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert expert.gpu_busy()
    assert not expert.gpu_busy()


def setup(monkeypatch, tmp_path, *, busy=True, bad_mount=False, stale=False):
    c = {'mount': str(tmp_path), 'volume_uuid': 'fixed-uuid', 'data': '/expected'}
    p=tmp_path/'config.json';p.write_text(json.dumps(c))
    monkeypatch.setattr(expert, 'CONFIG', p)
    monkeypatch.setattr(Path, 'is_mount', lambda self: True)
    monkeypatch.setattr(expert, 'read_config', lambda p: c)
    monkeypatch.setattr(expert, 'limits', lambda c: None)
    monkeypatch.setattr(expert, 'gpu_busy', lambda: busy)
    monkeypatch.setattr(expert, 'wait_for', lambda *a: None)
    monkeypatch.setattr(expert, 'listening', lambda port: True)
    monkeypatch.setattr(expert, 'status', lambda: {'gpu_busy': busy, 'search': True})
    calls=[]
    def command(args, timeout=20):
        calls.append(args)
        if 'info' in args: return b'{"MemTotal": 100}'
        if args[0]=='sysctl': return b'10000'
        if 'inspect' in args: return json.dumps([{'Mounts':[{'Source': '/wrong' if bad_mount else '/expected', 'Destination':'/var/lib/postgresql/data'}], 'State':{'Running':False}}]).encode()
        if 'start' in args and stale: raise subprocess.CalledProcessError(1,args,stderr=b'invalid mount config')
        return b'OK'
    monkeypatch.setattr(expert, 'command', command)
    monkeypatch.setattr(expert, 'start_process', lambda *a: pytest.fail('must not start model during teacher'))
    monkeypatch.setattr(expert, 'http', lambda *a, **kw: pytest.fail('must not load model during teacher'))
    return calls


def test_teacher_only_restores_sources(monkeypatch,tmp_path):
    calls=setup(monkeypatch,tmp_path)
    assert expert.prepare()=={'gpu_busy':True,'search':True}
    assert any('start' in a for a in calls)
    assert not any('stop' in a or 'restart' in a or 'rm' in a for a in calls)


def test_wrong_mount_never_started(monkeypatch,tmp_path):
    calls=setup(monkeypatch,tmp_path,bad_mount=True)
    with pytest.raises(RuntimeError,match='mount differs'): expert.prepare()
    assert not any('start' in a for a in calls)


def test_stale_docker_reports_action_without_restart(monkeypatch,tmp_path):
    calls=setup(monkeypatch,tmp_path,stale=True)
    with pytest.raises(RuntimeError,match='Restart Docker Desktop'):expert.prepare()
    assert not any('restart' in a for a in calls)


def test_model_warmup_uses_pinned_model_and_exclusive_lock(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path,busy=False)
    monkeypatch.setattr(expert,'LOCK',tmp_path/'gpu.lock')
    calls=[]
    def http(port,path,payload=None,**kw):
        calls.append((port,path,payload))
        if path=='api/tags': return {'models':[{'name':expert.MODEL,'digest':expert.MODEL_SHA}]}
        assert path=='api/generate'
        import fcntl
        with expert.LOCK.open('a+b') as f:
            with pytest.raises(BlockingIOError):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return {'done':True}
    monkeypatch.setattr(expert,'http',http)
    expert.prepare()
    assert calls[-1][2] == {'model':expert.MODEL,'stream':False,'keep_alive':'10m'}


def test_missing_model_never_downloaded(monkeypatch,tmp_path):
    calls=setup(monkeypatch,tmp_path,busy=False)
    monkeypatch.setattr(expert,'LOCK',tmp_path/'gpu.lock')
    monkeypatch.setattr(expert,'http',lambda *a,**k:{'models':[]})
    with pytest.raises(RuntimeError,match='No model was downloaded'):expert.prepare()
    assert not any('pull' in a for a in calls)
