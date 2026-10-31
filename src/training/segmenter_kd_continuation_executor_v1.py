"""Additive native KD continuation with safe-boundary cooperative pauses.

The frozen fresh-only executor is unchanged. Caller must bind/verify parent
checkpoint, independent backup, resource charge, identity and exclusive ownership.
"""
import json
import os
from pathlib import Path
import shutil
import time
import numpy as np
from src.data.manifest_records import canonical
from src.training.segmenter_full_executor_v1 import atomic_checkpoint
from src.training.segmenter_pancreas_region_executor_v1 import write_report
from src.training.segmenter_kd_native_evaluation_v1 import evaluate, bind_sidecar
from src.training.segmenter_kd_evidence_executor_v1 import journal_value
from src.data.segmenter_teacher_cache_v1 import sha


def execute(session,provider,output,*,checkpoint_hook,continuation=None,
            pause_requested=lambda:False,validate_every=2000,checkpoint_every=500,
            tick=lambda:None,track=lambda row:None,evaluator=evaluate,checkpoint=atomic_checkpoint):
    if validate_every<1 or checkpoint_every<1:raise ValueError('Positive cadences required')
    names=list(session.control['validation'])
    if not names or len(set(names))!=len(names):raise ValueError('Distinct development membership required')
    best=best_step=None; pending=False
    if continuation is None:
        if session.step!=0:raise ValueError('Bound continuation required')
    else:
        if (continuation['step']!=session.step or continuation['identity']!=session.identity
                or continuation['version']!='kd-checkpoint-continuation-1'):
            raise ValueError('Continuation/session mismatch')
        best=continuation['best_score'];best_step=continuation['selected_step']
        pending=continuation['pending_validation']
        if (best is None)!=(best_step is None):raise ValueError('Incomplete inherited selection')
        for path,pin in continuation['pins'].items():
            if sha(path)!=pin:raise ValueError('Parent evidence changed')
        with Path(continuation['journal']).open('rb') as stream:
            from src.data.manifest_records import digest
            if digest(stream.read(continuation['history_bytes']))!=continuation['journal_prefix_sha256']:
                raise ValueError('Parent journal prefix changed')
    output=Path(output);output.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    def preserve(path):
        if path.name.startswith('native-') and path.suffix=='.json':
            sidecar=bind_sidecar(path);checkpoint_hook(path);checkpoint_hook(sidecar)
        else:checkpoint_hook(path)
    with (output/'history.jsonl').open('xb') as journal:
        def event(row):
            value=journal_value(dict(utc_ms=int(time.time()*1000),elapsed_seconds=time.monotonic()-started,**row))
            journal.write(canonical(value));journal.flush();os.fsync(journal.fileno());track(value)
        def save(name):
            tick();p=output/name;checkpoint(p,session,best_score=best,history_bytes=journal.tell());preserve(p)
        def validation():
            nonlocal best,best_step
            save(f'step-{session.step:06d}.pt')
            rows=[];event(dict(event='native_started',step=session.step,completed_cases=0,total_cases=len(names)))
            for name in names:
                tick()
                def progress(done,total):
                    tick()
                    if done%25==0 or done==total:
                        event(dict(event='native_progress',step=session.step,completed_cases=len(rows),total_cases=len(names),tiles_done=done,total_tiles=total))
                row=evaluator(session,provider,name,progress)
                if row['case_id']!=name or row['step']!=session.step:raise ValueError('Native identity differs')
                rows.append(row);event(dict(event='native_case',variant='raw',**row))
            positives=[r['metrics']['lesion']['dice'] for r in rows if r['metrics']['lesion']['target_voxels']]
            if not positives:raise ValueError('Positive development required')
            score=float(np.mean(positives))
            if not np.isfinite(score) or not 0<=score<=1:raise ValueError('Invalid native score')
            report=dict(step=session.step,scope='native_provided_pancreas_region_development',cases=rows,lesion_positive_macro_dice=score)
            path=output/f'native-{session.step:06d}.json';write_report(path,report);preserve(path)
            if best is None or score>best:
                best,best_step=score,session.step;save('best.pt')
                path=output/'native-selected.json';write_report(path,dict(report,endpoint='selected'));preserve(path)
            if session.step==session.config['max_steps']:
                path=output/'native-terminal.json';write_report(path,dict(report,endpoint='terminal'));preserve(path)
            event(dict(event='native_completed',variant='raw',step=session.step,lesion_positive_macro_dice=score,selected_step=best_step))
        def pause():
            save('pause.pt')
            event(dict(event='paused',step=session.step,selected_step=best_step))
            return dict(status='paused',completed=False,completed_updates=session.step,selected_step=best_step,best_development_dice=best)
        event(dict(event='started',step=session.step,identity=session.identity,selected_step=best_step,
                   continuation=continuation,metric_scope='native_provided_pancreas_region_development'))
        try:
            if best_step is not None:
                report=continuation['selected_report']
                if report['step']!=best_step or report['lesion_positive_macro_dice']!=best:
                    raise ValueError('Inherited report differs')
                source=Path(continuation['journal']).parent/f'step-{best_step:06d}.pt'
                for name in (f'step-{best_step:06d}.pt','best.pt'):
                    target=output/name
                    with source.open('rb') as a,target.open('xb') as b:
                        shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
                    preserve(target)
                for name,body in ((f'native-{best_step:06d}.json',report),('native-selected.json',dict(report,endpoint='selected'))):
                    path=output/name;write_report(path,body);preserve(path)
            save('initial.pt')
            # A pre-validation checkpoint must evaluate before consuming another sample.
            if pending:validation()
            while session.step<session.config['max_steps']:
                if pause_requested():return pause()
                tick();event(dict(event='update',**session.update(provider)))
                terminal=session.step==session.config['max_steps']
                if session.step%checkpoint_every==0 or terminal:save('last.pt')
                if session.step%validate_every==0 or terminal:validation()
            event(dict(event='training_completed',step=session.step))
            result=dict(status='completed',completed=True,completed_updates=session.step,selected_step=best_step,
                        best_development_dice=best,training_seconds=time.monotonic()-started,
                        metric_scope='native_provided_pancreas_region_development')
            event(dict(event='completed',step=session.step,**{k:v for k,v in result.items() if k!='status'}))
            return result
        except BaseException as exc:
            event(dict(event='failed',step=session.step,error_type=type(exc).__name__,error=str(exc)));raise
