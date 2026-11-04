"""Fresh verifier fitting with tune-only checkpoint selection and durable events."""
import os,time,math
from pathlib import Path
import torch
from src.operations.verifier_candidate_archive_v1 import append_event,write_json

def execute(session,output,*,epochs=80,tick=lambda:None,backup=lambda p:None,track=lambda r:None):
    if session.step!=0 or session.epoch!=0 or epochs<1:raise ValueError('Fresh training only')
    output=Path(output);output.mkdir(exist_ok=False);journal=output/'history.jsonl';began=time.monotonic();best=None
    def event(kind,**data):
        r=dict(event=kind,utc_ms=int(time.time()*1000),elapsed_seconds=time.monotonic()-began,step=session.step,**data)
        append_event(journal,r);track(r)
    def save(name):
        tick();path=output/name
        if path.exists():raise ValueError('No checkpoint overwrite')
        with path.open('xb') as f:torch.save(session.state(),f);f.flush();os.fsync(f.fileno())
        backup(path);return name
    event('started',dataset_sha256=session.dataset.pin,metric_scope='verifier_candidate_classification')
    try:
        save('initial.pt')
        while session.epoch<epochs:
            tick();before=session.epoch;trace=session.update()
            if not math.isfinite(trace['loss']):raise ValueError('Nonfinite update')
            event('update',loss=trace['loss'],learning_rate=session.lr,epoch=session.epoch,gradient_norm=trace['gradient_norm'],input_sha256=trace['input_sha256'])
            if session.epoch!=before:
                tick();validation=session.evaluate();value=validation['patient_balanced_bce']
                event('verifier_tune',epoch=session.epoch,patient_balanced_bce=value,candidate_patients=validation['candidate_patients'])
                if best is None or value<best['patient_balanced_bce']:
                    name=save(f'selected-epoch-{session.epoch:03d}.pt')
                    best=dict(epoch=session.epoch,step=session.step,patient_balanced_bce=value,checkpoint=name)
        terminal=save('terminal.pt');event('training_completed',epoch=session.epoch)
        result=dict(status='VERIFIER_FIT_COMPLETE_CALIBRATION_PENDING',completed_updates=session.step,epochs=session.epoch,selected=best,
            terminal_checkpoint=terminal,training_seconds=time.monotonic()-began,development_cases_evaluated=0,calibration_cases_evaluated=0)
        write_json(output/'result.json',result);backup(output/'result.json');event('completed',**result);backup(journal);return result
    except BaseException as exc:event('failed',message=repr(exc));raise
