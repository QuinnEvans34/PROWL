"""One authorized original TotalSegmentator v1 acquisition; no automatic retry."""
import hashlib
import json
import shutil
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Volumes/PROWL-Data/PROWL/sources/totalsegmentator-v1-audit-20261106')
URL = 'https://zenodo.org/records/6802614/files/Totalsegmentator_dataset.zip?download=1'
SIZE = 28404091806
MD5 = 'f0fbb3f91d9d99f2169863545f577b30'

def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    request = dict(schema='prowl.public-acquisition.v1', url=URL, expected_bytes=SIZE,
                   publisher_md5=MD5, max_seconds=3600, external_free_floor=100*1024**3,
                   automatic_retries=0, authorized_scope='Original v1 archive and bounded local CPU overlap audit',
                   started_utc=datetime.now(timezone.utc).isoformat())
    (ROOT/'request.json').write_text(json.dumps(request, indent=2))
    start=time.monotonic(); total=0; md5=hashlib.md5(); sha=hashlib.sha256(); last=0
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, headers={'User-Agent':'PROWL-provenance-audit/1'}), timeout=60) as response:
            if int(response.headers.get('Content-Length', '-1')) != SIZE:
                raise ValueError('Unexpected archive Content-Length')
            with (ROOT/'Totalsegmentator_dataset.zip.partial').open('xb') as output:
                while block := response.read(8*1024**2):
                    if time.monotonic()-start>3600: raise RuntimeError('Download time bound')
                    if shutil.disk_usage(ROOT).free<100*1024**3: raise RuntimeError('External free-space floor')
                    total+=len(block)
                    if total>SIZE: raise RuntimeError('Archive size bound')
                    output.write(block); md5.update(block); sha.update(block)
                    if total-last>=512*1024**2:
                        print(json.dumps(dict(bytes=total, expected=SIZE, seconds=round(time.monotonic()-start,1))), flush=True)
                        last=total
        if total!=SIZE or md5.hexdigest()!=MD5: raise ValueError('Published size/MD5 verification failed')
        (ROOT/'Totalsegmentator_dataset.zip.partial').rename(ROOT/'Totalsegmentator_dataset.zip')
        result=dict(status='VERIFIED',bytes=total,md5=md5.hexdigest(),sha256=sha.hexdigest(),seconds=time.monotonic()-start)
    except Exception as error:
        result=dict(status='FAILED_PARTIAL_PRESERVED',bytes=total,md5_partial=md5.hexdigest(),sha256_partial=sha.hexdigest(),
                    seconds=time.monotonic()-start,error=repr(error))
    (ROOT/'download.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
    if result['status']!='VERIFIED':raise SystemExit(1)

if __name__=='__main__':main()
