"""D-312 objective; legacy loss dispatch deliberately does not accept this ID."""
import torch
import torch.nn.functional as F
from src.data.source_inventory_records import require

LOSS_ID = 'class_mean_25_75_ce_dice_v1'


def configured_loss(logits, target, config):
    require(config.get('loss_id') == LOSS_ID, 'Wrong class-mean objective')
    require(logits.ndim == 5 and logits.shape[0] > 0 and logits.shape[1] == 2 and
        all(n > 0 for n in logits.shape[2:]) and logits.is_floating_point() and
        target.shape == (logits.shape[0], 1, *logits.shape[2:]) and target.device == logits.device and
        torch.isfinite(logits).all().item() and torch.all((target == 0) | (target == 1)).item(),
        'Finite nonempty binary logits/target required')
    y = target[:, 0].long()
    per = F.cross_entropy(logits, y, reduction='none')
    cases = []
    for j in range(len(y)):
        fg, bg = y[j] == 1, y[j] == 0
        if fg.any() and bg.any():
            cases.append(.25 * per[j][fg].mean() + .75 * per[j][bg].mean())
        else:
            cases.append(per[j].mean())  # Sole class retains its full-strength mean.
    truth = y.float()
    p = logits.softmax(1)[:, 1]
    dims = (1, 2, 3)
    positive = truth.sum(dims) > 0
    dice = 1 - (2 * (p * truth).sum(dims) + 1e-5) / (p.sum(dims) + truth.sum(dims) + 1e-5)
    return torch.stack(cases).mean() + (dice[positive].mean() if positive.any() else p.sum() * 0)
