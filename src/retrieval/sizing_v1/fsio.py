"""Filesystem hook for run S (``sizing_v1.1``): every read and write in the run's areas goes here.

``run_sizing`` touches its three areas only through an injected ``SizingFs``:
- ``scratch``: the parent of ``sizing-<run_id>``;
- ``receipts``: the primary journals and the run lock;
- ``fallback``: the internal-disk fallback journals.

Areas are addressed by ``(area, rel)`` pairs. ``rel`` is either one bare component or
``sizing-<run_id>/<bare>``; nothing else is accepted.

``PlainFs`` is the default and reproduces ``sizing_v1``'s literal-path behaviour. The S1 binding
(Codex-owned) supplies a descriptor-guarded implementation of the same methods on top of its lease.
The parser child never receives paths: the parent opens the source and output through this hook
and passes file descriptors.

Contract, for any implementation (``PlainFs`` is the reference). Errors are raised as
exceptions: ``FileExistsError`` for a collision, ``OSError`` subclasses otherwise. ``run_sizing``
also treats any other ``Exception`` from the hook as a failure, never as success.

| Method | Contract |
|---|---|
| ``roots()`` | ``{area: literal root path}``. Checked against the signed configuration before anything else |
| ``display(area, rel)`` | String for journal events; no I/O |
| ``mkdir_exclusive(area, rel)`` | Create a directory; ``FileExistsError`` if any entry exists |
| ``create_exclusive(area, rel)`` | New, empty, regular file opened for binary writing. Returns a file object with ``write``, ``flush``, ``fileno`` (a real descriptor that ``os.fsync`` accepts and that can be passed to a child process) and ``close`` |
| ``open_read(area, rel)`` | Regular file opened for binary reading, positioned at offset 0, with a real ``fileno`` |
| ``list(area, prefix, suffix)`` | Every entry name (files and directories) in the area root that matches. No symlink following, no silent skipping: raise if the area cannot be listed |
| ``fsync_dir(area, subdir='')`` | Make directory entries durable |
| ``lock(area, rel)`` | Exclusive, non-blocking lock; returns an object with ``release()``. ``LockHeld`` only when another holder has it, ``LockUnsupported`` when locking is impossible there |
| ``remove_own_empty(area, rel, fh)`` | Remove ``rel`` only if it is the same file as the still-open handle ``fh`` (device and inode) and is empty. The caller closes ``fh`` afterwards |

**Guards are applied when a file is opened.** Writes and reads then use the descriptor:
``run_sizing`` passes the source and output descriptors of each parse to a child process, which
reads and writes them directly. The child rewinds both and checks that they are regular files and
that the output is empty. A guarded file object's ``write`` or ``close`` therefore does not see the
child's bytes, and ``close`` must not truncate, rename or otherwise commit by name.
"""
import os
import re

AREAS = ('scratch', 'receipts', 'fallback')
_BARE = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,200}')


class LockHeld(Exception):
    """Another holder has the lock."""


class LockUnsupported(Exception):
    """Locking is not available for this area."""


def check_rel(rel):
    """``rel`` is ``name`` or ``sizing-<id>/name``; components are bare names (no traversal)."""
    if not isinstance(rel, str):
        raise ValueError('relative name must be a string')
    parts = rel.split('/')
    if len(parts) not in (1, 2) or not all(_BARE.fullmatch(p) for p in parts):
        raise ValueError(f'invalid relative name {rel!r}')
    if len(parts) == 2 and not parts[0].startswith('sizing-'):
        raise ValueError(f'only sizing-<run_id>/ subdirectories are allowed: {rel!r}')
    return parts


class PlainFs:
    """Literal-path implementation (the ``sizing_v1`` behaviour). Areas left as None are unavailable."""

    def __init__(self, scratch_root=None, receipts_dir=None, fallback_dir=None):
        self._roots = dict(scratch=scratch_root, receipts=receipts_dir, fallback=fallback_dir)

    def roots(self):
        return dict(self._roots)

    def _path(self, area, rel=''):
        if area not in AREAS or self._roots.get(area) is None:
            raise ValueError(f'area {area!r} is not available')
        if rel == '':
            return self._roots[area]
        return os.path.join(self._roots[area], *check_rel(rel))

    def display(self, area, rel):
        return self._path(area, rel)

    def mkdir_exclusive(self, area, rel):
        os.mkdir(self._path(area, rel))

    def create_exclusive(self, area, rel):
        return open(self._path(area, rel), 'xb')

    def open_read(self, area, rel):
        return open(self._path(area, rel), 'rb')

    def list(self, area, prefix='', suffix=''):
        return sorted(n for n in os.listdir(self._path(area)) if n.startswith(prefix) and n.endswith(suffix))

    def fsync_dir(self, area, subdir=''):
        fd = os.open(self._path(area, subdir), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def lock(self, area, rel):
        return _FlockLock(self._path(area, rel))

    def remove_own_empty(self, area, rel, fh):
        path = self._path(area, rel)
        held, named = os.fstat(fh.fileno()), os.lstat(path)
        if (held.st_dev, held.st_ino) != (named.st_dev, named.st_ino) or named.st_size != 0:
            raise ValueError(f'refusing to remove {path}: not the empty file this run created')
        os.unlink(path)


class _FlockLock:
    def __init__(self, path):
        import errno
        import fcntl
        try:
            self._fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        except OSError as exc:
            raise LockUnsupported(f'lock file cannot be opened: {exc}') from exc
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self._fd)
            if exc.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise LockHeld('lock is held by another run') from exc
            raise LockUnsupported(f'lock is not supported here: {exc}') from exc

    def release(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
