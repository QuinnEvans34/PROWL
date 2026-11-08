"""Opt-in seven-case correction and new schedule primitives; no dispatcher."""
import copy
import hashlib
import math
import numpy as np

POLICY = 'pants-issue12-local-normal-mask-1'
EXPECTED = {
    'PanTS_00000044': (16, '864d92f2b268ceddc5c4943b24bd7f86ec47d7af3e6457ac4744ecd6861ff767'),
    'PanTS_00001819': (45, '876409ec79049b42af7242e2363ffd9965aa09c5f7f138b00cd7f17f88b0ecfe'),
    'PanTS_00003059': (12, '62601f3f027309af4fe82ec1f7bfacde58230442aa07c209b37d94cc535b5107'),
    'PanTS_00003548': (36, '25cdb9c2bab35a283dab87f8c1d02801c7dce77929f5d02e851f858bdf94d306'),
    'PanTS_00005693': (20, '30a4f23140398ca2cca54335961fa0232e3cb869bbaf613caf43ae3025fb1648'),
    'PanTS_00007933': (16, '6f84c81a34e4fe9e9faf4abb320b1d0a78ddb16609297a4976f1bd184cd9f830'),
    'PanTS_00007947': (32, 'bd0902047a074176c445c40d80b74f40be0e37ab069aee187b69b32341644b99'),
}


def corrected_target(case_id, pancreas, lesion, *, role, lesion_sha256):
    if role != 'train' or case_id not in EXPECTED:
        raise ValueError('Whitelist training role required')
    count, expected = EXPECTED[case_id]
    if lesion_sha256 != expected:
        raise ValueError('Original lesion identity differs')
    if (pancreas.dtype != np.uint8 or lesion.dtype != np.uint8
            or pancreas.ndim != 3 or pancreas.shape != lesion.shape
            or not np.isin(pancreas, [0, 1]).all() or not np.isin(lesion, [0, 1]).all()):
        raise ValueError('Aligned binary source masks required')
    if int(lesion.sum()) != count or not pancreas.any():
        raise ValueError('Source count or pancreas invalid')
    # Reconstruct from the original pancreas, including voxels overwritten by lesion.
    return pancreas.copy()


def continuation_lr(global_step):
    if type(global_step) is not int or not 12000 <= global_step < 24000:
        raise ValueError('Continuation zero-based global address required')
    s = global_step - 12000
    return 2e-5 * (s + 1) / 500 if s < 500 else 1e-5 * (1 + math.cos(math.pi * (s + 1 - 500) / 11500))


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
    seed = int.from_bytes(hashlib.sha256(b'stunet-corrected-continuation-20261108:42').digest()[:8], 'little')
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
        result.append(dict(row, global_address=s + 12000))
    return result
