"""Fixed-script duration worker dispatcher; exclusive consumption and owned-process watchdog."""
from pathlib import Path
import json
import os
import signal
import stat
import subprocess
import sys
import time

from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require
from src.training.segmenter_duration_executor_v1 import validate_request, authorize, put
from src.operations.localizer_run_storage import tree_bytes

REPO=Path(__file__).resolve().parents[2]
SCRIPT=REPO/"scripts/diagnostics/segmenter_duration_launch.py"


def read_control(path, trusted_pin, max_bytes=4*1024**2):
    path=Path(path)
    require(path.is_absolute() and path.resolve(strict=True)==path,"Absolute non-symlink control required")
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,"rb") as stream:
        info=os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=max_bytes,"Unsafe control file")
        raw=stream.read(max_bytes+1)
    require(len(raw)<=max_bytes and digest(raw)==trusted_pin,"Control size/identity changed")
    return raw


def read_metadata(path,max_bytes=1024**2):
    path=Path(path);require(path.is_absolute() and path.resolve(strict=True)==path,"Unsafe metadata path")
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,"rb") as stream:
        info=os.fstat(stream.fileno());require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=max_bytes,"Unsafe metadata size/type")
        raw=stream.read(max_bytes+1)
    require(len(raw)<=max_bytes,"Metadata size exceeded")
    return raw


def verify_code(request):
    for name,pin in request["source_pins"].items():
        path=Path(name)
        require(not path.is_absolute() and ".." not in path.parts and path.parts[0] in
                ("src","tests","docs","requirements","configs")
                and path.suffix in (".py",".json",".md",".txt"),"Code pin cannot point to data/weights")
        read_control(REPO/path,pin)


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
    start=time.monotonic();peak=0;samples=0;owned={process.pid}
    try:
        while process.poll() is None:
            ids,rss=owned_tree(process.pid);owned|=ids;peak=max(peak,rss);samples+=1
            require(time.monotonic()-start<seconds and rss<=rss_bytes,"Owned worker resource stop")
            tick();time.sleep(.05)
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
        process.duration_resources=dict(seconds=time.monotonic()-start,peak_owned_rss_bytes=peak,samples=samples,workers_reaped=not survivors)
        require(not survivors,"Owned worker descendant was not reaped")
    return dict(seconds=time.monotonic()-start,peak_owned_rss_bytes=peak,samples=samples,workers_reaped=True)


def dispatch(request_path, request_pin, dest, *, approval_path=None, approval_pin=None,
             storage_path=None, storage_pin=None, stage="producer"):
    raw=read_control(request_path,request_pin);request=json.loads(raw);validate_request(request)
    require(raw==canonical(request),"Request must use canonical bytes")
    require(stage in ("producer","cold","unit_echo","unit_sleep"),"Unknown fixed worker stage")
    unit=request["kind"]=="unit"
    if unit:
        require(stage in ("unit_echo","unit_sleep") and approval_path is None and storage_path is None,
                "Unit dispatcher cannot launch model/native worker")
        authorize(request)
    else:
        require(stage in ("producer","cold") and approval_path is not None and storage_path is not None,
                "Production dispatch needs exact job/storage authority")
        authorize(request,read_control(approval_path,approval_pin),trusted_approval_sha256=approval_pin)
        from src.operations.segmenter_duration_storage_v1 import validate_storage_authority
        validate_storage_authority(canonical(request["storage_capability"]),read_control(storage_path,storage_pin),storage_pin)
        verify_code(request)
    dest=Path(dest)
    require(dest.is_absolute() and dest.resolve(strict=True)==dest and dest.is_dir(),"Unsafe worker destination")
    started=time.time();remaining=request["limits"]["total_seconds"];producer_pin=None
    if stage=="cold":
        previous=json.loads(read_metadata(dest/"producer-dispatch-result.json"))
        require(previous["state"]=="complete" and previous["request_sha256"]==request_pin and previous["stage"]=="producer","Cold requires successful matching producer")
        producer_pin=previous["producer_result_sha256"]
        read_control(dest/"transaction.json",producer_pin,8*1024**2)
        first=json.loads(read_metadata(dest/"dispatch-producer-consumed.json"))
        require(first["request_sha256"]==request_pin and type(first["started_epoch"]) is float and first["started_epoch"]<=started,"Producer time authority")
        remaining-=started-first["started_epoch"]
        require(remaining>0,"Combined producer/cold time budget exhausted")
    if not unit:
        import yaml
        from src.operations.segmenter_duration_storage_v1 import areas
        cap=request['storage_capability']
        reg=yaml.safe_load(read_control(REPO/'configs/local/roots.yaml',cap['registry_sha256']))
        backup_root=Path(reg['roots']['prowl_backup']['path'])
        require(dest==backup_root/areas(cap)['controls'],"Dispatch output outside exact storage scope")
    def output_guard():
        require(tree_bytes(dest)<=request['limits']['output_bytes'],"Aggregate control/log reserve stop")
        if not unit:
            info=os.statvfs(dest);require(info.f_bavail*info.f_frsize>=request['storage_capability']['minimum_free_bytes'],"Control filesystem free-space stop")
    marker=dest/("dispatch-"+stage+"-consumed.json")
    put(marker,canonical(dict(request_sha256=request_pin,stage=stage,state="consumed",started_epoch=started)))
    command=[sys.executable,str(SCRIPT),"_"+stage,"--request",str(request_path),"--request-pin",request_pin,"--dest",str(dest)]
    if not unit:command+= ["--approval",str(approval_path),"--approval-pin",approval_pin,"--storage",str(storage_path),"--storage-pin",storage_pin]
    if stage=="cold":command += ["--producer-pin",producer_pin]
    env=dict(os.environ,OMP_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2",PYTORCH_ENABLE_MPS_FALLBACK="0")
    start=time.monotonic();result=None
    try:
        with (dest/(stage+"-worker.log")).open("xb") as log:
            process=subprocess.Popen(command,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
            limit=min(remaining,request["limits"]["recovery_seconds" if stage=="cold" else "producer_seconds"])
            result=watch(process,seconds=limit,rss_bytes=request["limits"]["rss_bytes"],
                tick=output_guard)
        record=dict(state="complete",request_sha256=request_pin,stage=stage,resources=result)
        if stage=="producer":record["producer_result_sha256"]=digest((dest/"transaction.json").read_bytes())
        put(dest/(stage+"-dispatch-result.json"),canonical(record));return record
    except BaseException as exc:
        record=dict(state="consumed_failed",request_sha256=request_pin,stage=stage,
                    seconds=time.monotonic()-start,error_type=type(exc).__name__,message=str(exc),resources=getattr(process,"duration_resources",None) if "process" in locals() else None)
        put(dest/(stage+"-dispatch-failure.json"),canonical(record));raise
