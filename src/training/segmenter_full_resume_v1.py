"""Pinned checkpoint continuation into a new segment; never truncate the parent journal."""
import hashlib
import io
import json
from pathlib import Path

import torch

from src.data.source_inventory_records import require
from src.training.segmenter_full_session_v1 import Session, identity_for


def read_checkpoint(cfg, control, *, checkpoint, checkpoint_sha256):
    path = Path(checkpoint)
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'Regular absolute checkpoint required')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == checkpoint_sha256, 'Resume checkpoint hash mismatch')
    payload = torch.load(io.BytesIO(raw), map_location='cpu', weights_only=True)
    require(set(payload) == {'session', 'best_score', 'history_bytes'}, 'Incomplete executor checkpoint')
    config = dict(cfg['full_segmenter']['session'], max_steps=cfg['_experiment']['run']['max_updates'])
    expected = identity_for(config, control, cfg['device'], cfg['_experiment']['initialization'])
    require(payload['session']['identity'] == expected, 'Resume configuration/cohort/engine identity differs')
    step = payload['session']['step']
    require(type(step) is int and 0 < step < config['max_steps'], 'No remaining checkpoint work')
    count = payload['history_bytes']; journal = path.parent / 'history.jsonl'
    require(type(count) is int and 0 < count <= journal.stat().st_size, 'Invalid checkpoint journal boundary')
    with journal.open('rb') as stream:
        prefix = stream.read(count)
    require(prefix.endswith(b'\n'), 'Incomplete checkpoint journal line')
    records = [json.loads(line) for line in prefix.splitlines()]
    require(records[0]['event'] == 'started' and records[0]['identity'] == expected,
            'Parent journal identity differs')
    progress = [r['step'] for r in records if r['event'] == 'update']
    start = records[0]['step']
    require(progress == list(range(start + 1, step + 1)), 'Parent journal progress is incomplete')
    scores = [r['lesion_positive_macro_dice'] for r in records if r['event'] == 'validation']
    inherited = [r['inherited_best'] for r in records if r['event'] == 'resumed' and r['inherited_best'] is not None]
    candidates = scores + inherited
    best = max(candidates) if candidates else None
    require(payload['best_score'] == best and (best is None or 0 <= best <= 1),
            'Checkpoint best score differs from journal')
    provenance = dict(checkpoint=str(path), checkpoint_sha256=checkpoint_sha256, step=step,
        parent_journal=str(journal), parent_history_bytes=count,
        parent_history_prefix_sha256=hashlib.sha256(prefix).hexdigest(),
        interrupted_tail_policy='preserve_parent_replay_only_updates_after_saved_state',
        restored_fields=['model', 'optimizer', 'step', 'exposure', 'cpu_rng', 'mps_rng'],
        comparison_scope='same_experiment_development_continuation_not_bit_exact_native_replay_claim')
    return payload, expected, provenance


def restore_checkpoint(cfg, control, **resume):
    payload, expected, provenance = read_checkpoint(cfg, control, **resume)
    session = Session.restore(payload['session'], expected)
    return session, payload['best_score'], provenance
