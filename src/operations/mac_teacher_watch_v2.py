"""Teacher-only bounded process-sampling recovery; original watchdog remains unchanged."""
import os, signal, subprocess, time
from src.data.source_inventory_records import require

def owned_tree(pid):
    rows=subprocess.check_output(["/bin/ps","-axo","pid=,ppid=,rss="],text=True,timeout=5)
    entries=[]
    for row in rows.splitlines():
        fields=row.split()
        if len(fields)==3:entries.append(tuple(map(int,fields)))
    ids={pid};changed=True
    while changed:
        expanded=ids|{p for p,parent,_ in entries if parent in ids};changed=expanded!=ids;ids=expanded
    return ids,sum(rss*1024 for p,_,rss in entries if p in ids)


def watch(process, *, seconds, rss_bytes, tick=lambda:None):
    start=time.monotonic();peak=0;samples=0;owned={process.pid};timeouts=0;consecutive=0
    try:
        while process.poll() is None:
            require(time.monotonic()-start<seconds,"Owned worker resource stop")
            try:
                ids,rss=owned_tree(process.pid)
            except subprocess.TimeoutExpired:
                timeouts+=1;consecutive+=1
                print(f'Process sample timeout {consecutive}/3; retaining owned worker and retrying boundedly',flush=True)
                require(consecutive<3,"Process monitoring unavailable after three samples")
                tick();continue
            consecutive=0
            owned|=ids;peak=max(peak,rss);samples+=1
            require(time.monotonic()-start<seconds and rss<=rss_bytes,"Owned worker resource stop")
            tick();time.sleep(2)
        require(process.returncode==0,"Duration worker failed")
    finally:
        # This group was created exclusively by dispatch. Reap descendants even if the leader exited.
        try:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        survivors=[]
        for _ in range(20):
            survivors=[]
            for pid in owned:
                try:os.kill(pid,0);survivors.append(pid)
                except ProcessLookupError:pass
            if not survivors:break
            time.sleep(.05)
        process.duration_resources=dict(seconds=time.monotonic()-start,peak_owned_rss_bytes=peak,samples=samples,process_sample_timeouts=timeouts,workers_reaped=not survivors)
        require(not survivors,"Owned worker descendant was not reaped")
    return dict(seconds=time.monotonic()-start,peak_owned_rss_bytes=peak,samples=samples,workers_reaped=True)

