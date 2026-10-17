"""Model-free checks of storage admission and runtime stop boundaries."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('pgplatform', Path(__file__).resolve().parents[1] / 'scripts/retrieval/check_pgvector_platform.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def config(tmp_path):
    return dict(mount=str(tmp_path), data=str(tmp_path/'db'), volume_uuid='ABC',
                password_file='/private/password', port=55432)


def test_valid_config(tmp_path):
    p.validate_config(config(tmp_path))


@pytest.mark.parametrize('field,value', [('data','/outside/db'),('data','relative'),('port',True),('port',543),('port',65536)])
def test_invalid_config(tmp_path, field, value):
    c = config(tmp_path); c[field] = value
    with pytest.raises(ValueError): p.validate_config(c)


def test_symlink_escape(tmp_path):
    (tmp_path/'link').symlink_to('/tmp')
    c = config(tmp_path); c['data'] = str(tmp_path/'link'/'db')
    with pytest.raises(ValueError): p.validate_config(c)


@pytest.mark.parametrize('change', ['uuid','mount','unmounted','internal','external','port'])
def test_admission_refusals(tmp_path, change):
    c = config(tmp_path)
    v = dict(VolumeUUID='ABC', MountPoint=str(tmp_path), Mounted=True)
    i, e, free = 104*p.GIB,408*p.GIB,True
    if change == 'uuid': v['VolumeUUID']='WRONG'
    if change == 'mount': v['MountPoint']='/elsewhere'
    if change == 'unmounted': v['Mounted']=False
    if change == 'internal': i-=1
    if change == 'external': e-=1
    if change == 'port': free=False
    assert p.check_observation(c,v,i,e,free)


def test_admission_exact_boundary(tmp_path):
    c=config(tmp_path)
    assert not p.check_observation(c,dict(VolumeUUID='abc',MountPoint=str(tmp_path),Mounted=True),104*p.GIB,408*p.GIB,True)


@pytest.mark.parametrize('args', [(1800,101,401,0),(0,99,401,0),(0,101,399,0),(0,101,401,8)])
def test_runtime_stop(args):
    seconds,i,e,d=args
    assert p.runtime_reason(seconds,i*p.GIB,e*p.GIB,d*p.GIB)


def test_runtime_below_ceiling():
    assert p.runtime_reason(1799,100*p.GIB,400*p.GIB,8*p.GIB-1) is None


def test_native_diskutil_without_mounted_key(tmp_path):
    c=config(tmp_path)
    assert not p.check_observation(c,dict(VolumeUUID='ABC',MountPoint=str(tmp_path)),104*p.GIB,408*p.GIB,True)


def test_blocked_preflight_prevents_run(tmp_path, monkeypatch):
    monkeypatch.setattr(p,'preflight',lambda c: {'ready':False,'errors':['space']})
    monkeypatch.setattr(p,'command',lambda *a,**k: pytest.fail('must not launch'))
    with pytest.raises(ValueError): p.run_owned(config(tmp_path),tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_existing_data_preserved(tmp_path, monkeypatch):
    c=config(tmp_path)
    d=tmp_path/'db'; d.mkdir(); (d/'retained').write_text('keep')
    monkeypatch.setattr(p,'preflight',lambda c: {'ready':True})
    monkeypatch.setattr(p,'command',lambda *a,**k: pytest.fail('must not launch'))
    with pytest.raises(ValueError): p.run_owned(c,tmp_path/'out')
    assert (d/'retained').read_text() == 'keep'


def test_public_password_refused(tmp_path, monkeypatch):
    c=config(tmp_path); (tmp_path/'db').mkdir()
    secret=tmp_path/'secret'; secret.write_text('a'*32); secret.chmod(0o644)
    c['password_file']=str(secret)
    monkeypatch.setattr(p,'preflight',lambda c: {'ready':True})
    monkeypatch.setattr(p,'command',lambda *a,**k: pytest.fail('must not launch'))
    with pytest.raises(ValueError): p.run_owned(c,tmp_path/'out')


@pytest.mark.parametrize('running,exit_code,confirmed', [(b'',0,True),(b'owned-container',0,False),(b'',1,False)])
def test_stop_checks_actual_state(tmp_path, monkeypatch, running, exit_code, confirmed):
    from types import SimpleNamespace
    monkeypatch.setattr(p.subprocess,'run',lambda *a,**k: SimpleNamespace(returncode=exit_code,stderr=b''))
    monkeypatch.setattr(p,'command',lambda *a,**k: SimpleNamespace(stdout=running))
    assert p.stop_trial(['docker','compose'],{},tmp_path)['stop_confirmed'] is confirmed


def test_stop_timeout_is_recorded(tmp_path, monkeypatch):
    def timeout(*args, **kwargs):
        raise p.subprocess.TimeoutExpired('stop',75)
    monkeypatch.setattr(p.subprocess,'run',timeout)
    result=p.stop_trial(['docker','compose'],{},tmp_path)
    assert not result['stop_confirmed']
    assert 'stop_error' in result


def test_resource_breach_retains_observation(tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(p,'command',lambda *a,**k: SimpleNamespace(stdout=b'0 data'))
    monkeypatch.setattr(p.shutil,'disk_usage',lambda path: SimpleNamespace(free=99*p.GIB))
    with pytest.raises(RuntimeError,match='Internal'):
        p.sample_resources(config(tmp_path),p.time.monotonic(),tmp_path)
    observation=p.json.loads((tmp_path/'metrics.jsonl').read_text())
    assert observation['internal_free']==99*p.GIB


def test_exact_measurement_query_and_percentile(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules,'check_pgvector_platform',p)
    module_spec=importlib.util.spec_from_file_location('exact_measure',Path(__file__).resolve().parents[1]/'scripts/retrieval/measure_pgvector_exact.py')
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    assert module.percentile95(list(range(1,21)))==19
    with pytest.raises(ValueError):module.percentile95([])
    for j,scope in [(0,'broad'),(21,'broad'),(True,'broad'),(1,"broad;DROP")]:
        with pytest.raises(ValueError):module.query(j,scope)
