"""Additive identity-aware watchdog; v2 producing pins remain unchanged."""
import subprocess, time
from src.data.source_inventory_records import require

from src.operations.mac_worker_cleanup_v3 import snapshot, key, observe, cleanup


def watch(process, *, seconds, rss_bytes, tick=lambda:None):
    start=time.monotonic();peak=0;samples=0;owned=set();timeouts=0;consecutive=0
    try:
        initial=snapshot()
        if process.pid in initial:owned.add(key(initial[process.pid]))
        else:require(process.poll() is not None,"Live worker identity unavailable")
        while process.poll() is None:
            require(time.monotonic()-start<seconds,"Owned worker resource stop")
            try:
                rss=observe(snapshot(),process.pid,owned)
            except subprocess.TimeoutExpired:
                timeouts+=1;consecutive+=1
                print(f'Process sample timeout {consecutive}/3; retaining owned worker and retrying boundedly',flush=True)
                require(consecutive<3,"Process monitoring unavailable after three samples")
                tick();continue
            consecutive=0
            peak=max(peak,rss);samples+=1
            require(time.monotonic()-start<seconds and rss<=rss_bytes,"Owned worker resource stop")
            tick();time.sleep(2)
        require(process.returncode==0,"Duration worker failed")
    finally:
        result=cleanup(process,owned)
        process.duration_resources=dict(seconds=time.monotonic()-start,peak_owned_rss_bytes=peak,samples=samples,process_sample_timeouts=timeouts,**result)
        require(result['workers_reaped'],"Owned worker cleanup unverified: "+repr(result))
    return dict(seconds=time.monotonic()-start,peak_owned_rss_bytes=peak,samples=samples,workers_reaped=True)

