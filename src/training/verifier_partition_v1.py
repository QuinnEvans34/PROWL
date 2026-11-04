"""Deterministic patient-role planning from existing training metadata only."""
from collections import Counter
import hashlib
import math

SEED = 'verifier-generator-20261023-v1'


def stratum(row):
    volume = row['lesion_volume_mm3']
    if not math.isfinite(volume) or volume < 0:
        raise ValueError('Invalid lesion volume')
    if not row['positive']:
        if volume != 0: raise ValueError('Negative case has lesion volume')
        return 'negative'
    if volume <= 0: raise ValueError('Positive case lacks lesion volume')
    return 'small' if volume < 1000 else 'medium' if volume <= 10000 else 'large'


def take(rows, count, stage):
    if not 0 <= count <= len(rows): raise ValueError('Invalid partition size')
    groups = {}
    for r in rows: groups.setdefault(stratum(r), []).append(r)
    if not rows: return [], []
    quotas = {s: count*len(g)//len(rows) for s,g in groups.items()}
    remainder = count-sum(quotas.values())
    order = sorted(groups, key=lambda s: (-(count*len(groups[s]) % len(rows)), s))
    for s in order[:remainder]: quotas[s] += 1
    selected=[];rest=[]
    for s in sorted(groups):
        ordered=sorted(groups[s], key=lambda r: hashlib.sha256(f'{SEED}:{stage}:{r["case_id"]}'.encode()).hexdigest())
        selected.extend(ordered[:quotas[s]]);rest.extend(ordered[quotas[s]:])
    return selected,rest


def partition(rows, development_ids, sizes=(800,333,200), fit_size=266):
    names=[r['case_id'] for r in rows];dev=list(development_ids)
    if len(set(names))!=len(names) or len(set(dev))!=len(dev) or set(names)&set(dev):
        raise ValueError('Duplicate or protected membership')
    if any(type(n) is not int or n<=0 for n in sizes) or sum(sizes)!=len(rows):
        raise ValueError('Every training patient must be assigned exactly once')
    if not 0<fit_size<sizes[1]:raise ValueError('Verifier needs fit and tuning patients')
    for r in rows:stratum(r)
    generator,remaining=take(rows,sizes[0],'generator')
    verifier,calibration=take(remaining,sizes[1],'verifier')
    fit,tune=take(verifier,fit_size,'fit')
    groups={'generator_train':generator,'verifier_fit':fit,'verifier_tune':tune,'verifier_calibration':calibration}
    return dict(seed=SEED,roles={k:sorted(r['case_id'] for r in v) for k,v in groups.items()},
                counts={k:dict(Counter(stratum(r) for r in v)) for k,v in groups.items()},
                development=sorted(dev),selection='fixed_terminal_24000_no_development_selection',
                status='PARTITIONS_ONLY_NOT_LAUNCH_READY')
