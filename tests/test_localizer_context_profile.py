import pytest
import torch
from scripts.diagnostics.localizer_context_profile import profile_size,profile_config,patch_batch
from src.training.localizer import validate_config

@pytest.mark.parametrize('size',[0,128,145,True,144.0])
def test_unprepared_profile_size_refused(size):
    with pytest.raises(ValueError):profile_size(size)

def test_production_guard_not_widened():
    with pytest.raises(ValueError):validate_config(profile_config(144))
    validate_config(profile_config(96))

@pytest.mark.parametrize('size',[96,144])
def test_synthetic_center_crop_is_exact_and_independent(size):
    x=torch.arange(160*160*160,dtype=torch.float32).reshape(1,160,160,160)
    y=torch.zeros_like(x);y[:,75:85,75:85,75:85]=1
    a,b,t=patch_batch(x,y,profile_config(size),step=0,member_id='invented')
    start=(160-size)//2
    assert a.shape==(1,1,size,size,size) and torch.equal(a[0],x[:,start:start+size,start:start+size,start:start+size])
    assert b.sum()==1000 and t['physical_span_mm']==2*size
    a.zero_();assert x.sum()>0
