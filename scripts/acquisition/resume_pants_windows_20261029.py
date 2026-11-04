"""Explicitly authorized continuation; preserves original log and partial bytes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import hashlib, json, os, time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from scripts.acquisition import download_pants_windows_20261029 as old
from scripts.acquisition.download_panorama_windows import retry_delay, validate_response

def transfer(item, record):
    name=item['name']
    if Path(name).name!=name or any(c in name for c in '/\\:'):
        raise ValueError('Unsafe name')
    final=old.DEST/name; part=old.DEST/(name+'.part')
    for p in (final,part):
        if p.is_symlink() or p.is_junction(): raise ValueError('Linked payload')
    if final.exists(): raise FileExistsError('No overwrites')
    offset=part.stat().st_size if part.exists() else 0
    if offset>item['bytes']: raise ValueError('Oversize partial')
    old.check(item['bytes']-offset)
    if offset<item['bytes']:
        headers={'Accept-Encoding':'identity','User-Agent':'PROWL-source-recovery/2.0'}
        if offset: headers['Range']=f'bytes={offset}-'
        if item.get('etag'): headers['If-Match']=item['etag']
        record('starting',name=name,resume_bytes=offset,expected_bytes=item['bytes'])
        with urlopen(Request(item['url'],headers=headers),timeout=60) as response:
            validate_response(response.status,response.headers,offset,item['bytes'])
            if item.get('etag') and response.headers.get('ETag')!=item['etag']:
                raise ValueError('Label entity changed')
            count=offset; last=time.monotonic()
            with part.open('ab' if offset else 'xb') as f:
                try:
                    for block in iter(lambda:response.read1(old.CHUNK),b''):
                        if count+len(block)>item['bytes']: raise ValueError('Oversize transfer')
                        old.check(len(block)); f.write(block); count+=len(block)
                        if time.monotonic()-last>=30:
                            f.flush();record('progress',name=name,bytes=count,expected_bytes=item['bytes']);last=time.monotonic()
                finally:
                    f.flush();os.fsync(f.fileno())
        if count!=item['bytes']: raise ConnectionError('Short network transfer; partial preserved')
    old.check(); digest=old.verify(part,item)
    if final.exists(): raise FileExistsError('Destination appeared')
    part.rename(final)
    record('verified_download',name=name,bytes=item['bytes'],sha256=digest)

def main():
    old.check()
    for p in [old.DEST,*old.DEST.parents]:
        if p.is_symlink() or p.is_junction(): raise ValueError('Linked destination')
    inventory=old.ROOT/'docs/capstone/data/acquisition-2026-09-19.json'
    raw=inventory.read_bytes(); pants=json.loads(raw)['pants']
    queue=[pants['files'][0],dict(pants['labels'],name='PanTSMini_Label.tar.gz'),*pants['files'][1:]]
    prior=(old.DEST/'events.jsonl').read_bytes()
    records=[json.loads(line) for line in prior.splitlines()]
    if records[-1]['event']!='failed': raise ValueError('Original failure required')
    verified={r['name']:r for r in records if r['event']=='verified_download'}
    old.check(sum(i['bytes'] for i in queue if i['name'] not in verified))
    with old.training_guard(old.DEST/'.download.lock'), (old.DEST/'continuation-01.jsonl').open('x') as log:
        def record(event,**kw):
            line=json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),event=event,**kw))
            log.write(line+'\n');log.flush();os.fsync(log.fileno());print(line,flush=True)
        record('continuation_started',original_log_sha256=hashlib.sha256(prior).hexdigest(),
               inventory_sha256=hashlib.sha256(raw).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               max_network_retries_per_file=8,extraction=False,source_ready=False)
        try:
            for item in queue:
                if item['name'] in verified:
                    p=old.DEST/item['name']; receipt=verified[item['name']]
                    if p.is_symlink() or p.is_junction() or p.stat().st_size!=item['bytes'] or receipt['bytes']!=item['bytes']:
                        raise ValueError('Completed file size/type mismatch')
                    if item.get('sha256') and receipt['sha256']!=item['sha256']: raise ValueError('Receipt mismatch')
                    record('reused_prior_verified_file',name=item['name'],sha256=receipt['sha256'],freshly_rehashed=False)
                    continue
                for retry in range(9):
                    try: transfer(item,record);break
                    except Exception as exc:
                        delay=retry_delay(exc,retry)
                        if delay is None or retry==8: raise
                        record('network_retry',name=item['name'],error=repr(exc),retry=retry+1,delay=delay)
                        while delay>0:
                            old.check();interval=min(5,delay);time.sleep(interval);delay-=interval
            record('archive_queue_complete',extraction=False,source_ready=False)
        except BaseException as exc:
            record('failed',error=repr(exc),partials_retained=True);raise

if __name__=='__main__': main()
