"""Bounded resumed range acquisition; preserves the slower eight-connection attempt."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import threading
import time
import urllib.request

from scripts.stunet_audit.download_totalseg_v1 import URL,SIZE,MD5

ROOT=Path('/Volumes/PROWL-Data/PROWL/sources/totalsegmentator-v1-audit-20261106-ranges-03')
CHUNK=16*1024**2

def main():
    ROOT.mkdir(parents=True,exist_ok=False);(ROOT/'parts').mkdir()
    request=dict(url=URL,expected_bytes=SIZE,publisher_md5=MD5,max_connections=32,range_bytes=CHUNK,
                 max_seconds=3600,minimum_free_bytes=100*1024**3,automatic_retries=0,
                 predecessor='/Volumes/PROWL-Data/PROWL/sources/totalsegmentator-v1-audit-20261106/download.json')
    (ROOT/'request.json').write_text(json.dumps(request,indent=2))
    start=time.monotonic();stop=threading.Event();completed=0
    predecessor=ROOT.parent/'totalsegmentator-v1-audit-20261106-ranges-02'
    reused=[]
    for source in sorted((predecessor/'parts').glob('*.part')):
        index=int(source.stem);expected=min(CHUNK,SIZE-index*CHUNK)
        if source.stat().st_size!=expected:raise ValueError('Predecessor completed part size differs')
        destination=ROOT/'parts'/source.name
        os.link(source,destination);completed+=expected
        reused.append(dict(index=index,bytes=expected,sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    (ROOT/'reuse.json').write_text(json.dumps(reused,indent=2))
    def fetch(index):
        if stop.is_set():raise RuntimeError('Earlier range failed; no retry')
        begin=index*CHUNK;end=min(SIZE,begin+CHUNK)-1;count=0
        if time.monotonic()-start>3600 or shutil.disk_usage(ROOT).free<100*1024**3:
            stop.set();raise RuntimeError('Elapsed/storage bound')
        req=urllib.request.Request(URL,headers={'Range':f'bytes={begin}-{end}','User-Agent':'PROWL-provenance-audit/1'})
        try:
            with urllib.request.urlopen(req,timeout=45) as r:
                if r.status!=206 or r.headers.get('Content-Range')!=f'bytes {begin}-{end}/{SIZE}':
                    raise ValueError('Range identity differs')
                path=ROOT/'parts'/f'{index:05d}.partial'
                with path.open('xb') as f:
                    while block:=r.read(1024**2):
                        if stop.is_set() or time.monotonic()-start>3600:raise RuntimeError('Stop/time bound')
                        count+=len(block)
                        if count>end-begin+1:raise ValueError('Range exceeded')
                        f.write(block)
                if count!=end-begin+1:raise ValueError('Truncated range')
                path.rename(path.with_suffix('.part'))
            return count
        except Exception:
            stop.set();raise
    result={}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
            futures={pool.submit(fetch,i):i for i in range((SIZE+CHUNK-1)//CHUNK) if not (ROOT/'parts'/f'{i:05d}.part').exists()}
            for f in concurrent.futures.as_completed(futures):
                completed+=f.result()
                if completed//(256*1024**2)>(completed-CHUNK)//(256*1024**2):
                    print(json.dumps(dict(bytes=completed,seconds=round(time.monotonic()-start,1))),flush=True)
        md5=hashlib.md5();sha=hashlib.sha256();total=0
        destination=ROOT/'Totalsegmentator_dataset.zip.partial'
        with destination.open('xb') as f:
            for path in sorted((ROOT/'parts').glob('*.part')):
                with path.open('rb') as part:
                    while block:=part.read(8*1024**2):
                        f.write(block);md5.update(block);sha.update(block);total+=len(block)
        if total!=SIZE or md5.hexdigest()!=MD5:raise ValueError('Final archive checksum/size mismatch')
        destination.rename(destination.with_suffix(''))
        result=dict(status='VERIFIED',bytes=total,md5=md5.hexdigest(),sha256=sha.hexdigest(),seconds=time.monotonic()-start,
                    parts_retained=True)
    except Exception as e:
        result=dict(status='FAILED_PARTIALS_PRESERVED',completed_bytes=completed,error=repr(e),seconds=time.monotonic()-start)
    (ROOT/'download.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
    if result['status']!='VERIFIED':raise SystemExit(1)

if __name__=='__main__':main()
