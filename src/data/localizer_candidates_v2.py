"""Nested, descriptive candidate selection. This never grants executable permission."""
from collections import Counter, defaultdict
import hashlib
from src.data.localizer_candidates import stratum

POLICY_ID = 'localizer-candidate-hybrid-v2'


def select_candidates(rows, roles, *, counts, retained, floors, seed):
    expected = {'train', 'validation'}
    if any(set(x) != expected for x in (counts, retained, floors)):
        raise ValueError('Explicit train and validation controls required')
    if not isinstance(seed, str) or not seed:
        raise ValueError('Explicit seed required')
    if any(type(v) is not int or v < 1 for x in (counts, floors) for v in x.values()):
        raise ValueError('Positive integer budgets and floors required')
    index = {}
    for row in rows:
        sid = row['case_id']
        if not isinstance(sid, str) or not sid or sid in index or sid not in roles:
            raise ValueError('Duplicate or unprotected candidate')
        index[sid] = stratum(row)
    if set(index) != set(roles) or set(roles.values()) - {'train', 'validation', 'test'}:
        raise ValueError('Incomplete protected universe')
    candidates, profiles = {}, {}
    for role in sorted(expected):
        old = list(retained[role])
        if len(old) != len(set(old)) or any(roles.get(s) != role for s in old):
            raise ValueError('Invalid retained role or duplicate')
        groups = defaultdict(list)
        for sid in sorted(index):
            if roles[sid] == role:
                groups[index[sid]].append(sid)
        if not len(old) <= counts[role] <= sum(map(len, groups.values())):
            raise ValueError('Candidate shortage or retained budget violation')
        chosen = {s: 'retained' for s in old}
        queues = {}
        for key in sorted(groups):
            queues[key] = sorted((s for s in groups[key] if s not in chosen), key=lambda s: (
                hashlib.sha256(f'{POLICY_ID}:{seed}:{role}:{s}'.encode()).hexdigest(), s))
            need = max(0, min(floors[role], len(groups[key])) - sum(index[s] == key for s in old))
            for s in queues[key][:need]:
                chosen[s] = 'coverage_floor'
            queues[key] = queues[key][need:]
        if len(chosen) > counts[role]:
            raise ValueError('Budget cannot satisfy retained members and floors')
        slots = counts[role] - len(chosen)
        population = sum(map(len, queues.values()))
        allocation = {k: (slots * len(q) // population if population else 0) for k, q in queues.items()}
        order = sorted(queues, key=lambda k: (-(slots * len(queues[k]) % population if population else 0), k))
        for key in order[:slots - sum(allocation.values())]:
            allocation[key] += 1
        for key in sorted(queues):
            for s in queues[key][:allocation[key]]:
                chosen[s] = 'proportional'
        assert len(chosen) == counts[role]
        candidates[role] = [dict(study_id='pants:study:' + s, protected_role=role,
            descriptive_stratum=index[s], selection_reason=chosen[s], status='candidate_not_qualified')
            for s in sorted(chosen)]
        profiles[role] = dict(universe_counts={k: len(v) for k, v in sorted(groups.items())},
            selected_counts=dict(sorted(Counter(index[s] for s in chosen).items())),
            reason_counts=dict(sorted(Counter(chosen.values()).items())),
            floor_shortfalls={k: floors[role] - len(v) for k, v in sorted(groups.items()) if len(v) < floors[role]},
            remaining_population={k: len(v) for k, v in sorted(queues.items())},
            proportional_allocation=allocation)
    return dict(policy_id=POLICY_ID, seed=seed, requested_counts=dict(counts), floors=dict(floors),
        candidates=candidates, profiles=profiles, status='selection_only_not_executable',
        qualification_or_target_permission_granted=False,
        replacement_policy='Preserve held candidates; no silent replacement.',
        tie_rule='Largest integer remainder first; equal remainders use lexical stratum order.')
