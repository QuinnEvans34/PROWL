import os
import subprocess
import sys
import pytest
from src.operations import mac_teacher_watch_v2 as watch
from src.operations.mac_teacher_supervision_v2 import run


def worker(): return subprocess.Popen([sys.executable,'-c','import time; time.sleep(0.3)'],start_new_session=True)


def test_transient_timeout_recovers(monkeypatch):
    actual=watch.owned_tree;calls=[]
    def sample(pid):
        calls.append(pid)
        if len(calls)==1:raise subprocess.TimeoutExpired('synthetic ps',5)
        return actual(pid)
    monkeypatch.setattr(watch,'owned_tree',sample)
    p=worker();watch.watch(p,seconds=10,rss_bytes=1024**3)
    assert p.returncode==0 and p.duration_resources['process_sample_timeouts']==1
    assert p.duration_resources['workers_reaped']


def test_repeated_timeout_stops_and_reaps(monkeypatch):
    def sample(pid):raise subprocess.TimeoutExpired('synthetic ps',5)
    monkeypatch.setattr(watch,'owned_tree',sample)
    p=worker()
    with pytest.raises(ValueError,match='three samples'):watch.watch(p,seconds=10,rss_bytes=1024**3)
    assert p.poll() is not None and p.duration_resources['workers_reaped']
    assert p.duration_resources['process_sample_timeouts']==3


@pytest.mark.parametrize('seconds,rss',[(0,1024**3),(10,1)])
def test_resource_limits_preserved(seconds,rss):
    p=worker()
    with pytest.raises(ValueError,match='resource stop'):watch.watch(p,seconds=seconds,rss_bytes=rss)
    assert p.duration_resources['workers_reaped']


def test_actual_supervisor_guardian_lifecycle(tmp_path):
    assert run([sys.executable,'-c','import time;time.sleep(0.3)'],tmp_path,seconds=10,rss_bytes=1024**3)
    import json
    result=json.loads((tmp_path/'resources.json').read_text())
    assert result['success'] and result['workers_reaped']


def test_monitor_continuation_charges_prior_time_and_rejects_other_failures(tmp_path):
    import json
    from src.data.segmenter_teacher_cache_v1 import sha
    from src.operations.mac_teacher_monitor_continuation_v1 import remaining_after_monitor_stop
    (tmp_path/'request.json').write_text(json.dumps({'limits':{'seconds':100}}))
    resources={'success':False,'workers_reaped':True,'exit_code':-15,'seconds':10.2,'error':"TimeoutExpired(['/bin/ps', '-axo', 'pid=,ppid=,rss='], 5)"}
    (tmp_path/'resources.json').write_text(json.dumps(resources));(tmp_path/'worker.log').write_text('retained')
    def review():
        value={'stopped':True,'reason':'process sample timeout','pause_receipt':False}
        for key,name in [('request_sha256','request.json'),('resources_sha256','resources.json'),('worker_log_sha256','worker.log')]:value[key]=sha(tmp_path/name)
        path=tmp_path/'review.json';path.write_text(json.dumps(value));return path
    assert remaining_after_monitor_stop(tmp_path,review())==89
    resources['error']='unknown failure';(tmp_path/'resources.json').write_text(json.dumps(resources))
    with pytest.raises(ValueError,match='reviewed'):remaining_after_monitor_stop(tmp_path,review())
