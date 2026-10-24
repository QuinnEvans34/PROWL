"""Owned process supervision with an independent parent-loss guardian (macOS/POSIX)."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def report(path, value):
    path=Path(path);temp=path.with_suffix(path.suffix+'.partial')
    with temp.open('x') as f:
        json.dump(value,f);f.flush();os.fsync(f.fileno())
    if path.exists():raise FileExistsError(path)
    os.replace(temp,path)


def identity(pid):
    return subprocess.check_output(['ps','-p',str(pid),'-o','lstart='],text=True).strip()


def stop_group(pid, expected):
    try:
        if identity(pid)!=expected:return
        os.killpg(pid,signal.SIGTERM);time.sleep(.2)
        os.killpg(pid,signal.SIGKILL)
    except (ProcessLookupError,subprocess.CalledProcessError):pass


def guard(parent,worker,expected,destination,ready):
    # Guardian's direct parent is the supervisor; reparenting detects SIGKILL too.
    report(ready,dict(ready=True,parent=parent,worker=worker))
    while os.getppid()==parent:time.sleep(.05)
    stop_group(worker,expected)
    report(destination,dict(supervisor_lost=True,worker=worker,cleanup_requested=True,
        success=False,note='Guardian cleanup evidence; no recovered peak RSS or successful run claim'))


def run(command, directory, *, seconds, rss_bytes, tick=lambda:None, env=None):
    from src.operations.segmenter_duration_dispatch_v1 import watch
    directory=Path(directory)
    old={s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGINT)}
    def interrupted(signum,frame):raise InterruptedError('Supervisor signal '+str(signum))
    for s in old:signal.signal(s,interrupted)
    worker=None;guardian=None;success=False;error=None
    try:
        with (directory/'worker.log').open('x') as log:
            worker=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                                    env=env,start_new_session=True)
            born=identity(worker.pid)
            report(directory/'process.json',dict(supervisor=os.getpid(),worker=worker.pid,worker_start=born))
            guardian=subprocess.Popen([sys.executable,__file__,'--guard',str(os.getpid()),str(worker.pid),born,
                str(directory/'guardian-failure.json'),str(directory/'guardian-ready.json')],start_new_session=True)
            deadline=time.monotonic()+5
            while not (directory/'guardian-ready.json').exists():
                if guardian.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Guardian did not start')
                time.sleep(.02)
            watch(worker,seconds=seconds,rss_bytes=rss_bytes,tick=tick);success=True
    except Exception as exc:error=repr(exc)
    finally:
        if worker is not None:
            try:os.killpg(worker.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:worker.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(worker.pid,signal.SIGKILL);worker.wait(timeout=5)
        if guardian is not None:
            guardian.terminate();guardian.wait(timeout=5)
        report(directory/'resources.json',dict(getattr(worker,'duration_resources',{}),success=success,error=error,
            exit_code=worker.returncode if worker else None))
        for s,handler in old.items():signal.signal(s,handler)
    return success


if __name__=='__main__' and sys.argv[1]=='--guard':
    guard(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],sys.argv[5],sys.argv[6])
