import pytest
from src.operations.workflow_plan_v1 import Stage, plan


def stage(id, deps=(), **kw): return Stage(id, deps, producer='a'*64, **kw)


def test_stable_order_and_snapshot():
    config={'value':1}
    stages=[stage('b',('a',)),stage('a',config=config)]
    first=plan(stages)
    assert first==plan(reversed(stages))
    config['value']=2
    assert first['stages'][0]['config']=={'value':1}


@pytest.mark.parametrize('stages', [[],[stage('a'),stage('a')], [stage('b',('missing',))],
    [stage('a',('b',)),stage('b',('a',))], [stage('a',('a',))],
    [stage('a',inputs={'source':'not-a-hash'})], [Stage('a')]])
def test_reject_bad_graph(stages):
    with pytest.raises(ValueError): plan(stages)


def test_selective_invalidation():
    def graph(v): return plan([stage('source'),stage('left',('source',),config={'v':v}),
                             stage('right',('source',)),stage('final',('left','right'))])
    a={r['id']:r['derivation'] for r in graph(1)['stages']}
    b={r['id']:r['derivation'] for r in graph(2)['stages']}
    assert {k for k in a if a[k]!=b[k]}=={'left','final'}
