"""Full-run session executor: independent cadences, atomic state and durable journal.

This never calls the historical general trainer or grants authority to old pilot consumers.
Performance selection is development-only; no early pilot recall gate is applied to this run.
"""
import json
import os
from pathlib import Path
import time

import torch

from src.data.source_inventory_records import require
from src.training.segmenter_full_session_v1 import Session


def atomic_checkpoint(path, session, *, best_score, history_bytes):
    path = Path(path); temporary = path.with_suffix('.partial')
    state = dict(session=session.state(), best_score=best_score, history_bytes=history_bytes)
    with temporary.open('xb') as stream:
        torch.save(state, stream); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def execute(session, provider, output, *, validate_every, checkpoint_every, tick=lambda:None,
            checkpoint_hook=lambda path:None):
    require(all(type(v) is int and v > 0 for v in (validate_every, checkpoint_every)), 'Positive cadences required')
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    best = None; started = time.monotonic()
    with (output / 'history.jsonl').open('xb') as journal:
        def event(row):
            journal.write((json.dumps(row, allow_nan=False) + '\n').encode())
            journal.flush(); os.fsync(journal.fileno())
        def save(name):
            tick()
            path = output / name
            atomic_checkpoint(path, session, best_score=best, history_bytes=journal.tell())
            checkpoint_hook(path)
        event(dict(event='started', identity=session.identity, step=session.step))
        save('initial.pt')
        try:
            while session.step < session.config['max_steps']:
                tick(); row = session.update(provider)
                event(dict(event='update', elapsed_seconds=time.monotonic()-started, **row))
                terminal = session.step == session.config['max_steps']
                if session.step % validate_every == 0 or terminal:
                    scores = []
                    for name in session.control['validation']:
                        tick(); result = session.evaluate_case(provider, name)
                        event(dict(event='validation_case', **result))
                        # Macro Dice of positive development cases; negative FP remains recorded separately.
                        m = result['metrics']['lesion']
                        if m['target_voxels']: scores.append(m['dice'])
                    require(scores, 'No positive development targets available for checkpoint selection')
                    score = sum(scores)/len(scores)
                    event(dict(event='validation', step=session.step, lesion_positive_macro_dice=score,
                               scope='tensor_grid_development'))
                    if best is None or score > best:
                        best = score; save('best.pt')
                if session.step % checkpoint_every == 0 or terminal: save('last.pt')
            event(dict(event='completed', step=session.step, best_development_dice=best))
        except BaseException as exc:
            event(dict(event='failed', step=session.step, dirty=session.dirty,
                       error_type=type(exc).__name__, error=str(exc)))
            raise
    return dict(completed_updates=session.step, best_development_dice=best)
