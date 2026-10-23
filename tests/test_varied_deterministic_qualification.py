import os
import pytest
import torch
from torch import nn
from torch.nn import functional as F
from scripts.diagnostics import deterministic_upsample_probe as det
from scripts.diagnostics import qualify_varied_deterministic as qualification


@pytest.mark.parametrize('shape',[(1,2,2,3,4),(1,1,3,3,3)])
def test_cpu_adjoint_exact_original_forward_backward(shape):
    torch.set_num_threads(2)
    x=torch.randn(shape,requires_grad=True); y=x.detach().clone().requires_grad_(True)
    a=F.interpolate(x,scale_factor=2.,mode='trilinear',align_corners=True); b=det._Trilinear.apply(y)
    assert torch.equal(a,b)
    grad=torch.randn_like(a); a.backward(grad); b.backward(grad)
    assert torch.equal(x.grad,y.grad)


def test_gradcheck():
    x=torch.randn(1,1,2,2,2,dtype=torch.double,requires_grad=True)
    assert torch.autograd.gradcheck(det._Trilinear.apply,(x,))


def test_adapter_preserves_state_dict_and_only_expected_modules():
    model=nn.Sequential(nn.Conv3d(1,1,1),*[nn.Upsample(scale_factor=2.,mode='trilinear',align_corners=True) for _ in range(3)])
    before={k:v.clone() for k,v in model.state_dict().items()}
    assert det.install(model)==3
    assert before.keys()==model.state_dict().keys()
    assert all(torch.equal(v,model.state_dict()[k]) for k,v in before.items())
    assert sum(isinstance(m,det.QualifiedUpsample) for m in model.modules())==3


def test_different_interpolation_refused():
    model=nn.Sequential(nn.Upsample(scale_factor=2.,mode='nearest'))
    with pytest.raises(ValueError,match='geometry'): det.install(model)


def test_environment_required(monkeypatch):
    monkeypatch.delenv('CUBLAS_WORKSPACE_CONFIG',raising=False)
    with pytest.raises(ValueError,match='environment'): det.configure()


def test_no_reuse_of_failed_stage_destination():
    assert qualification.SETUP!=qualification.setup.SETUP
    assert qualification.BACKUP!=qualification.old.BACKUP
    assert qualification.STAGES==('reference','producer','cold','production-cold')
