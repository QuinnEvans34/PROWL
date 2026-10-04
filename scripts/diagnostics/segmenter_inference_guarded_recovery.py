"""Supplementary D-324 cold recovery; original producer/request code remains immutable."""
import argparse,json,os,signal,sys,time
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import torch
from src.data.manifest_records import digest
from src.data.source_inventory_records import require
from src.operations.artifact_store import directory
from src.operations.segmenter_primary_read_guard_v1 import install
from src.operations.segmenter_inference_backup_v1 import restore_backup,validate_backup,EXTRA
from src.training import segmenter_inference_v1 as core
from scripts.diagnostics import segmenter_inference_qualification as old,segmenter_content_pilot as prior,segmenter_source_verification as source
CODE=['src/operations/segmenter_primary_read_guard_v1.py','scripts/diagnostics/segmenter_inference_guarded_recovery.py','tests/test_segmenter_primary_read_guard.py']
ROOT=old.ROOT/'SEGMENTER-INFERENCE-GUARDED-RECOVERY-attempt03-20261002'


def pins():return {n:digest((old.REPO/n).read_bytes()) for n in CODE}


def read_existing_restore(backup,restore,backup_ref,primary_ref,restore_ref,identity):
    validate=lambda f:validate_backup(f,identity,primary_ref)
    b,_=backup.resolve(backup_ref['artifact_id'],receipt_sha256=backup_ref['receipt_sha256'],expected_derivation=backup_ref['derivation_sha256'],validate=validate)
    r,_=restore.resolve(restore_ref['artifact_id'],receipt_sha256=restore_ref['receipt_sha256'],expected_derivation=backup_ref['receipt_sha256'],validate=validate)
    require(b==r,'Existing independent restore differs from verified backup')
    return {n:v for n,v in r.items() if n not in EXTRA},restore_ref


def worker(mode):
    dest=old.PROFILE if mode=='profile' else old.DEST;raw=(dest/'request.json').read_bytes();pin=digest(raw);req=old.checked(dest,pin)
    job=json.loads((ROOT/'invocation.json').read_bytes());require(job['source_pins']==pins() and job['producer_request_pins'][mode]==pin,'Supplementary recovery source/request changed')
    source.put(ROOT/(mode+'-worker-consumed.json'),dict(request_sha256=pin));install();denials=[]
    for name,call in [('absolute',lambda:os.listdir('/Volumes/PROWL-Data')),('component',lambda:os.open('PROWL-Data',os.O_RDONLY)),('nofollow_component_walk',lambda:directory('/Volumes/PROWL-Data/artifacts'))]:
        try:call();raise AssertionError('Primary denial failed')
        except ValueError:denials.append(name)
    volume_fd=os.open('/Volumes',os.O_RDONLY|os.O_DIRECTORY)
    try:
        try:os.open('PROWL-Data',os.O_RDONLY|os.O_DIRECTORY,dir_fd=volume_fd);raise AssertionError('dir_fd denial failed')
        except ValueError:denials.append('directory_relative_open')
    finally:os.close(volume_fd)
    start=time.monotonic();signal.alarm(1200);torch.set_num_threads(2);require(torch.backends.mps.is_available() and os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0','Native MPS required')
    torch.mps.set_per_process_memory_fraction(min(1.,old.LIMITS['driver_bytes']/torch.mps.recommended_max_memory()))
    tick=lambda:old.bounded(ROOT,start);saved=json.loads((dest/'result.json').read_bytes());_,backup,restore=old.stores(recovery=True,ceilings=req['storage_ceilings'])
    existing=json.loads((old.RECOVERY/'result.json').read_bytes())['restore_reference'];files,ref=read_existing_restore(backup,restore,saved['backup_reference'],saved['primary_reference'],existing,req['identity']);probe=core.recover_probe(files,req['identity'],device='mps',tick=tick);tick()
    source.put(ROOT/(mode+'-result.json'),dict(state='passed',decision='D-324',producer_request_sha256=pin,original_context_sha256=digest(files['identity.json']),restore_reference=ref,restored_members=len(files),restored_bytes=sum(map(len,files.values())),probe=probe,denial_probes=denials,primary_reads_blocked=True,recovery_mode='cold_existing_independent_restore',storage_writes=0,source_arrays_read=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),driver_bytes=torch.mps.driver_allocated_memory(),source_pins=pins(),original_source_pins=old.pins()));signal.alarm(0)


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',choices=['profile','real']);a=p.parse_args()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Guarded recovery deadline')))
    if a.worker:worker(a.worker);return
    old.pins();ROOT.mkdir();source.put(ROOT/'invocation.json',dict(decision='D-324',source_pins=pins(),producer_request_pins={m:digest(((old.PROFILE if m=='profile' else old.DEST)/'request.json').read_bytes()) for m in ('profile','real')},limits=old.LIMITS,storage_ceilings=old.budget()))
    # Single controller holds the existing MPS lock; inherited handles exclude primary.
    import fcntl
    fd=os.open(old.ROOT/'.mps-profile.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);ac,_=old.power();require(ac,'AC required')
        for mode in ('real',):
            env_mode=os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK');os.environ['PYTORCH_ENABLE_MPS_FALLBACK']='0'
            report=prior.supervise([sys.executable,'-m','scripts.diagnostics.segmenter_inference_guarded_recovery','--worker',mode],1200,old.LIMITS['rss_bytes'],ROOT/(mode+'.log'));source.put(ROOT/(mode+'-supervision.json'),report)
            ac,_=old.power();require(ac,'AC power required through recovery')
        source.put(ROOT/'result.json',dict(state='passed',decision='D-324',modes=['real'],source_pins=pins(),source_arrays_read=0,model_updates=0));print(prior.package(ROOT))
    finally:os.close(fd)

if __name__=='__main__':main()
