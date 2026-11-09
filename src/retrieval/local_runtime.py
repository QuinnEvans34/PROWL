"""Local expert inference admission. Battery use is allowed; training is separate."""
from contextlib import contextmanager
import os
from pathlib import Path


@contextmanager
def expert_gpu_guard(path):
    """Reserve the existing accelerator lock without imposing training's AC rule."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b'0'); handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
