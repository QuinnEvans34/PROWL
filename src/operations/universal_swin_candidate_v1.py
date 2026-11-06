"""CPU-only, strict acquisition audit for the official Universal Swin candidate.

The upstream implementation and weights remain external. This adapter neither
executes inference nor permits partially initialized backbone state.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

SOURCE_REVISION = '43c12399cc98a40f447342a8dc2cecae5edae84c'
WEIGHT_REVISION = '76f0304ff9387c1baccbbc1d9eac78c5c5ccfeed'
WEIGHT_SHA256 = 'cde35d9ca344a744c849ebe0cd086cb64984e79f605376c56bd04531c767ed07'
WEIGHT_BYTES = 758907945
WEIGHT_URL = ('https://huggingface.co/ljwztc/CLIP-Driven-Universal-Model/resolve/'
              + WEIGHT_REVISION + '/clip_driven_universal_swin_unetr.pth')
PANCREAS_CHANNEL, LESION_CHANNEL = 10, 27  # Zero-based; upstream labels 11/28.


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def map_state(state, expected):
    """Apply only the upstream DDP/backbone renaming, then require exact coverage."""
    import torch
    mapped = {}
    for key, tensor in state.items():
        if not isinstance(key, str) or not key.startswith('module.'):
            raise ValueError('Expected exactly one upstream module prefix')
        name = key[len('module.'):]
        if re.match(r'^(swinViT|encoder[0-9]+|decoder[0-9]+)\.', name):
            name = 'backbone.' + name
        if name in mapped:
            raise ValueError('Duplicate mapped tensor')
        if name not in expected or not isinstance(tensor, torch.Tensor):
            raise ValueError('Unexpected state entry: ' + name)
        target = expected[name]
        if tensor.shape != target.shape or tensor.dtype != target.dtype:
            raise ValueError('Tensor shape/dtype differs: ' + name)
        if tensor.is_floating_point() and not bool(torch.isfinite(tensor).all()):
            raise ValueError('Non-finite tensor: ' + name)
        mapped[name] = tensor
    if set(mapped) != set(expected):
        raise ValueError('Missing model state: ' + ', '.join(sorted(set(expected) - set(mapped))))
    return mapped


def audit(checkpoint, source, output):
    """Construct/load the exact external model on CPU, without a model forward."""
    import sys
    import torch
    checkpoint, source, output = map(lambda x: Path(x).resolve(), (checkpoint, source, output))
    if output.exists():
        raise FileExistsError('Fresh audit destination required')
    if source == output or source in output.parents:
        raise ValueError('Audit must not modify upstream source')
    output.mkdir(parents=True)
    try:
        if checkpoint.stat().st_size != WEIGHT_BYTES or digest(checkpoint) != WEIGHT_SHA256:
            raise ValueError('Official checkpoint size/hash differs')
        revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=no'], text=True)
        if revision != SOURCE_REVISION or dirty:
            raise ValueError('Upstream source revision/content differs')
        source_pins = {str(p.relative_to(source)): digest(p) for p in source.rglob('*.py')}
        # All deserialization is restricted and all tensors start on CPU.
        torch.set_num_threads(1)
        saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
        if not isinstance(saved, dict) or not isinstance(saved.get('net'), dict):
            raise ValueError('Expected upstream net state')
        sys.path.insert(0, str(source))
        from model.Universal_model import Universal_model
        model = Universal_model(img_size=(96, 96, 96), in_channels=1,
                                out_channels=32, backbone='swinunetr', encoding='word_embedding')
        mapped = map_state(saved['net'], model.state_dict())
        model.load_state_dict(mapped, strict=True)
        result = dict(schema='prowl.universal-swin.cpu-audit.v1', source_revision=revision,
                      weight_revision=WEIGHT_REVISION, weight_sha256=WEIGHT_SHA256,
                      weight_bytes=WEIGHT_BYTES, source_pins=source_pins,
                      state_entries=len(mapped), state_elements=sum(v.numel() for v in mapped.values()),
                      trainable_parameters=sum(p.numel() for p in model.parameters()),
                      pancreas_channel=PANCREAS_CHANNEL, lesion_channel=LESION_CHANNEL,
                      model_calls=0, optimizer_updates=0, device='cpu', strict_load=True,
                      code_license='CC-BY-NC-ND-4.0', model_card_license='MIT',
                      external_pretraining_overlap='unknown', qualification='NOT_GPU_QUALIFIED')
        for name, pin in source_pins.items():
            if digest(source / name) != pin:
                raise ValueError('Source changed during audit')
        (output / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    except Exception:
        import traceback
        (output / 'failure.txt').write_text(traceback.format_exc())
        raise
