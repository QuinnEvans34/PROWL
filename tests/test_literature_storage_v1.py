"""Invented S1 scope/identity/durability checks; no real roots, volumes or network."""
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import plistlib
from types import SimpleNamespace

import pytest

from src.operations import literature_storage_v1 as s


class Probe:
    def __init__(self, value):
        self.value, self.calls, self.error = value, 0, None

    def observe(self):
        self.calls += 1
        if self.error:
            raise self.error
        return dict(self.value)


@pytest.fixture
def env(tmp_path, monkeypatch):
    ext, internal = tmp_path / "external", tmp_path / "internal"
    scratch, artifacts = ext / "scratch", ext / "artifacts"
    for p in (scratch, artifacts, internal):
        p.mkdir(parents=True)
    obs = json.loads((Path(__file__).parent / "fixtures/literature_storage_v1/observations.json").read_text())
    obs['primary']['mount'], obs['internal']['mount'] = str(ext), str(internal)
    # Simulate two devices while leaving all actual no-follow/file/durability I/O active.
    def invented_device(fd):
        inode = os.fstat(fd).st_ino
        internal_inodes = {p.stat().st_ino for p in (internal, *internal.rglob('*'))}
        return 702 if inode in internal_inodes else 701
    monkeypatch.setattr(s, "device", invented_device)
    registry = dict(schema_version='1.0.0', scientific_runs_enabled=False,
                    failure_domains={n: dict(kind='physical_device', mount_path=str(m), volume_uuid=u,
                                             filesystem='apfs')
                                     for n, m, u in [('external_primary', ext, 'invented-primary'),
                                                     ('internal_backup', internal, 'invented-internal')]},
                    roots=dict(prowl_scratch=dict(path=str(scratch), role='scratch',
                                                   access='acquisition_and_scoped_setup', failure_domain='external_primary'),
                               prowl_artifacts=dict(path=str(artifacts), role='artifact', access='setup_only',
                                                     failure_domain='external_primary'),
                               source=dict(path=None, acquisition_parent=str(ext / 'sources'), role='source'),
                               backup=dict(path=str(internal / 'backup'), role='backup')))
    regpath = tmp_path / 'registry.json'
    regpath.write_text(json.dumps(registry))
    cap = s.Capability(version='literature-storage-v1', approval='D-341', purpose='bounded_setup',
                       writer_id='invented-writer', setup_id='invented-01',
                       registry_sha256=hashlib.sha256(regpath.read_bytes()).hexdigest(),
                       external_mount=str(ext), external_uuid='invented-primary',
                       internal_mount=str(internal), internal_uuid='invented-internal',
                       scratch_root=str(scratch / 'literature'),
                       receipts_dir=str(artifacts / 'literature/receipts'),
                       fallback_dir=str(internal / 'fallback'), setup_cap_bytes=s.MiB,
                       scratch_cap_bytes=40*s.GiB, receipts_cap_bytes=64*s.MiB,
                       fallback_cap_bytes=64*s.MiB, headroom_floor_bytes=s.floor(obs['primary']['capacity_bytes']),
                       internal_floor_bytes=s.floor(obs['internal']['capacity_bytes']))
    primary, fallback = Probe(obs['primary']), Probe(obs['internal'])
    clock = [0.0]
    store = s.LiteratureStorage(regpath, cap, primary=primary, internal=fallback, clock=lambda: clock[0])
    return SimpleNamespace(store=store, cap=cap, primary=primary, fallback=fallback, regpath=regpath,
                           registry=registry, clock=clock, scratch=scratch, internal=internal)


def rebuilt(e, cap=None):
    return s.LiteratureStorage(e.regpath, cap or e.cap, primary=e.primary, internal=e.fallback,
                              clock=lambda: e.clock[0])


@pytest.mark.parametrize(('field','value'), [('approval','missing'), ('version','v2'),
    ('purpose','live_sizing'), ('writer_id','../escape'), ('setup_id','/absolute'),
    ('setup_cap_bytes',s.MiB+1), ('receipts_cap_bytes',True), ('fallback_cap_bytes',0),
    ('scratch_cap_bytes',41*s.GiB), ('headroom_floor_bytes',0)])
def test_unapproved_capabilities_refused_before_creation(env, field, value):
    with pytest.raises(s.StorageRefused):
        rebuilt(env, replace(env.cap, **{field:value}))
    assert not Path(env.cap.scratch_root).exists()


@pytest.mark.parametrize(('field','value'), [('uuid','other'), ('mount','/unmounted'),
    ('filesystem','not-apfs'), ('role','source'), ('writable',False), ('device',999),
    ('free_bytes',True), ('free_bytes',1), ('capacity_bytes',0)])
def test_live_primary_identity_failures_refuse_setup(env, field, value):
    env.primary.value[field] = value
    with pytest.raises(s.StorageRefused):
        env.store.setup()
    assert not Path(env.cap.scratch_root).exists()


def test_registry_drift_is_not_normalized(env):
    env.regpath.write_text(env.regpath.read_text()+'\n')
    with pytest.raises(s.StorageRefused, match='registry drift'):
        env.store.setup()


@pytest.mark.parametrize('change', ['role','access','domain','source_overlap','fallback_backup'])
def test_registry_relationships_are_checked(env, change):
    r = env.registry
    if change == 'role': r['roots']['prowl_scratch']['role'] = 'source'
    if change == 'access': r['roots']['prowl_artifacts']['access'] = 'arbitrary'
    if change == 'domain': r['failure_domains']['external_primary']['volume_uuid'] = 'other'
    if change == 'source_overlap': r['roots']['source']['acquisition_parent'] = env.cap.scratch_root
    if change == 'fallback_backup': r['roots']['backup']['path'] = env.cap.fallback_dir
    env.regpath.write_text(json.dumps(r))
    c = replace(env.cap, registry_sha256=hashlib.sha256(env.regpath.read_bytes()).hexdigest())
    with pytest.raises(s.StorageRefused):
        rebuilt(env, c)


@pytest.mark.parametrize('path_kind', ['parent','child','fallback'])
def test_symlink_components_are_never_followed(env, tmp_path, path_kind):
    outside = tmp_path / 'outside'
    outside.mkdir()
    target = {'parent':env.scratch, 'child':Path(env.cap.scratch_root),
              'fallback':Path(env.cap.fallback_dir)}[path_kind]
    if target.exists(): target.rmdir()
    target.symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError): env.store.setup()
    assert not list(outside.iterdir())


def test_inode_switch_under_same_named_path_is_refused(env):
    env.store.setup()
    p = Path(env.cap.scratch_root)
    p.rename(p.with_name('preserved-old'))
    p.mkdir()
    with pytest.raises(s.StorageRefused, match='identity switched'):
        with env.store.writer(env.cap.writer_id) as w: w.begin()


def test_setup_preserves_existing_safe_content(env):
    env.store.setup()
    keep = Path(env.cap.fallback_dir) / 'old-receipt.txt'
    keep.write_bytes(b'invented previous receipt')
    env.store.setup()
    assert keep.read_bytes() == b'invented previous receipt'


def test_floor_plus_40gib_and_remaining_checks_at_boundaries_and_60s(env):
    env.primary.value['free_bytes'] = env.cap.headroom_floor_bytes + 40*s.GiB - 1
    with pytest.raises(s.StorageRefused): env.store.sizing_start_check()
    env.primary.value['free_bytes'] += 1
    env.store.sizing_start_check()
    before = env.primary.calls
    env.clock[0] = 59
    env.store.tick(40*s.GiB)
    assert env.primary.calls == before
    env.clock[0] = 60
    env.primary.value['free_bytes'] -= 1
    with pytest.raises(s.StorageRefused): env.store.tick(40*s.GiB)


@pytest.mark.parametrize('name', ['../escape','/absolute','a/b','..','.'])
def test_payload_paths_confined(env, name):
    env.store.setup()
    with env.store.writer(env.cap.writer_id) as w:
        w.begin()
        with pytest.raises(s.StorageRefused): w.write_invented(name,b'x')


def test_exclusive_lock_survives_old_mtime_and_wrong_writer_refused(env):
    env.store.setup()
    with pytest.raises(s.StorageRefused):
        with env.store.writer('other'): pass
    with env.store.writer(env.cap.writer_id):
        os.utime(Path(env.cap.receipts_dir)/'.literature-writer.lock',(1,1))
        with pytest.raises(BlockingIOError):
            with env.store.writer(env.cap.writer_id): pass


def test_payload_journal_durability_exclusivity_quota_and_terminal(env):
    env.store.setup()
    with env.store.writer(env.cap.writer_id) as w:
        w.begin()
        w.write_invented('invented.txt',b'x'*s.MiB)
        assert s.read_regular(str(Path(env.cap.scratch_root)/w.name/'invented.txt')) == b'x'*s.MiB
        with pytest.raises(s.StorageRefused): w.write_invented('too-much',b'x')
        w.record('readback_verified')
        w.record('completed')
        with pytest.raises(s.StorageRefused): w.record('completed')
    events = [json.loads(x) for x in (Path(env.cap.receipts_dir)/w.journal_name).read_text().splitlines()]
    assert [x['sequence'] for x in events] == [1,2,3]
    assert [x['event'] for x in events] == ['started','readback_verified','completed']
    with env.store.writer(env.cap.writer_id) as another:
        with pytest.raises(FileExistsError): another.begin()
    with pytest.raises(s.StorageRefused): w.write_invented('after-close',b'x')


def test_volume_loss_stops_then_only_terminal_event_falls_back(env):
    env.store.setup()
    with env.store.writer(env.cap.writer_id) as w:
        w.begin()
        env.primary.error = OSError('invented detached volume')
        with pytest.raises(OSError): w.write_invented('not-written',b'x')
        with pytest.raises(s.StorageRefused): w.record('completed')
        w.record('stopped_primary_failure')
    files = list(Path(env.cap.fallback_dir).iterdir())
    assert len(files) == 1 and files[0].name == w.journal_name
    assert json.loads(files[0].read_text())['event'] == 'stopped_primary_failure'
    assert not (Path(env.cap.scratch_root)/w.name/'not-written').exists()


def test_fallback_failure_preserves_incomplete_primary(env):
    env.store.setup()
    with env.store.writer(env.cap.writer_id) as w:
        w.begin()
        env.primary.error = env.fallback.error = OSError('invented observation failure')
        with pytest.raises(OSError): w.record('stopped_primary_failure')
    assert not list(Path(env.cap.fallback_dir).iterdir())
    assert 'completed' not in (Path(env.cap.receipts_dir)/w.journal_name).read_text()


def test_existing_fallback_journal_never_appended(env):
    env.store.setup()
    with env.store.writer(env.cap.writer_id) as w:
        w.begin()
        old = Path(env.cap.fallback_dir)/w.journal_name
        old.write_bytes(b'preserved invented collision\n')
        env.primary.error = OSError('invented unavailable')
        with pytest.raises(s.StorageRefused, match='already exists'): w.record('stopped_primary_failure')
        assert old.read_bytes() == b'preserved invented collision\n'


def test_capability_transport_pin(env, tmp_path):
    path = tmp_path/'capability.json'
    path.write_text(json.dumps(asdict(env.cap)))
    assert s.load_capability(str(path),hashlib.sha256(path.read_bytes()).hexdigest()) == env.cap
    with pytest.raises(s.StorageRefused): s.load_capability(str(path),'0'*64)


def test_native_volume_uses_bavail_not_bfree(env, monkeypatch):
    info = dict(VolumeUUID='invented',MountPoint=str(env.internal),FilesystemType='apfs',WritableVolume=True)
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**k: SimpleNamespace(stdout=plistlib.dumps(info)))
    monkeypatch.setattr(s.os,'fstatvfs',lambda fd: SimpleNamespace(f_bavail=3,f_bfree=99,f_frsize=4096,f_blocks=100))
    obs = s.NativeVolume(str(env.internal),'fallback').observe()
    assert type(obs['writable']) is bool and type(obs['free_bytes']) is int
    assert obs['free_bytes'] == 3*4096 and obs['capacity_bytes'] == 100*4096


def test_receipt_ceiling_is_cumulative(env):
    env.store.setup()
    (Path(env.cap.receipts_dir)/'invented-old').write_bytes(b'x'*(64*s.MiB))
    with env.store.writer(env.cap.writer_id) as w:
        with pytest.raises(s.StorageRefused): w.begin()
    assert (Path(env.cap.receipts_dir)/'invented-old').stat().st_size == 64*s.MiB


def test_file_collision_and_hardlink_lock_are_preserved(env, tmp_path):
    env.store.setup()
    with env.store.writer(env.cap.writer_id) as w:
        w.begin()
        w.write_invented('same',b'invented')
        with pytest.raises(FileExistsError): w.write_invented('same',b'changed')
    lock = Path(env.cap.receipts_dir)/'.literature-writer.lock'
    os.link(lock,tmp_path/'invented-hardlink')
    with pytest.raises(s.StorageRefused):
        with env.store.writer(env.cap.writer_id): pass


def test_space_is_rechecked_before_each_payload(env):
    env.store.setup()
    with env.store.writer(env.cap.writer_id) as w:
        w.begin()
        env.primary.value['free_bytes'] = env.cap.headroom_floor_bytes
        with pytest.raises(s.StorageRefused): w.write_invented('not-written',b'x')
        assert not (Path(env.cap.scratch_root)/w.name/'not-written').exists()


def test_symlink_writer_lock_is_refused_without_altering_target(env, tmp_path):
    env.store.setup()
    target = tmp_path/'invented-target'
    target.write_bytes(b'preserve')
    (Path(env.cap.receipts_dir)/'.literature-writer.lock').symlink_to(target)
    with pytest.raises(OSError):
        with env.store.writer(env.cap.writer_id): pass
    assert target.read_bytes() == b'preserve'


def test_lock_substitution_stops_the_held_writer(env):
    env.store.setup()
    with env.store.writer(env.cap.writer_id) as w:
        w.begin()
        lock = Path(env.cap.receipts_dir)/'.literature-writer.lock'
        lock.rename(lock.with_name('preserved-original-lock'))
        lock.touch()
        with pytest.raises(s.StorageRefused,match='lock replaced'): w.write_invented('not-written',b'x')


def test_fsync_fault_never_claims_completed(env, monkeypatch):
    env.store.setup()
    with env.store.writer(env.cap.writer_id) as w:
        w.begin()
        def fail(fd): raise OSError('invented fsync failure')
        monkeypatch.setattr(s.os,'fsync',fail)
        with pytest.raises(OSError): w.write_invented('partial-preserved',b'invented')
        with pytest.raises(s.StorageRefused): w.record('completed')
