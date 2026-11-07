"""One exact-identity restoration from local training archives; no model/test reads."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.operations.full_training_platform import require_ac,watch_windows,training_guard
from scripts.acquisition.download_pants_windows_20261029 import check as volume_check


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def write(p,value):
    with Path(p).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2);f.flush();os.fsync(f.fileno())


def copy_exact(source,destination,expected,check):
    h=hashlib.sha256();n=0
    with destination.open('xb') as f:
        for b in iter(lambda:source.read(1024**2),b''):
            check();n+=len(b)
            if n>expected['bytes']:raise ValueError('Oversize CT')
            f.write(b);h.update(b)
        f.flush();os.fsync(f.fileno())
    if n!=expected['bytes'] or h.hexdigest()!=expected['sha256']:
        raise ValueError('CT byte identity mismatch')


def extract(path,wanted,out,check,record):
    """Consume gzip EOF for CRC, never extract arbitrary archive paths."""
    found={};before=path.stat()
    with gzip.open(path,'rb') as gz:
        with tarfile.open(fileobj=gz,mode='r|') as archive:
            for m in archive:
                check();p=PurePosixPath(m.name)
                if p.is_absolute() or '..' in p.parts or '\\' in m.name or ':' in m.name:
                    raise ValueError('Unsafe archive name')
                if not(m.isdir() or m.isfile()) or m.issym() or m.islnk():raise ValueError('Unsafe archive member')
                name=p.parts[0] if m.isfile() and len(p.parts)==2 and p.parts[1]=='ct.nii.gz' else None
                if name not in wanted:continue
                if name in found or m.size!=wanted[name]['bytes']:raise ValueError('Duplicate/size mismatch')
                destination=out/(name+'.nii.gz.part')
                with archive.extractfile(m) as f:copy_exact(f,destination,wanted[name],check)
                final=out/(name+'.nii.gz')
                if final.exists():raise FileExistsError('Refusing replacement')
                destination.rename(final)
                found[name]=dict(wanted[name],path=str(final))
                record('ct_verified',case_id=name,bytes=m.size)
        while gz.read(1024**2):check()
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Archive mutated')
    if set(found)!=set(wanted):raise ValueError('Missing requested archive members')
    return found


def worker(request):
    r=json.loads(request.read_text());out=Path(r['output']);start=time.monotonic()
    journal=out/'progress.jsonl';found={};written=0
    def check():
        volume_check()
        if shutil.disk_usage('C:/').free<100*1024**3:raise RuntimeError('C free floor')
        if time.monotonic()-start>r['seconds']:raise TimeoutError('Restoration cap')
    def record(event,**kw):
        with journal.open('a',encoding='utf-8') as f:
            f.write(json.dumps(dict(event=event,seconds=time.monotonic()-start,**kw))+'\n');f.flush();os.fsync(f.fileno())
    try:
        check()
        for p,h in r['pins'].items():
            if digest(p)!=h:raise ValueError('Producing pin changed: '+p)
        with training_guard(out/'.restore.lock'):
            for name,row in r['cases'].items():
                if row.get('existing_path'):
                    p=Path(row['existing_path'])
                    if p.stat().st_size!=row['bytes'] or digest(p)!=row['sha256']:raise ValueError('Reused CT differs: '+name)
                    found[name]=dict(row,path=str(p));check()
            record('reuse_verified',cases=len(found))
            for item in r['archives']:
                path=Path(item['path']);wanted={n:v for n,v in r['cases'].items() if not v.get('existing_path') and item['low']<=int(n.split('_')[-1])<=item['high']}
                if not wanted:continue
                if path.stat().st_size!=item['bytes']:raise ValueError('Archive size changed')
                record('archive_started',name=path.name,wanted=len(wanted))
                new=extract(path,wanted,out,check,record);found.update(new)
                written+=sum(x['bytes'] for x in new.values())
                if written>r['new_bytes_cap']:raise ValueError('Output cap')
                record('archive_crc_verified',name=path.name,completed=len(found),total=len(r['cases']))
            if set(found)!=set(r['cases']):raise ValueError('Incomplete cohort')
            write(out/'restoration.json',dict(status='EXACT_CT_BYTES_ONLY',cases=found,source_ready=False,seconds=time.monotonic()-start))
            record('completed',cases=len(found),new_bytes=written)
    except BaseException as e:
        record('failed',error=repr(e),partials_preserved=True);raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--sha256');p.add_argument('--worker',action='store_true');a=p.parse_args()
    request=Path(a.request)
    if a.worker:return worker(request)
    if not a.sha256 or digest(request)!=a.sha256:raise ValueError('Request hash required')
    r=json.loads(request.read_text());out=Path(r['output']);out.mkdir(exist_ok=False)
    if r['new_bytes']>r['new_bytes_cap']:raise ValueError('Output request cap')
    volume_check(r['new_bytes']);require_ac()
    write(out/'dispatch.json',dict(request=str(request),sha256=a.sha256,supervisor=os.getpid()))
    child=None
    try:
        with (out/'worker.log').open('x') as log:
            child=subprocess.Popen([sys.executable,__file__,'--request',str(request),'--worker'],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            write(out/'owner.json',dict(worker=child.pid,supervisor=os.getpid()))
            result=watch_windows(child,seconds=r['seconds']+60,rss_bytes=r['rss_bytes'],tick=require_ac)
            write(out/'resources.json',dict(result,success=True,exit_code=child.returncode))
    except BaseException as e:
        write(out/'resources.json',dict(getattr(child,'duration_resources',{}),success=False,error=repr(e)));raise


if __name__=='__main__':main()
