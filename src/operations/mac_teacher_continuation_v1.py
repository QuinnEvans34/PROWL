"""Explicit case-boundary reuse after an operator-requested supervised stop."""
import json
import math
from pathlib import Path
import numpy as np
from src.data.segmenter_teacher_cache_v1 import sha


def remaining_seconds(request, resources, *, owned_worker_kill=False):
    stopped = resources.get('error') == "InterruptedError('Supervisor signal 15')"
    killed = (owned_worker_kill is True and resources.get('exit_code') == -9
              and resources.get('error') == "ValueError('Duration worker failed')")
    if (resources.get('workers_reaped') is not True
            or resources.get('success') is not False
            or not (stopped or killed)):
        raise ValueError('Verified operator stop and reaped workers required')
    spent = resources.get('seconds')
    if type(spent) not in (int, float) or not math.isfinite(spent) or spent < 0:
        raise ValueError('Missing supervised elapsed time')
    remaining = request['limits']['seconds'] - math.ceil(spent)
    if remaining <= 0:
        raise ValueError('Original generation time budget exhausted')
    return remaining


def completed_members(root, request):
    """Ignore incomplete payloads; completed records must all verify or fail."""
    root = Path(root); members = {}
    names = request['train']
    if len(set(names)) != len(names): raise ValueError('Duplicate training members')
    for name in names:
        if Path(name).name != name or name in ('.', '..'):
            raise ValueError('Unsafe case name')
        record = root/(name+'.json')
        if not record.exists(): continue
        row = json.loads(record.read_text()); payload = root/(name+'.npz')
        if row['case_id'] != name or payload.stat().st_size != row['bytes'] or sha(payload) != row['payload_sha256']:
            raise ValueError('Completed teacher payload changed')
        with np.load(payload, allow_pickle=False) as data:
            if data.files != ['probability'] or data['probability'].dtype != np.uint16 or list(data['probability'].shape) != row['native_geometry']['shape']:
                raise ValueError('Completed probability shape/type mismatch')
        members[name] = row
    if not members: raise ValueError('No verified completed cases to reuse')
    return members
