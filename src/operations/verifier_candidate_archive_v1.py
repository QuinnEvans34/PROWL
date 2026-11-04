"""Durable append-only candidate receipts and independent, verified copies."""
import json,os,shutil
from pathlib import Path
from src.training.experiment_config import sha256

def tree_bytes(root):
    return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())

def check_capacity(*, used_e, used_c, free_e, free_c, reserve_e=0, reserve_c=0):
    if min(reserve_e,reserve_c)<0:raise ValueError('Negative reservation')
    if used_e+reserve_e>64*1024**3 or used_c+reserve_c>40*1024**3:
        raise ValueError('Approved storage cap exceeded')
    if min(free_e-reserve_e,free_c-reserve_c)<100*1024**3:
        raise ValueError('Free-space floor')

def write_json(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,sort_keys=True,allow_nan=False);f.flush();os.fsync(f.fileno())

def backup_file(source,destination,*,reserve=lambda n:None,independent=True):
    source,destination=Path(source),Path(destination)
    if destination.exists() or destination.with_suffix(destination.suffix+'.partial').exists():
        raise ValueError('Backup already started; no overwrite/retry')
    if independent and source.stat().st_dev==destination.parent.stat().st_dev:
        raise ValueError('Independent device required')
    reserve(source.stat().st_size)
    temp=destination.with_suffix(destination.suffix+'.partial')
    with source.open('rb') as a,temp.open('xb') as b:
        shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
    pin=sha256(source)
    if sha256(temp)!=pin:raise ValueError('Independent backup mismatch')
    # Windows rename refuses an existing destination; never replace evidence.
    temp.rename(destination)
    return pin

def append_event(path,row):
    with Path(path).open('ab') as f:
        f.write((json.dumps(row,sort_keys=True,allow_nan=False)+'\n').encode());f.flush();os.fsync(f.fileno())

def process_cases(cases,*,produce,reuse,backup,record,journal,tick):
    """Injectable orchestration; receipt is committed only after BOTH backups."""
    names=[c['case_id'] for c in cases]
    if len(set(names))!=len(names):raise ValueError('Duplicate case schedule')
    completed=[]
    for case in cases:
        tick();n=case['case_id']
        append_event(journal,dict(event='case_started',case_id=n,completed=len(completed)))
        row,path=(reuse(case) if case.get('reuse') else produce(case))
        if row['case_id']!=n or row['role']!=case['role']:raise ValueError('Produced identity differs')
        archive_pin=backup(path)
        if archive_pin!=row['prediction_sha256']:raise ValueError('Prediction identity differs from backup')
        receipt=record(row);backup(receipt)
        completed.append(row)
        append_event(journal,dict(event='case_completed',case_id=n,role=case['role'],
            completed=len(completed),total=len(cases),reused=bool(case.get('reuse')),
            prediction_sha256=archive_pin))
    return completed
