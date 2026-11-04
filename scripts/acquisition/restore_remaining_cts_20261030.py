"""Restore only the 178 unfinished reserved CT inputs; no inference or labels."""
import sys
from pathlib import Path, PurePosixPath
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import hashlib,json,os,tarfile,time
from datetime import datetime,timezone
from scripts.acquisition import download_pants_windows_20261029 as download

BASE=Path('E:/PROWL')
OUT=BASE/'sources/pants/restored-candidate-ct-20261030'
CACHE=BASE/'cache/pants-setup-20261010/cfab5906fce0fe759599990ec3b1a5955eddb77d1b7b60eeb93e171e7b990bf4'
REQUEST=BASE/'readiness/verifier-candidate-export-20261027-a01/request.json'
JOURNAL=BASE/'artifacts/verifier-candidates-20261027-a01/progress.jsonl'

def member_case(m):
    p=PurePosixPath(m.name)
    if p.is_absolute() or '..' in p.parts or '\\' in m.name or ':' in m.name:
        raise ValueError('Unsafe archive path')
    if m.issym() or m.islnk() or not (m.isdir() or m.isfile()):
        raise ValueError('Unsupported archive member')
    return p.parts[0] if m.isfile() and len(p.parts)==2 and p.parts[1]=='ct.nii.gz' else None

def main():
    if OUT.exists(): raise FileExistsError('Restoration already started; inspect evidence')
    download.check()
    request=json.loads(REQUEST.read_text())
    if hashlib.sha256(REQUEST.read_bytes()).hexdigest()!='edd8824e401aad8e5d8aefbf228f876931f3e792caaa457a7b28b32ca38b6a31':
        raise ValueError('Frozen export request changed')
    completed=[json.loads(l)['case_id'] for l in JOURNAL.read_text().splitlines() if json.loads(l)['event']=='case_completed']
    if len(completed)!=355 or len(set(completed))!=355: raise ValueError('Completion membership changed')
    cases={c['case_id']:c for c in request['cases'] if c['case_id'] not in completed}
    if len(cases)!=178: raise ValueError('Remaining membership changed')
    control=json.loads((CACHE/'control.json').read_text())
    expected={n:dict(bytes=control['observations'][n]['ct']['bytes'],sha256=json.loads((CACHE/(n+'.json')).read_text())['source_sha256']['ct']) for n in cases}
    budget=sum(x['bytes'] for x in expected.values())
    if budget>7*1024**3: raise ValueError('Restoration budget')
    download.check(budget)
    inv=json.loads((download.ROOT/'docs/capstone/data/acquisition-2026-09-19.json').read_text())
    receipts={}
    for name in ('events.jsonl','continuation-01.jsonl','continuation-02.jsonl'):
        for line in (download.DEST/name).read_text().splitlines():
            r=json.loads(line)
            if r['event']=='verified_download': receipts[r['name']]=r
    archives=[]
    for item in inv['pants']['files']:
        if item['kind']!='training_archive': continue
        lo,hi=map(int,item['name'].removesuffix('.tar.gz').split('_')[-2:])
        if not any(lo<=int(n.split('_')[-1])<=hi for n in cases): continue
        receipt=receipts[item['name']];path=download.DEST/item['name']
        if path.stat().st_size!=item['bytes'] or receipt['sha256']!=item['sha256']: raise ValueError('Archive receipt mismatch')
        archives.append((item,path))
    OUT.mkdir()
    started=time.monotonic(); found={}
    with (OUT/'progress.jsonl').open('x') as log:
        def record(event,**kw):
            line=json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),event=event,**kw))
            log.write(line+'\n');log.flush();os.fsync(log.fileno());print(line,flush=True)
        def check(needed=0):
            download.check(needed)
            if time.monotonic()-started>7200: raise TimeoutError('Two-hour restoration cap')
        record('started',patients=178,expected_bytes=budget,archives=len(archives),test_reads=False,lesion_reads=False,
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        try:
            for item,path in archives:
                before=path.stat();record('archive_started',name=item['name'])
                with tarfile.open(path,'r|gz') as archive:
                    for m in archive:
                        check();n=member_case(m)
                        if n not in cases: continue
                        if n in found: raise ValueError('Duplicate CT member')
                        e=expected[n]
                        if m.size!=e['bytes']: raise ValueError('Original CT size mismatch: '+n)
                        check(m.size);target=OUT/(n+'.nii.gz.part');h=hashlib.sha256();count=0
                        with archive.extractfile(m) as src,target.open('xb') as dst:
                            for block in iter(lambda:src.read(1024**2),b''):
                                check();dst.write(block);h.update(block);count+=len(block)
                            dst.flush();os.fsync(dst.fileno())
                        if count!=m.size or h.hexdigest()!=e['sha256']: raise ValueError('Original CT byte identity mismatch: '+n)
                        final=OUT/(n+'.nii.gz');target.rename(final)
                        found[n]=dict(path=str(final),bytes=count,sha256=h.hexdigest(),role=cases[n]['role'])
                        record('ct_verified',case_id=n,completed=len(found),bytes=count)
                after=path.stat()
                if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns): raise ValueError('Archive changed during read')
            if set(found)!=set(cases): raise ValueError('Missing CT inputs')
            with (OUT/'restoration.json').open('x') as f:
                json.dump(dict(status='BYTE_IDENTICAL_CT_RESTORATION_ONLY',cases=found,source_ready=False),f);f.flush();os.fsync(f.fileno())
            record('completed',patients=len(found),seconds=time.monotonic()-started,source_ready=False)
        except BaseException as exc:
            record('failed',error=repr(exc),partials_preserved=True);raise

if __name__=='__main__':main()
