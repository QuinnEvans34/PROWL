"""Read-only training-session accounting. No model, checkpoint, CT or MLflow writes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3

MAX_JOURNAL = 128*1024**2


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def read_json(path):
    raw=Path(path).read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()


def journal(path):
    with Path(path).open('rb') as stream:raw=stream.read(MAX_JOURNAL+1)
    if len(raw)>MAX_JOURNAL:raise ValueError('Journal exceeds read-only accounting limit')
    # A live writer may have an incomplete final line; only complete records count.
    raw=raw[:raw.rfind(b'\n')+1]
    rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
    timed=[v for v in rows if type(v.get('elapsed_seconds')) in (int,float)]
    if not timed:raise ValueError('No recorded elapsed counter')
    values=[v['elapsed_seconds'] for v in timed]
    if any(not math.isfinite(v) or v<0 for v in values) or any(b<a for a,b in zip(values,values[1:])):
        raise ValueError('Counter reset requires separate attempt records')
    return max(values),hashlib.sha256(raw).hexdigest(),rows


def entry(identity,machine,title,seconds,category,basis,**extra):
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:
        raise ValueError('Invalid recorded duration')
    return dict(execution_id=identity,machine=machine,title=title,seconds=seconds,
                category=category,basis=basis,**extra)


def summarize(entries):
    by_id={};aliases={}
    for e in entries:
        if e['execution_id'] in by_id:
            if encoded(by_id[e['execution_id']])!=encoded(e):raise ValueError('Conflicting execution records')
            continue
        entry(e['execution_id'],e['machine'],e['title'],e['seconds'],e['category'],e['basis'])
        for alias in e.get('aliases',[]):
            if alias in aliases:raise ValueError('Overlapping execution aliases; reconcile before summing')
            aliases[alias]=e['execution_id']
        by_id[e['execution_id']]=e
    rows=list(by_id.values());totals={}
    for e in rows:
        group=totals.setdefault(e['machine'],dict(training_seconds=0,legacy_estimated_seconds=0,teacher_seconds=0))
        if e['category']=='training':group['training_seconds']+=e['seconds']
        elif e['category']=='legacy_estimate':group['legacy_estimated_seconds']+=e['seconds']
        elif e['category']=='teacher_targets':group['teacher_seconds']+=e['seconds']
        else:raise ValueError('Unrecognized accounting category')
    measured=sum(t['training_seconds'] for t in totals.values())
    estimated=sum(t['legacy_estimated_seconds'] for t in totals.values())
    teacher=sum(t['teacher_seconds'] for t in totals.values())
    return rows,dict(training_seconds=measured,legacy_estimated_seconds=estimated,
        recorded_training_seconds=measured+estimated,teacher_seconds=teacher,
        recorded_model_work_seconds=measured+estimated+teacher,machines=totals)


def collect(config):
    entries=[];issues=[];sources=[]
    # The early file is attribution evidence, not an independent third machine.
    db=Path(config['legacy_db'])
    conn=sqlite3.connect('file:'+str(db.resolve())+'?mode=ro',uri=True)
    conn.execute('BEGIN')
    legacy=[];excluded=0
    for rid,title,status,start,end,artifact in conn.execute('select run_uuid,name,status,start_time,end_time,artifact_uri from runs order by start_time'):
        source=conn.execute("select value from tags where run_uuid=? and key='mlflow.source.name'",(rid,)).fetchone()
        source=source[0] if source else ''
        points=conn.execute("select timestamp,step from metrics where run_uuid=? and key='train/loss' order by timestamp",(rid,)).fetchall()
        if source.endswith('train.py') and points:
            stop=points[-1][0] # Never extrapolate stale RUNNING rows to the present.
            if end is not None:stop=min(stop,end)
            basis='MLflow run start to last train/loss timestamp; estimated session span'
        elif source.endswith('tune_optuna.py') and end is not None:
            stop=end;basis='MLflow trial start/end; estimated tuning-session span'
        else:excluded+=1;continue
        if not artifact.startswith('/Users/quintonevans/'):
            raise ValueError('Historical machine attribution needs review')
        e=entry('mlflow:'+rid,'Mac',title,max(0,(stop-start)/1000),'legacy_estimate',basis,
            aliases=['mlflow:'+rid],status='historical',period='Early MLflow',
            source_status=status,last_step=points[-1][1] if points else None,
            as_of_utc=datetime.fromtimestamp(stop/1000,timezone.utc).isoformat(),
            start_utc=datetime.fromtimestamp(start/1000,timezone.utc).isoformat())
        legacy.append(e)
    # Fingerprint the logical read snapshot; hashing a live SQLite file is not a transaction snapshot.
    legacy_sha=hashlib.sha256(encoded(legacy)).hexdigest()
    conn.rollback();conn.close()
    for e in legacy:e['evidence_sha256']=legacy_sha
    entries+=legacy
    sources.append(dict(name='Historical Mac MLflow',as_of_utc=max(e['as_of_utc'] for e in legacy),
        fingerprint=legacy_sha,records=len(legacy),excluded_nontraining_runs=excluded))
    issues.append('Historical MLflow durations are timestamp estimates, not measured accelerator-active time. Two old RUNNING labels are not live jobs.')
    for path in config['older_mac_journals']:
        seconds,pin,rows=journal(path)
        key=Path(path).parents[1].name
        entries.append(entry('mac-journal:'+key,'Mac',key,seconds,'training','Last recorded monotonic journal counter; unrecorded tail excluded',
            aliases=['mac-journal:'+key],period='Full-cohort Mac',status='historical',evidence_sha256=pin))
    current=Path(config['current_kd_root']);ready,ready_sha=read_json(current/'ready.json')
    for arm,segments in ready['segments'].items():
        for segment in segments:
            root=Path(segment['root']);seconds,pin,rows=journal(root/arm/'execution/history.jsonl')
            entries.append(entry('mlflow:'+segment['run_id'],'Mac','KD '+arm+' · '+root.name,seconds,'training',
                'Last recorded monotonic journal counter for this attempt; pause gaps excluded',aliases=['mlflow:'+segment['run_id']],
                period='KD comparison',arm=arm,status='closed',evidence_sha256=pin))
    dispatch,_=read_json(current/'treatment/dispatch.json')
    seconds,pin,rows=journal(current/'treatment/execution/history.jsonl')
    updates=[r for r in rows if r.get('event')=='update']
    terminal=any(r.get('event') in ('completed','paused') for r in rows)
    as_of=next((r['utc_ms'] for r in reversed(rows) if 'utc_ms' in r),None)
    entries.append(entry('mlflow:'+dispatch['run_id'],'Mac','KD treatment · current attempt',seconds,'training',
        'Last recorded monotonic journal counter; no wall-clock extrapolation',aliases=['mlflow:'+dispatch['run_id']],
        period='KD comparison',arm='treatment',status='closed' if terminal else 'last_recorded',last_step=updates[-1]['step'] if updates else None,
        as_of_utc=datetime.fromtimestamp(as_of/1000,timezone.utc).isoformat() if as_of else None,evidence_sha256=pin))
    sources.append(dict(name='Mac KD lineage',as_of_utc=entries[-1]['as_of_utc'],fingerprint=ready_sha,
        records=sum(len(v) for v in ready['segments'].values())+1))
    for path in config['teacher_resources']:
        d,pin=read_json(path)
        entries.append(entry('teacher:'+Path(path).parent.name,'Mac','Teacher targets · '+Path(path).parent.name,d['seconds'],
            'teacher_targets','Supervised worker elapsed counter; target-generation only',aliases=['teacher:'+Path(path).parent.name],
            period='Teacher targets',status='closed',evidence_sha256=pin))
    issues.append('Teacher attempt01 has no measured resource duration. Its 600-second safety-budget charge is excluded rather than presented as measured time. Teacher pilots/qualification are outside this counter.')
    windows,windows_sha=read_json(config['lenovo_snapshot'])
    for r in windows['runs']:
        rid=r.get('mlflow_run_id')
        entries.append(entry('lenovo:'+r['run_key'],'Lenovo',r['title'],r['dashboard_seconds'],'training',r['source_counter'],
            aliases=['mlflow:'+rid] if rid else ['lenovo:'+r['run_key']],period='Lenovo scientific runs',
            status=r['status'],evidence_sha256=r['journal']['sha256'],as_of_utc=windows['as_of_utc']))
    sources.append(dict(name='Lenovo verified export',as_of_utc=windows['as_of_utc'],fingerprint=windows_sha,records=len(windows['runs'])))
    result,totals=summarize(entries)
    return dict(schema='prowl-combined-training-hours-v1',generated_at=datetime.now(timezone.utc).isoformat(),
        policy='Recorded training-session time includes in-run validation, checkpoint and I/O work. It is not GPU-busy time or personal working hours.',
        complete_project_history=False,entries=result,totals=totals,sources=sources,issues=issues,
        excluded=['Standalone evaluation','CT restoration and data preparation','Engineering and qualification tests','Unknown or missing durations','Human working hours'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--output')
    a=p.parse_args();config,_=read_json(a.config);result=collect(config)
    raw=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if a.output:Path(a.output).write_text(raw)
    else:print(raw,end='')
