"""Offline lesion-probability distillation primitive; not a training launcher.

The supervised objective is supplied unchanged by the caller. This module neither
loads a teacher nor changes any existing Session. No production integration yet.
"""
from dataclasses import dataclass
import math

import torch
import torch.nn.functional as F

POLICY = 'lesion_bernoulli_kd_gt_agreement_stratified_v1'


@dataclass(frozen=True)
class DistillationConfig:
    max_weight: float = 0.1
    temperature: float = 2.0
    ramp_updates: int = 1000

    def __post_init__(self):
        if (type(self.max_weight) not in (int, float) or
                not math.isfinite(self.max_weight) or not 0 <= self.max_weight <= 1):
            raise ValueError('KD weight must be finite and within [0, 1]')
        if (type(self.temperature) not in (int, float) or
                not math.isfinite(self.temperature) or not 1 <= self.temperature <= 10):
            raise ValueError('KD temperature must be finite and within [1, 10]')
        if type(self.ramp_updates) is not int or self.ramp_updates < 0:
            raise ValueError('KD ramp must be a nonnegative integer')

    def weight(self, one_based_update):
        if type(one_based_update) is not int or one_based_update < 1:
            raise ValueError('Positive one-based update required')
        fraction = min(one_based_update / self.ramp_updates, 1.) if self.ramp_updates else 1.
        return self.max_weight * fraction


def lesion_guidance(logits, target, teacher_probability, valid, *, temperature):
    """Bernoulli KL on the student's lesion-vs-rest margin, not teacher class order.

Inputs: logits Bx3xDxHxW; other tensors BxDxHxW. valid is real image support,
not a confidence mask. Only teacher/annotation agreement contributes to KD;
ALL annotated voxels still contribute to the external supervised objective.
Average nonempty GT strata (background/pancreas/lesion) equally within each
case, then average cases equally, including zero-guidance cases. Teacher is detached.
"""
    if type(temperature) not in (int, float) or not math.isfinite(temperature) or not 1 <= temperature <= 10:
        raise ValueError('Invalid KD temperature')
    if not isinstance(logits, torch.Tensor) or logits.ndim != 5 or logits.shape[1] != 3 or min(logits.shape) < 1:
        raise ValueError('Expected nonempty Bx3xDxHxW student logits')
    shape = (logits.shape[0], *logits.shape[2:])
    if any(not isinstance(t, torch.Tensor) or tuple(t.shape) != shape or t.device != logits.device
           for t in (target, teacher_probability, valid)):
        raise ValueError('KD shape/device mismatch; implicit resizing is forbidden')
    if logits.dtype not in (torch.float32, torch.float64) or not torch.isfinite(logits).all().item():
        raise ValueError('Finite float32/float64 logits required')
    if target.dtype not in (torch.uint8, torch.int16, torch.int32, torch.int64) or not ((target >= 0) & (target <= 2)).all().item():
        raise ValueError('Targets must be integer background/pancreas/lesion codes')
    if valid.dtype != torch.bool or not valid.flatten(1).any(1).all().item():
        raise ValueError('Every case needs boolean, nonempty real support')
    if not teacher_probability.is_floating_point() or not torch.isfinite(teacher_probability).all().item():
        raise ValueError('Finite teacher probabilities required')
    if not ((teacher_probability >= 0) & (teacher_probability <= 1)).all().item():
        raise ValueError('Teacher probabilities must be within [0, 1]')
    if (target[~valid] != 0).any().item():
        raise ValueError('Annotated voxels outside valid support')

    q_raw = teacher_probability.detach().to(logits.dtype)
    positive = target == 2
    # Ties at .5 agree with neither label: no confident binary decision.
    agree = ((q_raw > .5) & positive) | ((q_raw < .5) & ~positive)
    eligible = valid & agree
    q = torch.sigmoid(torch.logit(q_raw.clamp(1e-6, 1 - 1e-6)) / temperature)
    margin = (logits[:, 2] - torch.logsumexp(logits[:, :2], dim=1)) / temperature
    entropy = torch.xlogy(q, q) + torch.xlogy(1 - q, 1 - q)
    divergence = (entropy - q * F.logsigmoid(margin) - (1 - q) * F.logsigmoid(-margin)) * temperature**2
    # KL can be a few ulps negative at equality; remove that numerical artifact.
    divergence = divergence.clamp_min(0.)
    cases = []
    for index in range(logits.shape[0]):
        means = []
        for code in (0, 1, 2):
            mask = eligible[index] & (target[index] == code)
            if mask.any().item():
                means.append(divergence[index][mask].mean())
        cases.append(torch.stack(means).mean() if means else logits[index].sum() * 0.)
    value = torch.stack(cases).mean()
    return value, dict(valid_voxels=int(valid.sum().item()),
                      eligible_voxels=int(eligible.sum().item()),
                      conflict_or_tie_voxels=int((valid & ~agree).sum().item()))


def add_teacher_guidance(supervised_loss, logits, target, teacher_probability, valid,
                         *, config, one_based_update):
    """Return total and diagnostics; weight-zero is the exact supplied control loss."""
    if not isinstance(config, DistillationConfig):
        raise ValueError('Versioned KD configuration required')
    if not isinstance(supervised_loss, torch.Tensor) or supervised_loss.ndim != 0 or not torch.isfinite(supervised_loss).item():
        raise ValueError('Finite scalar supervised loss required')
    weight = config.weight(one_based_update)
    if weight == 0:
        return supervised_loss, dict(policy=POLICY, weight=0., kd=None, teacher_accessed=False)
    if supervised_loss.device != logits.device:
        raise ValueError('Supervised/logit device mismatch')
    kd, metrics = lesion_guidance(logits, target, teacher_probability, valid,
                                  temperature=config.temperature)
    return supervised_loss + weight * kd, dict(metrics, policy=POLICY, weight=weight,
        kd=kd.detach(), teacher_accessed=True)
