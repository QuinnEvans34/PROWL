"""Fixed-terminal restricted generator executor. No evaluation/selection hook.

Does not launch a process, choose a device or grant scientific authority.
"""
import math,os,time
from pathlib import Path
from src.data.manifest_records import canonical
from src.training.segmenter_full_executor_v1 import atomic_checkpoint


def execute(session,provider,output,*,checkpoint_every=500,tick=lambda:None,
            checkpoint_hook=lambda path:None,track=lambda row:None,checkpoint=atomic_checkpoint):
    if session.step!=0 or type(checkpoint_every)!=int or checkpoint_every<1:
        raise ValueError('Fresh session, positive checkpoint cadence; no resume')
    restriction=provider.control.get('restricted_generator',{})
    if restriction.get('selection')!='fixed_terminal_no_heldout_selection' or restriction.get('evaluation_enabled') is not False:
        raise ValueError('Restricted fixed-terminal provider required')
    if session.control!=provider.control or session.control_pin!=provider.pin:
        raise ValueError('Session/provider identity mismatch')
    names=set(session.control['train']);horizon=session.config['max_steps']
    if not names or type(horizon)!=int or horizon<1:raise ValueError('Invalid training horizon')
    output=Path(output);output.mkdir(parents=True,exist_ok=False);began=time.monotonic()
    with (output/'history.jsonl').open('xb') as journal:
        def event(row):
            v=dict(utc_ms=int(time.time()*1000),elapsed_seconds=time.monotonic()-began,**row)
            journal.write(canonical(v));journal.flush();os.fsync(journal.fileno());track(v)
        def save(name):
            tick();path=output/name
            checkpoint(path,session,best_score=None,history_bytes=journal.tell());checkpoint_hook(path)
        event(dict(event='started',step=0,identity=session.identity,
                   metric_scope='generator_optimizer_only_no_development_selection'))
        try:
            save('initial.pt')
            while session.step<horizon:
                tick();before=session.step;row=session.update(provider)
                if session.step!=before+1 or row['step']!=session.step or row['member_id'] not in names:
                    raise ValueError('Noncontiguous or protected optimizer update')
                if not math.isfinite(row['loss']):raise ValueError('Nonfinite training loss')
                event(dict(event='update',**row))
                if session.step%checkpoint_every==0 or session.step==horizon:save('last.pt')
            # Completion means owned prefetch is drained, not merely last update.
            provider.close()
            save('terminal.pt')
            event(dict(event='training_completed',step=session.step))
            result=dict(completed_updates=session.step,selected_step=session.step,
                selected_checkpoint='terminal.pt',selection='fixed_terminal',
                development_cases_evaluated=0,training_seconds=time.monotonic()-began,
                metric_scope='generator_optimizer_only_no_development_selection')
            event(dict(event='completed',step=session.step,**result));return result
        except BaseException as exc:
            event(dict(event='failed',step=session.step,error_type=type(exc).__name__,error=str(exc)))
            raise
        finally:provider.close()
