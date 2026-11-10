import copy
import pytest
from src.data.stunet_errata_20261108 import EXPECTED, new_schedule as prior_schedule
from src.data.stunet_longer_schedule_20261110 import new_schedule
from src.training.stunet_longer_session_20261110 import continuation_lr

def members():
    names = list(EXPECTED) + [f'synthetic-{n}' for n in range(1326)]
    return {n: dict(positive=7 <= k < 671, cover=[[0, 0, 0], [1, 0, 0]]) for k,n in enumerate(names)}


def test_schedule_exact_coverage_ratio_and_global_addresses():
    m = members(); before = copy.deepcopy(m); s = new_schedule(m)
    assert s == new_schedule(m) and m == before
    assert [x['global_address'] for x in s] == list(range(24000,36000))
    assert sum(x['kind'] == 'context' for x in s) == 3000
    actual = {(x['case_id'], tuple(x['origin'])) for x in s if x['kind'] == 'coverage'}
    assert actual == {(n,tuple(o)) for n,v in m.items() for o in v['cover']}
    assert all((x['kind'] == 'context') == (k % 4 == 3) for k,x in enumerate(s))


def test_schedule_rejects_stale_targets():
    m = members(); m[next(iter(EXPECTED))]['positive'] = True
    with pytest.raises(ValueError): new_schedule(m)


def test_learning_rate_boundaries():
    assert continuation_lr(24000) == pytest.approx(4e-8)
    assert continuation_lr(24499) == pytest.approx(2e-5)
    assert continuation_lr(35999) == 0
    assert all(continuation_lr(x+1) <= continuation_lr(x) for x in range(24499,35999))
    for x in [23999,36000,True,24000.0]:
        with pytest.raises(ValueError): continuation_lr(x)


def test_not_a_replay_of_prior_sampling():
    m=members(); old=prior_schedule(m); new=new_schedule(m)
    assert {r["global_address"] for r in old}.isdisjoint(r["global_address"] for r in new)
    assert [r["case_id"] for r in old] != [r["case_id"] for r in new]
