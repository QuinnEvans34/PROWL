"""Run S journal: exclusive durable append, fallback, terminal status, prior-run proof (invented)."""
import json
import os
import socket

import pytest

from src.retrieval.sizing_v1 import JournalError, RunRefused
from src.retrieval.sizing_v1.fsio import PlainFs
from src.retrieval.sizing_v1.journal import (Journal, JournalUnwritable, fallback_name, plan_run, primary_name,
                                             prior_runs, read_events)

pytestmark = pytest.mark.failure_injection
SHA = 'a' * 64


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def deny(*a, **k):
        raise AssertionError('network denied in sizing_v1 tests')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(socket, 'getaddrinfo', deny)


@pytest.fixture
def dirs(tmp_path):
    receipts, fallback, scratch = tmp_path / 'receipts', tmp_path / 'internal-fallback', tmp_path / 'scratch'
    for d in (receipts, fallback, scratch):
        d.mkdir()

    class Env:
        pass
    env = Env()
    env.receipts, env.fallback, env.scratch = str(receipts), str(fallback), str(scratch)
    env.fs = PlainFs(env.scratch, env.receipts, env.fallback)
    return env


def wall():
    return '2026-10-03T00:00:00Z'


def finished(dirs, run_id, status='completed', net=10, scr=20, sha=SHA):
    j = Journal(dirs.fs, run_id, sha, wall)
    j.append('start', counters=dict(network_used=0, scratch_used=0))
    j.final(status, counters=dict(network_used=net, scratch_used=scr))
    j.close()
    return j


class BrokenFile:
    def write(self, s):
        raise OSError('invented: primary volume unwritable')

    def flush(self):
        pass

    def fileno(self):
        raise OSError('gone')

    def close(self):
        pass


def test_exclusive_create_and_ordered_durable_events(dirs):
    j = Journal(dirs.fs, 'r1', SHA, wall)
    j.append('start')
    j.append('volume_check', ok=True)
    j.final('completed', counters=dict(network_used=1, scratch_used=2))
    j.close()
    events = read_events(dirs.fs, 'receipts', primary_name('r1'))
    assert [e['event'] for e in events] == ['start', 'volume_check', 'final']
    assert [e['seq'] for e in events] == [0, 1, 2]
    with pytest.raises(RunRefused):
        Journal(dirs.fs, 'r1', SHA, wall)


def test_exactly_one_final_and_valid_statuses(dirs):
    j = Journal(dirs.fs, 'r1', SHA, wall)
    with pytest.raises(ValueError):
        j.final('done')
    with pytest.raises(ValueError):
        j.final('stopped_')
    j.final('stopped_network_cap', counters={})
    with pytest.raises(JournalError):
        j.final('completed')
    with pytest.raises(JournalError):
        j.append('late_event')


def test_primary_failure_moves_remaining_events_to_fallback_and_stops(dirs):
    j = Journal(dirs.fs, 'r1', SHA, wall)
    j.append('start')
    j._fh = BrokenFile()
    with pytest.raises(JournalError) as exc:
        j.append('file_start', name='invented.xml.gz')
    assert exc.value.reason == 'journal_primary_lost'
    j.final('stopped_journal_primary_lost', counters=dict(network_used=5, scratch_used=6))
    j.close()
    fb = read_events(dirs.fs, 'fallback', fallback_name('r1'))
    assert [e['event'] for e in fb] == ['primary_lost', 'file_start', 'final']
    runs = prior_runs(dirs.fs, SHA)
    assert runs[0]['status'] == 'stopped_journal_primary_lost' and runs[0]['counters']['network_used'] == 5


def test_fallback_failure_leaves_run_incomplete(dirs, monkeypatch):
    j = Journal(dirs.fs, 'r1', SHA, wall)
    j.append('start')
    j._fh = BrokenFile()
    os.chmod(dirs.fallback, 0o500)
    try:
        if os.access(dirs.fallback, os.W_OK):
            pytest.skip('running with privileges that ignore directory permissions')
        with pytest.raises(JournalUnwritable):
            j.append('file_start')
    finally:
        os.chmod(dirs.fallback, 0o700)
    with pytest.raises(RunRefused):
        plan_run(dirs.fs, SHA)          # primary has no final: incomplete, re-run refused


def test_fallback_failure_via_injected_write(dirs, monkeypatch):
    j = Journal(dirs.fs, 'r1', SHA, wall)
    j.append('start')
    j._fh = BrokenFile()
    real_open = open

    def failing_open(path, mode='r', *a, **k):
        if 'fallback' in str(path) and 'x' in mode:
            raise OSError('invented: internal disk unavailable')
        return real_open(path, mode, *a, **k)
    monkeypatch.setattr('builtins.open', failing_open)
    with pytest.raises(JournalUnwritable):
        j.append('file_start')
    monkeypatch.setattr('builtins.open', real_open)
    with pytest.raises(RunRefused):
        plan_run(dirs.fs, SHA)          # no final status anywhere: incomplete, re-run refused


def test_fresh_run_only_after_proving_no_prior_run(dirs):
    assert plan_run(dirs.fs, SHA) == (1, dict(network_used=0, scratch_used=0), [])
    finished(dirs, 'other', sha='b' * 64, net=999)      # another signed copy is ignored
    assert plan_run(dirs.fs, SHA)[0] == 1


def test_second_run_inherits_counters_and_third_is_refused(dirs):
    finished(dirs, 'r1', status='stopped_network_cap', net=123, scr=456)
    index, counters, prior = plan_run(dirs.fs, SHA)
    assert index == 2 and counters == dict(network_used=123, scratch_used=456)
    finished(dirs, 'r2', net=200, scr=500)
    with pytest.raises(RunRefused):
        plan_run(dirs.fs, SHA)


def test_missing_final_status_refuses_rerun(dirs):
    j = Journal(dirs.fs, 'r1', SHA, wall)
    j.append('start')
    j.close()
    with pytest.raises(RunRefused):
        plan_run(dirs.fs, SHA)


def test_truncated_or_unreadable_journal_refuses(dirs):
    finished(dirs, 'r1')
    path = os.path.join(dirs.receipts, primary_name('r1'))
    with open(path, 'a', encoding='utf-8') as fh:
        fh.write('{"seq": 2, "torn')
    with pytest.raises(RunRefused):
        plan_run(dirs.fs, SHA)


def test_fallback_without_primary_or_mixed_identity_refuses(dirs, tmp_path):
    line = json.dumps(dict(seq=0, run_id='r9', signed_copy_sha256=SHA, event='primary_lost')) + '\n'
    with open(os.path.join(dirs.fallback, fallback_name('r9')), 'w', encoding='utf-8') as fh:
        fh.write(line)
    with pytest.raises(RunRefused):
        plan_run(dirs.fs, SHA)
    os.rename(os.path.join(dirs.fallback, fallback_name('r9')), str(tmp_path / 'moved'))
    mixed = [dict(seq=0, run_id='r1', signed_copy_sha256=SHA, event='start'),
             dict(seq=1, run_id='r2', signed_copy_sha256=SHA, event='final', status='completed', counters={})]
    with open(os.path.join(dirs.receipts, primary_name('r1')), 'w', encoding='utf-8') as fh:
        fh.write(''.join(json.dumps(e) + '\n' for e in mixed))
    with pytest.raises(RunRefused):
        plan_run(dirs.fs, SHA)


def test_final_without_counters_refuses(dirs):
    j = Journal(dirs.fs, 'r1', SHA, wall)
    j.final('completed')
    j.close()
    with pytest.raises(RunRefused):
        plan_run(dirs.fs, SHA)


def test_primary_cannot_be_created_refuses_start(tmp_path):
    with pytest.raises(RunRefused):
        Journal(PlainFs(None, str(tmp_path / 'missing-receipts'), str(tmp_path)), 'r1', SHA, wall)


def _fail_on_call(monkeypatch, n, land=True, torn=False):
    real = Journal._write
    count = {'n': 0}

    def write(self, line):
        if not self.primary_lost:
            count['n'] += 1
            if count['n'] == n:
                if land:
                    self._fh.write(line[:len(line) // 2] if torn else line)
                    self._fh.flush()
                raise OSError('invented EIO at fsync')
        return real(self, line)
    monkeypatch.setattr(Journal, '_write', write)


@pytest.mark.parametrize('land,torn', [(True, False), (True, True), (False, False)])
def test_failed_primary_line_landed_torn_or_absent_still_joins(dirs, monkeypatch, land, torn):
    _fail_on_call(monkeypatch, 3, land=land, torn=torn)
    j = Journal(dirs.fs, 'r1', SHA, wall)
    j.append('start')
    j.append('volume_check', ok=True)
    with pytest.raises(JournalError):
        j.append('file_start', name='invented.xml.gz')
    j.final('stopped_journal_primary_lost', counters=dict(network_used=1, scratch_used=2))
    j.close()
    runs = prior_runs(dirs.fs, SHA)
    assert len(runs) == 1 and runs[0]['status'] == 'stopped_journal_primary_lost'
    fb = read_events(dirs.fs, 'fallback', fallback_name('r1'))
    assert fb[0]['failed_seq'] == 2 and [e['seq'] for e in fb] == [3, 4, 5]


def test_final_line_landing_in_primary_is_not_double_counted(dirs, monkeypatch):
    _fail_on_call(monkeypatch, 2, land=True)
    j = Journal(dirs.fs, 'r1', SHA, wall)
    j.append('start')
    j.final('completed', counters=dict(network_used=1, scratch_used=2))
    j.close()
    assert prior_runs(dirs.fs, SHA)[0]['status'] == 'completed'


def test_signal_during_append_is_deferred_until_the_line_is_durable(dirs, monkeypatch):
    import signal as sig
    from src.retrieval.sizing_v1 import Interrupted
    from src.retrieval.sizing_v1.runner import install_signal_handlers
    previous = install_signal_handlers()
    real = Journal._write

    def write(self, line):
        os.kill(os.getpid(), sig.SIGTERM)
        return real(self, line)
    try:
        j = Journal(dirs.fs, 'r1', SHA, wall)
        monkeypatch.setattr(Journal, '_write', write)
        with pytest.raises(Interrupted):
            j.append('start')
        monkeypatch.setattr(Journal, '_write', real)
        j.final('interrupted', counters=dict(network_used=0, scratch_used=0))
        j.close()
    finally:
        for s, h in previous.items():
            sig.signal(s, h)
    events = read_events(dirs.fs, 'receipts', primary_name('r1'))
    assert [e['seq'] for e in events] == [0, 1] and events[-1]['status'] == 'interrupted'


def test_run_lock_is_exclusive_per_signed_copy(dirs):
    from src.retrieval.sizing_v1.journal import RunLock
    lock = RunLock(dirs.fs, SHA)
    try:
        with pytest.raises(RunRefused):
            RunLock(dirs.fs, SHA)
        RunLock(dirs.fs, 'b' * 64).release()
    finally:
        lock.release()
    RunLock(dirs.fs, SHA).release()


def test_scratch_directory_without_a_journal_refuses(dirs, tmp_path):
    os.mkdir(os.path.join(dirs.scratch, 'sizing-ghost'))
    with pytest.raises(RunRefused):
        plan_run(dirs.fs, SHA)
    finished(dirs, 'ghost')
    assert plan_run(dirs.fs, SHA)[0] == 2


def test_unencodable_text_does_not_break_sequence(dirs):
    j = Journal(dirs.fs, 'r1', SHA, wall)
    j.append('start', note='bad \udc80 surrogate')
    j.final('completed', counters=dict(network_used=0, scratch_used=0))
    j.close()
    assert [e['seq'] for e in read_events(dirs.fs, 'receipts', primary_name('r1'))] == [0, 1]


def test_receipts_dir_fsync_failure_leaves_no_blocking_file(dirs, monkeypatch):
    def fail(self, area, subdir=''):
        raise OSError('invented: directory fsync unsupported')
    monkeypatch.setattr(PlainFs, 'fsync_dir', fail)
    with pytest.raises(RunRefused):
        Journal(dirs.fs, 'r1', SHA, wall)
    assert not os.path.exists(os.path.join(dirs.receipts, primary_name('r1')))


def test_cli_signal_handlers_cover_quit_and_terminal_stop():
    import signal as sig
    from src.retrieval.sizing_v1.runner import install_signal_handlers
    previous = install_signal_handlers()
    try:
        names = {s.name for s in previous}
        assert {'SIGTERM', 'SIGINT', 'SIGHUP', 'SIGQUIT', 'SIGTSTP'} <= names
    finally:
        for s, h in previous.items():
            sig.signal(s, h)
