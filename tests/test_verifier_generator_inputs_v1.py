from copy import deepcopy
import pytest
from src.data.verifier_generator_inputs_v1 import GeneratorInputs
from src.data.segmenter_fast_varied_v1 import FastVariedInputs


@pytest.fixture
def make(monkeypatch):
    def init(self,**kwargs):
        self.pin='p'*64;self.control=dict(train=['a','b','c','d'],validation=['dev'])
        self.rows={n:{} for n in ['a','b','c','d','dev']};self.observations=deepcopy(self.rows)
        self.cache_manifest=dict(members={n:{} for n in ['a','b','c','d']})
        self._closed=False;self._executor=None;self._future=None;self._next=None
    monkeypatch.setattr(FastVariedInputs,'__init__',init)
    def factory(**changes):
        args=dict(partitions=dict(roles=dict(generator_train=['a'],verifier_fit=['b'],verifier_tune=['c'],verifier_calibration=['d']),development=['dev']),partition_sha256='a'*64,focused_counts={'a':18},expected_parent_pin='p'*64)
        args.update(changes);return GeneratorInputs(**args)
    return factory


def test_restricted_control(make):
    p=make()
    assert p.control['train']==['a'] and set(p.rows)==set(p.observations)=={'a'}
    assert set(p.cache_manifest['members'])=={'a'}
    assert p.pin!='p'*64 and not p.control['restricted_generator']['evaluation_enabled']
    p.check_role('a','train','optimizer');p.close()


@pytest.mark.parametrize('name',['b','c','d','dev','unknown'])
def test_reject_before_io(make,name):
    p=make()
    with pytest.raises(ValueError):p.load(name,role='train',operation='optimizer')
    with pytest.raises(ValueError):p.cache_member(name)
    with pytest.raises(ValueError):p.plan_next((name,1,0,42))
    assert p._next is None;p.close()


def test_no_development_eval(make):
    p=make()
    with pytest.raises(ValueError):p.load('dev',role='validation',operation='evaluator')
    p.close()


def test_parent_and_schedule_binding(make):
    with pytest.raises(ValueError):make(expected_parent_pin='wrong')
    with pytest.raises(ValueError):make(focused_counts={'b':18})


def test_worker_shutdown(make):
    p=make();p.enable_prefetch();p.close();assert p._closed
    with pytest.raises(ValueError):p.enable_prefetch()
