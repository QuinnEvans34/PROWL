"""Describe exposed evaluation changes without inventing review decisions."""
from copy import deepcopy

from .query import normalize_question

CORE = ('question', 'primary_need', 'family', 'difficulty', 'intent_group',
        'finding', 'expected', 'concepts')


def delta_cases(before, after):
    """Report added/removed/changed content; never equate unchanged with accepted."""
    def index(cases):
        result = {}
        for case in cases:
            if case.get('split') != 'development' or case['id'] in result:
                raise ValueError('Expected unique exposed development cases')
            result[case['id']] = case
        return result
    old, new = index(before), index(after)
    rows = []
    for key, case in new.items():
        previous = old.get(key)
        fields = [f for f in CORE if previous is None or previous[f] != case[f]]
        old_spans = previous['labels']['spans'] if previous else []
        old_judgments = previous['source_judgments'] if previous else []
        rows.append(dict(id=key, new=previous is None, changed_core_fields=fields,
            added_or_changed_spans=[s for s in case['labels']['spans'] if s not in old_spans],
            removed_spans=[s for s in old_spans if s not in case['labels']['spans']],
            added_or_changed_judgments=[s for s in case['source_judgments'] if s not in old_judgments],
            removed_judgments=[s for s in old_judgments if s not in case['source_judgments']],
            gap_recheck_required=case['expected']['status'] == 'insufficient_evidence'))
    return dict(cases=rows, removed_ids=[key for key in old if key not in new],
                acceptance_recorded=False, ready_for_tuning=False)


def extend_exposure(inventory, sources):
    """Union explicit public wording sources, retaining every previous origin."""
    result = deepcopy(inventory)
    rows = {r['normalized_wording']: r for r in result['rows']}
    if len(rows) != len(result['rows']):
        raise ValueError('Duplicate normalized exposure row')
    count = result['record_count']
    for source in sources:
        if source['exposure'] != 'development_only':
            raise ValueError('Protected or unknown exposure is forbidden')
        for case in source['cases']:
            wording = case['question']
            normalized = normalize_question(wording).casefold()
            row = rows.setdefault(normalized, dict(normalized_wording=normalized, variants=[], origins=[]))
            if wording not in row['variants']:
                row['variants'].append(wording)
            row['origins'].append(dict(file=source['path'], sha256=source['sha256'], case_id=case['id']))
            count += 1
    result.update(rows=[rows[k] for k in sorted(rows)], record_count=count,
                  distinct_wording_count=len(rows))
    return result
