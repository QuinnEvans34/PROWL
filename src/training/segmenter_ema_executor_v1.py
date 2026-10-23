"""Paired raw/EMA development execution with local-first durable evidence."""
import json
import os
from pathlib import Path
import time
from src.data.source_inventory_records import require
from src.training.segmenter_full_executor_v1 import atomic_checkpoint


def execute(session,provider,output,*,validate_every=2000,checkpoint_every=500,retain_steps=(),
            tick=lambda:None,checkpoint_hook=lambda p:None,track=lambda r:None,native=None):
    require(validate_every>0 and checkpoint_every>0,'Invalid cadence')
    require(list(retain_steps)==sorted(set(retain_steps)) and all(0<s<=session.config['max_steps'] for s in retain_steps),'Invalid milestones')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    best={'raw':None,'ema':None};started=time.monotonic()
    with (output/'history.jsonl').open('xb') as journal:
        def event(row):
            row=dict(utc_ms=int(time.time()*1000),**row)
            journal.write((json.dumps(row,allow_nan=False)+'\n').encode());journal.flush();os.fsync(journal.fileno())
            track(row)
        def save(name):
            tick();path=output/name
            atomic_checkpoint(path,session,best_score=best.copy(),history_bytes=journal.tell());checkpoint_hook(path)
        event(dict(event='started',identity=session.identity,step=session.step));save('initial.pt')
        try:
            while session.step<session.config['max_steps']:
                tick();result=session.update(provider)
                event(dict(event='update',elapsed_seconds=time.monotonic()-started,**result))
                terminal=session.step==session.config['max_steps']
                if session.step%validate_every==0 or terminal:
                    for kind in ('raw','ema'):
                        if kind=='ema' and session.ema is None:continue
                        scores=[]
                        with session.weights(kind):
                            for name in session.control['validation']:
                                tick();row=session.raw.evaluate_case(provider,name)
                                event(dict(event='validation_case',variant=kind,**row))
                                m=row['metrics']['lesion']
                                if m['target_voxels']:scores.append(m['dice'])
                        require(scores,'No positive development scores');score=sum(scores)/len(scores)
                        event(dict(event='validation',variant=kind,step=session.step,lesion_positive_macro_dice=score,scope='tensor_grid_development'))
                        if best[kind] is None or score>best[kind]:best[kind]=score;save('best-'+kind+'.pt')
                if session.step%checkpoint_every==0 or terminal:save('last.pt')
                if session.step in retain_steps:
                    save(f'step-{session.step:06d}.pt')
                    if native is not None:
                        for kind in ('raw','ema'):
                            with session.weights(kind):
                                for name in session.control['validation']:
                                    tick();event(dict(event='native_case',variant=kind,**native(session.raw,provider,name)))
                            event(dict(event='native_completed',variant=kind,step=session.step))
            event(dict(event='completed',step=session.step,best_development_dice=best,elapsed_seconds=time.monotonic()-started))
        except BaseException as exc:
            event(dict(event='failed',step=session.step,error_type=type(exc).__name__,error=str(exc)));raise
    return dict(completed_updates=session.step,best_development_dice=best)
