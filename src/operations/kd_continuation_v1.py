"""Bind a KD checkpoint to its durable journal prefix and completed selection.

Read-only. Does not stop workers, restore a model, grant launch authority, or
change any producer. Call again after cleanup before preparing a continuation.
"""
import json
import math
from pathlib import Path
import torch
from src.data.segmenter_teacher_cache_v1 import sha
from src.training.native_error_review_v1 import component_table
from src.data.manifest_records import digest


def remaining_budget(limit, resources):
    if type(limit) is not int or limit <= 0 or not resources:
        raise ValueError('Bounded parent attempts required')
    charged = 0
    for row in resources:
        seconds = row.get('seconds')
        if (row.get('workers_reaped') is not True or isinstance(seconds,bool)
                or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds < 0):
            raise ValueError('Reaped parent with measured elapsed time required')
        charged += math.ceil(seconds)
    remaining = limit-charged
    if remaining <= 0: raise ValueError('Original cumulative runtime budget exhausted')
    return dict(charged_seconds=charged, remaining_seconds=remaining, original_seconds=limit)


def inspect_checkpoint(execution, backup, filename, *, validate_every=2000):
    execution, backup = Path(execution), Path(backup)
    if Path(filename).name != filename or not filename.endswith('.pt'):
        raise ValueError('Checkpoint basename required')
    checkpoint = execution/filename; independent = backup/filename
    pin = sha(checkpoint)
    if sha(independent) != pin: raise ValueError('Independent checkpoint mismatch')
    saved = torch.load(independent,weights_only=True,map_location='cpu')
    state=saved['session']; step=state['student']['raw']['step']
    length=saved['history_bytes']; journal=execution/'history.jsonl'
    if type(length) is not int or length <= 0 or type(step) is not int or step < 0:
        raise ValueError('Invalid checkpoint counters')
    with journal.open('rb') as stream: prefix=stream.read(length)
    if len(prefix)!=length or not prefix.endswith(b'\n'):
        raise ValueError('Incomplete checkpoint journal prefix')
    rows=[json.loads(line) for line in prefix.splitlines()]
    if rows[0].get('identity') != state['identity']:
        raise ValueError('Checkpoint/journal identity differs')
    updates=[r for r in rows if r['event']=='update']
    start=rows[0].get('step',0)
    if [r['step'] for r in updates] != list(range(start+1,step+1)):
        raise ValueError('Checkpoint journal update sequence differs')
    completed=[r for r in rows if r['event']=='native_completed']
    selected_step=completed[-1]['selected_step'] if completed else None
    # Resumed journals explicitly bind inherited selection in their first event.
    if selected_step is None: selected_step=rows[0].get('selected_step')
    report=None; pins={str(checkpoint):pin,str(independent):pin}
    if selected_step is not None:
        if not 0 < selected_step <= step: raise ValueError('Invalid selected step')
        report_path=execution/f'native-{selected_step:06d}.json'
        sidecar=report_path.with_name(report_path.stem+'-components.json')
        best_checkpoint=execution/f'step-{selected_step:06d}.pt'
        for path in (report_path,sidecar,best_checkpoint):
            h=sha(path)
            if sha(backup/path.name)!=h: raise ValueError('Independent selection evidence mismatch')
            pins[str(path)]=h; pins[str(backup/path.name)]=h
        raw=report_path.read_bytes(); report=json.loads(raw)
        component_table(json.loads(sidecar.read_text()),report,digest(raw))
        if report['step']!=selected_step: raise ValueError('Selected report step differs')
        if saved['best_score'] != report['lesion_positive_macro_dice']:
            raise ValueError('Checkpoint best score differs from completed selection')
    elif saved['best_score'] is not None:
        raise ValueError('Missing historical selection')
    pending=step>0 and step%validate_every==0 and not any(r['step']==step for r in completed)
    if sha(checkpoint)!=pin or sha(independent)!=pin:
        raise ValueError('Checkpoint changed during inspection')
    return dict(version='kd-checkpoint-continuation-1',step=step,identity=state['identity'],
        checkpoint=str(independent),checkpoint_sha256=pin,journal=str(journal),
        history_bytes=length,journal_prefix_sha256=digest(prefix),pins=pins,
        best_score=saved['best_score'],selected_step=selected_step,selected_report=report,
        pending_validation=pending,scientific_ready=False)
