"""Portable STU-Net-B transfer primitives; no data reader or launch authority.

Upstream source/weights stay external. Only four hash-bound architecture classes
are compiled. No nnUNet trainer imports, unsafe pickle fallback or source edits.
"""
import ast
import hashlib
from pathlib import Path

SOURCE_SHA = '53da5fa6ea87c0b63177af6a93b5b148bda96b6e4be22290a8e5d49a4ef261bc'
CHECKPOINT_SHA = '7232a6296d320da1d60debe873a1d3fcad74e9404272db8f7440e30d62c5997a'
CHECKPOINT_BYTES = 466715133
CLASSES = ('Decoder', 'STUNet', 'BasicResBlock', 'Upsample_Layer_nearest')
BODY_PARAMETERS = 58157984
HEAD_PARAMETERS = 2991


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(b)
    return h.hexdigest()


def architecture(source):
    import torch
    b = Path(source).read_bytes()
    if hashlib.sha256(b).hexdigest() != SOURCE_SHA:
        raise ValueError('STU source pin mismatch')
    tree = ast.parse(b, filename=str(source))
    selected = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in CLASSES]
    if len(selected) != len(CLASSES) or {n.name for n in selected} != set(CLASSES):
        raise ValueError('Architecture class inventory')
    namespace = {'torch': torch, 'nn': torch.nn, '__name__': 'prowl_external_stunet'}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['STUNet']


def make_model(source, *, pools, seed=42):
    import torch
    if len(pools) != 5 or any(len(p) != 3 or any(type(x) is not int or x not in (1, 2) for x in p) for p in pools):
        raise ValueError('Five explicit 3D pool strides of one or two required')
    cls = architecture(source)
    # Preserve caller RNG and make fresh heads reproducible on both hosts.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        model = cls(1, 3, depth=[1]*6, dims=[32,64,128,256,512,512],
                    pool_op_kernel_sizes=[list(p) for p in pools],
                    conv_kernel_sizes=[[3,3,3] for _ in range(6)], enable_deep_supervision=True)
    body = sum(p.numel() for n,p in model.named_parameters() if not n.startswith('seg_outputs.'))
    heads = sum(p.numel() for n,p in model.named_parameters() if n.startswith('seg_outputs.'))
    if (body, heads) != (BODY_PARAMETERS, HEAD_PARAMETERS):
        raise ValueError('Unexpected STU-Net-B body/head sizes')
    return model


def transfer_state(source, expected):
    """Require every body tensor exactly; discard only validated segmentation heads."""
    import torch
    if not isinstance(source, dict) or set(source) != set(expected):
        raise ValueError('Exact checkpoint tensor names required; no prefix guessing')
    transferred = {}; old_classes = set()
    for name, dst in expected.items():
        src = source[name]
        if not isinstance(src, torch.Tensor) or src.dtype != dst.dtype or not torch.isfinite(src).all():
            raise ValueError('Invalid tensor: '+name)
        if name.startswith('seg_outputs.'):
            if src.ndim != dst.ndim or src.shape[1:] != dst.shape[1:] or src.shape[0] < 2:
                raise ValueError('Invalid old segmentation head: '+name)
            old_classes.add(src.shape[0]); transferred[name] = dst.clone()
        else:
            if src.shape != dst.shape:
                raise ValueError('Body shape mismatch: '+name)
            transferred[name] = src
    if len(old_classes) != 1:
        raise ValueError('Inconsistent or missing source heads')
    return transferred


def load_transfer(source, checkpoint, *, pools, seed=42):
    import numpy as np
    import torch
    checkpoint = Path(checkpoint)
    if checkpoint.stat().st_size != CHECKPOINT_BYTES or sha256(checkpoint) != CHECKPOINT_SHA:
        raise ValueError('Original STU checkpoint pin mismatch')
    # Exact inert NumPy metadata types authorized by the original checkpoint audit.
    from numpy.core.multiarray import scalar
    with torch.serialization.safe_globals([(scalar, 'numpy.core.multiarray.scalar'),
                                           np.dtype, type(np.dtype('float32')), type(np.dtype('float64'))]):
        raw = torch.load(checkpoint, map_location='cpu', weights_only=True)
    if not isinstance(raw, dict) or not isinstance(raw.get('state_dict'), dict):
        raise ValueError('Expected original state_dict envelope')
    model = make_model(source, pools=pools, seed=seed)
    initial_heads = {n:t.clone() for n,t in model.state_dict().items() if n.startswith('seg_outputs.')}
    model.load_state_dict(transfer_state(raw['state_dict'], model.state_dict()), strict=True)
    for n,t in model.state_dict().items():
        expected = initial_heads[n] if n in initial_heads else raw['state_dict'][n]
        if not torch.equal(t, expected):
            raise ValueError('Post-load equality mismatch: '+n)
    return model, dict(checkpoint_sha256=CHECKPOINT_SHA, source_sha256=SOURCE_SHA,
                      body_parameters=BODY_PARAMETERS, fresh_head_parameters=HEAD_PARAMETERS,
                      seed=seed, pools=pools, strict_body_equality=True, fresh_heads_equal=True,
                      scientific_updates=0, qualification='CPU_LOAD_ONLY')


def deep_supervision_loss(outputs, target):
    """Proposed exact reduction, not yet a qualified scientific recipe.

Target B,D,H,W long, labels 0/1/2. Highest-resolution output must match.
At lower scales use nearest-neighbor labels. Per-scale CE is voxel mean;
soft Dice is mean over batch and foreground classes 1/2, spatial sums only,
smooth numerator/denominator 1e-5, absent classes included. CE + Dice loss.
Five scale weights [16,8,4,2,1]/31. Coarse tiny-target loss requires review.
"""
    import torch
    from torch.nn import functional as F
    if not isinstance(outputs, (tuple,list)) or len(outputs) != 5:
        raise ValueError('Exactly five deep supervision scales required')
    if target.dtype != torch.long or target.ndim != 4 or not ((target >= 0)&(target <= 2)).all():
        raise ValueError('Target must be long B,D,H,W with labels 0,1,2')
    if tuple(outputs[0].shape) != (target.shape[0],3,*target.shape[1:]):
        raise ValueError('Full-resolution supervision must match')
    losses=[]; previous=target.shape[1:]
    for out in outputs:
        if out.ndim != 5 or out.shape[:2] != (target.shape[0],3) or any(a>b for a,b in zip(out.shape[2:],previous)):
            raise ValueError('Invalid deep-supervision shape/order')
        if not torch.isfinite(out).all(): raise ValueError('Nonfinite logits')
        previous=out.shape[2:]
        small=F.interpolate(target[:,None].float(),size=out.shape[2:],mode='nearest')[:,0].long()
        onehot=F.one_hot(small,3).movedim(-1,1).float()[:,1:]
        prob=out.float().softmax(1)[:,1:]; axes=(2,3,4)
        dice=(2*(prob*onehot).sum(axes)+1e-5)/(prob.sum(axes)+onehot.sum(axes)+1e-5)
        losses.append(F.cross_entropy(out.float(),small,reduction='mean') + 1-dice.mean())
    return sum(w*l for w,l in zip((16/31,8/31,4/31,2/31,1/31),losses))
