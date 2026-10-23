"""Platform operations for the full trainer; historical dispatchers remain separate."""
from contextlib import contextmanager
import ctypes
import os
from pathlib import Path
import subprocess
import time


def durable_replace(source, destination):
    if os.name == 'nt':
        from ctypes import wintypes
        move = ctypes.WinDLL('kernel32', use_last_error=True).MoveFileExW
        move.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
        move.restype = wintypes.BOOL
        # File contents are already fsynced by the caller. Write through the rename.
        if not move(str(Path(source).resolve()), str(Path(destination).resolve()), 0x1 | 0x8):
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        os.replace(source, destination)
        fd = os.open(Path(destination).parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def require_ac():
    if os.name == 'nt':
        from ctypes import wintypes
        class Power(ctypes.Structure):
            _fields_ = [('ACLineStatus', ctypes.c_ubyte), ('BatteryFlag', ctypes.c_ubyte),
                ('BatteryLifePercent', ctypes.c_ubyte), ('SystemStatusFlag', ctypes.c_ubyte),
                ('BatteryLifeTime', wintypes.DWORD), ('BatteryFullLifeTime', wintypes.DWORD)]
        value = Power()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(value)) or value.ACLineStatus != 1:
            raise RuntimeError('AC power required')
    elif 'AC Power' not in subprocess.check_output(['pmset', '-g', 'batt'], text=True):
        raise RuntimeError('AC power required')


@contextmanager
def training_guard(path):
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
            awake = False
            try:
                require_ac()
                awake = bool(ctypes.windll.kernel32.SetThreadExecutionState(0x80000001))
                if not awake:
                    raise RuntimeError('Could not inhibit idle sleep')
                yield
            finally:
                if awake:
                    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            require_ac()
            yield


def watch_windows(process, *, seconds, rss_bytes, tick=lambda: None):
    """Monitor this worker and its descendants; kill the job if the supervisor exits."""
    from ctypes import wintypes
    import psutil
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    class Basic(ctypes.Structure):
        _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64), ('PerJobUserTimeLimit', ctypes.c_int64),
            ('LimitFlags', wintypes.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t),
            ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', wintypes.DWORD),
            ('Affinity', ctypes.c_size_t), ('PriorityClass', wintypes.DWORD), ('SchedulingClass', wintypes.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in
            ('ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
             'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]
    class Extended(ctypes.Structure):
        _fields_ = [('BasicLimitInformation', Basic), ('IoInfo', IO),
            ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t),
            ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    job = kernel.CreateJobObjectW(None, None)
    start = time.monotonic(); peak = 0; samples = 0; owned = {}
    try:
        if not job:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Extended(); limits.BasicLimitInformation.LimitFlags = 0x2000
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.AssignProcessToJobObject(job, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
        root = psutil.Process(process.pid); owned[root.pid] = root
        while process.poll() is None:
            try:
                current = [root] + root.children(recursive=True)
            except psutil.NoSuchProcess:
                if process.poll() is not None:
                    break
                raise
            rss = 0
            for child in current:
                owned[child.pid] = child
                try:
                    rss += child.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
            peak = max(peak, rss); samples += 1
            if time.monotonic() - start >= seconds or rss > rss_bytes:
                raise RuntimeError('Owned worker resource stop')
            tick(); time.sleep(.1)
        if process.returncode:
            raise RuntimeError(f'Training worker failed with exit {process.returncode}')
    finally:
        if job:
            kernel.CloseHandle(job)
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)
        _, alive = psutil.wait_procs(list(owned.values()), timeout=5)
        process.duration_resources = dict(seconds=time.monotonic()-start,
            peak_owned_rss_bytes=peak, samples=samples, workers_reaped=not alive)
        if alive:
            raise RuntimeError('Owned worker descendant was not reaped')
    return process.duration_resources
