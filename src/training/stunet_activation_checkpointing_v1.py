"""Optional block recomputation; no parameter, state-key or inference changes.

Apply after strict pretrained loading and before optimizer construction/restore.
This is a distinct execution policy requiring device qualification before use.
"""
from functools import wraps


def enable(model):
    import torch
    from torch.utils.checkpoint import checkpoint
    if getattr(model, '_prowl_checkpointing_v1', False):
        raise ValueError('Activation checkpointing already enabled')
    groups = ('conv_blocks_context', 'conv_blocks_localization')
    blocks = [block for name in groups for block in getattr(model, name)]
    if not blocks:
        raise ValueError('No STU-Net encoder/decoder blocks')
    for block in blocks:
        original = block.forward

        @wraps(original)
        def forward(*args, _block=block, _original=original, **kwargs):
            if _block.training and torch.is_grad_enabled():
                return checkpoint(_original, *args, use_reentrant=False,
                                  preserve_rng_state=True, **kwargs)
            return _original(*args, **kwargs)

        block.forward = forward
    model._prowl_checkpointing_v1 = True
    return dict(policy='stunet-block-recomputation-1', blocks=len(blocks),
                use_reentrant=False, preserve_rng_state=True)
