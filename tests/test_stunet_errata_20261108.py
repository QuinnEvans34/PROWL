import copy
import numpy as np
import pytest
from src.data.stunet_errata_20261108 import EXPECTED, corrected_target, continuation_lr, new_schedule


@pytest.mark.parametrize('name', list(EXPECTED))
def test_preserves_original_pancreas_and_inputs(name):
    count, digest = EXPECTED[name]
    p = np.ones((5, 5, 5), dtype=np.uint8); l = np.zeros_like(p); l.flat[:count] = 1
    oldp, oldl = p.copy(), l.copy()
    out = corrected_target(name, p, l, role='train', lesion_sha256=digest)
    assert np.array_equal(out, oldp) and np.array_equal(p, oldp) and np.array_equal(l, oldl)
    assert not np.shares_memory(out, p) and not (out == 2).any()


@pytest.mark.parametrize('failure', ['role', 'hash', 'count', 'nonbinary', 'shape', 'unlisted'])
def test_rejects_invalid_corrections(failure):
    name = next(iter(EXPECTED)); count, digest = EXPECTED[name]
    p = np.ones((5, 5, 5), dtype=np.uint8); l = np.zeros_like(p); l.flat[:count] = 1; role = 'train'
    if failure == 'role': role = 'development'
    if failure == 'hash': digest = '0' * 64
    if failure == 'count': l.flat[count] = 1
    if failure == 'nonbinary': p.flat[0] = 2
    if failure == 'shape': p = p[:2]
    if failure == 'unlisted': name = 'unknown'
    with pytest.raises(ValueError): corrected_target(name, p, l, role=role, lesion_sha256=digest)


def members():
    names = list(EXPECTED) + [f'synthetic-{n}' for n in range(1326)]
    return {n: dict(positive=7 <= k < 671, cover=[[0, 0, 0], [1, 0, 0]]) for k,n in enumerate(names)}


def test_schedule_exact_coverage_ratio_and_global_addresses():
    m = members(); before = copy.deepcopy(m); s = new_schedule(m)
    assert s == new_schedule(m) and m == before
    assert [x['global_address'] for x in s] == list(range(12000,24000))
    assert sum(x['kind'] == 'context' for x in s) == 3000
    actual = {(x['case_id'], tuple(x['origin'])) for x in s if x['kind'] == 'coverage'}
    assert actual == {(n,tuple(o)) for n,v in m.items() for o in v['cover']}
    assert all((x['kind'] == 'context') == (k % 4 == 3) for k,x in enumerate(s))


def test_schedule_rejects_stale_targets():
    m = members(); m[next(iter(EXPECTED))]['positive'] = True
    with pytest.raises(ValueError): new_schedule(m)


def test_learning_rate_boundaries():
    assert continuation_lr(12000) == pytest.approx(4e-8)
    assert continuation_lr(12499) == pytest.approx(2e-5)
    assert continuation_lr(23999) == 0
    assert all(continuation_lr(x+1) <= continuation_lr(x) for x in range(12499,23999))
    for x in [11999,24000,True,12000.0]:
        with pytest.raises(ValueError): continuation_lr(x)
