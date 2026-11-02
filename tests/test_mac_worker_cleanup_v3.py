import subprocess
import sys
import pytest
from src.operations import mac_worker_cleanup_v3 as cleanup
from src.operations.mac_teacher_watch_v3 import watch


def row(pid, born='original', parent=1, group=10, state='S'):
    return dict(pid=pid, born=born, parent=parent, group=group, state=state, rss_bytes=100)


def test_recycled_pid_is_not_owned_or_counted():
    known={(10,'original'),(11,'old-child')}
    rows={11:row(11,'new-unrelated'),12:row(12,parent=11)}
    assert cleanup.observe(rows,10,known)==0
    assert cleanup.survivors(rows,known)==[]


def test_reparented_owned_child_remains_tracked():
    known={(10,'original')}
    rows={10:row(10),11:row(11,parent=10)}
    assert cleanup.observe(rows,10,known)==200
    assert cleanup.survivors({11:row(11)},known)==[row(11)]


def test_zombie_is_not_claimed_reaped():
    assert cleanup.survivors({10:row(10,state='Z')},{(10,'original')})


class Process:
    pid=10
    def wait(self,timeout): return 0


def test_recycled_process_never_signalled(monkeypatch):
    monkeypatch.setattr(cleanup,'snapshot',lambda:{10:row(10,'reused')})
    monkeypatch.setattr(cleanup.os,'killpg',lambda *args:pytest.fail('unowned signal'))
    assert cleanup.cleanup(Process(),{(10,'original')})['workers_reaped']


def test_real_survivor_fails_with_identity(monkeypatch):
    monkeypatch.setattr(cleanup,'snapshot',lambda:{10:row(10)})
    monkeypatch.setattr(cleanup.os,'killpg',lambda *args:None)
    monkeypatch.setattr(cleanup.time,'sleep',lambda _:None)
    result=cleanup.cleanup(Process(),{(10,'original')})
    assert not result['workers_reaped']
    assert result['surviving_workers']==[row(10)]


def test_sample_failure_is_not_success(monkeypatch):
    def fail(): raise subprocess.TimeoutExpired('ps',5)
    monkeypatch.setattr(cleanup,'snapshot',fail)
    result=cleanup.cleanup(Process(),{(10,'original')})
    assert not result['workers_reaped'] and result['cleanup_error']


@pytest.mark.parametrize('seconds,rss,code,match',[
    (10,1024**3,'import time;time.sleep(.1)',None),
    (0,1024**3,'import time;time.sleep(10)','resource stop'),
    (10,1,'import time;time.sleep(10)','resource stop'),
    (10,1024**3,'raise SystemExit(3)','Duration worker failed'),
])
def test_real_worker_lifecycle(seconds,rss,code,match):
    p=subprocess.Popen([sys.executable,'-c',code],start_new_session=True)
    if match:
        with pytest.raises(ValueError,match=match):watch(p,seconds=seconds,rss_bytes=rss)
    else:
        watch(p,seconds=seconds,rss_bytes=rss)
    assert p.poll() is not None
    assert p.duration_resources['workers_reaped']


def test_real_parent_reaps_child():
    code='import subprocess,sys; p=subprocess.Popen([sys.executable,"-c","pass"]); p.wait()'
    p=subprocess.Popen([sys.executable,'-c',code],start_new_session=True)
    watch(p,seconds=10,rss_bytes=1024**3)
    assert p.duration_resources['workers_reaped']


def test_v3_supervisor_lifecycle(tmp_path):
    import json
    from src.operations.mac_teacher_supervision_v3 import run
    assert run([sys.executable,'-c','import time;time.sleep(.1)'],tmp_path,
               seconds=10,rss_bytes=1024**3)
    result=json.loads((tmp_path/'resources.json').read_text())
    assert result['success'] and result['workers_reaped']
    assert result['surviving_workers']==[] and result['cleanup_error'] is None


def test_transient_sampling_timeout(monkeypatch):
    from src.operations import mac_teacher_watch_v3 as module
    actual=module.snapshot
    calls=[]
    def sample():
        calls.append(1)
        if len(calls)==2:raise subprocess.TimeoutExpired('ps',5)
        return actual()
    monkeypatch.setattr(module,'snapshot',sample)
    p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(.2)'],start_new_session=True)
    module.watch(p,seconds=10,rss_bytes=1024**3)
    assert p.duration_resources['process_sample_timeouts']==1
    assert p.duration_resources['workers_reaped']


def test_repeated_sampling_timeout(monkeypatch):
    from src.operations import mac_teacher_watch_v3 as module
    actual=module.snapshot
    calls=[]
    def sample():
        calls.append(1)
        if len(calls)>1:raise subprocess.TimeoutExpired('ps',5)
        return actual()
    monkeypatch.setattr(module,'snapshot',sample)
    p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True)
    with pytest.raises(ValueError,match='three samples'):
        module.watch(p,seconds=10,rss_bytes=1024**3)
    assert p.duration_resources['process_sample_timeouts']==3
    assert p.duration_resources['workers_reaped']


def test_parent_loss_guardian_stops_worker(tmp_path):
    import json
    import os
    import signal
    import time
    code=('from src.operations.mac_teacher_supervision_v3 import run; import sys; '
          'run([sys.executable,"-c","import time;time.sleep(60)"],sys.argv[1],seconds=90,rss_bytes=1024**3)')
    supervisor=subprocess.Popen([sys.executable,'-c',code,str(tmp_path)])
    worker_pid=None
    try:
        deadline=time.monotonic()+10
        while not (tmp_path/'guardian-ready.json').exists():
            assert supervisor.poll() is None and time.monotonic()<deadline
            time.sleep(.05)
        worker_pid=json.loads((tmp_path/'process.json').read_text())['worker']
        supervisor.kill();supervisor.wait(timeout=5)
        while not (tmp_path/'guardian-failure.json').exists():
            assert time.monotonic()<deadline
            time.sleep(.05)
        evidence=json.loads((tmp_path/'guardian-failure.json').read_text())
        assert evidence['supervisor_lost'] and not evidence['success']
        rows=cleanup.snapshot()
        assert worker_pid not in rows or rows[worker_pid]['state'].startswith('Z')
    finally:
        if supervisor.poll() is None:supervisor.kill();supervisor.wait(timeout=5)
        if worker_pid:
            try:os.killpg(worker_pid,signal.SIGKILL)
            except ProcessLookupError:pass
