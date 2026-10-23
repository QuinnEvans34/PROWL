"""Extract tensors from the specific legacy JHU release without importing its classes.

Each reviewed legacy module GLOBAL resolves to an inert record, never executable
checkpoint model code. PyTorch's restricted weights-only unpickler remains enabled.
No dynamic allowlisting, unsafe pickle fallback, or model forward is permitted.
"""
from collections import OrderedDict
import torch

LEGACY_MODULES = frozenset('''
torch.nn.modules.dropout.Dropout
torch.nn.modules.linear.Linear
torch.nn.modules.activation.Sigmoid
torch.nn.modules.instancenorm.InstanceNorm3d
torch.nn.modules.container.ModuleList
torch.nn.modules.pooling.AdaptiveAvgPool3d
torch.nn.modules.container.Sequential
torch.nn.modules.activation.ReLU
torch.nn.modules.conv.Conv3d
torch.nn.modules.activation.GELU
torch.nn.modules.linear.Identity
torch.nn.modules.normalization.LayerNorm
model.dim3.medformer.MedFormer
model.dim3.medformer_utils.BasicLayer
model.dim3.medformer_utils.SemanticMapGeneration
model.dim3.medformer_utils.BidirectionAttention
model.dim3.medformer_utils.up_block
model.dim3.medformer_utils.BidirectionAttentionBlock
model.dim3.medformer_utils.inconv
model.dim3.medformer_utils.PatchMerging
model.dim3.medformer_utils.SemanticMapFusion
model.dim3.medformer_utils.down_block
model.dim3.conv_layers.ConvNormAct
model.dim3.conv_layers.MBConv
model.dim3.conv_layers.DepthwiseSeparableConv
model.dim3.conv_layers.DropPath
model.dim3.conv_layers.BasicBlock
model.dim3.conv_layers.SEBlock
model.dim3.trans_layers.PreNorm
model.dim3.trans_layers.TransformerBlock
model.dim3.trans_layers.Attention
model.dim3.trans_layers.Mlp
'''.split())


class InertModuleRecord:
    """No methods, constructors, hooks or state restoration from the original class."""
    pass


def tensor_state(value):
    if isinstance(value, (dict, OrderedDict)) and value and all(
            isinstance(k, str) and type(v) is torch.Tensor for k, v in value.items()):
        return OrderedDict((k, v.detach()) for k, v in value.items())
    result = OrderedDict()

    def visit(module, prefix, ancestors):
        if type(module) is not InertModuleRecord or id(module) in ancestors:
            raise ValueError('Unexpected or cyclic legacy module tree')
        if any(module.__dict__.get(k) for k in ('_state_dict_hooks', '_state_dict_pre_hooks',
                '_load_state_dict_pre_hooks', '_load_state_dict_post_hooks')):
            raise ValueError('Custom state hooks require separate review')
        children = module.__dict__.get('_modules')
        parameters = module.__dict__.get('_parameters')
        buffers = module.__dict__.get('_buffers')
        omitted = module.__dict__.get('_non_persistent_buffers_set', set())
        if not all(isinstance(x, (dict, OrderedDict)) for x in (children, parameters, buffers)) or type(omitted) is not set:
            raise ValueError('Malformed legacy module state')
        for group, nonpersistent in ((parameters, set()), (buffers, omitted)):
            for name, tensor in group.items():
                if not isinstance(name, str) or not name or '.' in name: raise ValueError('Parameter name')
                if tensor is None or name in nonpersistent: continue
                if type(tensor) not in (torch.Tensor, torch.nn.Parameter): raise ValueError('Nontensor parameter')
                key = prefix + name
                if key in result: raise ValueError('Duplicate state key')
                result[key] = tensor.detach()
        for name, child in children.items():
            if not isinstance(name, str) or not name or '.' in name: raise ValueError('Module name')
            if child is not None: visit(child, prefix + name + '.', ancestors | {id(module)})

    visit(value, '', set())
    if not result: raise ValueError('Empty teacher state')
    return result


def read_legacy_release(path):
    unknown = set(torch.serialization.get_unsafe_globals_in_checkpoint(path))
    if not unknown <= LEGACY_MODULES:
        raise ValueError('Unreviewed pickle globals: ' + ', '.join(sorted(unknown - LEGACY_MODULES)))
    # Map each known GLOBAL to OUR inert class; do not import/execute upstream types.
    with torch.serialization.safe_globals([(InertModuleRecord, name) for name in sorted(unknown)]):
        value = torch.load(path, map_location='cpu', weights_only=True, mmap=True)
    if not isinstance(value, dict): raise ValueError('Release root must be a dictionary')
    return value, sorted(unknown)
