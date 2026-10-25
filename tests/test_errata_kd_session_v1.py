from copy import deepcopy
import pytest
import torch
from test_distillation_integration_v1 import Provider,store,same,isolated_cpu
from src.training import segmenter_full_session_v1 as full
from src.training.segmenter_errata_kd_session_v1 import OnDemandStudent,ErrataKDSession
from src.training.segmenter_distillation_v1 import DistillationConfig

def session(p,pin,weight):
    c=dict(max_steps=8,tensor_shape=[16]*3,seed=42,learning_rate=1e-4,weight_decay=1e-5,warmup_steps=0,lr_schedule='constant',loss_id=full.DICE_FOCAL)
    raw=full.Session(c,p.control,device='cpu',initialization={'kind':'scratch'})
    return ErrataKDSession(OnDemandStudent(raw),teacher_identity={'weights':{'sha256':'a'*64}},loss_config=DistillationConfig(max_weight=weight,ramp_updates=2),target_manifest_sha256=pin)

def test_on_demand_positive_kd_restore_continues_exactly(tmp_path):
    p=Provider();targets=store(tmp_path,p);a=session(p,targets.pin,.1)
    a.update(p,targets);state=a.state();b=ErrataKDSession.restore(state,a.identity)
    x=a.update(p,targets);y=b.update(Provider(),targets)
    assert x==y and same(a.state(),b.state())
    assert a.identity['student']['throughput']['prefetch'] is False

def test_zero_kd_and_wrong_restore_identity(tmp_path):
    p=Provider();a=session(p,'a'*64,0);row=a.update(p)
    assert not row['teacher_accessed']
    wrong=deepcopy(a.identity);wrong['student']['throughput']['prefetch']=True
    with pytest.raises(ValueError):ErrataKDSession.restore(a.state(),wrong)
