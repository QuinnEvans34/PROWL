"""End-to-end run S orchestration against an invented NLM-like fake (network denied)."""
import ast
import gzip
import hashlib
import json
import os
import socket
import sys
from pathlib import Path

import pytest

from src.retrieval.sizing_v1 import GIB, Interrupted, RunRefused
from src.retrieval.sizing_v1.fsio import PlainFs
from src.retrieval.sizing_v1.journal import Journal, fallback_name, plan_run, primary_name, read_events
from src.retrieval.sizing_v1.parser import InProcessLauncher
from src.retrieval.sizing_v1.runner import (CODE_FILES, MESH_FALLBACK_ALLOWANCE, code_identity, run_sizing,
                                            validate_config)

pytestmark = pytest.mark.integration
FIX = Path(__file__).parent / 'fixtures' / 'sizing_v1'
REPO = Path(__file__).resolve().parents[2]
BASE = 'https://nlm.invalid/pubmed/baseline/'
UPD = 'https://nlm.invalid/pubmed/updatefiles/'
MESH = 'https://nlm.invalid/mesh/desc2026.xml'
SHA = 'd' * 64
CODE = 'c' * 64
BASELINE_SAMPLES = ('pubmed26n0001.xml.gz', 'pubmed26n0667.xml.gz', 'pubmed26n1334.xml.gz')
UPDATE_SAMPLES = ('pubmed26n1340.xml.gz', 'pubmed26n1341.xml.gz')
MESH_BODY = b'<?xml version="1.0"?><DescriptorRecordSet><Invented/></DescriptorRecordSet>\n'


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def deny(*a, **k):
        raise AssertionError('network denied in sizing_v1 tests')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(socket, 'getaddrinfo', deny)


class Clock:
    def __init__(self):
        self.t = 5000.0

    def __call__(self):
        return self.t


class Resp:
    def __init__(self, world, status=200, body=b'', headers=None, header_bytes=180, length=True):
        self.world, self.status, self.body, self.pos = world, status, body, 0
        self.headers = dict(headers or {})
        if length and 'content-length' not in self.headers:
            self.headers['content-length'] = str(len(body))
        self.header_bytes = header_bytes

    def read(self, n):
        data = self.body[self.pos:self.pos + n]
        self.pos += len(data)
        self.world.served += len(data)
        self.world.clock.t += 0.5
        return data

    def close(self):
        pass


class World:
    """Invented NLM-like server: each (method, url) serves a queue of response specs."""

    def __init__(self, clock, sample_sizes=None, mesh_head=True, update_body=None, baseline_body=None):
        self.clock, self.served, self.calls, self.fail_on = clock, 0, [], {}
        doc = gzip.compress((FIX / 'pubmed_style_doctype.xml').read_bytes(), mtime=0)
        upd = update_body or gzip.compress((FIX / 'update_with_deletes.xml').read_bytes(), mtime=0)
        self.bodies = {n: (baseline_body or doc) for n in BASELINE_SAMPLES}
        self.bodies.update({n: upd for n in UPDATE_SAMPLES})
        sizes = sample_sizes or {}
        base_rows = []
        for i in range(1, 1335):
            n = f'pubmed26n{i:04d}.xml.gz'
            size = sizes.get(n, str(len(self.bodies[n])) if n in self.bodies else '22M')
            base_rows += [(n, size), (n + '.md5', '60')]
        upd_rows = []
        for i in range(1335, 1342):
            n = f'pubmed26n{i:04d}.xml.gz'
            size = sizes.get(n, str(len(self.bodies[n])) if n in self.bodies else '1M')
            upd_rows += [(n, size), (n + '.md5', '60')]
        self.routes = {('GET', BASE): [dict(body=self.listing(base_rows + [('README.txt', '2K')]))],
                       ('GET', UPD): [dict(body=self.listing(upd_rows))],
                       ('HEAD', MESH): [dict(headers={'content-length': str(len(MESH_BODY))} if mesh_head else {},
                                             length=False)],
                       ('GET', MESH): [dict(body=MESH_BODY)]}
        for base, names in ((BASE, BASELINE_SAMPLES), (UPD, UPDATE_SAMPLES)):
            for n in names:
                md5 = hashlib.md5(self.bodies[n]).hexdigest()
                self.routes[('GET', base + n + '.md5')] = [dict(body=f'MD5({n})= {md5}\n'.encode())] * 2
                self.routes[('GET', base + n)] = [dict(body=self.bodies[n])] * 2

    @staticmethod
    def listing(rows):
        body = ''.join(f'<a href="{n}">{n}</a>  2025-12-10 14:15  {s}\n' for n, s in rows)
        return f'<html><body><pre><a href="../">Parent Directory</a>\n{body}</pre></body></html>'.encode()

    def request(self, method, url, timeout):
        self.calls.append((method, url))
        if (method, url) in self.fail_on:
            raise self.fail_on[(method, url)]
        spec = self.routes[(method, url)].pop(0)
        return Resp(self, **spec)


class Volume:
    def __init__(self, overrides=None):
        self.calls, self.overrides = 0, overrides or {}

    def observe(self):
        self.calls += 1
        obs = dict(uuid='UUID-INVENTED', mount='/Volumes/Invented', writable=True, free_bytes=200 * GIB)
        obs.update(self.overrides.get(self.calls, {}))
        return obs


@pytest.fixture
def config(tmp_path):
    for d in ('scratch', 'receipts', 'internal-fallback'):
        (tmp_path / d).mkdir()
    return dict(signed_copy_sha256=SHA, baseline_url=BASE, update_url=UPD, mesh_url=MESH, mesh_name='desc2026.xml',
                fallback_dir=str(tmp_path / 'internal-fallback'), scratch_root=str(tmp_path / 'scratch'),
                receipts_dir=str(tmp_path / 'receipts'), executor='Quinton (invented test)', tool_code_hash=CODE,
                user_agent='PROWL-capstone-sizing/1', headroom_floor_bytes=100 * GIB, volume_uuid='UUID-INVENTED',
                volume_mount='/Volumes/Invented', memory_cap_bytes=4 * GIB, expansion_limit=20)


def fs_of(config):
    return PlainFs(config['scratch_root'], config['receipts_dir'], config['fallback_dir'])


def go(config, world, volume=None, run_id='r1'):
    return run_sizing(config, transport=world, clock=world.clock, wall=lambda: '2026-10-03T00:00:00Z',
                      volume=volume or Volume(), launcher=InProcessLauncher(), run_id=run_id, code_hash=CODE)


def events(config, run_id='r1'):
    return read_events(fs_of(config), 'receipts', primary_name(run_id))


def test_completed_run_records_everything_in_order(config):
    world = World(Clock())
    assert go(config, world) == 'completed'
    ev = events(config)
    names = [e['event'] for e in ev]
    assert names[0] == 'start' and names[-1] == 'final' and ev[-1]['status'] == 'completed'
    resolved = names.index('preflight_resolved')
    first_sample = next(i for i, e in enumerate(ev) if e['event'] == 'file_start' and 'pubmed26n' in e['name'])
    assert resolved < first_sample
    assert [c for c in world.calls if c == ('GET', BASE)] == [('GET', BASE)]      # frozen once, never re-listed
    final = ev[-1]
    headers = 180 * len(world.calls)
    assert final['counters']['network_used'] == world.served + headers
    rep = final['summary']['representativeness']
    assert rep['update_names'] == list(UPDATE_SAMPLES) and rep['baseline_names'] == list(BASELINE_SAMPLES)
    assert rep['projection_ratio'] == pytest.approx(max(rep['parsed_ratios']) * 1.5)
    parsed = [e for e in ev if e['event'] == 'parsed']
    assert len(parsed) == 5 and all(e['measurements']['records'] >= 1 for e in parsed)
    assert sum(e['measurements']['deletes'] for e in parsed) == 4
    assert final['summary']['baseline_totals']['file_count'] == 1334
    assert ev[0]['caps']['network'] == 10 * GIB and ev[0]['memory_method'].startswith('watchdog')


def test_cap_precheck_stops_before_any_sample_transfer(config):
    world = World(Clock(), sample_sizes={'pubmed26n0001.xml.gz': '6G', 'pubmed26n0667.xml.gz': '6G'})
    assert go(config, world) == 'stopped_preflight'
    assert not any('pubmed26n0001.xml.gz' in url for _, url in world.calls)


def test_mesh_without_head_size_reserves_one_gib(config):
    world = World(Clock(), mesh_head=False)
    assert go(config, world) == 'completed'
    resolved = next(e for e in events(config) if e['event'] == 'preflight_resolved')
    assert resolved['mesh']['allowance'] == MESH_FALLBACK_ALLOWANCE and resolved['mesh']['head_size'] is None


def test_mesh_larger_than_head_size_stops(config):
    world = World(Clock())
    world.routes[('HEAD', MESH)] = [dict(headers={'content-length': '10'}, length=False)]
    assert go(config, world) == 'stopped_size_allowance'


def test_volume_identity_mismatch_at_start_stops_before_scratch(config):
    world = World(Clock())
    assert go(config, world, Volume({1: dict(uuid='OTHER')})) == 'stopped_volume_check'
    assert os.listdir(config['scratch_root']) == []
    assert world.calls == []


def test_free_space_drop_before_a_later_file_stops(config):
    world = World(Clock())
    assert go(config, world, Volume({4: dict(free_bytes=100 * GIB)})) == 'stopped_volume_check'


def test_start_requires_floor_plus_40_gib(config):
    world = World(Clock())
    assert go(config, world, Volume({1: dict(free_bytes=140 * GIB - 1)})) == 'stopped_volume_check'


def test_rerun_inherits_cumulative_counters_and_third_run_refused(config):
    world = World(Clock())
    bad = BASE + 'pubmed26n0667.xml.gz.md5'
    world.routes[('GET', bad)] = [dict(body=b'MD5(pubmed26n0667.xml.gz)= ' + b'0' * 32 + b'\n')] * 2
    assert go(config, world, run_id='r1') == 'stopped_transfer_failed'
    first = events(config, 'r1')[-1]['counters']
    world2 = World(Clock())
    assert go(config, world2, run_id='r2') == 'completed'
    ev2 = events(config, 'r2')
    assert ev2[0]['run_index'] == 2 and ev2[0]['counters']['network_used'] == first['network_used']
    assert ev2[-1]['counters']['network_used'] > first['network_used']
    with pytest.raises(RunRefused):
        go(config, World(Clock()), run_id='r3')
    assert not os.path.exists(os.path.join(config['receipts_dir'], primary_name('r3')))


def test_interrupted_is_terminal(config):
    world = World(Clock())
    world.fail_on[('GET', UPD + 'pubmed26n1340.xml.gz')] = Interrupted('invented SIGTERM')
    assert go(config, world) == 'interrupted'
    assert plan_run(fs_of(config), SHA)[0] == 2


def test_code_hash_mismatch_refuses_without_journal(config):
    with pytest.raises(RunRefused):
        run_sizing(config, transport=World(Clock()), clock=Clock(), wall=lambda: 'x', volume=Volume(),
                   launcher=InProcessLauncher(), run_id='r1', code_hash='e' * 64)
    assert os.listdir(config['receipts_dir']) == []


@pytest.mark.parametrize('change', [dict(memory_cap_bytes=8 * GIB), dict(expansion_limit=30), dict(executor=''),
                                    dict(mesh_name='other.xml'), dict(baseline_url=BASE.rstrip('/'))])
def test_config_cannot_loosen_or_omit(config, change):
    with pytest.raises(RunRefused):
        validate_config(dict(config, **change))


def test_fallback_inside_scratch_refused(config):
    with pytest.raises(RunRefused):
        validate_config(dict(config, fallback_dir=os.path.join(config['scratch_root'], 'fb')))


def test_malformed_sample_stops_naming_the_file(config):
    bad = gzip.compress((FIX / 'malformed.xml').read_bytes(), mtime=0)
    world = World(Clock(), baseline_body=bad)
    assert go(config, world) == 'stopped_malformed_xml'
    final = events(config)[-1]
    assert final['detail']['source_file'] == 'pubmed26n0001.xml.gz'


def test_primary_journal_loss_stops_and_finishes_in_fallback(config, monkeypatch):
    real_write = Journal._write
    count = {'n': 0}

    def flaky(self, line):
        if not self.primary_lost:
            count['n'] += 1
            if count['n'] > 6:
                raise OSError('invented: external volume vanished')
        return real_write(self, line)
    monkeypatch.setattr(Journal, '_write', flaky)
    world = World(Clock())
    assert go(config, world) == 'stopped_journal_primary_lost'
    fb = read_events(fs_of(config), 'fallback', fallback_name('r1'))
    assert fb[0]['event'] == 'primary_lost' and fb[-1]['status'] == 'stopped_journal_primary_lost'
    calls_at_stop = len(world.calls)
    assert calls_at_stop < 12


def test_sizing_modules_import_nothing_outside_stdlib_and_package():
    allowed_prefix = 'src.retrieval.sizing_v1'
    stdlib = set(sys.stdlib_module_names)
    for rel in CODE_FILES:
        tree = ast.parse((REPO / rel).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or '']
            else:
                continue
            for mod in mods:
                assert mod.startswith(allowed_prefix) or mod.split('.')[0] in stdlib, (rel, mod)


def test_code_identity_is_stable_and_sensitive(tmp_path):
    ident = code_identity(str(REPO))
    assert ident == code_identity(str(REPO)) and len(ident) == 64
    for rel in CODE_FILES:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((REPO / rel).read_bytes())
    assert code_identity(str(tmp_path)) == ident
    (tmp_path / CODE_FILES[1]).write_bytes((REPO / CODE_FILES[1]).read_bytes() + b'\n')
    assert code_identity(str(tmp_path)) != ident


def test_cli_readiness_lists_unmet_and_execute_is_refused(config, tmp_path, capsys):
    sys.path.insert(0, str(REPO / 'scripts' / 'retrieval'))
    import run_s_sizing_v1 as cli
    signed = tmp_path / 'RUN-S-SIGNED-invented.md'
    signed.write_text('invented signed copy\n')
    cfg = dict(config, signed_copy_sha256=hashlib.sha256(signed.read_bytes()).hexdigest(),
               tool_code_hash=code_identity(str(REPO)),
               s3_capacity_reading=dict(volume_uuid='UUID-INVENTED', free_bytes=1, headroom_floor_bytes=1))
    unmet = cli.readiness(cfg, str(signed))
    assert unmet == [cli.S1_BINDING_NOTE]
    assert 'executor must be named' in ' '.join(cli.readiness(dict(cfg, executor='Claude'), str(signed)))
    assert any('SHA-256' in u for u in cli.readiness(dict(cfg, signed_copy_sha256='0' * 64), str(signed)))
    path = tmp_path / 'cfg.json'
    path.write_text(json.dumps(cfg))
    assert cli.main(['--check', str(path), '--signed-copy', str(signed), '--execute']) == 2
    assert cli.main(['--check', str(path), '--signed-copy', str(signed)]) == 1
    out = capsys.readouterr().out
    assert '"ready": false' in out


def test_unexpected_exception_still_writes_a_final_status_and_allows_rerun(config):
    class Boom:
        def parse(self, periodic=None, **kwargs):
            raise RuntimeError('invented unexpected failure')
    world = World(Clock())
    status = run_sizing(config, transport=world, clock=world.clock, wall=lambda: 'x', volume=Volume(),
                        launcher=Boom(), run_id='r1', code_hash=CODE)
    assert status == 'stopped_internal_error'
    ev = events(config)
    charge = next(e for e in ev if e['event'] == 'parse_failed_charge')
    assert charge['decompressed_upper'] == 20 * len(world.bodies[BASELINE_SAMPLES[0]])
    assert plan_run(fs_of(config), SHA)[0] == 2


def test_volume_observation_failure_and_mid_run_mount_change_stop(config):
    class Flaky(Volume):
        def observe(self):
            if self.calls >= 2:
                raise OSError('invented: volume vanished')
            return super().observe()
    assert go(config, World(Clock()), Flaky()) == 'stopped_volume_check'
    config2 = dict(config, receipts_dir=config['receipts_dir'])
    world = World(Clock())
    assert go(config2, world, Volume({6: dict(mount='/Volumes/Other')}), run_id='r2') == 'stopped_volume_check'


def test_primary_loss_writes_no_payload_to_the_fallback(config, monkeypatch):
    real_write = Journal._write
    count = {'n': 0}

    def flaky(self, line):
        if not self.primary_lost:
            count['n'] += 1
            if count['n'] > 4:
                raise OSError('invented: external volume vanished')
        return real_write(self, line)
    monkeypatch.setattr(Journal, '_write', flaky)
    assert go(config, World(Clock())) == 'stopped_journal_primary_lost'
    assert os.listdir(config['fallback_dir']) == ['run-S-r1.fallback.jsonl']


def test_memory_cap_through_the_runner_with_the_live_launcher(config):
    from src.retrieval.sizing_v1.parser import WatchdogLauncher

    class Huge:
        def rss_bytes(self, pid):
            return 5 * GIB
    world = World(Clock())
    status = run_sizing(config, transport=world, clock=world.clock, wall=lambda: 'x', volume=Volume(),
                        launcher=WatchdogLauncher(probe=Huge(), poll=0.01), run_id='r1', code_hash=CODE)
    assert status == 'stopped_memory_cap'


def test_truncated_listing_stops_preflight(config):
    world = World(Clock())
    body = world.routes[('GET', UPD)][0]['body']
    world.routes[('GET', UPD)] = [dict(body=body.replace(b'</pre></body></html>', b''))]
    assert go(config, world) == 'stopped_preflight'


def test_two_hour_deadline_is_enforced(config):
    class Slow(Volume):
        def __init__(self, clock):
            super().__init__()
            self.clock = clock

        def observe(self):
            self.clock.t += 3000
            return super().observe()
    world = World(Clock())
    assert go(config, world, Slow(world.clock)) == 'stopped_time_cap'


def test_sample_larger_than_listed_size_stops(config):
    world = World(Clock(), sample_sizes={'pubmed26n0001.xml.gz': '10'})
    assert go(config, world) == 'stopped_size_allowance'


def test_rerun_redownloads_into_a_new_scratch_directory(config):
    world = World(Clock())
    world.fail_on[('GET', UPD + 'pubmed26n1341.xml.gz')] = Interrupted('invented')
    assert go(config, world, run_id='r1') == 'interrupted'
    world2 = World(Clock())
    assert go(config, world2, run_id='r2') == 'completed'
    assert ('GET', BASE + 'pubmed26n0001.xml.gz') in world2.calls
    assert sorted(os.listdir(config['scratch_root'])) == ['sizing-r1', 'sizing-r2']


def test_scratch_holds_only_samples_listings_and_sizing_partitions(config):
    assert go(config, World(Clock())) == 'completed'
    files = os.listdir(os.path.join(config['scratch_root'], 'sizing-r1'))
    allowed = ('.attempt1', '.attempt2', '.sizing.jsonl.gz', '.sizing.jsonl.gz.manifest.json')
    assert files and all(f.endswith(allowed) for f in files)
    assert not any('snapshot' in f or 'event-log' in f or 'final' in f for f in files)
    assert sum(f.endswith('.sizing.jsonl.gz') for f in files) == 5


def test_concurrent_run_is_refused_by_the_lock(config):
    from src.retrieval.sizing_v1.journal import RunLock
    lock = RunLock(fs_of(config), SHA)
    try:
        with pytest.raises(RunRefused):
            go(config, World(Clock()))
    finally:
        lock.release()


def test_run_id_and_fallback_location_are_confined(config, tmp_path):
    with pytest.raises(RunRefused):
        go(config, World(Clock()), run_id='../escape')
    repo = tmp_path / 'checkout'
    (repo / '.git').mkdir(parents=True)
    with pytest.raises(RunRefused):
        validate_config(dict(config, fallback_dir=str(repo / 'receipts')))
    with pytest.raises(RunRefused):
        validate_config(dict(config, mesh_name='../desc2026.xml'))
    with pytest.raises(RunRefused):
        validate_config(dict(config, headroom_floor_bytes='100'))


# -- sizing_v1.1 filesystem hook -------------------------------------------------------------------

import builtins  # noqa: E402
import threading  # noqa: E402


class GuardFs(PlainFs):
    """Test double: real PlainFs operations, recorded, with a flag the bypass detector honours."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.calls, self._local = [], threading.local()

    def _guarded(name):
        def method(self, *args, **kwargs):
            self.calls.append((name, args))
            self._local.inside = True
            try:
                return getattr(PlainFs, name)(self, *args, **kwargs)
            finally:
                self._local.inside = False
        return method

    for _n in ('mkdir_exclusive', 'create_exclusive', 'open_read', 'list', 'fsync_dir', 'lock',
               'remove_own_empty'):
        locals()[_n] = _guarded(_n)
    del _n

    def inside(self):
        return getattr(self._local, 'inside', False)


@pytest.fixture
def no_bypass(monkeypatch):
    """Any open/create/list/delete under an area root that does not come through GuardFs fails."""
    state = {}

    def install(fs):
        roots = [os.path.realpath(r) for r in fs.roots().values()]

        def under(path):
            try:
                p = os.path.realpath(os.fspath(path))
            except TypeError:
                return False                       # file descriptors, not paths
            return any(p == r or p.startswith(r + os.sep) for r in roots)

        def wrap(fn, label):
            def checked(path, *a, **k):
                if under(path) and not fs.inside():
                    raise AssertionError(f'filesystem hook bypassed: {label}({path!r})')
                return fn(path, *a, **k)
            return checked
        for mod, name in ((builtins, 'open'), (os, 'open'), (os, 'mkdir'), (os, 'unlink'), (os, 'remove'),
                          (os, 'listdir'), (os, 'scandir'), (os, 'rmdir')):
            monkeypatch.setattr(mod, name, wrap(getattr(mod, name), name))
        state['fs'] = fs
        return fs
    return install


def guard_fs(config):
    return GuardFs(config['scratch_root'], config['receipts_dir'], config['fallback_dir'])


@pytest.mark.parametrize('live_launcher', [False, True])
def test_every_area_read_and_write_goes_through_the_hook(config, no_bypass, live_launcher):
    from src.retrieval.sizing_v1.parser import WatchdogLauncher
    fs = no_bypass(guard_fs(config))
    world = World(Clock())
    launcher = WatchdogLauncher(poll=0.02) if live_launcher else InProcessLauncher()
    status = run_sizing(config, transport=world, clock=world.clock, wall=lambda: 'x', volume=Volume(),
                        launcher=launcher, run_id='r1', code_hash=CODE, fs=fs)
    assert status == 'completed'
    used = {c[0] for c in fs.calls}
    assert {'mkdir_exclusive', 'create_exclusive', 'open_read', 'list', 'fsync_dir', 'lock'} <= used
    created = [c[1] for c in fs.calls if c[0] == 'create_exclusive']
    assert ('receipts', 'run-S-r1.jsonl') in created
    assert sum(1 for area, rel in created if rel.endswith('.sizing.jsonl.gz')) == 5
    assert sum(1 for area, rel in created if rel.endswith('.manifest.json')) == 5


def test_fallback_journal_also_goes_through_the_hook(config, no_bypass, monkeypatch):
    fs = no_bypass(guard_fs(config))
    real_write = Journal._write
    count = {'n': 0}

    def flaky(self, line):
        if not self.primary_lost:
            count['n'] += 1
            if count['n'] > 4:
                raise OSError('invented: external volume vanished')
        return real_write(self, line)
    monkeypatch.setattr(Journal, '_write', flaky)
    world = World(Clock())
    status = run_sizing(config, transport=world, clock=world.clock, wall=lambda: 'x', volume=Volume(),
                        launcher=InProcessLauncher(), run_id='r1', code_hash=CODE, fs=fs)
    assert status == 'stopped_journal_primary_lost'
    assert ('fallback', 'run-S-r1.fallback.jsonl') in [c[1] for c in fs.calls if c[0] == 'create_exclusive']


def test_hook_roots_must_match_the_configuration(config, tmp_path):
    other = tmp_path / 'elsewhere'
    other.mkdir()
    fs = PlainFs(str(other), config['receipts_dir'], config['fallback_dir'])
    with pytest.raises(RunRefused):
        run_sizing(config, transport=World(Clock()), clock=Clock(), wall=lambda: 'x', volume=Volume(),
                   launcher=InProcessLauncher(), run_id='r1', code_hash=CODE, fs=fs)
    assert os.listdir(config['receipts_dir']) == []


def test_hook_failures_end_cleanly(config):
    from src.retrieval.sizing_v1.fsio import LockUnsupported

    class NoLock(PlainFs):
        def lock(self, area, rel):
            raise LockUnsupported('invented: flock not supported on this volume')

    class NoList(PlainFs):
        def list(self, area, prefix='', suffix=''):
            raise OSError('invented: listing denied')

    class NoCreate(PlainFs):
        def create_exclusive(self, area, rel):
            if rel.endswith('.attempt1'):
                raise PermissionError('invented: write denied by the lease')
            return super().create_exclusive(area, rel)

    args = (config['scratch_root'], config['receipts_dir'], config['fallback_dir'])
    for cls, needle in ((NoLock, 'not supported'), (NoList, 'cannot be listed')):
        with pytest.raises(RunRefused) as exc:
            run_sizing(config, transport=World(Clock()), clock=Clock(), wall=lambda: 'x', volume=Volume(),
                       launcher=InProcessLauncher(), run_id='r1', code_hash=CODE, fs=cls(*args))
        assert needle in str(exc.value)
    world = World(Clock())
    status = run_sizing(config, transport=world, clock=world.clock, wall=lambda: 'x', volume=Volume(),
                        launcher=InProcessLauncher(), run_id='r1', code_hash=CODE, fs=NoCreate(*args))
    assert status == 'stopped_scratch_write_failed'


def test_relative_names_cannot_escape_their_area(config):
    from src.retrieval.sizing_v1.fsio import check_rel
    for bad in ('../x', 'a/b', 'sizing-r1/../x', '/abs', '', '.hidden', 'sizing-r1/a/b'):
        with pytest.raises(ValueError):
            check_rel(bad)
    assert check_rel('sizing-r1/pubmed26n0001.xml.gz.attempt1') == ['sizing-r1', 'pubmed26n0001.xml.gz.attempt1']


def test_non_oserror_hook_failure_on_journal_write_still_ends_with_a_final_status(config):
    class LeaseError(Exception):
        pass

    class LeaseLost(PlainFs):
        armed = False

        def create_exclusive(self, area, rel):
            fh = super().create_exclusive(area, rel)
            if area != 'receipts':
                return fh
            outer = self

            class Guarded:
                def __init__(self):
                    self.n = 0

                def write(self, data):
                    self.n += 1
                    if self.n > 3:
                        raise LeaseError('invented: lease revoked')
                    return fh.write(data)

                def __getattr__(self, name):
                    return getattr(fh, name)

                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    fh.close()
            outer.armed = True
            return Guarded()
    fs = LeaseLost(config['scratch_root'], config['receipts_dir'], config['fallback_dir'])
    world = World(Clock())
    status = run_sizing(config, transport=world, clock=world.clock, wall=lambda: 'x', volume=Volume(),
                        launcher=InProcessLauncher(), run_id='r1', code_hash=CODE, fs=fs)
    assert status == 'stopped_journal_primary_lost'
    fb = read_events(fs_of(config), 'fallback', fallback_name('r1'))
    assert fb[0]['error'].startswith('LeaseError') and fb[-1]['status'] == 'stopped_journal_primary_lost'


def test_child_rewinds_a_source_a_hook_has_read_ahead(config):
    from src.retrieval.sizing_v1.parser import WatchdogLauncher

    class ReadAhead(PlainFs):
        def open_read(self, area, rel):
            fh = super().open_read(area, rel)
            if rel.endswith('.xml.gz.attempt1'):
                fh.read(2)                         # e.g. a magic-byte check inside a guarded hook
            return fh
    fs = ReadAhead(config['scratch_root'], config['receipts_dir'], config['fallback_dir'])
    world = World(Clock())
    status = run_sizing(config, transport=world, clock=world.clock, wall=lambda: 'x', volume=Volume(),
                        launcher=WatchdogLauncher(poll=0.02), run_id='r1', code_hash=CODE, fs=fs)
    assert status == 'completed'


def test_remove_own_empty_only_removes_the_file_this_run_created(config):
    fs = fs_of(config)
    fh = fs.create_exclusive('receipts', 'mine.jsonl')
    other = fs.create_exclusive('receipts', 'other.jsonl')
    with pytest.raises(ValueError):
        fs.remove_own_empty('receipts', 'other.jsonl', fh)      # different inode
    fs.remove_own_empty('receipts', 'mine.jsonl', fh)
    assert not os.path.exists(os.path.join(config['receipts_dir'], 'mine.jsonl'))
    other.write(b'x')
    other.flush()
    with pytest.raises(ValueError):
        fs.remove_own_empty('receipts', 'other.jsonl', other)  # not empty
    fh.close()
    other.close()
