"""User-approved continuation02 after pause; reuse unchanged range-transfer code."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.acquisition import resume_pants_windows_20261029 as prior
import hashlib, json, os, time
from datetime import datetime, timezone

def receipts(logs):
    result={}
    for raw in logs:
        for line in raw.splitlines():
            r=json.loads(line)
            if r['event']=='verified_download':
                if r['name'] in result and result[r['name']]['sha256']!=r['sha256']:
                    raise ValueError('Conflicting receipts')
                result[r['name']]=r
    return result

def main():
    old=prior.old
    old.check()
    for p in [old.DEST,*old.DEST.parents]:
        if p.is_symlink() or p.is_junction(): raise ValueError('Linked destination')
    raw=(old.ROOT/'docs/capstone/data/acquisition-2026-09-19.json').read_bytes()
    pants=json.loads(raw)['pants']
    queue=[pants['files'][0],dict(pants['labels'],name='PanTSMini_Label.tar.gz'),*pants['files'][1:]]
    logs={name:(old.DEST/name).read_bytes() for name in ('events.jsonl','continuation-01.jsonl')}
    verified=receipts(logs.values())
    old.check(sum(i['bytes'] for i in queue if i['name'] not in verified))
    with old.training_guard(old.DEST/'.download.lock'), (old.DEST/'continuation-02.jsonl').open('x') as log:
        def record(event,**kw):
            line=json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),event=event,**kw))
            log.write(line+'\n');log.flush();os.fsync(log.fileno());print(line,flush=True)
        record('continuation_started',reason='explicit_user_resume_after_pause',
               prior_log_hashes={k:hashlib.sha256(v).hexdigest() for k,v in logs.items()},
               inventory_sha256=hashlib.sha256(raw).hexdigest(),
               producer_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(prior.__file__),Path(old.__file__))},
               max_network_retries_per_file=8,extraction=False,source_ready=False)
        try:
            for item in queue:
                if item['name'] in verified:
                    p=old.DEST/item['name'];r=verified[item['name']]
                    if p.is_symlink() or p.is_junction() or p.stat().st_size!=item['bytes'] or r['bytes']!=item['bytes']:
                        raise ValueError('Completed payload size/type mismatch')
                    if item.get('sha256') and r['sha256']!=item['sha256']: raise ValueError('Receipt mismatch')
                    record('reused_prior_verified_file',name=item['name'],sha256=r['sha256'],freshly_rehashed=False)
                    continue
                for retry in range(9):
                    try: prior.transfer(item,record);break
                    except Exception as exc:
                        delay=prior.retry_delay(exc,retry)
                        if delay is None or retry==8: raise
                        record('network_retry',name=item['name'],error=repr(exc),retry=retry+1,delay=delay)
                        while delay>0:
                            old.check();interval=min(5,delay);time.sleep(interval);delay-=interval
            record('archive_queue_complete',source_ready=False,extraction=False)
        except BaseException as exc:
            record('failed',error=repr(exc),partials_retained=True);raise

if __name__=='__main__': main()
