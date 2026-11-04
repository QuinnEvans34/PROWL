"""Read-only audit of the failed export; preserves its original evidence."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import export_verifier_candidates_20261027 as old
from src.operations.verifier_candidate_archive_v1 import write_json,append_event
from src.training.experiment_config import sha256
OUT=Path('E:/PROWL/readiness/verifier-export-recovery-20261030-a01')
OLD_SHA='edd8824e401aad8e5d8aefbf228f876931f3e792caaa457a7b28b32ca38b6a31'

def completion_split(request,events):
    done=[r for r in events if r['event']=='case_completed']
    ids=[r['case_id'] for r in done]
    expected={c['case_id']:c for c in request['cases']}
    if len(ids)!=355 or len(set(ids))!=355 or not set(ids)<=set(expected):
        raise ValueError('Unexpected prior completion membership')
    for row in done:
        if row['role']!=expected[row['case_id']]['role']:raise ValueError('Prior role mismatch')
    remaining=[dict(c,reuse=False) for c in request['cases'] if c['case_id'] not in ids]
    if len(remaining)!=178 or remaining[0]['case_id']!='PanTS_00005914':raise ValueError('Unexpected continuation membership')
    return done,remaining

def audit():
    if OUT.exists():raise ValueError('Audit already started; inspect existing evidence')
    OUT.mkdir();log=OUT/'progress.jsonl';start=time.monotonic()
    try:
        append_event(log,dict(event='started'))
        request=old.check(OLD_SHA)
        resources=old.read(old.SETUP/'resources.json')
        if resources['success'] or resources['exit_code']!=1 or not resources['workers_reaped']:raise ValueError('Old worker not failed/reaped')
        events=[json.loads(l) for l in (old.OUT/'progress.jsonl').read_text().splitlines()]
        if events[-1]['event']!='failed':raise ValueError('Old failure journal changed')
        done,remaining=completion_split(request,events)
        if sha256(old.BACKUP/'request.json')!=OLD_SHA:raise ValueError('Original request backup mismatch')
        if (old.OUT/'manifest.json').exists():raise ValueError('Unexpected old manifest')
        rows=[];pins={str(old.SETUP/'request.json'):OLD_SHA}
        for event in done:
            n=event['case_id'];sidecar=old.OUT/(n+'.json');row=old.read(sidecar)
            if row['case_id']!=n or row['role']!=event['role'] or row['label_access']!='none' or row['optimizer_updates']!=0 or row['gap_voxels']!=0:raise ValueError('Invalid old provenance')
            if row['prediction_sha256']!=event['prediction_sha256']:raise ValueError('Old journal/archive identity')
            archive=Path(row['prediction_path'])
            for path,expected in ((archive,row['prediction_sha256']),(sidecar,sha256(sidecar))):
                backup=old.BACKUP/path.name
                if path.stat().st_dev==backup.stat().st_dev:raise ValueError('Non-independent backup')
                if sha256(path)!=expected or sha256(backup)!=expected:raise ValueError('Old artifact/backup changed: '+n)
                pins[str(path)]=expected;pins[str(backup)]=expected
            rows.append(row)
            append_event(log,dict(event='verified',case_id=n,completed=len(rows)))
        for c in remaining:
            if any((base/(c['case_id']+suffix)).exists() for base in (old.OUT,old.BACKUP) for suffix in ('.npz','.json','.npz.partial','.json.partial')):
                raise ValueError('Uncommitted artifact requires explicit review: '+c['case_id'])
        for p in (old.OUT/'progress.jsonl',old.SETUP/'resources.json',Path(__file__)):
            pins[str(p)]=sha256(p)
        old.resources()
        write_json(OUT/'audit.json',dict(status='PRIOR_355_INDEPENDENT_BACKUPS_VERIFIED',rows=rows,remaining=remaining,pins=pins,
            inherited_pins=len(request['pins']),remaining_seconds=request['seconds']-resources['seconds'],seconds=time.monotonic()-start))
        append_event(log,dict(event='completed',patients=len(rows),seconds=time.monotonic()-start))
    except BaseException as exc:
        append_event(log,dict(event='failed',message=repr(exc)));raise

if __name__=='__main__':audit()
