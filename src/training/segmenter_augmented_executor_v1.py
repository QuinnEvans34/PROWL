"""Ordinary-only 24k experiment, durable augmentation traces and native endpoints."""
import json
import os
from pathlib import Path
import time

import torch

from src.data.manifest_records import canonical
from src.data.source_inventory_records import require
from src.training.experiment_config import sha256
from src.training.segmenter_augmentation_v1 import AugmentedSession
from src.training.segmenter_full_executor_v1 import atomic_checkpoint


def execute(session, provider, output, *, validate_every=2000, checkpoint_every=500,
            retain_steps=(), tick=lambda: None, checkpoint_hook=lambda p: None,
            track=lambda r: None, native=None):
    require(validate_every > 0 and checkpoint_every > 0, 'Invalid cadence')
    require(list(retain_steps) == sorted(set(retain_steps)) and
            all(0 < s <= session.config['max_steps'] for s in retain_steps), 'Invalid milestones')
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    best, best_step = None, None
    started = time.monotonic()
    with (output/'history.jsonl').open('xb') as journal:
        def event(row):
            row = dict(utc_ms=int(time.time()*1000), **row)
            journal.write((json.dumps(row, allow_nan=False)+'\n').encode())
            journal.flush(); os.fsync(journal.fileno()); track(row)

        def save(name):
            tick(); path = output/name
            atomic_checkpoint(path, session, best_score=best, history_bytes=journal.tell())
            checkpoint_hook(path)

        event(dict(event='started', identity=session.identity, step=session.step))
        try:
            save('initial.pt')
            while session.step < session.config['max_steps']:
                tick(); result = session.update(provider)
                event(dict(event='update', elapsed_seconds=time.monotonic()-started, **result))
                terminal = session.step == session.config['max_steps']
                if session.step % validate_every == 0 or terminal:
                    scores = []
                    for name in session.control['validation']:
                        tick(); row = session.raw.evaluate_case(provider, name)
                        event(dict(event='validation_case', variant='raw', **row))
                        if row['metrics']['lesion']['target_voxels']:
                            scores.append(row['metrics']['lesion']['dice'])
                    require(scores, 'No positive development scores'); score = sum(scores)/len(scores)
                    event(dict(event='validation', variant='raw', step=session.step,
                               lesion_positive_macro_dice=score, scope='tensor_grid_development'))
                    if best is None or score > best:
                        best, best_step = score, session.step; save('best.pt')
                if session.step % checkpoint_every == 0 or terminal: save('last.pt')
                if session.step in retain_steps: save(f'step-{session.step:06d}.pt')
            training_seconds = time.monotonic()-started
            event(dict(event='training_completed', step=session.step, elapsed_seconds=training_seconds))
            reports = {}
            if native is not None:
                for endpoint, filename in [('selected', 'best.pt'), ('terminal', 'last.pt')]:
                    tick(); path = output/filename
                    state = torch.load(path, map_location='cpu', weights_only=True)['session']
                    model = AugmentedSession.restore(state, session.identity)
                    rows = []
                    for name in session.control['validation']:
                        tick(); row = native(model.raw, provider, name); rows.append(row)
                        event(dict(event='native_case', variant='raw', endpoint=endpoint, **row))
                    report = dict(endpoint=endpoint, step=model.step, checkpoint_sha256=sha256(path),
                                  cases=rows, scope='native_provided_pancreas_development')
                    report_path = output/('native-'+endpoint+'.json')
                    with report_path.open('xb') as stream:
                        stream.write(canonical(report)); stream.flush(); os.fsync(stream.fileno())
                    checkpoint_hook(report_path)
                    event(dict(event='native_completed', variant='raw', endpoint=endpoint, step=model.step))
                    reports[endpoint] = str(report_path)
                    del model, state
            result = dict(completed_updates=session.step, best_development_dice=best, selected_step=best_step,
                          training_seconds=training_seconds, elapsed_seconds=time.monotonic()-started,
                          native_reports=reports)
            event(dict(event='completed', step=session.step, **result))
        except BaseException as exc:
            event(dict(event='failed', step=session.step, error_type=type(exc).__name__, error=str(exc)))
            raise
    return result
