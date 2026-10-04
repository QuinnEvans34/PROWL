import math
import pytest
import torch
from src.training.localizer_diagnostics import probability_summary,logit_diagnostics


def test_probability_decomposition_and_empty_oracle():
    p=torch.tensor([.2,.7]);y=torch.tensor([0,1]);r=probability_summary(p,y)
    ce=-(math.log(.8)+math.log(.7))/2
    dice=1-(1.4+1e-5)/(1.9+1e-5)
    assert r['ce']==pytest.approx(ce,abs=1e-6)
    assert r['total']==pytest.approx(ce+dice,abs=1e-6)
    assert r['ce_foreground_contribution']==pytest.approx(-math.log(.7)/2,abs=1e-6)
    assert r['threshold_diagnostics'][-1]['dice']==1
    assert probability_summary(p,torch.zeros_like(y))['foreground_probability'] is None
    assert probability_summary(p,torch.zeros_like(y))['soft_dice_loss']==0


def test_gradients_match_independent_derivatives_and_leave_inputs_unchanged():
    p=torch.tensor([.2,.7]);d=torch.logit(p);logits=torch.stack([torch.zeros_like(d),d]).reshape(1,2,1,1,2)
    y=torch.tensor([0,1]).reshape(1,1,1,1,2);original=logits.clone();r=logit_diagnostics(logits,y)
    assert torch.equal(original,logits) and logits.grad is None
    ce=r['terms']['ce'];assert ce['groups']['foreground']['signed_sum']==pytest.approx(-.15,abs=1e-6)
    assert ce['groups']['background']['signed_sum']==pytest.approx(.1,abs=1e-6)
    def independent(shift):
        prob=[1/(1+math.exp(-(v+shift))) for v in d.tolist()]
        return 1-(2*prob[1]+1e-5)/(sum(prob)+1+1e-5)
    eps=1e-4;fd=(independent(eps)-independent(-eps))/(2*eps)
    assert r['terms']['soft_dice']['uniform_logit_shift_derivative']==pytest.approx(fd,abs=1e-6)


@pytest.mark.parametrize('p,y',[(torch.tensor([float('nan')]),torch.tensor([1])),(torch.tensor([1.1]),torch.tensor([1])),(torch.tensor([.2]),torch.tensor([2]))])
def test_invalid_probabilities_or_targets_refused(p,y):
    with pytest.raises(ValueError):probability_summary(p,y)
