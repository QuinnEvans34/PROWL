"""Mac request/dispatch boundaries; no patient data or GPU use."""
import copy
import json
import sys
import pytest
from scripts.diagnostics import qualify_physical_cascade_mac_20261102 as launch
from tests.test_week05_physical_executor_20261102 import request as windows_request
from src.operations.mac_teacher_supervision_v3 import run


def request():
    r=windows_request()
    r.update(version='physical-cascade-mac-reference-1',limits=copy.deepcopy(launch.LIMITS),
             comparison=copy.deepcopy(launch.COMPARISON),output=str(launch.BASE/'output'),backup=str(launch.BACKUP))
    return r


@pytest.mark.parametrize('key,value',[('case_id','other'),('policy','largest_component_26'),
    ('limits',{}),('reference_path','label.nii.gz'),('models',{}),('units','unknown')])
def test_frozen_request(key,value):
    r=request();launch.validate_request(r);r[key]=value
    with pytest.raises(ValueError):launch.validate_request(r)


def test_duplicate_dispatch(tmp_path,monkeypatch):
    monkeypatch.setattr(launch,'BASE',tmp_path)
    monkeypatch.setattr(launch,'check_request',lambda p:request())
    (tmp_path/'worker.log').write_text('preserved')
    with pytest.raises(FileExistsError):launch.run('pin')


@pytest.mark.parametrize('mode',['normal','timeout','cancel'])
def test_owned_mac_cleanup(tmp_path,mode):
    def tick():
        if mode=='cancel':raise RuntimeError('operator cancellation')
    code='print("ok")' if mode=='normal' else 'import time; time.sleep(30)'
    ok=run([sys.executable,'-c',code],tmp_path,seconds=.5 if mode=='timeout' else 20,rss_bytes=1024**3,tick=tick)
    r=json.loads((tmp_path/'resources.json').read_text())
    assert ok == (mode=='normal')
    assert r['workers_reaped'] and not r['surviving_workers'] and not r['supervisor_cleanup_error']
