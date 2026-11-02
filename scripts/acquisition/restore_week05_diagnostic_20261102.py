"""One exact CT from an already verified training archive, never masks/test data."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.acquisition import download_pants_windows_20261029 as source
from scripts.acquisition.restore_remaining_cts_20261030 import member_case

OUT=Path('E:/PROWL/sources/pants/week05-diagnostic-20261102-a01')
NAME='PanTSMini_ImageTr_00001001_00002000.tar.gz'
EXPECTED='90bf329d4a959144dfc453c5f1adce83ac18b1d5493984cb8aaa3911a1f1000f'


def main():
    if OUT.exists():raise FileExistsError('Restoration already started; inspect, never repeat')
    source.check(64*1024**2)
    inventory=json.loads((ROOT/'docs/capstone/data/acquisition-2026-09-19.json').read_text())
    item=next(i for i in inventory['pants']['files'] if i['name']==NAME and i['kind']=='training_archive')
    receipts=[]
    for name in ('events.jsonl','continuation-01.jsonl','continuation-02.jsonl'):
        receipts += [json.loads(line) for line in (source.DEST/name).read_text().splitlines()
                     if line.strip()]
    if not any(r.get('event')=='verified_download' and r.get('name')==NAME and r.get('sha256')==item['sha256'] for r in receipts):
        raise ValueError('Prior verified archive receipt missing')
    archive=source.DEST/NAME;before=archive.stat()
    if before.st_size!=item['bytes']:raise ValueError('Archive size changed')
    OUT.mkdir();start=time.monotonic();last=0
    try:
        with tarfile.open(archive,'r|gz') as tar:
            for member in tar:
                if time.monotonic()-start>600:raise TimeoutError('Restoration 600s ceiling')
                if time.monotonic()-last>5:
                    source.check();last=time.monotonic()
                if member_case(member)!='PanTS_00001070':continue
                if member.size!=24789800:raise ValueError('CT size differs from prior admission')
                h=hashlib.sha256();partial=OUT/'PanTS_00001070.nii.gz.part'
                with tar.extractfile(member) as src,partial.open('xb') as dst:
                    for chunk in iter(lambda:src.read(1024**2),b''):
                        dst.write(chunk);h.update(chunk)
                    dst.flush();os.fsync(dst.fileno())
                if h.hexdigest()!=EXPECTED:raise ValueError('CT bytes differ from original')
                after=archive.stat()
                if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Archive changed')
                target=OUT/'PanTS_00001070.nii.gz';partial.rename(target)
                result=dict(status='EXACT_CT_RESTORED',path=str(target),sha256=EXPECTED,bytes=member.size,
                    seconds=time.monotonic()-start,source_archive=NAME,source_archive_receipt_sha256=item['sha256'],
                    test_reads=False,mask_reads=False)
                (OUT/'restoration.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
                return
        raise ValueError('Diagnostic CT absent from expected training archive')
    except BaseException as exc:
        (OUT/'failure.json').write_text(json.dumps(dict(error=repr(exc),seconds=time.monotonic()-start)))
        raise


if __name__=='__main__':main()
