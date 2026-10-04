"""Read-only v3 loss decomposition. No optimizer interface or alternate training recipe."""
import math
import torch
import torch.nn.functional as F
from src.data.source_inventory_records import require
from src.training import segmenter_session_v1 as numerical

TASK = 'segmenter_v3_loss_gradient_audit_v1'
HEAD = ('conv_final.2.conv.weight', 'conv_final.2.conv.bias')


def terms(z, y):
    require(z.ndim == 5 and z.shape[1] == 3 and y.shape == (len(z), *z.shape[2:])
            and z.dtype in (torch.float32, torch.float64) and y.dtype == torch.long
            and z.device == y.device and z.numel() > 0 and torch.isfinite(z).all().item()
            and ((y >= 0) & (y <= 2)).all().item(), 'Invalid audit logits/targets')
    p = z.softmax(1); logp = z.log_softmax(1); w = z.new_tensor([1., 1., 256.])
    den = w[y].sum(); rows = []
    ce_parts = [-((y == k) * logp[:, k]).sum() * w[k] / den for k in range(3)]
    ce = F.cross_entropy(z, y, weight=w, reduction='mean')
    gd = torch.zeros_like(p); dice_terms = []
    for i in range(len(y)):
        present = [k for k in (1, 2) if (y[i] == k).any().item()]
        parts = []
        for k in present:
            t = (y[i] == k).to(z.dtype)
            d = p[i, k].sum() + t.sum() + 1e-5
            n = 2 * (p[i, k] * t).sum() + 1e-5
            loss = 1 - n / d; parts.append(loss)
            gd[i, k] = (n - 2 * t * d) / d.square() / (len(y) * len(present))
            rows.append(dict(batch=i, class_id=k, loss=float(loss.detach().cpu())))
        dice_terms.append(torch.stack(parts).mean() if parts else p[i].sum() * 0)
    dice = torch.stack(dice_terms).mean()
    onehot = F.one_hot(y, 3).movedim(-1, 1).to(z.dtype)
    gce = w[y][:, None] / den * (p - onehot)
    gdi = p * (gd - (p * gd).sum(1, keepdim=True))
    return ce, dice, p, gce, gdi, dict(
        weighted_denominator=float(den.detach().cpu()),
        class_counts=[int((y == k).sum().item()) for k in range(3)],
        ce_by_true_class=[float(v.detach().cpu()) for v in ce_parts],
        dice_present_terms=rows)


def vector_stats(v):
    v = v.detach().cpu().double()
    require(torch.isfinite(v).all().item(), 'Nonfinite gradient')
    return dict(sum=float(v.sum()), l1=float(v.abs().sum()), l2=float(v.norm()),
                max_abs=float(v.abs().max()) if v.numel() else 0.)


def logit_stats(g, y):
    return [[vector_stats(g[:, j][y == k]) for j in range(3)] for k in range(3)]


def head_stats(gradients):
    a = torch.cat([g.detach().cpu().double().reshape(3, -1) for g in gradients], 1)
    require(torch.isfinite(a).all().item(), 'Nonfinite head gradient')
    return dict(channels=[vector_stats(row) for row in a], values=a.tolist(), l2=float(a.norm()))


def analyze(model, x, y):
    """One forward, two head VJPs. Caller supplies a verified analysis clone and sealed batch."""
    require(x.ndim == 5 and x.shape[:2] == (1, 1) and y.shape == (1, *x.shape[2:])
            and x.dtype == torch.float32 and torch.isfinite(x).all().item()
            and x.min().item() >= 0 and x.max().item() <= 1, 'Invalid normalized audit image')
    params = dict(model.named_parameters())
    require(all(n in params for n in HEAD) and params[HEAD[0]].shape == (3, 16, 1, 1, 1)
            and params[HEAD[1]].shape == (3,), 'Wrong final head')
    require(not model.training and all(p.requires_grad == (n in HEAD) for n, p in params.items())
            and all(p.grad is None for p in params.values()), 'Read-only head analysis clone required')
    before = numerical.state_hash(model.state_dict()); rng = torch.get_rng_state().clone()
    mr = torch.mps.get_rng_state().clone() if x.device.type == 'mps' else None
    z = model(x); ce, di, p, gc, gd, row = terms(z, y)
    expected = numerical.objective(z, y, numerical.LOSS_V3)
    delta = float((ce + di - expected).abs().detach().cpu())
    require(delta <= 2e-5, 'Accepted objective parity failed')
    head = [params[n] for n in HEAD]
    a = torch.autograd.grad(ce, head, retain_graph=True)
    b = torch.autograd.grad(di, head)
    hs = [head_stats(v) for v in (a, b, tuple(u + v for u, v in zip(a, b)))]
    av = torch.tensor(hs[0]['values'], dtype=torch.float64).flatten()
    bv = torch.tensor(hs[1]['values'], dtype=torch.float64).flatten()
    dot = float(av @ bv); norm = float(av.norm() * bv.norm())
    pp = p.detach().cpu(); yy = y.cpu(); pred = pp.argmax(1)
    conditional = []; confusion = []
    for k in range(3):
        mask = yy == k; n = int(mask.sum())
        confusion.append([int((mask & (pred == j)).sum()) for j in range(3)])
        conditional.append(dict(true_class=k, count=n,
            probability_mean=[float(pp[:, j][mask].double().mean()) if n else None for j in range(3)],
            pancreas_minus_lesion_mean=float((pp[:, 1] - pp[:, 2])[mask].double().mean()) if n else None,
            true_class_margin_mean=float((pp[:, k] - pp[:, [j for j in range(3) if j != k]].max(1).values)[mask].double().mean()) if n else None))
    row.update(ce=float(ce.detach().cpu()), dice=float(di.detach().cpu()), total=float(expected.detach().cpu()),
        scalar_parity_max_abs=delta, ce_denominator_shares=[n * w / row['weighted_denominator'] for n, w in zip(row['class_counts'], (1, 1, 256))],
        confusion_true_by_predicted=confusion, conditional=conditional,
        logit_gradients_true_by_output={n:logit_stats(v.detach().cpu(), yy) for n, v in [('ce', gc), ('dice', gd), ('total', gc + gd)]},
        head_gradients=dict(ce=hs[0], dice=hs[1], total=hs[2], ce_dice_dot=dot, ce_dice_cosine=dot / norm if norm else None),
        model_forwards=1, head_vjp_queries=2, optimizer_calls=0)
    require(before == numerical.state_hash(model.state_dict()) and torch.equal(rng, torch.get_rng_state())
            and (mr is None or torch.equal(mr, torch.mps.get_rng_state()))
            and all(p.grad is None for p in params.values()), 'Audit mutated weights/RNG/grad fields')
    row['nonmutation_verified'] = True
    return row


def analysis_clone(model, device):
    from copy import deepcopy
    out = deepcopy(model).to(device).eval()
    for n, p in out.named_parameters():
        p.requires_grad_(n in HEAD); p.grad = None
    return out
