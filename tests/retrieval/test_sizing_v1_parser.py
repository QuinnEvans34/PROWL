"""Sizing-only parser: XML safety, expansion/scratch guards, output format, watchdog (invented data)."""
import gzip
import json
import os
import socket
import sys
import time
import zlib
from pathlib import Path

import pytest

from src.retrieval.sizing_v1 import (GIB, CapExceeded, ParserGuard, SizingOnlyRefused, UnexpectedFile)
from src.retrieval.sizing_v1 import parser as P

pytestmark = pytest.mark.component
FIX = Path(__file__).parent / 'fixtures' / 'sizing_v1'


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def deny(*a, **k):
        raise AssertionError('network denied in sizing_v1 tests')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(socket, 'getaddrinfo', deny)


def gz_fixture(tmp_path, name, data=None):
    raw = data if data is not None else (FIX / name).read_bytes()
    path = tmp_path / (name + '.gz')
    path.write_bytes(gzip.compress(raw, mtime=0))
    return path


def run(tmp_path, src, out_name='out.jsonl.gz', allowance=GIB, limit=20, chunk=P.CHUNK):
    out = tmp_path / out_name
    return P.parse_file(str(src), str(out), source_file=src.name, compressed_size=os.path.getsize(src),
                        scratch_allowance=allowance, seconds_left=60, expansion_limit=limit, chunk=chunk), out


def rows(out):
    with gzip.open(out, 'rt', encoding='utf-8') as fh:
        return [json.loads(line) for line in fh]


def test_pubmed_style_doctype_parses_without_fetch_and_extracts_fields(tmp_path):
    m, out = run(tmp_path, gz_fixture(tmp_path, 'pubmed_style_doctype.xml'))
    assert m['records'] == 4 and m['deletes'] == 0
    assert m['doctype']['system_id'].endswith('pubmed_250101.dtd')
    got = rows(out)
    assert all(r['sizing_only'] is True and r['partition_format'] == P.PARTITION_FORMAT for r in got)
    first = got[0]
    assert first['pmid'] == '900000001' and first['pmid_version'] == '1' and first['event'] == 'add_or_replace'
    f = first['fields']
    assert set(f) == set(P.ARTICLE_FIELDS)
    assert f['title'] == 'An invented study of synthetic lesion outlines & reader timing.'
    assert f['abstract'][0] == dict(label='PURPOSE', text='Invented purpose text for a fixture.')
    assert '²' in f['abstract'][1]['text'] and '<5%' in f['abstract'][1]['text']
    assert f['pub_year'] == 2019 and f['doi'] == '10.0000/invented.0001' and f['pmcid'] == 'PMC9000001'
    assert f['mesh'][0] == dict(ui='D900001', name='Invented Organ', major=True,
                                qualifiers=[dict(ui='Q900001', name='invented imaging', major=False)])
    assert f['date_revised'] == '2026-01-15' and f['keywords'] == ['invented keyword']
    assert got[1]['fields']['pub_year'] == 2008 and got[1]['fields']['languages'] == ['eng', 'fre']
    assert got[1]['pmid_version'] == '2'
    assert got[3]['record_kind'] == 'book' and got[3]['pmid'] == '900000004'
    assert m['observed_years'] == {'2019': 1, '2008': 1, '2025': 1, 'unknown': 1}


def test_deletes_counted_as_local_events(tmp_path):
    m, out = run(tmp_path, gz_fixture(tmp_path, 'update_with_deletes.xml'))
    got = rows(out)
    assert m['records'] == 1 and m['deletes'] == 2
    assert [r['event'] for r in got] == ['add_or_replace', 'delete', 'delete']
    assert [r['seq'] for r in got] == [0, 1, 2] and got[1]['fields'] is None


@pytest.mark.parametrize('name,reason', [('external_entity.xml', 'xml_guard'), ('billion_laughs.xml', 'xml_guard'),
                                         ('internal_entity.xml', 'xml_guard'), ('undeclared_entity.xml', 'xml_guard'),
                                         ('malformed.xml', 'malformed_xml')])
def test_xml_guards_refuse(tmp_path, name, reason):
    with pytest.raises(ParserGuard) as exc:
        run(tmp_path, gz_fixture(tmp_path, name))
    assert exc.value.reason == reason


def test_wrong_root_refused(tmp_path):
    with pytest.raises(UnexpectedFile):
        run(tmp_path, gz_fixture(tmp_path, 'wrong_root.xml'))


def test_truncated_and_corrupt_gzip_refused(tmp_path):
    good = gz_fixture(tmp_path, 'pubmed_style_doctype.xml').read_bytes()
    trunc = tmp_path / 'trunc.xml.gz'
    trunc.write_bytes(good[:len(good) // 2])
    with pytest.raises(ParserGuard) as exc:
        run(tmp_path, trunc, 'o1')
    assert exc.value.reason == 'malformed_xml'
    bad = tmp_path / 'bad.xml.gz'
    bad.write_bytes(good[:10] + b'\x00' * 40 + good[50:])
    with pytest.raises(ParserGuard):
        run(tmp_path, bad, 'o2')


def test_expansion_guard_boundary(tmp_path):
    padding = b'<!--' + b' ' * 400000 + b'-->'
    raw = (FIX / 'update_with_deletes.xml').read_bytes().replace(b'<PubmedArticleSet>', b'<PubmedArticleSet>' + padding)
    src = gz_fixture(tmp_path, 'padded.xml', raw)
    ratio = len(raw) / os.path.getsize(src)
    assert ratio > 20
    with pytest.raises(ParserGuard) as exc:
        run(tmp_path, src, 'o1', limit=20)
    assert exc.value.reason == 'expansion_guard'
    m, _ = run(tmp_path, src, 'o2', limit=int(ratio) + 1)
    assert m['decompressed_bytes'] == len(raw)


def test_scratch_allowance_counts_decompressed_and_output(tmp_path):
    src = gz_fixture(tmp_path, 'pubmed_style_doctype.xml')
    m, _ = run(tmp_path, src, 'o1')
    assert m['scratch_charged'] == m['decompressed_bytes'] + m['output_bytes'] + m['manifest_bytes']
    with pytest.raises(CapExceeded) as exc:
        run(tmp_path, src, 'o2', allowance=m['decompressed_bytes'] + 10)
    assert exc.value.reason == 'scratch_cap'


def test_streaming_chunks_and_multi_member_give_same_output(tmp_path):
    raw = (FIX / 'pubmed_style_doctype.xml').read_bytes()
    src = gz_fixture(tmp_path, 'doc.xml', raw)
    m1, o1 = run(tmp_path, src, 'o1')
    m2, o2 = run(tmp_path, src, 'o2', chunk=7)
    assert o1.read_bytes() == o2.read_bytes()      # deterministic: gzip mtime 0, sorted keys
    half = len(raw) // 2
    multi = tmp_path / 'multi.xml.gz'
    multi.write_bytes(gzip.compress(raw[:half], mtime=0) + gzip.compress(raw[half:], mtime=0))
    m3, o3 = run(tmp_path, multi, 'o3')
    assert [(r['pmid'], r['fields']) for r in rows(o3)] == [(r['pmid'], r['fields']) for r in rows(o1)]
    assert m3['records'] == m1['records']


def test_output_and_manifest_are_marked_and_refused_by_consumers(tmp_path):
    m, out = run(tmp_path, gz_fixture(tmp_path, 'pubmed_style_doctype.xml'))
    manifest = json.loads((tmp_path / 'out.jsonl.gz.manifest.json').read_text())
    assert manifest['sizing_only'] is True and manifest['rows'] == m['rows']
    with pytest.raises(SizingOnlyRefused):
        P.load_partition_for_consumer(str(out))
    with pytest.raises(SizingOnlyRefused):
        P.refuse_sizing_only({'pmid': '900000001'})           # unmarked is refused too (fail closed)
    assert P.refuse_sizing_only({'sizing_only': False}) == {'sizing_only': False}


def test_exclusive_output_creation(tmp_path):
    (tmp_path / 'out.jsonl.gz').write_bytes(b'existing')
    with pytest.raises(CapExceeded) as exc:
        run(tmp_path, gz_fixture(tmp_path, 'pubmed_style_doctype.xml'))
    assert exc.value.reason == 'scratch_collision'


def test_old_expat_refused(monkeypatch):
    monkeypatch.setattr(P.pyexpat, 'version_info', (2, 4, 0))
    with pytest.raises(ParserGuard):
        P.check_expat()


class FixedProbe:
    def __init__(self, value=None, error=None):
        self.value, self.error, self.calls = value, error, 0

    def rss_bytes(self, pid):
        self.calls += 1
        if self.error:
            raise self.error
        return self.value


SLEEPER = [sys.executable, '-c', 'import time; time.sleep(30)']


def test_watchdog_kills_child_above_memory_cap():
    with pytest.raises(ParserGuard) as exc:
        P.run_with_watchdog(SLEEPER, probe=FixedProbe(5 * GIB), memory_cap=4 * GIB, poll=0.01, seconds_left=20)
    assert exc.value.reason == 'memory_cap'


def test_watchdog_monitor_failure_denies():
    with pytest.raises(ParserGuard) as exc:
        P.run_with_watchdog(SLEEPER, probe=FixedProbe(error=OSError('invented ps failure')), poll=0.01,
                            seconds_left=20)
    assert exc.value.reason == 'memory_monitor'


def test_watchdog_time_limit():
    with pytest.raises(CapExceeded) as exc:
        P.run_with_watchdog(SLEEPER, probe=FixedProbe(1), poll=0.01, seconds_left=0.05)
    assert exc.value.reason == 'time_cap'


def test_watchdog_launcher_parses_in_child_with_real_probe(tmp_path):
    src = gz_fixture(tmp_path, 'pubmed_style_doctype.xml')
    launcher = P.WatchdogLauncher(poll=0.05)
    with open(src, 'rb') as s_fh, open(tmp_path / 'child.jsonl.gz', 'xb') as o_fh:
        m = launcher.parse(src=s_fh, out=o_fh, source_file=src.name, compressed_size=os.path.getsize(src),
                           scratch_allowance=GIB, seconds_left=30, expansion_limit=20)
    assert m['records'] == 4 and m['peak_rss_polled'] >= 0
    assert os.path.getsize(tmp_path / 'child.jsonl.gz') == m['output_bytes']
    assert [r['pmid'] for r in rows(tmp_path / 'child.jsonl.gz')][:2] == ['900000001', '900000002']

def test_watchdog_launcher_propagates_child_guard(tmp_path):
    src = gz_fixture(tmp_path, 'billion_laughs.xml')
    with open(src, 'rb') as s_fh, open(tmp_path / 'c.jsonl.gz', 'xb') as o_fh:
        with pytest.raises(ParserGuard) as exc:
            P.WatchdogLauncher(poll=0.05).parse(src=s_fh, out=o_fh, source_file=src.name,
                                                compressed_size=os.path.getsize(src), scratch_allowance=GIB,
                                                seconds_left=30, expansion_limit=20)
    assert exc.value.reason == 'xml_guard'

def test_zlib_wbits_is_gzip_only(tmp_path):
    raw_deflate = tmp_path / 'raw.xml.gz'
    raw_deflate.write_bytes(zlib.compress((FIX / 'update_with_deletes.xml').read_bytes()))
    with pytest.raises(ParserGuard):
        run(tmp_path, raw_deflate)


def test_watchdog_no_reading_for_live_child_fails_closed():
    probe = FixedProbe(None)
    with pytest.raises(ParserGuard) as exc:
        P.run_with_watchdog(SLEEPER, probe=probe, poll=0.01, seconds_left=20)
    assert exc.value.reason == 'memory_monitor' and probe.calls == P.MAX_MISSING_READINGS + 1


def test_watchdog_tolerates_a_brief_gap_then_resumes():
    class Gappy:
        def __init__(self):
            self.n = 0

        def rss_bytes(self, pid):
            self.n += 1
            return None if self.n <= P.MAX_MISSING_READINGS else 5 * GIB
    with pytest.raises(ParserGuard) as exc:
        P.run_with_watchdog(SLEEPER, probe=Gappy(), memory_cap=4 * GIB, poll=0.01, seconds_left=20)
    assert exc.value.reason == 'memory_cap'


def test_watchdog_runs_periodic_volume_check_and_stops_on_failure():
    from src.retrieval.sizing_v1 import VolumeCheckFailed
    calls = []

    def periodic():
        calls.append(1)
        raise VolumeCheckFailed('invented mount loss during parse')
    with pytest.raises(VolumeCheckFailed):
        P.run_with_watchdog(SLEEPER, probe=FixedProbe(1), poll=0.01, seconds_left=20, periodic=periodic,
                            check_interval=0.02)
    assert calls == [1]


def test_noisy_child_stderr_cannot_block_the_watchdog():
    noisy = [sys.executable, '-c', 'import sys; sys.stderr.write("x" * 300000); print("{}")']
    rc, out, err, _ = P.run_with_watchdog(noisy, probe=P.PsMemoryProbe(), poll=0.01, seconds_left=20)
    assert rc == 0 and len(err) == P.DIAG_STDERR_TAIL and out.strip() == b'{}'


def test_child_crash_reports_parser_failed_with_file(tmp_path):
    src = gz_fixture(tmp_path, 'pubmed_style_doctype.xml')
    (tmp_path / 'readonly.out').write_bytes(b'')
    with open(src, 'rb') as s_fh, open(tmp_path / 'readonly.out', 'rb') as o_fh:   # unwritable output fd
        with pytest.raises(ParserGuard) as exc:
            P.WatchdogLauncher(poll=0.05).parse(src=s_fh, out=o_fh, source_file=src.name,
                                                compressed_size=os.path.getsize(src), scratch_allowance=GIB,
                                                seconds_left=30, expansion_limit=20)
    assert exc.value.reason == 'parser_failed' and exc.value.detail['source_file'] == src.name

def test_child_malformed_xml_names_the_file(tmp_path):
    src = gz_fixture(tmp_path, 'malformed.xml')
    with open(src, 'rb') as s_fh, open(tmp_path / 'm.jsonl.gz', 'xb') as o_fh:
        with pytest.raises(ParserGuard) as exc:
            P.WatchdogLauncher(poll=0.05).parse(src=s_fh, out=o_fh, source_file='pubmed26n0667.xml.gz',
                                                compressed_size=os.path.getsize(src), scratch_allowance=GIB,
                                                seconds_left=30, expansion_limit=20)
    assert exc.value.reason == 'malformed_xml' and exc.value.detail['source_file'] == 'pubmed26n0667.xml.gz'

def test_refuse_sizing_only_rejects_uncheckable_inputs():
    for bad in (({'sizing_only': False},), (x for x in [{'sizing_only': False}]), ['row'], None, 'text'):
        with pytest.raises(SizingOnlyRefused):
            P.refuse_sizing_only(bad)
    assert P.refuse_sizing_only([{'sizing_only': False}]) == [{'sizing_only': False}]


def test_non_ascii_digit_year_does_not_crash(tmp_path):
    raw = (FIX / 'pubmed_style_doctype.xml').read_bytes().replace(b'<Year>2025</Year>', '<Year>²</Year>'.encode())
    m, out = run(tmp_path, gz_fixture(tmp_path, 'odd_year.xml', raw))
    assert rows(out)[2]['fields']['pub_year'] is None and m['records'] == 4


def test_child_receives_descriptors_not_paths(tmp_path, monkeypatch):
    seen = {}
    real = P.run_with_watchdog

    def spy(argv, **kw):
        seen['argv'], seen['pass_fds'] = argv, kw.get('pass_fds')
        return real(argv, **kw)
    monkeypatch.setattr(P, 'run_with_watchdog', spy)
    src = gz_fixture(tmp_path, 'update_with_deletes.xml')
    with open(src, 'rb') as s_fh, open(tmp_path / 'fd.jsonl.gz', 'xb') as o_fh:
        P.WatchdogLauncher(poll=0.05).parse(src=s_fh, out=o_fh, source_file='invented.xml.gz',
                                            compressed_size=os.path.getsize(src), scratch_allowance=GIB,
                                            seconds_left=30, expansion_limit=20)
        fds = (s_fh.fileno(), o_fh.fileno())
    args = json.loads(seen['argv'][-1])
    assert seen['pass_fds'] == fds and (args['src_fd'], args['out_fd']) == fds
    assert not any(str(tmp_path) in a for a in seen['argv'])
    assert not any(isinstance(v, str) and os.sep in v for v in args.values())


def test_handover_rejects_non_regular_nonempty_or_identical_descriptors(tmp_path):
    from src.retrieval.sizing_v1 import UnexpectedFile
    src = gz_fixture(tmp_path, 'update_with_deletes.xml')
    full = tmp_path / 'full.out'
    full.write_bytes(b'already here')
    r, w = os.pipe()
    try:
        with open(src, 'rb') as s_fh, open(full, 'r+b') as f_fh, open(tmp_path / 'e.out', 'xb') as e_fh:
            with pytest.raises(UnexpectedFile):
                P.check_handover_fds(s_fh.fileno(), f_fh.fileno())        # output not empty
            with pytest.raises(UnexpectedFile):
                P.check_handover_fds(r, e_fh.fileno())                    # source is a pipe
            with pytest.raises(UnexpectedFile):
                P.check_handover_fds(e_fh.fileno(), e_fh.fileno())        # same file
            s_fh.read(5)
            P.check_handover_fds(s_fh.fileno(), e_fh.fileno())
            assert os.lseek(s_fh.fileno(), 0, os.SEEK_CUR) == 0
    finally:
        os.close(r)
        os.close(w)


def _open_fds():
    return set(os.listdir('/dev/fd'))


@pytest.mark.parametrize('stream', ['stdout', 'stderr'])
def test_diagnostics_overflow_stops_and_reaps_the_child(stream):
    code = f'import sys, time; sys.{stream}.buffer.write(b"x" * (2 * 1024 * 1024)); sys.{stream}.flush(); time.sleep(30)'
    before = _open_fds()
    t0 = time.monotonic()
    with pytest.raises(ParserGuard) as exc:
        P.run_with_watchdog([sys.executable, '-c', code], probe=FixedProbe(1), poll=0.01, seconds_left=20)
    assert exc.value.reason == 'diagnostics_overflow' and time.monotonic() - t0 < 10
    assert _open_fds() <= before | {'3'}                     # no leaked pipe descriptors


def test_overflow_after_exit_is_still_a_failed_parse():
    code = 'import sys; sys.stderr.buffer.write(b"y" * (2 * 1024 * 1024))'
    with pytest.raises(ParserGuard) as exc:
        P.run_with_watchdog([sys.executable, '-c', code], probe=P.PsMemoryProbe(), poll=0.01, seconds_left=20)
    assert exc.value.reason == 'diagnostics_overflow'


def test_checks_stay_active_under_pipe_pressure():
    code = ('import sys, time\n'
            'for _ in range(200):\n'
            '    sys.stdout.buffer.write(b"o" * 4096); sys.stderr.buffer.write(b"e" * 4096)\n'
            '    sys.stdout.flush(); sys.stderr.flush(); time.sleep(0.01)\n'
            'time.sleep(30)\n')
    calls = []

    def periodic():
        calls.append(1)
        raise VolumeCheckFailed('invented mount loss under pipe pressure')
    from src.retrieval.sizing_v1 import VolumeCheckFailed
    t0 = time.monotonic()
    with pytest.raises(VolumeCheckFailed):
        P.run_with_watchdog([sys.executable, '-c', code], probe=FixedProbe(1), poll=0.01, seconds_left=20,
                            periodic=periodic, check_interval=0.3)
    assert calls == [1] and time.monotonic() - t0 < 10
    with pytest.raises(ParserGuard) as exc:
        P.run_with_watchdog([sys.executable, '-c', code], probe=FixedProbe(5 * GIB), poll=0.01, seconds_left=20)
    assert exc.value.reason == 'memory_cap'


def test_no_diagnostic_file_is_created(monkeypatch):
    import tempfile

    def refuse(*a, **k):
        raise AssertionError('no temporary diagnostic file may be created')
    monkeypatch.setattr(tempfile, 'TemporaryFile', refuse)
    monkeypatch.setattr(tempfile, 'NamedTemporaryFile', refuse)
    monkeypatch.setattr(tempfile, 'mkstemp', refuse)
    code = 'import sys; sys.stderr.write("diag" * 10); print("{}")'
    rc, out, err, _ = P.run_with_watchdog([sys.executable, '-c', code], probe=P.PsMemoryProbe(), poll=0.01,
                                          seconds_left=20)
    assert rc == 0 and err == b'diag' * 10


def test_descriptors_closed_after_each_exit_path():
    before = _open_fds()
    P.run_with_watchdog([sys.executable, '-c', 'print("{}")'], probe=P.PsMemoryProbe(), poll=0.01, seconds_left=20)
    with pytest.raises(ParserGuard):
        P.run_with_watchdog(SLEEPER, probe=FixedProbe(5 * GIB), poll=0.01, seconds_left=20)
    with pytest.raises(CapExceeded):
        P.run_with_watchdog(SLEEPER, probe=FixedProbe(1), poll=0.01, seconds_left=0.05)
    assert _open_fds() <= before | {'3'}


def test_failed_child_writes_no_manifest_through_the_launcher(tmp_path):
    src = gz_fixture(tmp_path, 'malformed.xml')
    with open(src, 'rb') as s_fh, open(tmp_path / 'nm.jsonl.gz', 'xb') as o_fh:
        with pytest.raises(ParserGuard):
            P.WatchdogLauncher(poll=0.02).parse(src=s_fh, out=o_fh, source_file='x.xml.gz',
                                                compressed_size=os.path.getsize(src), scratch_allowance=GIB,
                                                seconds_left=30, expansion_limit=20)
    assert not (tmp_path / 'nm.jsonl.gz.manifest.json').exists()


def test_grandchild_holding_pipes_is_killed_and_no_drain_thread_survives(tmp_path):
    import threading
    code = ('import subprocess, sys\n'
            'g = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])\n'
            'print(g.pid, flush=True)\n')
    t0 = time.monotonic()
    rc, out, err, _ = P.run_with_watchdog([sys.executable, '-c', code], probe=P.PsMemoryProbe(), poll=0.01,
                                          seconds_left=20)
    assert rc == 0 and time.monotonic() - t0 < 8
    gpid = int(out.split()[0])
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(gpid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        pytest.fail('grandchild survived the parse')
    assert not [t for t in threading.enumerate() if t.name == 'run-s-diag-drain' and t.is_alive()]
    probe_file = tmp_path / 'unrelated.bin'
    probe_file.write_bytes(b'z' * 200000)
    with open(probe_file, 'rb') as fh:                 # a reused descriptor number is not read by anyone
        time.sleep(0.3)
        assert len(fh.read()) == 200000


def test_stderr_tail_keeps_updating_after_overflow():
    import threading
    r, w = os.pipe()
    reader = os.fdopen(r, 'rb')

    def write():
        with os.fdopen(w, 'wb') as fh:
            fh.write(b'a' * (2 * 1024 * 1024))
            fh.write(b'END-OF-STREAM')
    th = threading.Thread(target=write)
    th.start()
    drain = P._BoundedDrain(reader, P.DIAG_STREAM_LIMIT, P.DIAG_STDERR_TAIL)
    th.join(10)
    drain.thread.join(10)
    assert reader.closed and not drain.thread.is_alive()
    assert drain.overflow and drain.total == 2 * 1024 * 1024 + 13
    assert len(drain.data()) == P.DIAG_STDERR_TAIL and drain.data().endswith(b'END-OF-STREAM')


def test_child_stops_when_the_watchdog_parent_is_gone(tmp_path, monkeypatch):
    monkeypatch.setattr(P, '_PARENT_PID', os.getppid() + 999999)      # simulate a re-parented child
    with pytest.raises(ParserGuard) as exc:
        run(tmp_path, gz_fixture(tmp_path, 'pubmed_style_doctype.xml'))
    assert exc.value.reason == 'parent_lost'


def test_group_kill_happens_once_and_only_before_reaping(monkeypatch):
    calls, anchors = [], []
    real_killpg, real_anchor = os.killpg, P._GroupAnchor

    def spy(pgid, sig):
        calls.append(pgid)
        assert anchors and anchors[-1].proc.returncode is None   # anchor unreaped: the group ID is pinned
        return real_killpg(pgid, sig)

    class Spy(real_anchor):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            anchors.append(self)
    monkeypatch.setattr(os, 'killpg', spy)
    monkeypatch.setattr(P, '_GroupAnchor', Spy)
    P.run_with_watchdog([sys.executable, '-c', 'print("{}")'], probe=P.PsMemoryProbe(), poll=0.01, seconds_left=20)
    assert calls == [anchors[-1].pgid] and anchors[-1].proc.returncode is not None
    calls.clear()
    with pytest.raises(ParserGuard):
        P.run_with_watchdog(SLEEPER, probe=FixedProbe(5 * GIB), poll=0.01, seconds_left=20)
    assert calls == [anchors[-1].pgid] and anchors[-1].proc.returncode is not None

def test_cleanup_works_without_os_waitid_as_on_macos(tmp_path, monkeypatch):
    monkeypatch.delattr(os, 'waitid', raising=False)            # native macOS Python has no os.waitid
    test_grandchild_holding_pipes_is_killed_and_no_drain_thread_survives(tmp_path)


def test_parser_child_and_grandchild_share_the_anchor_group(monkeypatch):
    anchors = []
    real_anchor = P._GroupAnchor

    class Spy(real_anchor):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            anchors.append(self)
    monkeypatch.setattr(P, '_GroupAnchor', Spy)
    code = ('import os, subprocess, sys\n'
            'g = subprocess.Popen([sys.executable, "-c", "import os; print(os.getpgid(0), flush=True)"],'
            ' stdout=subprocess.PIPE)\n'
            'print(os.getpgid(0), g.communicate()[0].decode().strip(), flush=True)\n')
    rc, out, err, _ = P.run_with_watchdog([sys.executable, '-c', code], probe=P.PsMemoryProbe(), poll=0.01,
                                          seconds_left=20)
    child_pgid, grandchild_pgid = (int(x) for x in out.split())
    assert rc == 0 and child_pgid == grandchild_pgid == anchors[-1].pgid != os.getpgid(0)


def test_launch_failure_cleans_up_the_anchor(monkeypatch):
    anchors = []
    real_anchor = P._GroupAnchor

    class Spy(real_anchor):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            anchors.append(self)
    monkeypatch.setattr(P, '_GroupAnchor', Spy)
    with pytest.raises(OSError):
        P.run_with_watchdog(['/nonexistent/invented-binary'], probe=FixedProbe(1), poll=0.01, seconds_left=5)
    assert anchors[-1].proc.returncode is not None


def test_hard_killed_parent_leaves_no_unwatched_parser(tmp_path):
    import signal as sig
    import subprocess
    helper = tmp_path / 'helper.py'
    pidfile = tmp_path / 'child.pid'
    helper.write_text(
        'import sys, time\n'
        f'sys.path.insert(0, {str(P.REPO_ROOT)!r})\n'
        'from src.retrieval.sizing_v1 import parser as P\n'
        'class Probe:\n'
        '    def rss_bytes(self, pid):\n'
        f'        open({str(pidfile)!r}, "w").write(str(pid)); return 1\n'
        'P.run_with_watchdog([sys.executable, "-c", "import time; time.sleep(60)"], probe=Probe(), poll=0.05,'
        ' seconds_left=60)\n')
    h = subprocess.Popen([sys.executable, str(helper)])
    try:
        deadline = time.monotonic() + 10
        while not (pidfile.exists() and pidfile.read_text()) and time.monotonic() < deadline:
            time.sleep(0.05)
        child = int(pidfile.read_text())
        os.kill(h.pid, sig.SIGKILL)                       # hard kill: no finally block runs in the parent
        h.wait(10)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            pytest.fail('parser child outlived its hard-killed parent')
    finally:
        if h.poll() is None:
            h.kill()
            h.wait(10)
