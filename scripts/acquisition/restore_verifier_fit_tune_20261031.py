"""Restore exact CT bytes for fit/tune only; no masks, inference or training."""
import sys,json,hashlib,os,time,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.acquisition import restore_remaining_cts_20261030 as prior
from scripts.acquisition import download_pants_windows_20261029 as download
from src.operations.verifier_candidate_archive_v1 import write_json,append_event
from src.training.experiment_config import sha256
OUT=Path('E:/PROWL/sources/pants/verifier-fit-tune-ct-20261031')
PART=Path('E:/PROWL/readiness/verifier-generator-20261023-a01/partitions.json')

def copy_exact(source,dest,expected):
    h=hashlib.sha256();count=0
    with dest.open('xb') as f:
        for block in iter(lambda:source.read(1024**2),b''):
            download.check(len(block));count+=len(block)
            if count>expected['bytes']:raise ValueError('Oversize CT')
            f.write(block);h.update(block)
        f.flush();os.fsync(f.fileno())
    if count!=expected['bytes'] or h.hexdigest()!=expected['sha256']:raise ValueError('CT identity differs')

def main():
    if OUT.exists():raise ValueError('Restore already started')
    if sha256(PART)!='e70e110078d59d35b4171a9711bd2e0ea1ffa9f25aaf405e0d010f31e030fd35':raise ValueError('Partition changed')
    part=json.loads(PART.read_text());roles={n:role for role in ('verifier_fit','verifier_tune') for n in part['roles'][role]}
    existing=json.loads((prior.OUT/'restoration.json').read_text())['cases']
    control=json.loads((prior.CACHE/'control.json').read_text())
    expected={n:dict(bytes=control['observations'][n]['ct']['bytes'],sha256=json.loads((prior.CACHE/(n+'.json')).read_text())['source_sha256']['ct']) for n in roles}
    missing=set(roles)-set(existing);size=sum(expected[n]['bytes'] for n in missing)
    if len(roles)!=333 or size>8*1024**3:raise ValueError('Source scope/budget')
    download.check(size);OUT.mkdir();began=time.monotonic();found={}
    write_json(OUT/'request.json',dict(cases=roles,missing=sorted(missing),expected_new_bytes=size,seconds=10800,new_bytes_cap=8*1024**3,
        script_sha256=sha256(__file__),partition_sha256=sha256(PART),prior_restoration_sha256=sha256(prior.OUT/'restoration.json')))
    journal=OUT/'progress.jsonl'
    def record(event,**kw):append_event(journal,dict(event=event,seconds=time.monotonic()-began,**kw))
    try:
        with download.training_guard(OUT/'.restore.lock'):
            for n in sorted(set(roles)&set(existing)):
                row=existing[n];path=Path(row['path'])
                if row['role']!=roles[n] or path.stat().st_size!=expected[n]['bytes'] or sha256(path)!=expected[n]['sha256']:raise ValueError('Reused CT changed')
                found[n]=row
            record('reused_exact',patients=len(found))
            inv=json.loads((ROOT/'docs/capstone/data/acquisition-2026-09-19.json').read_text())
            receipts={}
            for log in ('events.jsonl','continuation-01.jsonl','continuation-02.jsonl'):
                for line in (download.DEST/log).read_text().splitlines():
                    r=json.loads(line)
                    if r['event']=='verified_download':receipts[r['name']]=r
            for item in inv['pants']['files']:
                if item['kind']!='training_archive':continue
                lo,hi=map(int,item['name'].removesuffix('.tar.gz').split('_')[-2:])
                wanted={n for n in missing if lo<=int(n.split('_')[-1])<=hi}
                if not wanted:continue
                path=download.DEST/item['name'];before=path.stat()
                if before.st_size!=item['bytes'] or receipts[item['name']]['sha256']!=item['sha256']:raise ValueError('Archive receipt mismatch')
                record('archive_started',name=item['name'])
                with tarfile.open(path,'r|gz') as archive:
                    for member in archive:
                        download.check()
                        if time.monotonic()-began>10800:raise TimeoutError('Restore time cap')
                        n=prior.member_case(member)
                        if n not in wanted:continue
                        if n in found or member.size!=expected[n]['bytes']:raise ValueError('Duplicate/wrong CT member')
                        target=OUT/(n+'.nii.gz.part')
                        with archive.extractfile(member) as source:copy_exact(source,target,expected[n])
                        final=OUT/(n+'.nii.gz');target.rename(final)
                        found[n]=dict(path=str(final),role=roles[n],**expected[n]);record('ct_verified',case_id=n,completed=len(found),total=333)
                after=path.stat()
                if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Archive changed')
            if set(found)!=set(roles):raise ValueError('Missing inputs')
            write_json(OUT/'restoration.json',dict(status='BYTE_IDENTICAL_CT_RESTORATION_ONLY',cases=found,source_ready=False))
            record('completed',patients=333,new_cts=len(missing))
    except BaseException as exc:record('failed',message=repr(exc));raise

if __name__=='__main__':main()
