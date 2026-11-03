import json
import numpy as np
import pytest
import torch
from src.inference.cascade_trace_forward_v1 import TraceForward


class Model(torch.nn.Module):
    def forward(self,x):return torch.cat([x,x+1,x*2],dim=1)


def test_trace_exact_output_input_rng_and_no_extra_calls(tmp_path):
    model=Model();trace=TraceForward(model,tmp_path,{0:[0,0,0],2:[72,0,0]})
    x=torch.arange(64,dtype=torch.float32).reshape(1,1,4,4,4)
    expected=model(x);before=x.clone();rng=torch.get_rng_state().clone()
    for _ in range(3):assert torch.equal(trace(x),expected)
    assert torch.equal(x,before) and torch.equal(torch.get_rng_state(),rng)
    trace.finish([[0,0,0],[36,0,0],[72,0,0]])
    assert json.loads((tmp_path/'trace.json').read_text())['extra_forwards']==0
    assert len(list(tmp_path.glob('*.npy')))==4
    assert np.array_equal(np.load(tmp_path/'trace-000-input.npy'),x.numpy())
    assert np.array_equal(np.load(tmp_path/'trace-002-logits.npy'),expected.numpy())


def test_trace_rejects_grid_change_and_duplicate_write(tmp_path):
    trace=TraceForward(Model(),tmp_path,{0:[0,0,0],1:[1,0,0]});x=torch.ones(1,1,2,2,2)
    trace(x);trace(x)
    with pytest.raises(ValueError,match='origins'):trace.finish([[0,0,0],[2,0,0]])
    duplicate=TraceForward(Model(),tmp_path,{0:[0,0,0],1:[1,0,0]})
    with pytest.raises(FileExistsError):duplicate(x)
