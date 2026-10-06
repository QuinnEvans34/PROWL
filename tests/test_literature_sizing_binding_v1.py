"""Invented guarded-hook qualification. No live roots, literature or network."""
from contextlib import contextmanager
from dataclasses import replace
import fcntl
import os
from pathlib import Path
import socket
import threading

import pytest
from test_literature_storage_v1 import env, rebuilt
from src.operations import literature_storage_v1 as s
from src.operations import literature_sizing_binding_v1 as b
from src.retrieval.sizing_v1.parser import InProcessLauncher, WatchdogLauncher
from src.retrieval.sizing_v1.journal import read_events, primary_name, fallback_name, plan_run, RunRefused, JournalUnwritable
from scripts.diagnostics.literature_sizing_binding_qualification_v1 import invented_transport, config_for

REPO = Path(__file__).resolve().parents[1]

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*a, **kw): raise AssertionError('network forbidden')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(socket, 'getaddrinfo', deny)

@pytest.fixture
def capability(env):
    return b.QualificationCapability('literature-sizing-binding-v1', 'offline_invented_qualification',
        'D-346/D-350', 'invented-qual', 'invented-executor', ('invented-success', 'invented-failure'),
        'a'*64, b.S2_IDENTITY, invented_transport().identity, b.runtime_pins(REPO), env.cap, 701, 702)

@contextmanager
def hooked(e, cap):
    e.store.setup()
    with e.store.writer(e.cap.writer_id) as lease:
        fs = b.GuardedSizingFs(e.store, lease, cap, REPO, clock=lambda: e.clock[0])
        fs.prepare_areas()
        yield fs

@pytest.mark.parametrize('field,value', [('purpose','live'), ('approval','none'), ('executor','../bad'),
    ('primary_device',702), ('s2_identity','0'*64), ('code_pins',()), ('payload_cap_bytes',s.MiB+1),
    ('journal_cap_bytes',65537), ('seconds',121), ('run_ids',('x','x'))])
def test_capability_rejects(env, capability, field, value):
    with pytest.raises(s.StorageRefused): replace(capability, **{field:value}).validate(REPO)
    assert not Path(env.cap.scratch_root).exists()

@pytest.mark.parametrize('field,value', [('role','source'), ('uuid','wrong'), ('device',999),
    ('writable',False), ('filesystem','other'), ('free_bytes',1), ('mount','/missing')])
def test_guard_fresh_identity(env, capability, field, value):
    with hooked(env, capability) as fs:
        env.primary.value[field] = value
        with pytest.raises(s.StorageRefused): fs.observe()

@pytest.mark.parametrize('fault', ['registry','closed','wall','child_substitute','symlink'])
def test_guard_relationship_drift(env, capability, fault):
    with hooked(env, capability) as fs:
        if fault == 'registry': env.regpath.write_text(env.regpath.read_text()+'\n')
        if fault == 'closed': fs.lease.active = False
        if fault == 'wall': env.clock[0] = 121
        if fault in ('child_substitute','symlink'):
            root = Path(fs.roots()['scratch']); root.rename(root.with_name('retained'))
            if fault == 'child_substitute': root.mkdir()
            else: root.symlink_to(root.with_name('retained'), target_is_directory=True)
        with pytest.raises((s.StorageRefused, OSError)): fs.observe()

def test_wrong_lease(env, capability):
    env.store.setup()
    other = rebuilt(env)
    with env.store.writer(env.cap.writer_id) as lease:
        with pytest.raises(s.StorageRefused): b.GuardedSizingFs(other, lease, capability, REPO)
        with pytest.raises(BlockingIOError):
            with other.writer(env.cap.writer_id): pass

@pytest.mark.parametrize('area,rel', [('source','x'),('fallback','../escape'),('receipts','/absolute'),
    ('scratch','sizing-other/payload'),('fallback','payload'),('receipts','unapproved.jsonl')])
def test_denied_paths(env, capability, area, rel):
    with hooked(env, capability) as fs:
        fs.active_run = capability.run_ids[0]
        with pytest.raises((s.StorageRefused, ValueError)): fs.create_exclusive(area, rel)

@pytest.mark.parametrize('kind', ['symlink','hardlink','file_substitution'])
def test_file_substitution_preserves_sentinel(env, capability, kind):
    with hooked(env, capability) as fs:
        fs.active_run = capability.run_ids[0]
        fs.mkdir_exclusive('scratch','sizing-'+fs.active_run)
        rel = 'sizing-'+fs.active_run+'/data'
        with fs.create_exclusive('scratch',rel) as fh:
            path = Path(fs.display('scratch',rel)); old = path.with_name('retained'); path.rename(old)
            sentinel = path.with_name('sentinel'); sentinel.write_bytes(b'unchanged')
            if kind == 'symlink': path.symlink_to(sentinel)
            elif kind == 'hardlink': os.link(sentinel,path)
            else: path.write_bytes(b'unchanged')
            with pytest.raises((s.StorageRefused, OSError)): fh.write(b'bad')
        assert sentinel.read_bytes() == b'unchanged'
        assert old.read_bytes() == b''

def test_child_descriptor_close_never_commits_by_name(env, capability):
    with hooked(env, capability) as fs:
        fs.active_run = capability.run_ids[0]; fs.mkdir_exclusive('scratch','sizing-'+fs.active_run)
        rel='sizing-'+fs.active_run+'/delegated'
        fh=fs.create_exclusive('scratch',rel); fd=fh.fileno()
        path=Path(fs.display('scratch',rel)); old=path.with_name('held'); path.rename(old)
        path.write_bytes(b'untouched'); os.write(fd,b'child descriptor bytes'); fh.close()
        assert old.read_bytes()==b'child descriptor bytes' and path.read_bytes()==b'untouched'

def test_signed_lock_competition_and_substitution(env, capability):
    with hooked(env, capability) as fs:
        name='run-S-'+capability.signed_copy_sha256[:16]+'.lock'
        lock=fs.lock('receipts',name)
        try:
            with pytest.raises(b.LockHeld): fs.lock('receipts',name)
            path=Path(fs.display('receipts',name)); path.rename(path.with_name('retained.lock')); path.touch()
            with pytest.raises(s.StorageRefused): fs.list('receipts')
        finally: lock.release()

def test_unsupported_lock(env, capability, monkeypatch):
    with hooked(env, capability) as fs:
        def fail(*a): raise OSError('unsupported')
        monkeypatch.setattr(fcntl,'flock',fail)
        with pytest.raises(b.LockUnsupported): fs.lock('receipts','run-S-'+capability.signed_copy_sha256[:16]+'.lock')

@pytest.mark.parametrize('area', ['scratch','receipts','fallback'])
def test_quota_retains_failed_attempt_and_no_refund(env, capability, area):
    cap=replace(capability,payload_cap_bytes=20,journal_cap_bytes=20)
    with hooked(env,cap) as fs:
        fs.active_run=cap.run_ids[0]
        if area=='scratch': fs.mkdir_exclusive(area,'sizing-'+fs.active_run); rel='sizing-'+fs.active_run+'/data'
        else: rel='run-S-'+fs.active_run+('.fallback.jsonl' if area=='fallback' else '.jsonl')
        with fs.create_exclusive(area,rel) as fh:
            fh.write(b'x'*20)
            with pytest.raises(s.StorageRefused): fh.write(b'z')
        assert Path(fs.display(area,rel)).read_bytes()==b'x'*20
        assert fs.charged[area]==20

@pytest.mark.parametrize('area', ['receipts','fallback'])
def test_old_contents_count_toward_global_limit(env, capability, area):
    with hooked(env,capability) as fs:
        base=Path(env.cap.receipts_dir if area=='receipts' else env.cap.fallback_dir)
        with open(base/'retained-old','wb') as fh: fh.truncate(64*s.MiB)
        fs.active_run=capability.run_ids[0]
        rel='run-S-'+fs.active_run+('.fallback.jsonl' if area=='fallback' else '.jsonl')
        with fs.create_exclusive(area,rel) as fh:
            with pytest.raises(s.StorageRefused): fh.write(b'x')
        assert (base/'retained-old').stat().st_size==64*s.MiB

def test_empty_journal_is_retained(env, capability):
    with hooked(env,capability) as fs:
        fs.active_run=capability.run_ids[0]; rel=primary_name(fs.active_run)
        with fs.create_exclusive('receipts',rel) as fh:
            with pytest.raises(s.StorageRefused): fs.remove_own_empty('receipts',rel,fh)
        assert Path(fs.display('receipts',rel)).exists()
        with pytest.raises(RunRefused): plan_run(fs,capability.signed_copy_sha256)

@pytest.mark.parametrize('live', [False,True])
def test_full_invented_runner_and_two_run_counters(env, capability, live):
    with hooked(env,capability) as fs:
        cfg=config_for(capability,fs)
        launcher=WatchdogLauncher(poll=0.02) if live else InProcessLauncher()
        before_threads={t.ident for t in threading.enumerate()}
        assert fs.run(cfg,transport=invented_transport(),launcher=launcher,run_id=capability.run_ids[0])=='completed'
        index,inherited,prior=plan_run(fs,capability.signed_copy_sha256)
        assert index==2 and inherited['network_used']>0 and inherited['scratch_used']>0
        world=invented_transport()
        def fault(method,url):
            if (method,url)==('GET',b.BASE): env.primary.value['writable']=False
        world.on_request=fault
        assert fs.run(cfg,transport=world,launcher=launcher,run_id=capability.run_ids[1])=='stopped_internal_error'
        env.primary.value['writable']=True
        final=read_events(fs,'fallback',fallback_name(capability.run_ids[1]))[-1]
        assert all(final['counters'][k]>=v for k,v in inherited.items())
        with pytest.raises(RunRefused): plan_run(fs,capability.signed_copy_sha256)
        assert not [t for t in threading.enumerate() if t.ident not in before_threads and t.is_alive()]

@pytest.mark.parametrize('fallback_fails', [False,True])
def test_midstream_primary_loss_stops_and_never_false_success(env, capability, fallback_fails):
    with hooked(env,capability) as fs:
        cfg=config_for(capability,fs); world=invented_transport()
        def fail(method,url):
            if (method,url)==('GET',b.BASE):
                env.primary.value['free_bytes']=1
                if fallback_fails: env.fallback.value['free_bytes']=1
        world.on_request=fail
        if fallback_fails:
            with pytest.raises(JournalUnwritable): fs.run(cfg,transport=world,launcher=InProcessLauncher(),run_id=capability.run_ids[0])
            status='incomplete'
        else:
            status=fs.run(cfg,transport=world,launcher=InProcessLauncher(),run_id=capability.run_ids[0])
        assert status!='completed'
        env.primary.value['free_bytes']=10*s.TiB if hasattr(s,'TiB') else 10000*s.GiB
        env.fallback.value['free_bytes']=10000*s.GiB
        if not fallback_fails:
            events=read_events(fs,'fallback',fallback_name(capability.run_ids[0]))
            assert events[-1]['status']==status and events[0]['event']=='primary_lost'
        else:
            with pytest.raises(RunRefused): plan_run(fs,capability.signed_copy_sha256)

@pytest.mark.parametrize('field,value', [('scratch_root','/outside'),('tool_code_hash','0'*64),
    ('executor','other'),('headroom_floor_bytes',1),('baseline_url','https://example.com')])
def test_config_identity_refused_before_runner(env, capability, field, value):
    with hooked(env,capability) as fs:
        cfg=config_for(capability,fs); cfg[field]=value
        with pytest.raises(s.StorageRefused): fs.run(cfg,transport=invented_transport(),launcher=InProcessLauncher(),run_id=capability.run_ids[0])
        assert not fs.list('scratch',prefix='sizing-')

@pytest.mark.parametrize('fault', ['short','fsync'])
def test_partial_and_durability_faults_preserve_bytes_and_charge(env,capability,monkeypatch,fault):
    with hooked(env,capability) as fs:
        fs.active_run=capability.run_ids[0]; rel=primary_name(fs.active_run)
        with fs.create_exclusive('receipts',rel) as fh:
            if fault=='short':
                real=fh.stream
                class Short:
                    def fileno(self): return real.fileno()
                    def write(self,data): return real.write(data[:2])
                    def close(self): real.close()
                fh.stream=Short()
                with pytest.raises(OSError,match='short'): fh.write(b'abcd')
                assert fs.charged['receipts']==4
                assert Path(fs.display('receipts',rel)).read_bytes()==b'ab'
            else:
                fh.write(b'abcd')
                monkeypatch.setattr(os,'fsync',lambda fd: (_ for _ in ()).throw(OSError('fsync fault')))
                with pytest.raises(OSError): os.fsync(fh.fileno())
                assert Path(fs.display('receipts',rel)).read_bytes()==b'abcd'
                assert fs.charged['receipts']==4

def test_periodic_guard_loss_during_child_kills_and_preserves_output(env,capability,monkeypatch):
    with hooked(env,capability) as fs:
        cfg=config_for(capability,fs)
        real=WatchdogLauncher.parse
        def parse(self,**kw):
            old=kw['periodic']
            def fault():
                env.primary.value['free_bytes']=1
                old()
            kw['periodic']=fault
            return real(self,**kw)
        monkeypatch.setattr(WatchdogLauncher,'parse',parse)
        from src.retrieval.sizing_v1 import parser
        original_watchdog=parser.run_with_watchdog
        def immediate(*a,**kw):
            kw['check_interval']=0
            return original_watchdog(*a,**kw)
        monkeypatch.setattr(parser,'run_with_watchdog',immediate)
        status=fs.run(cfg,transport=invented_transport(),launcher=WatchdogLauncher(poll=0.01),run_id=capability.run_ids[0])
        assert status!='completed'
        env.primary.value['free_bytes']=10000*s.GiB
        assert list(Path(fs.roots()['scratch']).rglob('*'))
        assert read_events(fs,'fallback',fallback_name(capability.run_ids[0]))[-1]['status']==status

@pytest.mark.parametrize('change',['memory','python','probe','poll'])
def test_watchdog_bounds_cannot_be_weakened(env,capability,change):
    with hooked(env,capability) as fs:
        launcher=WatchdogLauncher()
        if change=='memory': launcher.memory_cap=5*s.GiB
        if change=='python': launcher.python='/unreviewed/python'
        if change=='probe': launcher.probe=object()
        if change=='poll': launcher.poll=5
        with pytest.raises(s.StorageRefused): fs.run(config_for(capability,fs),transport=invented_transport(),launcher=launcher,run_id=capability.run_ids[0])
        assert not fs.list('scratch',prefix='sizing-')

@pytest.mark.parametrize('kind',['orphan','truncated','unknown'])
def test_prior_history_never_silently_skips_ambiguity(env,capability,kind):
    with hooked(env,capability) as fs:
        if kind=='orphan': Path(fs.roots()['scratch'],'sizing-old').mkdir()
        else:
            Path(fs.roots()['receipts'],'run-S-old.jsonl').write_bytes(b'{torn' if kind=='truncated' else b'{"event":"unknown"}\n')
        with pytest.raises(RunRefused): plan_run(fs,capability.signed_copy_sha256)

def test_original_cli_still_refuses():
    from scripts.retrieval.run_s_sizing_v1 import main
    with pytest.raises(SystemExit) as exc: main(['--execute'])
    assert exc.value.code!=0

def test_qualification_executor_end_to_end_in_invented_volumes(env,capability,monkeypatch):
    """Full qualifier/real watchdog; no dependency on an existing local outputs directory."""
    import hashlib,json,shutil
    from dataclasses import asdict
    from types import SimpleNamespace
    from scripts.diagnostics import literature_sizing_binding_qualification_v1 as q
    env.store.setup()
    clone=env.regpath.parent/'invented-repository'
    for name in b.RUNTIME_FILES:
        dest=clone/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,dest)
    monkeypatch.setattr(q,'REPO',clone)
    monkeypatch.setattr(s,'NativeVolume',lambda mount,role: env.primary if role=='literature' else env.fallback)
    root=clone/'outputs/prowl/invented-controls';root.mkdir(parents=True)
    q.exclusive_json(root/'capability.json',asdict(capability))
    cap_hash=hashlib.sha256((root/'capability.json').read_bytes()).hexdigest()
    q.exclusive_json(root/'request.json',dict(capability_sha256=cap_hash,roots=capability.roots()))
    args=SimpleNamespace(capability=str(root/'capability.json'),capability_sha256=cap_hash,
        request_sha256=hashlib.sha256((root/'request.json').read_bytes()).hexdigest(),registry=str(env.regpath))
    q.execute(args)
    result=json.loads((root/'result.json').read_text())
    assert result['success']=='completed' and result['failure']=='stopped_internal_error'
    assert result['native_parser'] and len(result['lock_checks'])==2
    assert result['cleanup']['tracked_children']>=10
    assert result['cleanup']['live_children']==[] and result['cleanup']['extra_descriptors']=={}
    assert result['cleanup']['live_threads']==[] and result['run_s'] is False
    assert (root/'consumed.json').exists()
    with pytest.raises(FileExistsError): q.execute(args)
