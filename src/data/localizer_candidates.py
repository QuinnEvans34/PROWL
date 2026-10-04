"""Deterministic candidate selection only; never qualification or executable membership."""
from collections import defaultdict
import hashlib
import math

POLICY_ID = 'localizer-candidate-diversity-v1'
FIELDS = ('case_id', 'ct phase', 'spacing')


def stratum(row):
    phase = str(row.get('ct phase') or '').strip().lower() or 'missing'
    try:
        values = [float(x) for x in row.get('spacing', '').split(',')]
        if len(values) != 3 or not all(math.isfinite(x) and x > 0 for x in values):
            raise ValueError('Invalid descriptive spacing')
        z = values[2]
        thickness = 'thin_le2mm' if z <= 2 else 'medium_le5mm' if z <= 5 else 'thick_gt5mm'
    except (ValueError, TypeError, AttributeError):
        thickness = 'missing'
    return phase + '|' + thickness


def select_candidates(rows, roles, *, counts, retained_train=(), seed='prowl-sept29-v1'):
    """Round-robin strata, rare strata first; hash-ranked within each stratum.

    Historical spacing/phase are descriptive, not verified geometry. No model, label quality,
    tumor metadata, or presumed eligibility enters selection. Holds remain selected candidates.
    """
    if set(counts) != {'train', 'validation'} or any(type(n) != int or n < 1 for n in counts.values()):
        raise ValueError('Positive train/validation budgets required')
    index = {}
    for row in rows:
        sid = row['case_id']
        if sid in index or sid not in roles:
            raise ValueError('Duplicate or unprotected candidate')
        index[sid] = {k:row.get(k, '') for k in FIELDS}
    if set(index) != set(roles) or any(r not in ('train','validation','test') for r in roles.values()):
        raise ValueError('Incomplete protected metadata universe')
    retained = list(retained_train)
    if len(set(retained)) != len(retained) or any(roles.get(s) != 'train' for s in retained) or len(retained) > counts['train']:
        raise ValueError('Invalid retained training members')
    selected, profiles = {}, {}
    def rank(s):
        return hashlib.sha256(f'{POLICY_ID}:{seed}:{s}'.encode()).hexdigest()
    for role in counts:
        groups = defaultdict(list)
        for sid,row in index.items():
            if roles[sid] == role:
                groups[stratum(row)].append(sid)
        order = sorted(groups, key=lambda k:(len(groups[k]), k))
        queues = {k:sorted(groups[k], key=lambda s:(rank(s),s)) for k in order}
        chosen = sorted(retained) if role == 'train' else []
        for k in order:
            queues[k] = [s for s in queues[k] if s not in chosen]
        while len(chosen) < counts[role]:
            progressed = False
            for k in order:
                if queues[k] and len(chosen) < counts[role]:
                    chosen.append(queues[k].pop(0));progressed = True
            if not progressed:
                raise ValueError('Candidate shortage; no cross-role fill')
        selected[role] = [dict(study_id='pants:study:'+s,protected_role=role,
            descriptive_stratum=stratum(index[s]),status='candidate_not_qualified',
            retained_smoke_member=s in retained) for s in sorted(chosen)]
        covered = {r['descriptive_stratum'] for r in selected[role]}
        profiles[role] = dict(universe_counts={k:len(groups[k]) for k in order},
                             represented_strata=sorted(covered),unrepresented_strata=sorted(set(groups)-covered))
    return dict(policy_id=POLICY_ID,seed=seed,status='selection_only_not_executable',
                requested_counts=counts,candidates=selected,profiles=profiles,
                replacement_policy='No silent replacement for holds; preserve candidates and publish a new explicit selection version for expansion.',
                qualification_or_target_permission_granted=False)
