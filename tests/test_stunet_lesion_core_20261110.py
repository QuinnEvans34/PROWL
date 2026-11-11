import numpy as np
import pytest

from scripts.diagnostics.screen_stunet_lesion_core_20261110 import core_support, summarize


def test_core_rule_uses_full_affine_and_grows_only_adjacent_background():
    code = np.zeros((7,4,4),np.uint8)
    code[0,0,0] = 8
    code[1:5,0,0] = 4
    code[0,1,0] = 1  # the incumbent's raw predicted pancreas
    code[0,0,1] = 2  # background fallback, direct neighbor
    code[0,0,2] = 2  # two steps from core, never admitted
    code[1,0,1] = 2  # diagonal neighbor, physical distance sqrt(5)
    code[1,1,0] = 3  # pancreas fallback, never admitted
    affine = np.diag([2.,1.,1.,1.])
    baseline, tiers, distance, shells = core_support(code,affine,trim_levels=[2,3],grow_radii=[0,1.5,3])
    to_xyz = lambda indices: list(zip(*np.unravel_index(indices,code.shape)))
    assert to_xyz(baseline[(tiers>2)|(distance<=4)]) == [(0,0,0),(1,0,0),(2,0,0)]
    assert to_xyz(shells[0]) == []
    assert to_xyz(shells[1.5]) == [(0,0,1)]
    assert to_xyz(shells[3]) == [(0,0,1),(1,0,1)]
    affine[0,2] = 2.
    assert to_xyz(core_support(code,affine,trim_levels=[2,3],grow_radii=[0,1.5,3])[3][1.5]) == []


def test_higher_dice_does_not_override_recall_or_false_positive_guard():
    rows = []
    for i in range(70):
        positive = i < 36
        base = dict(p=100 if positive else 1,t=50 if positive else 0,hits=[1] if positive else [])
        arms = {'incumbent':base}
        for name in ['safe','lose_recall','increase_empty_fp']+[f'noop{j}' for j in range(15)]:
            c = dict(base,added_voxels=0,added_tp=0,dropped_voxels=0,dropped_tp=0)
            if positive and name in ('safe','lose_recall','increase_empty_fp'):
                c['p'] = 80
            if positive and name == 'lose_recall':
                c['t'] -= 1
            if not positive and name == 'increase_empty_fp':
                c['p'] += 1
            arms[name] = c
        rows.append(dict(case_id=str(i),n=100 if positive else 0,small=i<5,
                         reference_count=2 if i<9 else int(positive),voxel_mm3=1,arms=arms))
    result = summarize(rows)
    assert result['qualified_count'] == 1 and result['selected'] == 'safe'
    assert result['candidates']['lose_recall']['checks']['dice_improved']
    assert not result['candidates']['lose_recall']['checks']['recall_non_decrease']
    assert not result['candidates']['increase_empty_fp']['checks']['empty_fp_nonincrease']
    with pytest.raises(ValueError,match='denominators'):
        summarize(rows[:-1])
