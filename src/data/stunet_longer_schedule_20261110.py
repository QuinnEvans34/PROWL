"""New deterministic addresses for the approved same-patient longer phase."""
import copy,hashlib
import numpy as np
from src.data.stunet_errata_20261108 import EXPECTED
def new_schedule(members):
    names = sorted(members)
    if len(names) != 1333 or not set(EXPECTED).issubset(members):
        raise ValueError('Complete training membership required')
    if sum(bool(m['positive']) for m in members.values()) != 664:
        raise ValueError('Corrected positive count required')
    if any(members[n]['positive'] for n in EXPECTED):
        raise ValueError('Stale original positive target')
    total = sum(len(m['cover']) for m in members.values())
    if not 0 < total <= 9000 or any(not m['cover'] for m in members.values()):
        raise ValueError('Insufficient coverage slots')
    seed = int.from_bytes(hashlib.sha256(b'stunet-longer-36k-20261110:42').digest()[:8], 'little')
    rng = np.random.Generator(np.random.PCG64(seed)); focus = []
    for cycle in range(max(len(m['cover']) for m in members.values())):
        for index in rng.permutation(len(names)):
            name = names[int(index)]
            if cycle < len(members[name]['cover']):
                focus.append(dict(case_id=name, kind='coverage', origin=copy.deepcopy(members[name]['cover'][cycle])))
    for kind, target, entries in [('component_jitter', 9000, focus), ('context', 3000, context := [])]:
        while len(entries) < target:
            for index in rng.permutation(len(names)):
                if len(entries) == target: break
                entries.append(dict(case_id=names[int(index)], kind=kind))
    result = []; fi = ci = 0
    for s in range(12000):
        if s % 4 == 3: row = context[ci]; ci += 1
        else: row = focus[fi]; fi += 1
        result.append(dict(row, global_address=s + 24000))
    return result
