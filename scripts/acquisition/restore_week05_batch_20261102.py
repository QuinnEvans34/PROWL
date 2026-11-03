"""One bounded four-CT restoration; exact old identities, no label/test extraction."""
import sys,json,os,tarfile,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.acquisition import download_pants_windows_20261029 as source
from scripts.acquisition.restore_remaining_cts_20261030 import member_case,CACHE
from scripts.diagnostics.qualify_matched_physical_cascade_20261102 import sha,write,resource_gate,supervise
OUT=Path('E:/PROWL/sources/pants/week05-batch-20261102-a01')
EVIDENCE=Path('E:/PROWL/readiness/week05-four-case-20261102-a01')
SPEC=ROOT/'docs/capstone/operations/WEEK-05-FOUR-CASE-EXCEPTION-20261102.json'

def restore():
    spec=json.loads(SPEC.read_text()); names=spec['cases'];control=json.loads((CACHE/'control.json').read_text())
    expected={n:dict(bytes=control['observations'][n]['ct']['bytes'],sha256=json.loads((CACHE/(n+'.json')).read_text())['source_sha256']['ct']) for n in names}
    if sum(v['bytes'] for v in expected.values())>256*1024**2:raise ValueError('Restore byte cap')
    resource_gate();OUT.mkdir();start=time.monotonic();found={}
    write(OUT/'request.json',dict(expected=expected,exception_sha256=sha(SPEC),script_sha256=sha(__file__),seconds=4800,rss_bytes=2*1024**3))
    inventory=json.loads((ROOT/'docs/capstone/data/acquisition-2026-09-19.json').read_text())
    receipts={}
    for log in ('events.jsonl','continuation-01.jsonl','continuation-02.jsonl'):
        for line in (source.DEST/log).read_text().splitlines():
            r=json.loads(line)
            if r['event']=='verified_download':receipts[r['name']]=r
    def event(**r):
        with (OUT/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(seconds=time.monotonic()-start,**r))+'\n')
    try:
        for item in inventory['pants']['files']:
            if item['kind']!='training_archive':continue
            lo,hi=map(int,item['name'].removesuffix('.tar.gz').split('_')[-2:])
            wanted={n for n in names if lo<=int(n.split('_')[-1])<=hi}
            if not wanted:continue
            p=source.DEST/item['name'];before=p.stat()
            if before.st_size!=item['bytes'] or receipts[item['name']]['sha256']!=item['sha256']:raise ValueError('Archive receipt changed')
            event(stage='archive_started',archive=item['name']);last=0
            with tarfile.open(p,'r|gz') as tar:
                for m in tar:
                    if time.monotonic()-start>4800:raise TimeoutError('Restore cap')
                    if time.monotonic()-last>10:resource_gate();event(stage='scanning',archive=item['name'],uncompressed_offset=m.offset);last=time.monotonic()
                    n=member_case(m)
                    if n not in wanted:continue
                    if n in found or m.size!=expected[n]['bytes']:raise ValueError('Member identity/duplicate')
                    dest=OUT/(n+'.nii.gz.part');h=hashlib.sha256()
                    with tar.extractfile(m) as src,dest.open('xb') as f:
                        for block in iter(lambda:src.read(1024**2),b''):f.write(block);h.update(block)
                        f.flush();os.fsync(f.fileno())
                    if h.hexdigest()!=expected[n]['sha256']:raise ValueError('CT hash mismatch')
                    final=OUT/(n+'.nii.gz');dest.rename(final);found[n]=dict(path=str(final),**expected[n]);event(stage='ct_verified',case_id=n)
                    if wanted.issubset(found):break
            after=p.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Archive changed')
        if set(found)!=set(names):raise ValueError('Missing CT')
        write(OUT/'restoration.json',dict(status='EXACT_FOUR_CT_RESTORED',cases=found,seconds=time.monotonic()-start));event(stage='completed')
    except BaseException as e:write(OUT/'failure.json',dict(error=repr(e)));raise

if __name__=='__main__':
    if '--worker' in sys.argv:restore()
    else:
        if OUT.exists() or (EVIDENCE/'restore.log').exists():raise FileExistsError('Already started; no retry')
        EVIDENCE.mkdir(exist_ok=True);resource_gate()
        supervise([sys.executable,__file__,'--worker'],log=EVIDENCE/'restore.log',seconds=4800,rss_bytes=2*1024**3,tick=resource_gate)
