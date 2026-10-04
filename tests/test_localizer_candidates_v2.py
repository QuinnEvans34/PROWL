import pytest
from src.data.localizer_candidates_v2 import select_candidates


def fixture():
    rows = [dict(case_id=f'{r}{i}', **{'ct phase': 'rare' if i < 2 else 'common', 'spacing': '1,1,1'})
            for r in ('t', 'v', 'x') for i in range(20)]
    roles = {r['case_id']: {'t':'train','v':'validation','x':'test'}[r['case_id'][0]] for r in rows}
    args = dict(counts={'train':8,'validation':7}, retained={'train':['t0'],'validation':['v0']},
                floors={'train':3,'validation':2}, seed='fixed')
    return rows, roles, args


def test_nested_and_score_independent():
    rows, roles, args = fixture()
    a = select_candidates(rows, roles, **args)
    for row in rows:
        row.update(dice=0, quality='bad', held=True, tumor='yes')
    assert a == select_candidates(rows[::-1], dict(reversed(list(roles.items()))), **args)
    for role in args['counts']:
        group = a['candidates'][role]
        assert len(group) == args['counts'][role]
        assert all(roles[x['study_id'].split(':')[-1]] == role for x in group)
        assert next(x for x in group if x['study_id'].endswith(args['retained'][role][0]))['selection_reason'] == 'retained'
    assert a['profiles']['train']['floor_shortfalls'] == {'rare|thin_le2mm':1}
    assert not a['qualification_or_target_permission_granted']


@pytest.mark.parametrize('fault', ['duplicate','incomplete','wrong_role','repeat_retained','small_budget','shortage','bad_floor','bad_seed'])
def test_refusals(fault):
    rows, roles, args = fixture()
    if fault == 'duplicate': rows.append(rows[0])
    if fault == 'incomplete': rows.pop()
    if fault == 'wrong_role': args['retained']['train'] = ['v0']
    if fault == 'repeat_retained': args['retained']['train'] *= 2
    if fault == 'small_budget': args['counts']['train'] = 2
    if fault == 'shortage': args['counts']['train'] = 21
    if fault == 'bad_floor': args['floors']['train'] = True
    if fault == 'bad_seed': args['seed'] = ''
    with pytest.raises(ValueError): select_candidates(rows, roles, **args)


def test_largest_remainder_and_missing_metadata():
    rows, roles, args = fixture()
    for row in rows: row['ct phase'] = ''; row['spacing'] = ''
    result = select_candidates(rows, roles, **args)
    assert result['profiles']['train']['selected_counts'] == {'missing|missing':8}
    args['counts'] = {'train':20,'validation':20}
    assert len(select_candidates(rows, roles, **args)['candidates']['train']) == 20


def test_exact_integer_remainders_and_lexical_ties():
    rows = [dict(case_id=f'{r}{k}{i}', **{'ct phase':k,'spacing':'1,1,1'})
            for r in ('t','v') for k,n in [('a',5),('b',5),('c',8)] for i in range(n)]
    roles = {x['case_id']: 'train' if x['case_id'][0]=='t' else 'validation' for x in rows}
    result = select_candidates(rows, roles, counts={'train':8,'validation':8},
        retained={'train':[],'validation':[]}, floors={'train':1,'validation':1}, seed='tie')
    # Remaining 4/4/7, five slots: floors 1/1/2 and equal 5/15 remainders; a wins.
    assert result['profiles']['train']['proportional_allocation'] == {'a|thin_le2mm':2,'b|thin_le2mm':1,'c|thin_le2mm':2}
