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
    monkeypatch.setattr(expert, 'OUT', tmp_path/'services')
    monkeypatch.setattr(expert, 'ac_power', lambda: True)
    monkeypatch.setattr(expert, 'require_ac', lambda: None)
    monkeypatch.setattr(Path, 'is_mount', lambda self: True)
    monkeypatch.setattr(expert, 'read_config', lambda p: c)
    monkeypatch.setattr(expert, 'limits', lambda c: None)
    monkeypatch.setattr(expert, 'gpu_busy', lambda: busy)
    monkeypatch.setattr(expert, 'wait_for', lambda *a, **kw: None)
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
    monkeypatch.setattr(expert, 'http', lambda port, *a, **kw: {'storage_identity': expert.digest(expert.read_config(expert.CONFIG))} if port == 8016 else pytest.fail('must not load model during teacher'))
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
        if port==8016: return {'storage_identity':expert.digest(expert.read_config(expert.CONFIG))}
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
    monkeypatch.setattr(expert,'http',lambda port,*a,**k:{'storage_identity':expert.digest(expert.read_config(expert.CONFIG))} if port==8016 else {'models':[]})
    with pytest.raises(RuntimeError,match='No model was downloaded'):expert.prepare()
    assert not any('pull' in a for a in calls)


def test_internal_preparation_never_mounts_external_drive(monkeypatch,tmp_path):
    calls=setup(monkeypatch,tmp_path)
    c={'storage':'internal','project':'prowl-literature-internal','mount':'/System/Volumes/Data','data':'/expected'}
    expert.CONFIG.write_text(json.dumps(c))
    monkeypatch.setattr(expert,'read_config',lambda _:c)
    monkeypatch.setattr(Path,'is_mount',lambda _:pytest.fail('internal mode must not mount external disk'))
    expert.prepare()
    assert not any(a[0]=='diskutil' for a in calls)
    assert any(a[-1]=='prowl-literature-internal-db-1' and 'start' in a for a in calls)


def test_existing_wrong_search_configuration_fails_without_stopping_process(monkeypatch,tmp_path):
    calls=setup(monkeypatch,tmp_path)
    monkeypatch.setattr(expert,'http',lambda *a,**k:{'backend':'checked','storage_identity':'old'})
    with pytest.raises(RuntimeError,match='different or older search configuration'):
        expert.prepare()
    assert not any('stop' in a or 'restart' in a or 'kill' in a for a in calls)


@pytest.mark.parametrize('training_busy', [False, True])
def test_new_backend_selects_fast_preview_only_when_gpu_free(monkeypatch,tmp_path,training_busy):
    setup(monkeypatch,tmp_path)
    monkeypatch.setattr(expert,'listening',lambda port:False)
    states=iter([training_busy,training_busy,True])
    monkeypatch.setattr(expert,'gpu_busy',lambda:next(states))
    monkeypatch.setattr(expert,'prepare_model',lambda: not training_busy)
    starts=[]
    monkeypatch.setattr(expert,'start_process',lambda argv,name:starts.append(argv))
    expert.prepare()
    assert len(starts)==1
    assert Path(starts[0][1]).name=='serve_single_summary_candidate.py'
    assert ('--sources-only' in starts[0]) is training_busy


def test_cold_start_warms_model_before_candidate_lifetime_reservation(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path,busy=False)
    state={'reserved':False,'warmed':False}; events=[]
    monkeypatch.setattr(expert,'listening',lambda port:False)
    monkeypatch.setattr(expert,'gpu_busy',lambda:state['reserved'])
    def warm():
        assert not state['reserved']
        state['warmed']=True; events.append('warm'); return True
    def start(argv,name):
        assert state['warmed']
        assert Path(argv[1]).name=='serve_single_summary_candidate.py'
        state['reserved']=True; events.append('reserve')
    monkeypatch.setattr(expert,'prepare_model',warm)
    monkeypatch.setattr(expert,'start_process',start)
    expert.prepare()
    assert events==['warm','reserve']


def test_warmup_returns_without_model_calls_when_another_owner_holds_lock(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path)
    monkeypatch.setattr(expert,'LOCK',tmp_path/'gpu.lock')
    import fcntl
    with expert.LOCK.open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert expert.prepare_model() is False


def test_battery_preparation_starts_only_source_search_never_model(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path,busy=False)
    monkeypatch.setattr(expert,'ac_power',lambda:False)
    monkeypatch.setattr(expert,'listening',lambda _:False)
    monkeypatch.setattr(expert,'prepare_model',lambda:pytest.fail('No battery model warmup'))
    starts=[]
    monkeypatch.setattr(expert,'start_process',lambda argv,name:starts.append(argv))
    expert.prepare()
    assert len(starts)==1 and '--sources-only' in starts[0]


def test_power_gate_precedes_every_model_service_or_allocation_call(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path,busy=False)
    def denied():raise RuntimeError('AC power required')
    monkeypatch.setattr(expert,'require_ac',denied)
    monkeypatch.setattr(expert,'http',lambda *a,**k:pytest.fail('No model request before power admission'))
    with pytest.raises(RuntimeError,match='AC power required'):expert.prepare_model()


def test_existing_owned_source_service_upgrades_only_after_power_and_warmup(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path,busy=False)
    monkeypatch.setattr(expert,'http',lambda *a,**k:{'storage_identity':expert.digest(expert.read_config(expert.CONFIG)),'answer_policy':'sources-only'})
    events=[]
    monkeypatch.setattr(expert,'prepare_model',lambda:events.append('warm') or True)
    monkeypatch.setattr(expert,'stop_owned_sources',lambda:events.append('stop-owned'))
    monkeypatch.setattr(expert,'start_process',lambda argv,name:events.append(('start',argv)))
    expert.prepare()
    assert events[:2]==['warm','stop-owned']
    assert len(events)==3 and '--sources-only' not in events[-1][1]


def test_unverified_owner_is_never_signalled(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path)
    monkeypatch.setattr(expert.os,'kill',lambda *a:pytest.fail('Must not signal unknown owner'))
    with pytest.raises(RuntimeError,match='ownership could not be verified'):expert.stop_owned_sources()


def test_ready_owner_uses_post_startup_identity(monkeypatch,tmp_path):
    from types import SimpleNamespace
    setup(monkeypatch,tmp_path)
    expert.OUT.mkdir()
    record=expert.OUT/'literature-owner.json'
    record.write_text(json.dumps({'pid':123,'argv':['fixed'],'identity':'transient interpreter'}))
    monkeypatch.setattr(expert,'process_identity',lambda pid:'stable interpreter')
    expert.record_ready_owner(SimpleNamespace(pid=123,poll=lambda:None))
    assert json.loads(record.read_text())=={'pid':123,'argv':['fixed'],'identity':'stable interpreter'}


def test_exited_child_is_reported_immediately_with_stage_instead_of_generic_timeout():
    class Exited:
        def poll(self):return 1
    with pytest.raises(RuntimeError,match='Literature search service exited before'):
        expert.wait_for(lambda:False,35,stage='Literature search service',process=Exited())


def test_sources_only_http_refuses_model_routes_and_keeps_queries(monkeypatch):
    import importlib.util,sys,threading
    from types import SimpleNamespace
    from urllib.request import Request,urlopen
    from urllib.error import HTTPError
    path=expert.ROOT/'scripts/serve_single_summary_candidate.py'
    sys.path.insert(0,str(expert.ROOT/'scripts'))
    try:
        spec=importlib.util.spec_from_file_location('source_only_candidate_test',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    finally:sys.path.pop(0)
    source=SimpleNamespace(config={'collection':'fixture','retriever':'fixture'},storage_identity='fixture',check_backend=lambda:None,
                           search=lambda request:{'state':'evidence_unassessed','generation':'not_called'})
    monkeypatch.setattr(module,'create_service',lambda _:source)
    monkeypatch.setattr(module,'create_study_answers',lambda _:(source,None))
    monkeypatch.setattr(module,'training_guard',lambda _:pytest.fail('No GPU/training guard for CPU sources'))
    monkeypatch.setattr(module,'SinglePassAnswers',lambda _:pytest.fail('No model answer object for CPU sources'))
    original=module.LocalFixtureServer
    seen=[]
    class TestServer(original):
        def serve_forever(self):
            thread=threading.Thread(target=super().serve_forever,daemon=True);thread.start()
            try:
                for route in ['query','answer','interpret']:
                    request=Request(f'http://127.0.0.1:{self.server_port}/literature-search/{route}',
                                    data=b'{"schema_version":"prowl-expert-request-v1","request_id":"7597e91c-6023-4610-a7b5-f27c73c8a540","question":"Why are pancreas boundaries difficult to outline?"}',headers={'Content-Type':'application/json'})
                    try:
                        with urlopen(request,timeout=5) as r:seen.append((route,r.status,json.load(r)))
                    except HTTPError as r:seen.append((route,r.code,json.load(r)))
            finally:self.shutdown();thread.join(5)
    monkeypatch.setattr(module,'LocalFixtureServer',TestServer)
    module.run_candidate('fixture',0,sources_only=True)
    assert [(r,s) for r,s,_ in seen]==[('query',200),('answer',409),('interpret',409)]
    assert seen[0][2]['generation']=='not_called'
    assert source.answer_gpu_reserved is False
