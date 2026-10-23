"""Durable provided-pancreas region training with complete native development selection."""
import json
import os
from pathlib import Path
import time
import numpy as np
from src.data.manifest_records import canonical
from src.training.segmenter_full_executor_v1 import atomic_checkpoint
from src.training.segmenter_physical_windows_session_v1 import predict_native
from src.training.pants_native_evaluation import native_metrics
from src.operations.full_training_platform import durable_replace


def write_report(path, value):
    path = Path(path); temporary = path.with_suffix('.partial')
    with temporary.open('xb') as stream:
        stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())
    durable_replace(temporary, path)


from src.training.segmenter_pancreas_region_session_v1 import evaluate


def execute(session, provider, output, *, validate_every=2000, checkpoint_every=500,
            tick=lambda: None, checkpoint_hook=lambda path: None, track=lambda row: None,
            evaluator=evaluate, validation_names=None, checkpoint=atomic_checkpoint):
    if validate_every < 1 or checkpoint_every < 1 or session.step != 0:
        raise ValueError('Fresh session and positive cadences required; no automatic resume')
    names = list(session.control['validation'] if validation_names is None else validation_names)
    if not names or len(set(names)) != len(names) or not set(names) <= set(session.control['validation']):
        raise ValueError('Invalid development membership')
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    best = best_step = None; started = time.monotonic()
    with (output/'history.jsonl').open('xb') as journal:
        def event(row):
            value = dict(utc_ms=int(time.time()*1000), elapsed_seconds=time.monotonic()-started, **row)
            journal.write(canonical(value)); journal.flush(); os.fsync(journal.fileno()); track(value)

        def save(filename):
            tick(); path = output/filename
            checkpoint(path, session, best_score=best, history_bytes=journal.tell())
            checkpoint_hook(path)

        event(dict(event='started', step=0, identity=session.identity, metric_scope='native_provided_pancreas_region_development'))
        try:
            save('initial.pt')
            while session.step < session.config['max_steps']:
                tick(); event(dict(event='update', **session.update(provider)))
                terminal = session.step == session.config['max_steps']
                if session.step % checkpoint_every == 0 or terminal: save('last.pt')
                if session.step % validate_every == 0 or terminal:
                    # Retain the trained state BEFORE expensive validation begins.
                    save(f'step-{session.step:06d}.pt')
                    rows = []
                    event(dict(event='native_started', step=session.step, completed_cases=0, total_cases=len(names)))
                    for name in names:
                        tick()
                        def progress(done, total):
                            tick()
                            if done % 25 == 0 or done == total:
                                event(dict(event='native_progress', step=session.step, completed_cases=len(rows),
                                           total_cases=len(names), tiles_done=done, total_tiles=total))
                        row = evaluator(session, provider, name, progress)
                        if row['case_id'] != name or row['step'] != session.step:
                            raise ValueError('Native evaluation identity mismatch')
                        rows.append(row); event(dict(event='native_case', variant='raw', **row))
                    if {row['case_id'] for row in rows} != set(names): raise ValueError('Incomplete development')
                    positives = [row['metrics']['lesion']['dice'] for row in rows if row['metrics']['lesion']['target_voxels']]
                    if not positives: raise ValueError('No positive development cases')
                    score = float(np.mean(positives))
                    if not np.isfinite(score) or not 0 <= score <= 1: raise ValueError('Invalid native score')
                    report = dict(step=session.step, scope='native_provided_pancreas_region_development', cases=rows,
                                  lesion_positive_macro_dice=score)
                    path = output/f'native-{session.step:06d}.json'
                    write_report(path, report); checkpoint_hook(path)
                    if best is None or score > best:
                        best, best_step = score, session.step; save('best.pt')
                        write_report(output/'native-selected.json', dict(report, endpoint='selected'))
                        checkpoint_hook(output/'native-selected.json')
                    if terminal:
                        write_report(output/'native-terminal.json', dict(report, endpoint='terminal'))
                        checkpoint_hook(output/'native-terminal.json')
                    event(dict(event='native_completed', variant='raw', step=session.step,
                               lesion_positive_macro_dice=score, selected_step=best_step))
            elapsed = time.monotonic()-started
            event(dict(event='training_completed', step=session.step))
            result = dict(completed_updates=session.step, selected_step=best_step, best_development_dice=best,
                          training_seconds=elapsed, metric_scope='native_provided_pancreas_region_development')
            event(dict(event='completed', step=session.step, **result))
            return result
        except BaseException as exc:
            event(dict(event='failed', step=session.step, error_type=type(exc).__name__, error=str(exc)))
            raise
