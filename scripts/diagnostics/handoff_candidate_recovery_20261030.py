"""One local recovery handoff; no recurring task, retries, or new training."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import continue_candidate_export_20261030 as stage
from scripts.acquisition import restore_remaining_cts_20261030 as restore
from src.operations.verifier_candidate_archive_v1 import write_json,append_event,backup_file
from src.operations.full_training_platform import watch_windows,require_ac
from src.training.experiment_config import sha256

def restored_gate():
    events=[json.loads(l) for l in (restore.OUT/'progress.jsonl').read_text().splitlines()]
    if any(r['event']=='failed' for r in events):raise ValueError('Restoration failed; no automatic retry')
    if not events or events[-1]['event']!='completed':return False
    r=stage.read(restore.OUT/'restoration.json')
    stage.verify_membership(stage.read(stage.recovery.OUT/'audit.json'),r)
    return True

def main(pid):
    import psutil,ctypes
    root=stage.SETUP
    if any((root/n).exists() for n in ('handoff-started.json','preparation-started.json','request.json','dispatch.json')):raise ValueError('Handoff/stage already started')
    proc=psutil.Process(pid)
    if 'restore_remaining_cts_20261030.py' not in ' '.join(proc.cmdline()):raise ValueError('Unexpected restoration process')
    write_json(root/'handoff-started.json',dict(pid=pid,process_create_time=proc.create_time(),script_sha256=sha256(__file__),automatic_retry=False))
    journal=root/'handoff.jsonl';append_event(journal,dict(event='waiting_for_owned_restoration',pid=pid))
    started=time.monotonic()
    try:
        if not ctypes.windll.kernel32.SetThreadExecutionState(0x80000001):raise RuntimeError('Cannot inhibit idle sleep')
        while proc.is_running():
            require_ac()
            if time.monotonic()-started>7200:raise TimeoutError('Restoration wait cap')
            if any(json.loads(l)['event']=='failed' for l in (restore.OUT/'progress.jsonl').read_text().splitlines()):raise ValueError('Restoration failed')
            time.sleep(5)
        if not restored_gate():raise ValueError('Restoration stopped without completion')
        append_event(journal,dict(event='preparing'))
        # CPU preparation gets a bounded job and must exit cleanly before dispatch.
        with (root/'prepare.log').open('x') as log:
            p=subprocess.Popen([sys.executable,stage.__file__,'--prepare'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            success=False
            try:watch_windows(p,seconds=1800,rss_bytes=12*1024**3,tick=require_ac);success=True
            finally:write_json(root/'prepare-resources.json',dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode))
        ready=stage.read(root/'request.json');checks=stage.read(root/'source-checks.json')
        if ready['status']!='APPROVED_RECOVERY_INFERENCE_ONLY' or ready['optimizer_updates']!=0 or not checks['failed_case_full_read'] or len(checks['cases'])!=178:raise ValueError('Readiness gate')
        pin=sha256(root/'request.json');append_event(journal,dict(event='launching_once',request_sha256=pin))
        stage.run(pin)
        result=stage.read(root/'resources.json')
        if not result['success'] or not result['workers_reaped'] or result['exit_code']!=0:raise ValueError('Continuation not cleanly complete')
        manifest=stage.read(stage.OUT/'manifest.json')
        if manifest['patients']!=533 or manifest['status']!='COMPLETE_PREDICTIONS_ONLY':raise ValueError('Merged manifest incomplete')
        for row in manifest['cases']:
            archive=Path(row['prediction_path']);old=row['case_id'] in {r['case_id'] for r in stage.read(stage.recovery.OUT/'audit.json')['rows']}
            sidecar=(stage.old.OUT if old else stage.OUT)/(row['case_id']+'.json');backup=stage.old.BACKUP if old else stage.BACKUP
            for path,expected in ((archive,row['prediction_sha256']),(sidecar,sha256(sidecar))):
                if sha256(path)!=expected or sha256(backup/path.name)!=expected:raise ValueError('Final backup changed')
        if sha256(stage.OUT/'manifest.json')!=sha256(stage.BACKUP/'manifest.json'):raise ValueError('Manifest backup mismatch')
        backup_file(root/'resources.json',stage.BACKUP/'resources.json',reserve=lambda n:stage.resources(reserve_c=n))
        append_event(journal,dict(event='complete_predictions_only',patients=533,optimizer_updates=0))
        backup_file(journal,stage.BACKUP/'handoff.jsonl',reserve=lambda n:stage.resources(reserve_c=n))
    except BaseException as exc:
        append_event(journal,dict(event='failed_stop_no_retry',message=repr(exc)));raise
    finally:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--restore-pid',type=int,required=True);main(ap.parse_args().restore_pid)
