"""Load pinned inference-only SegResNet weights; never construct an optimizer."""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import torch
from src.models.segresnet import build_model
from src.training.segmenter_session_v1 import ARCH
from src.data.source_inventory_records import require


def architecture(role):
    require(role in ('localizer','segmenter'),'Known model role required')
    return dict(deepcopy(ARCH),out_channels=2 if role=='localizer' else 3)


def load_weights(path, *, expected_sha256, role):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size<=128*1024**2,
            'Regular bounded weight file required')
    raw=p.read_bytes();require(sha256(raw).hexdigest()==expected_sha256,'Weight file SHA256 mismatch')
    payload=torch.load(BytesIO(raw),map_location='cpu',weights_only=True)
    require(type(payload) is dict and set(payload)=={'format','role','architecture','source_checkpoint_sha256','state_dict'},
            'Inference-only weight bundle required')
    require(payload['format']=='prowl-cascade-weights-1' and payload['role']==role
            and payload['architecture']==architecture(role),'Weight role/architecture mismatch')
    pin=payload['source_checkpoint_sha256']
    require(isinstance(pin,str) and len(pin)==64 and all(c in '0123456789abcdef' for c in pin),
            'Source checkpoint hash required')
    state=payload['state_dict']
    require(isinstance(state,dict) and state and all(isinstance(v,torch.Tensor) and
            v.dtype==torch.float32 and torch.isfinite(v).all().item() for v in state.values()),
            'Finite float32 model tensors required')
    with torch.random.fork_rng(devices=[]):
        model=build_model({'model':architecture(role)})
    model.load_state_dict(state,strict=True);model.eval();model.requires_grad_(False)
    return model,dict(role=role,weights_sha256=expected_sha256,source_checkpoint_sha256=pin)
