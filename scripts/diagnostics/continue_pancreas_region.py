"""Two bounded chunks using the SAME frozen serial audit function; reuse its prefix."""
import argparse,json,os,sys,time,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import qualify_pancreas_region as audit
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256
from src.operations.full_training_platform import watch_windows,require_ac,durable_replace
BASE=audit.OUT;DEST=BASE/'cohort-complete'


def read(p):return json.loads(Path(p).read_text())
def rows(p):
    if not Path(p).exists():return []
    with Path(p).open() as f:return [json.loads(s) for s in f if s.strip() and s.endswith('\n')]
def write(p,v):
    with Path(p).open('xb') as f:f.write(canonical(v));f.flush();os.fsync(f.fileno())
def checked():
    r=read(DEST/'request.json')
    for p,h in r['pins'].items():
        if sha256(p)!=h:raise ValueError('Continuation pin changed')
    return r


def prepare():
    original=read(BASE/'request.json');stop=read(BASE/'serial-stop.json')
    if not stop['workers_reaped']:raise ValueError('Serial workers still active')
    for p,h in original['pins'].items():
        if sha256(p)!=h:raise ValueError('Original audit changed')
    source=rows(audit.SOURCE);prefix=rows(BASE/'cases.jsonl')
    if [r['case_id'] for r in prefix]!=[r['case_id'] for r in source[:len(prefix)]]:raise ValueError('Not exact prefix')
    if any(not r['coverage_pass'] for r in prefix):raise ValueError('Prior coverage failure')
    DEST.mkdir(exist_ok=False)
    files=[Path(__file__),BASE/'request.json',BASE/'serial-stop.json',BASE/'cases.jsonl',audit.SOURCE]
    remaining=source[len(prefix):]
    for index in range(2):
        chunk=DEST/str(index);chunk.mkdir()
        selected=remaining[index::2]
        with (chunk/'source.jsonl').open('xb') as f:
            for r in selected:f.write(canonical(r))
        request=dict(original,pins=dict(original['pins'],**{str(chunk/'source.jsonl'):sha256(chunk/'source.jsonl')}))
        write(chunk/'request.json',request);files.extend([chunk/'request.json',chunk/'source.jsonl'])
    write(DEST/'request.json',dict(pins={str(p):sha256(p) for p in files},reused=len(prefix),remaining=len(remaining),
        seconds_remaining=7200-stop['charged_seconds'],serial_seconds=stop['charged_seconds'],workers=2,rss_bytes=12*1024**3))
    print(json.dumps(dict(reused=len(prefix),remaining=len(remaining))),flush=True)


def chunk_worker(index):
    checked();audit.OUT=DEST/str(index);audit.SOURCE=audit.OUT/'source.jsonl'
    audit.audit()  # Unmodified pinned numerical/checking code.


def manager():
    request=checked();children=[];logs=[]
    try:
        for i in range(2):
            log=(DEST/str(i)/'worker.log').open('x');logs.append(log)
            children.append(subprocess.Popen([sys.executable,__file__,'--chunk',str(i)],stdout=log,stderr=subprocess.STDOUT,cwd=ROOT))
        while any(p.poll() is None for p in children):
            if any(p.poll() not in (None,0) for p in children):raise ValueError('Chunk failed; no retry')
            current=rows(BASE/'cases.jsonl')+rows(DEST/'0/cases.jsonl')+rows(DEST/'1/cases.jsonl')
            temp=DEST/'progress.partial';write(temp,dict(completed=len(current),total=1403,failures=sum(not r['coverage_pass'] for r in current)))
            durable_replace(temp,DEST/'progress.json');time.sleep(5)
        if any(p.returncode for p in children):raise ValueError('Chunk failed')
        checked();records=rows(BASE/'cases.jsonl')+rows(DEST/'0/cases.jsonl')+rows(DEST/'1/cases.jsonl')
        by_name={r['case_id']:r for r in records};source=rows(audit.SOURCE)
        if len(records)!=1403 or len(by_name)!=1403 or set(by_name)!={r['case_id'] for r in source}:raise ValueError('Incomplete/duplicate cohort')
        with (DEST/'cases.jsonl').open('xb') as f:
            for s in source:
                r=by_name[s['case_id']]
                if r['role']!=s['role']:raise ValueError('Role changed')
                f.write(canonical(r))
            f.flush();os.fsync(f.fileno())
        import numpy as np
        write(DEST/'result.json',dict(completed=True,all_pass=all(r['coverage_pass'] for r in records),cases=1403,
            failed=[r['case_id'] for r in records if not r['coverage_pass']],reused=request['reused'],ct_reads=0,test_reads=0,
            median_region_fraction=float(np.median([r['region_fraction'] for r in records]))))
    finally:
        for p in children:
            if p.poll() is None:p.terminate()
        for p in children:p.wait()
        for f in logs:f.close()


def run():
    request=checked();last=[0.]
    def tick():
        if time.monotonic()-last[0]>10:
            require_ac()
            if any(shutil.disk_usage(d).free<100*1024**3 for d in ('C:/','E:/')):raise ValueError('Disk floor')
            last[0]=time.monotonic()
    tick()
    with (DEST/'worker.log').open('x') as log:
        p=subprocess.Popen([sys.executable,__file__,'--manager'],stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
        try:watch_windows(p,seconds=request['seconds_remaining'],rss_bytes=request['rss_bytes'],tick=tick)
        finally:
            r=getattr(p,'duration_resources',{});r['serial_seconds']=request['serial_seconds']
            r['total_supervised_seconds']=request['serial_seconds']+r.get('seconds',0)
            r['serial_peak_rss_unknown']=True
            write(DEST/'resources.json',r)


if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true');g.add_argument('--manager',action='store_true');g.add_argument('--chunk',type=int,choices=[0,1]);a=ap.parse_args()
    if a.prepare:prepare()
    elif a.run:run()
    elif a.manager:manager()
    else:chunk_worker(a.chunk)
