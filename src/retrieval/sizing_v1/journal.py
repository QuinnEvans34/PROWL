"""Append-only run S journal with the internal-disk fallback, plus prior-run discovery.

- All journal I/O goes through the injected ``SizingFs`` (``fsio``); areas are ``receipts`` and
  ``fallback``.
- The primary journal ``<receipts>/run-S-<run_id>.jsonl`` is created exclusively and its directory
  is ``fsync``-ed. If it cannot be created, the run never starts (``RunRefused``).
- Each event is one JSON line, written, flushed and ``fsync``-ed before the call returns.
  - The sequence number is reserved before the write.
  - SIGINT, SIGTERM and SIGHUP are deferred during the write, so a handled signal cannot tear a
    line or reuse a number.
- If a primary write fails, the remaining events go to
  ``<fallback_dir>/run-S-<run_id>.fallback.jsonl``, also created exclusively.
  - It starts with ``primary_lost``, which records the sequence number whose write failed. That
    line may or may not have reached the primary; readers accept either case.
  - The caller is told to stop (``JournalError``, reason ``journal_primary_lost``). Only journal
    events go to the fallback.
  - If the fallback also fails, ``JournalUnwritable`` propagates and the run has no final status,
    so it is incomplete.
- Exactly one final status: ``completed``, ``stopped_<reason>`` or ``interrupted``. A journal
  without one is incomplete; it is never treated as completed or retried automatically.
- ``RunLock`` holds an advisory exclusive lock per signed copy for the whole run, so two runs
  cannot overlap.
"""
import contextlib
import json
import os
import signal

from src.retrieval.sizing_v1 import JournalError, RunRefused
from src.retrieval.sizing_v1.fsio import LockHeld, LockUnsupported

FINAL = 'final'
MAX_RUNS = 2
_DEFERRED = {s for s in (getattr(signal, 'SIGINT', None), getattr(signal, 'SIGTERM', None),
                         getattr(signal, 'SIGHUP', None)) if s is not None}


class JournalUnwritable(Exception):
    """Neither primary nor fallback can be written. The run ends without a final status."""


def primary_name(run_id):
    return f'run-S-{run_id}.jsonl'


def fallback_name(run_id):
    return f'run-S-{run_id}.fallback.jsonl'


def _valid_final(status):
    return status in ('completed', 'interrupted') or (status.startswith('stopped_') and len(status) > 8)


@contextlib.contextmanager
def signals_deferred():
    if hasattr(signal, 'pthread_sigmask'):
        old = signal.pthread_sigmask(signal.SIG_BLOCK, _DEFERRED)
        try:
            yield
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, old)
    else:
        yield


class RunLock:
    """Exclusive non-blocking lock for one signed copy, in the receipts area (through the fs hook)."""

    def __init__(self, fs, signed_copy_sha256):
        self.name = f'run-S-{signed_copy_sha256[:16]}.lock'
        try:
            self._lock = fs.lock('receipts', self.name)
        except LockHeld as exc:
            raise RunRefused('another run for this signed copy holds the lock') from exc
        except LockUnsupported as exc:
            raise RunRefused(f'run lock is not supported here: {exc}') from exc
        except Exception as exc:   # noqa: BLE001 - any other hook failure refuses the start
            raise RunRefused(f'run lock failed: {type(exc).__name__}: {exc}') from exc

    def release(self):
        if self._lock is not None:
            self._lock.release()
            self._lock = None


class Journal:
    def __init__(self, fs, run_id, signed_copy_sha256, wall):
        self.fs = fs
        self.run_id = run_id
        self.signed_copy_sha256 = signed_copy_sha256
        self.wall = wall
        self.seq = 0
        self.finalized = False
        self.primary_lost = False
        self.rel = primary_name(run_id)
        self.path = fs.display('receipts', self.rel)
        self.path_fallback = None
        try:
            self._fh = fs.create_exclusive('receipts', self.rel)
        except Exception as exc:   # noqa: BLE001 - any hook failure: the run never starts
            raise RunRefused(f'primary journal cannot be created exclusively: {exc}') from exc
        try:
            fs.fsync_dir('receipts')
        except Exception as exc:   # noqa: BLE001
            try:
                fs.remove_own_empty('receipts', self.rel, self._fh)   # leaving it would block every later run
                note = ''
            except Exception as exc2:   # noqa: BLE001
                note = f'; the empty journal {self.path} could not be removed ({exc2}) and needs review'
            finally:
                try:
                    self._fh.close()
                except Exception:   # noqa: BLE001
                    pass
            raise RunRefused(f'receipts directory cannot be made durable: {exc}{note}') from exc

    def _line(self, seq, event, fields):
        record = dict(seq=seq, run_id=self.run_id, signed_copy_sha256=self.signed_copy_sha256,
                      at=self.wall(), event=event)
        record.update(fields)
        return (json.dumps(record, sort_keys=True, ensure_ascii=True, default=str) + '\n').encode('ascii')

    def _write(self, line):
        self._fh.write(line)
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def _next(self):
        seq = self.seq
        self.seq += 1
        return seq

    def append(self, event, **fields):
        if self.finalized:
            raise JournalError('journal already has a final status', reason='journal')
        with signals_deferred():
            seq = self.seq
            line = self._line(seq, event, fields)      # a failure here consumes no sequence number
            self.seq += 1                              # reserved: the write may land even if it fails
            try:
                self._write(line)
            except Exception as exc:   # noqa: BLE001 - any hook failure counts as a failed write
                if self.primary_lost:
                    raise JournalUnwritable(f'fallback journal write failed: {exc}') from exc
                self._switch_to_fallback(seq, f'{type(exc).__name__}: {exc}')
                try:
                    self._write(self._line(self._next(), event, fields))
                except Exception as exc2:   # noqa: BLE001
                    raise JournalUnwritable(f'fallback journal write failed: {exc2}') from exc2
                if event == FINAL:
                    self.finalized = True
                    return
                raise JournalError('primary journal lost; remaining events go to the fallback',
                                   reason='journal_primary_lost') from exc
            if event == FINAL:
                self.finalized = True

    def _switch_to_fallback(self, failed_seq, error):
        try:
            self._fh.close()
        except Exception:   # noqa: BLE001
            pass
        self.primary_lost = True
        rel = fallback_name(self.run_id)
        try:
            self._fh = self.fs.create_exclusive('fallback', rel)
            dir_error = None
            try:
                self.fs.fsync_dir('fallback')
            except Exception as exc:   # noqa: BLE001
                dir_error = str(exc)            # the file itself is still fsynced on every write
            self._write(self._line(self._next(), 'primary_lost',
                                   dict(primary_path=self.path, failed_seq=failed_seq, error=error,
                                        fallback_dir_fsync_error=dir_error)))
        except Exception as exc:   # noqa: BLE001
            raise JournalUnwritable(f'fallback journal cannot be created: {exc}') from exc
        self.path_fallback = self.fs.display('fallback', rel)

    def final(self, status, **fields):
        if not _valid_final(status):
            raise ValueError(f'invalid final status {status!r}')
        self.append(FINAL, status=status, **fields)

    def close(self):
        try:
            self._fh.close()
        except Exception:   # noqa: BLE001
            pass


def parse_events(data, label, allow_torn_tail=False):
    """Strict parser: every line must be a complete JSON object.

    ``allow_torn_tail`` drops one incomplete last line. It is used only for a primary journal whose
    run continued in a fallback.
    """
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise RunRefused(f'journal is not UTF-8 {label}') from exc
    if not text:
        raise RunRefused(f'empty journal {label}')
    lines = text.split('\n')
    if lines[-1] == '':
        lines.pop()
    elif allow_torn_tail:
        lines.pop()
    else:
        raise RunRefused(f'truncated journal (no trailing newline) {label}')
    events = []
    for n, line in enumerate(lines, 1):
        try:
            event = json.loads(line)
        except ValueError as exc:
            raise RunRefused(f'unreadable journal line {n} in {label}') from exc
        if not isinstance(event, dict) or 'run_id' not in event or 'signed_copy_sha256' not in event:
            raise RunRefused(f'journal line {n} lacks identity fields in {label}')
        events.append(event)
    if not events:
        raise RunRefused(f'journal has no complete events {label}')
    return events


def read_events(fs, area, rel, allow_torn_tail=False):
    try:
        with fs.open_read(area, rel) as fh:
            data = fh.read()
    except Exception as exc:   # noqa: BLE001 - an unreadable journal refuses the start
        raise RunRefused(f'journal cannot be read: {area}:{rel}: {exc}') from exc
    return parse_events(data, f'{area}:{rel}', allow_torn_tail)


def _identity(events, label):
    ids = {e['run_id'] for e in events}
    shas = {e['signed_copy_sha256'] for e in events}
    if len(ids) != 1 or len(shas) != 1:
        raise RunRefused(f'journal mixes run identities: {label}')
    return ids.pop(), shas.pop()


def _merge(run_id, primary, fallback):
    """Primary seqs 0..k; fallback starts with primary_lost(failed_seq=F) at seq F+1."""
    if [e.get('seq') for e in primary] != list(range(len(primary))):
        raise RunRefused(f'primary journal sequence is not continuous for run {run_id}')
    if fallback is None:
        return primary
    head = fallback[0]
    failed = head.get('failed_seq')
    if head.get('event') != 'primary_lost' or not isinstance(failed, int):
        raise RunRefused(f'fallback journal does not start with primary_lost for run {run_id}')
    if [e.get('seq') for e in fallback] != list(range(failed + 1, failed + 1 + len(fallback))):
        raise RunRefused(f'fallback journal sequence is not continuous for run {run_id}')
    last = primary[-1]['seq']
    if last == failed:
        primary = primary[:-1]                   # the failed line landed; it is re-written in the fallback
    elif last != failed - 1:
        raise RunRefused(f'primary and fallback journals do not join for run {run_id}')
    return primary + fallback


def prior_runs(fs, signed_copy_sha256, check_scratch=True):
    """All earlier runs for this signed copy, each proven terminal. Anything ambiguous refuses.

    With ``check_scratch``, every ``sizing-<run_id>`` directory in the scratch area must belong to a
    journal, so a run whose journal was lost cannot reset the allowance.
    """
    known_ids = set()
    fallbacks = {}
    try:
        fallback_names = fs.list('fallback', 'run-S-', '.fallback.jsonl')
        primary_names = [n for n in fs.list('receipts', 'run-S-', '.jsonl') if not n.endswith('.fallback.jsonl')]
        scratch_names = fs.list('scratch', 'sizing-') if check_scratch else []
    except Exception as exc:   # noqa: BLE001
        raise RunRefused(f'run areas cannot be listed: {exc}') from exc
    for name in fallback_names:
        events = read_events(fs, 'fallback', name)
        run_id, sha = _identity(events, name)
        known_ids.add(run_id)
        if sha == signed_copy_sha256:
            if run_id in fallbacks:
                raise RunRefused(f'ambiguous: two fallback journals for run {run_id}')
            fallbacks[run_id] = events
    primaries = {}
    for name in primary_names:
        stem = name[len('run-S-'):-len('.jsonl')]
        events = read_events(fs, 'receipts', name, allow_torn_tail=stem in fallbacks)
        run_id, sha = _identity(events, name)
        known_ids.add(run_id)
        if sha == signed_copy_sha256:
            primaries[run_id] = events
    for name in scratch_names:
        if name[len('sizing-'):] not in known_ids:
            raise RunRefused(f'scratch directory without a journal: {name}')
    result = []
    for run_id in sorted(set(primaries) | set(fallbacks)):
        if run_id not in primaries:
            raise RunRefused(f'fallback journal without its primary for run {run_id}')
        events = _merge(run_id, primaries[run_id], fallbacks.get(run_id))
        finals = [e for e in events if e.get('event') == FINAL]
        if len(finals) != 1 or events[-1].get('event') != FINAL:
            raise RunRefused(f'run {run_id} has no single final status (incomplete); a re-run is refused')
        counters = finals[0].get('counters')
        if not isinstance(counters, dict) or not all(
                isinstance(counters.get(k), int) for k in ('network_used', 'scratch_used')):
            raise RunRefused(f'run {run_id} final status lacks cumulative counters')
        result.append(dict(run_id=run_id, status=finals[0]['status'], counters=counters,
                           started=events[0].get('at')))
    return result


def plan_run(fs, signed_copy_sha256, check_scratch=True):
    """Returns ``(run_index, inherited_counters, prior)``. Refuses a third run."""
    prior = prior_runs(fs, signed_copy_sha256, check_scratch)
    if len(prior) >= MAX_RUNS:
        raise RunRefused('at most two runs are allowed per signed copy')
    if not prior:
        return 1, dict(network_used=0, scratch_used=0), prior
    counters = prior[0]['counters']
    return 2, dict(network_used=counters['network_used'], scratch_used=counters['scratch_used']), prior
