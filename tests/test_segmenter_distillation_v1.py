import math

import pytest
import torch

from src.training.segmenter_distillation_v1 import (
    DistillationConfig, add_teacher_guidance, lesion_guidance,
)


@pytest.fixture(autouse=True)
def one_cpu_thread():
    before = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(before)


def tensors():
    logits = torch.zeros((1, 3, 2, 2, 2), requires_grad=True)
    y = torch.tensor([0, 1, 2, 0, 1, 2, 0, 0]).reshape(1, 2, 2, 2)
    q = torch.where(y == 2, .9, .1).requires_grad_()
    return logits, y, q, torch.ones_like(y, dtype=torch.bool)


@pytest.mark.parametrize('kwargs', [
    {'max_weight': -1}, {'max_weight': float('nan')}, {'max_weight': True},
    {'max_weight': 1.1}, {'temperature': 0}, {'temperature': float('inf')},
    {'temperature': True}, {'ramp_updates': -1}, {'ramp_updates': 1.2},
])
def test_invalid_config(kwargs):
    with pytest.raises(ValueError): DistillationConfig(**kwargs)


def test_weight_schedule_and_identity():
    c = DistillationConfig()
    assert c.weight(1) == pytest.approx(.0001)
    assert c.weight(500) == pytest.approx(.05)
    assert c.weight(1000) == c.weight(24000) == .1
    assert DistillationConfig(ramp_updates=0).weight(1) == .1
    with pytest.raises(ValueError): c.weight(0)
    with pytest.raises(ValueError): c.weight(True)


def test_zero_weight_is_exact_control_without_teacher_access():
    base = torch.tensor(1.234, requires_grad=True)
    total, report = add_teacher_guidance(base, None, None, None, None,
        config=DistillationConfig(max_weight=0), one_based_update=1)
    assert total is base and not report['teacher_accessed'] and report['kd'] is None
    total.backward()
    assert base.grad.item() == 1.


def test_finite_student_gradients_and_frozen_teacher():
    z, y, q, valid = tensors()
    base = z.square().mean() + 1
    total, report = add_teacher_guidance(base, z, y, q, valid,
        config=DistillationConfig(ramp_updates=0), one_based_update=1)
    total.backward()
    assert torch.isfinite(total) and torch.isfinite(z.grad).all()
    assert q.grad is None and report['eligible_voxels'] == 8
    # Descent raises the lesion logit on positives, lowers it on negatives.
    assert (z.grad[:, 2][y == 2] < 0).all()
    assert (z.grad[:, 2][y != 2] > 0).all()


def test_matching_binary_distributions_have_zero_kl():
    z, y, q, valid = tensors()
    z = z.detach().double()
    z[:, 2] = torch.logit(q.detach().double()) + math.log(2)
    value, _ = lesion_guidance(z, y, q.double(), valid, temperature=2.)
    assert value.item() == pytest.approx(0, abs=1e-14)


def test_teacher_contradictions_and_ties_never_override_annotations():
    z, y, q, valid = tensors()
    wrong = torch.where(y == 2, .1, .9)
    for probability in (wrong, torch.full_like(q, .5)):
        value, report = lesion_guidance(z, y, probability, valid, temperature=2.)
        assert value.item() == 0 and report['eligible_voxels'] == 0
        value.backward()
        assert torch.equal(z.grad, torch.zeros_like(z))
        z.grad = None
    assert torch.equal(y, tensors()[1])


def test_padding_does_not_change_loss_or_gradient():
    z, y, q, valid = tensors()
    valid[..., -1, -1, -1] = False
    value, _ = lesion_guidance(z, y, q, valid, temperature=1.)
    changed = z.detach().clone()
    changed[..., -1, -1, -1] = 1000
    other, _ = lesion_guidance(changed, y, q, valid, temperature=1.)
    torch.testing.assert_close(value, other)
    value.backward()
    assert (z.grad[..., -1, -1, -1] == 0).all()


def test_background_volume_cannot_dilute_positive_stratum():
    def loss(n):
        y = torch.tensor([2] + [0] * n).reshape(1, 1, 1, n + 1)
        z = torch.zeros((1, 3, 1, 1, n + 1))
        z[:, 2, ..., 0] = -3
        q = torch.where(y == 2, .9, .1)
        return lesion_guidance(z, y, q, torch.ones_like(y, dtype=torch.bool), temperature=2.)[0]
    torch.testing.assert_close(loss(1), loss(1000))


def test_cases_are_equally_weighted_including_zero_guidance_case():
    z, y, q, valid = tensors()
    single, _ = lesion_guidance(z, y, q, valid, temperature=2.)
    both, _ = lesion_guidance(z.repeat(2, 1, 1, 1, 1), y.repeat(2, 1, 1, 1),
        torch.cat((q, 1 - q)), valid.repeat(2, 1, 1, 1), temperature=2.)
    torch.testing.assert_close(both, single / 2)


def test_negative_only_case_and_extreme_logits_are_finite():
    z = torch.full((1, 3, 2, 2, 2), -1000.)
    z[:, 2] = 1000
    z.requires_grad_()
    y = torch.zeros((1, 2, 2, 2), dtype=torch.long)
    value, report = lesion_guidance(z, y, torch.zeros_like(y, dtype=torch.float),
        torch.ones_like(y, dtype=torch.bool), temperature=2.)
    value.backward()
    assert torch.isfinite(value) and torch.isfinite(z.grad).all()
    assert report['eligible_voxels'] == 8


@pytest.mark.parametrize('bad', ['shape', 'nan', 'range', 'label', 'floating_label', 'support', 'empty_support', 'outside', 'logits'])
def test_invalid_targets_fail_closed(bad):
    z, y, q, valid = tensors()
    q = q.detach()
    if bad == 'shape': q = q[..., :1]
    if bad == 'nan': q[0, 0, 0, 0] = float('nan')
    if bad == 'range': q[0, 0, 0, 0] = 1.1
    if bad == 'label': y[0, 0, 0, 0] = 3
    if bad == 'floating_label': y = y.float()
    if bad == 'support': valid = valid.float()
    if bad == 'empty_support': valid[:] = False
    if bad == 'outside': valid[y == 2] = False
    if bad == 'logits': z = z.detach(); z[0, 0, 0, 0, 0] = float('inf')
    with pytest.raises(ValueError): lesion_guidance(z, y, q, valid, temperature=2.)


def test_no_cuda_context_created():
    assert not torch.cuda.is_initialized()
