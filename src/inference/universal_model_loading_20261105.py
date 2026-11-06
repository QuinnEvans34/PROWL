"""Strict, CPU-only loading of the external official Universal Model release.

No upstream source is redistributed or modified. No inference is performed here.
"""
from pathlib import Path
import hashlib
import importlib
import sys

SOURCE_REVISION = '43c12399cc98a40f447342a8dc2cecae5edae84c'
WEIGHT_REVISION = '76f0304ff9387c1baccbbc1d9eac78c5c5ccfeed'
WEIGHT_SHA256 = 'cde35d9ca344a744c849ebe0cd086cb64984e79f605376c56bd04531c767ed07'
WEIGHT_BYTES = 758907945
CHANNELS = {'pancreas': 10, 'pancreatic_tumor': 27}  # zero-based, independent sigmoid


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def map_state(source, expected):
    """Official DDP/backbone rename, with exact coverage rather than random fill."""
    mapped = {}
    for key, value in source.items():
        if not key.startswith('module.'):
            raise ValueError('Expected exact module prefix: ' + key)
        name = key[len('module.'):]
        if any(part in key for part in ('swinViT', 'encoder', 'decoder')):
            name = 'backbone.' + name
        if name in mapped:
            raise ValueError('Mapped key collision: ' + name)
        mapped[name] = value
    if set(mapped) != set(expected):
        raise ValueError(f'State coverage differs: missing={sorted(set(expected)-set(mapped))}; unexpected={sorted(set(mapped)-set(expected))}')
    for key in expected:
        if mapped[key].shape != expected[key].shape or mapped[key].dtype != expected[key].dtype:
            raise ValueError('State shape/dtype differs: ' + key)
    return mapped


def load_cpu(source_root, checkpoint, source_receipt):
    import torch
    root = Path(source_root).resolve()
    if source_receipt['revision'] != SOURCE_REVISION:
        raise ValueError('Wrong source revision')
    for item in source_receipt['files']:
        p = (root / item['path']).resolve()
        if not p.is_relative_to(root) or digest(p) != item['sha256']:
            raise ValueError('Source pin mismatch')
    checkpoint = Path(checkpoint)
    if checkpoint.stat().st_size != WEIGHT_BYTES or digest(checkpoint) != WEIGHT_SHA256:
        raise ValueError('Checkpoint pin mismatch')
    # Fresh worker required: prevent loading a same-named module from another model.
    if any(k == 'model' or k.startswith('model.') for k in sys.modules):
        raise ValueError('Use a fresh CPU worker; model namespace already imported')
    sys.path.insert(0, str(root))
    cls = importlib.import_module('model.Universal_model').Universal_model
    model = cls(img_size=(96, 96, 96), in_channels=1, out_channels=32,
                backbone='swinunetr', encoding='word_embedding')
    raw = torch.load(checkpoint, map_location='cpu', weights_only=True)
    mapped = map_state(raw['net'], model.state_dict())
    model.load_state_dict(mapped, strict=True)
    model.eval()
    state_hash = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        state_hash.update(name.encode())
        state_hash.update(str((tuple(value.shape), value.dtype)).encode())
        state_hash.update(value.contiguous().numpy().tobytes())
    return model, {'state_tensors': len(mapped),
                   'loaded_state_sha256': state_hash.hexdigest(),
                   'parameters': sum(p.numel() for p in model.parameters()),
                   'state_elements': sum(p.numel() for p in mapped.values()),
                   'checkpoint_sha256': WEIGHT_SHA256,
                   'source_revision': SOURCE_REVISION,
                   'forward_calls': 0, 'gpu_used': False}
