"""Qualification ONLY: identical CUDA forward, native CPU trilinear adjoint.

PyTorch 2.11 has no deterministic CUDA trilinear backward. Never install this
adapter in scientific training. No parameter, shape or interpolation change.
"""
import torch
from torch import nn
from torch.nn import functional as F


class _Trilinear(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value):
        ctx.input_size = tuple(value.shape)
        result = F.interpolate(value, scale_factor=2., mode='trilinear', align_corners=False)
        ctx.output_size = tuple(result.shape[2:])
        return result

    @staticmethod
    def backward(ctx, gradient):
        cpu = gradient.detach().to('cpu').contiguous()
        result = torch.ops.aten.upsample_trilinear3d_backward.default(
            cpu, ctx.output_size, ctx.input_size, False, 2., 2., 2.)
        return result.to(device=gradient.device)


class QualifiedUpsample(nn.Module):
    def forward(self, value):
        return _Trilinear.apply(value)


def install(model):
    count = 0
    for parent in list(model.modules()):
        for name, child in list(parent.named_children()):
            if isinstance(child, nn.Upsample):
                if (child.mode != 'trilinear' or child.align_corners is not False
                    or child.size is not None or child.scale_factor not in (2., (2.,2.,2.))
                    or child.recompute_scale_factor not in (None,False)):
                    raise ValueError('Unsupported qualification interpolation geometry')
                setattr(parent, name, QualifiedUpsample()); count += 1
    if count != 3: raise ValueError('Expected exactly three original upsampling modules')
    return count


def configure():
    import os
    if os.environ.get('CUBLAS_WORKSPACE_CONFIG') != ':4096:8':
        raise ValueError('Deterministic cuBLAS environment required before CUDA initialization')
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.set_num_threads(2)


