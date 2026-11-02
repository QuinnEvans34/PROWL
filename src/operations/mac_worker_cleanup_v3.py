"""Identity-aware cleanup for new runs; never alters historical supervision receipts."""
import os
import signal
import subprocess
import time


def snapshot():
    text = subprocess.check_output(
        ['/bin/ps', '-axo', 'pid=,ppid=,pgid=,rss=,stat=,lstart='],
        text=True, timeout=5)
    rows = {}
    for line in text.splitlines():
        fields = line.split(None, 5)
        if len(fields) != 6:
            raise ValueError('Incomplete process identity sample')
        pid, parent, group, rss = map(int, fields[:4])
        rows[pid] = dict(pid=pid, parent=parent, group=group,
                         rss_bytes=rss * 1024, state=fields[4], born=fields[5])
    return rows


def key(row):
    return row['pid'], row['born']


def observe(rows, leader, known):
    """Follow only the original leader/descendants, never recycled numeric IDs."""
    active = {pid for pid, row in rows.items() if key(row) in known}
    changed = True
    while changed:
        expanded = active | {pid for pid, row in rows.items() if row['parent'] in active}
        changed = expanded != active
        active = expanded
    for pid in active:
        known.add(key(rows[pid]))
    return sum(rows[pid]['rss_bytes'] for pid in active)


def survivors(rows, known):
    # Zombies are deliberately still failures: absence, not merely inactivity,
    # is required before declaring all workers reaped.
    return [row for row in rows.values() if key(row) in known]


def cleanup(process, known):
    """Bounded cleanup. Unknown identities are never signalled; uncertainty fails."""
    error = None
    remaining = []
    try:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            rows = snapshot()
            observe(rows, process.pid, known)
            owned = survivors(rows, known)
            group = [row for row in rows.values() if row['group'] == process.pid]
            # A group signal is safe only when every member is currently owned.
            if group and all(key(row) in known for row in group):
                os.killpg(process.pid, sig)
            elif owned or (group and process.pid not in rows):
                raise ValueError('Unverified process-group membership; refusing signal')
            try:
                process.wait(timeout=2 if sig == signal.SIGTERM else 5)
            except subprocess.TimeoutExpired:
                if sig == signal.SIGKILL:
                    raise
        for _ in range(20):
            rows = snapshot()
            observe(rows, process.pid, known)
            remaining = survivors(rows, known)
            if not remaining:
                break
            time.sleep(.05)
    except ProcessLookupError:
        # Re-sample rather than declaring success from a signal race.
        try:
            process.wait(timeout=5)
            remaining = survivors(snapshot(), known)
        except Exception as exc:
            error = repr(exc)
    except Exception as exc:
        error = repr(exc)
    return dict(workers_reaped=not remaining and error is None,
                cleanup_error=error, surviving_workers=remaining,
                tracked_worker_identities=len(known))
