"""Read-only metadata accounting; never access arrays, checkpoints or tracking writes."""
import collections,datetime,hashlib,json,os,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MONITOR=Path('C:/Users/quinn/PROWL-Monitor')
DB=Path('C:/Users/quinn/PROWL-Tracking/mlflow.db')
DEST=ROOT/'docs/capstone/operations/WINDOWS-TRAINING-HOURS-20261103.json'
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def evidence(p):return dict(path=str(p),sha256=digest(p))
def main():
    registry=json.loads((MONITOR/'experiments.json').read_text());entries=registry['runs']+[registry['pending_run']]
    db=sqlite3.connect('file:'+DB.as_posix()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON')
    records=[]
    for rid,name,status in db.execute('SELECT run_uuid,name,status FROM runs'):
        tags=dict(db.execute('SELECT key,value FROM tags WHERE run_uuid=?',(rid,)))
        elapsed=db.execute("SELECT value,step FROM latest_metrics WHERE run_uuid=? AND key='train/elapsed_seconds'",(rid,)).fetchone()
        records.append(dict(id=rid,name=name,status=status,tags=tags,latest_elapsed=elapsed))
    runs=[];used=set()
    for entry in entries:
        root=Path(entry['root']);p=root/'execution/history.jsonl';events=collections.Counter();last_elapsed=0.;training=None;completed=None;lastupdate=None;steps=0;starts=[];resets=[];native_start=None;native_seconds=0.;native_pairs=0;previous=-1.
        for line in p.open():
            row=json.loads(line);event=row['event'];events[event]+=1
            if 'elapsed_seconds' in row:
                t=row['elapsed_seconds']
                if t<previous:resets.append(dict(event=event,before=previous,after=t))
                previous=t;last_elapsed=t
            if event in ['started','resumed']:starts.append(dict(event=event,step=row.get('step')))
            if event=='update':steps=row['step'];lastupdate=row['elapsed_seconds']
            if event=='training_completed':training=row['elapsed_seconds']
            if event=='completed':completed=row.get('elapsed_seconds')
            if event=='native_started' and 'elapsed_seconds' in row:native_start=row['elapsed_seconds']
            if event=='native_completed' and native_start is not None:
                native_seconds+=row['elapsed_seconds']-native_start;native_pairs+=1;native_start=None
        assert not resets and events['started']==1 and not events['resumed'],'Requires attempt reconciliation'
        seconds=training if training is not None else last_elapsed
        tracking=root/'tracking.json';rid=json.loads(tracking.read_text())['run_id'] if tracking.exists() else None
        candidates=[v for v in records if v['id']==rid or v['tags'].get('prowl_run_key')==root.name or v['name']==entry['title']]
        if not candidates:
            # Some launchers store no tracking.json. Bind by the exact locally recorded run key/known MLflow identity.
            known={'pants_candidate_verifier_20261031':'4475886fbdbf41c8a02d4f814a9733ac','pants_full_coverage_physical_24k_20261018':'ecb6e402f0f84bc8a9df5e11239e5972','pants_pancreas_region_24k_20261019':'1edf56ad4b7b48a5a5baa0e729e46a5c','pants_varied_focus_24k_20261022':'a84c0a6ae0cb424ca182350425adc7aa','pants_reserved_verifier_generator_24k_20261025':'0acb9a8f7e8a463194dd599a01b78507'}
            candidates=[v for v in records if v['id']==known.get(root.name)]
        assert len(candidates)==1,(root.name,'ambiguous MLflow mapping')
        m=candidates[0];used.add(m['id']);stop=root/'operator-stop.json'
        row=dict(run_key=root.name,title=entry['title'],machine='QUINNS-LAPTOP',attempts=starts,status='stopped' if stop.exists() else m['status'],optimizer_updates=steps,
            dashboard_seconds=seconds,source_counter='training_completed.elapsed_seconds' if training is not None else ('completed.elapsed_seconds' if completed is not None else 'last_update.elapsed_seconds'),
            last_update_elapsed_seconds=lastupdate,completed_elapsed_seconds=completed,training_completed_elapsed_seconds=training,
            journal=evidence(p),mlflow_run_id=m['id'],mlflow_status=m['status'],mlflow_latest_train_elapsed=m['latest_elapsed'],mlflow_is_same_work_not_additional=True,
            exact_optimizer_only_seconds=None,attempt_resets_detected=resets,scope='scientific training session including in-loop validation/checkpoint/I/O overhead',
            timed_native_validation_seconds=native_seconds if native_pairs else None,timed_native_validation_pairs=native_pairs,
            native_validation_included=events['native_completed']>0 and entry['id']!='augmentation',
            final_native_validation_excluded=entry['id']=='augmentation',
            final_untimed_tail_missing=entry['id'] in ['baseline','panorama','full-coverage'])
        if stop.exists():row['stop_evidence']=evidence(stop)
        if 'source_history_sha256' in m['tags']:
            assert m['tags']['source_history_sha256']==row['journal']['sha256'];row['mlflow_backfill_source_hash_matches']=True
        runs.append(row)
    firstsix=[r for r in runs if r['run_key'] not in ['pants_varied_focus_24k_20261022','pants_reserved_verifier_generator_24k_20261025','pants_candidate_verifier_20261031']]
    old=sum(r['dashboard_seconds'] for r in firstsix);assert abs(old-751607.078)<1e-6
    total=sum(r['dashboard_seconds'] for r in runs)
    excluded=[dict(mlflow_run_id=r['id'],title=r['name'],status=r['status'],reason=r['tags'].get('stage',r['tags'].get('purpose','standalone native evaluation')),seconds_added=0) for r in records if r['id'] not in used]
    snapshot=dict(schema='prowl-training-time-reconciliation-v1',as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),machine=dict(hostname=os.environ.get('COMPUTERNAME'),manufacturer='LENOVO',model='21FWS0DU00',identity_source='Win32_ComputerSystem read-only query'),
        total_dashboard_session_seconds=total,total_dashboard_session_hours=total/3600,first_six_seconds=old,first_six_hours=old/3600,runs=runs,excluded_mlflow_runs=excluded,
        evidence=[evidence(MONITOR/'experiments.json'),evidence(MONITOR/'experiments.py'),evidence(DB)],
        exclusions=['standalone inference/native evaluation','candidate prediction exports and failed export attempts','teacher-target generation','CT restoration/downloads','CPU/GPU engineering pilots and cold replay','Mac scientific runs','human active working time'],
        reconciliation_keys=['machine+run_key+attempt start step','journal SHA256','MLflow run ID; never add MLflow as a second duration'],
        limitations=['This is a journal-derived session counter, not exact optimizer or GPU-busy time.','In-loop validation/checkpoint/I/O are included; baseline/PANORAMA final untimed tails and stopped-run unjournaled tail are unavailable.','No elapsed journal resets/resumed events in these nine histories; no start/end calendar subtraction used. OS sleep/suspension time cannot be separated from monotonic elapsed counters using these records alone.','Historical first-five-weeks training database is not present at configured outputs/mlflow.db or root mlflow.db on this checkout. Local mlruns/3 contains verifier artifacts only, not historical runtime records.','No complete cross-machine total can be certified until Mac and historical attempt records are reconciled. Imported copies may overlap; match IDs and hashes before addition.','Human active work time is not measured; concurrent machine-hours are additive compute effort, not calendar elapsed time.'],
        historical_mlflow_coverage=dict(local_sqlite_runs=len(records),scientific_session_matches=len(used),engineering_or_evaluation_excluded=len(excluded),legacy_configured_db_present=(ROOT/'outputs/mlflow.db').exists()),
        teacher_target_generation_seconds_included=0,human_active_seconds=None,optimizer_only_total_seconds=None)
    with DEST.open('x') as f:json.dump(snapshot,f,indent=2,allow_nan=False)
    print(json.dumps(dict(path=str(DEST),sha256=digest(DEST),seconds=total,hours=total/3600,first_six=old,runs=len(runs),excluded=len(excluded))))
if __name__=='__main__':main()
