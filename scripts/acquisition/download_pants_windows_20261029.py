"""Fresh archive-only recovery; original acquisition and training pins untouched."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.acquisition.download_panorama_windows import volume_id, validate_response
from src.operations.full_training_platform import require_ac, training_guard

MOUNT = Path('E:/')
VOLUME = '\\\\?\\Volume{424d39a3-ac76-4f41-aa1c-8b9f5ce0b829}\\'
DEST = MOUNT / 'PROWL/sources/pants/acquisition-20261029'
FLOOR = 100 * 1024**3
CHUNK = 1024**2

def check(needed=0):
    if volume_id(MOUNT) != VOLUME:
        raise RuntimeError('Destination volume absent/changed')
    require_ac()
    if shutil.disk_usage(MOUNT).free < FLOOR + needed:
        raise RuntimeError('100 GiB free-space floor')

def verify(path, item):
    if path.stat().st_size != item['bytes']:
        raise ValueError('Wrong downloaded size')
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8*CHUNK), b''):
            h.update(block)
    actual = h.hexdigest()
    if item.get('sha256') and actual != item['sha256']:
        raise ValueError('Publisher checksum mismatch; preserved')
    return actual

def transfer(item, record):
    name = item['name']
    if Path(name).name != name or any(c in name for c in '/\\:'):
        raise ValueError('Unsafe name')
    final, partial = DEST/name, DEST/(name+'.part')
    if final.exists() or partial.exists():
        raise FileExistsError('One fresh attempt only; no overwrite or implicit resume')
    check(item['bytes'])
    headers = {'Accept-Encoding':'identity', 'User-Agent':'PROWL-source-recovery/1.0'}
    if item.get('etag'):
        headers['If-Match'] = item['etag']
    record('starting', name=name, expected_bytes=item['bytes'])
    with urlopen(Request(item['url'], headers=headers), timeout=60) as response:
        validate_response(response.status, response.headers, 0, item['bytes'])
        if item.get('etag') and response.headers.get('ETag') != item['etag']:
            raise ValueError('Label entity changed')
        count = 0
        last = time.monotonic()
        with partial.open('xb') as f:
            try:
                for block in iter(lambda: response.read1(CHUNK), b''):
                    if count + len(block) > item['bytes']:
                        raise ValueError('Oversize response')
                    check(len(block))
                    f.write(block)
                    count += len(block)
                    if time.monotonic()-last >= 30:
                        f.flush()
                        record('progress', name=name, bytes=count, expected_bytes=item['bytes'])
                        last = time.monotonic()
            finally:
                f.flush()
                os.fsync(f.fileno())
    check()
    digest = verify(partial, item)
    if final.exists():
        raise FileExistsError('Refusing overwrite')
    partial.rename(final)
    record('verified_download', name=name, bytes=count, sha256=digest,
           publisher_sha256_available=bool(item.get('sha256')))

def main():
    inventory = ROOT/'docs/capstone/data/acquisition-2026-09-19.json'
    raw = inventory.read_bytes()
    pants = json.loads(raw)['pants']
    queue = [pants['files'][0], dict(pants['labels'],name='PanTSMini_Label.tar.gz'), *pants['files'][1:]]
    check(sum(x['bytes'] for x in queue))
    current = MOUNT
    for part in DEST.relative_to(MOUNT).parts:
        current = current/part
        if current.is_symlink() or current.is_junction():
            raise ValueError('Linked destination')
        current.mkdir(exist_ok=True)
    with training_guard(DEST/'.download.lock'), (DEST/'events.jsonl').open('x') as log:
        def record(event, **kw):
            line = json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),event=event,**kw))
            log.write(line+'\n'); log.flush(); os.fsync(log.fileno())
            print(line,flush=True)
        record('started', volume_id=VOLUME, total_bytes=sum(x['bytes'] for x in queue),
               inventory_sha256=hashlib.sha256(raw).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               free_floor_bytes=FLOOR, extraction=False, source_ready=False,
               publisher_test_archive='opaque_only', automatic_retry=False)
        try:
            for item in queue:
                transfer(item,record)
            record('archive_queue_complete', source_ready=False, extraction=False)
        except BaseException as exc:
            record('failed', error=repr(exc), partials_retained=True)
            raise

if __name__ == '__main__':
    main()
