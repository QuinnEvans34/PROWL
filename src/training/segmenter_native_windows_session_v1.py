"""Native-window optimizer and full-CT reconstruction; separate from frozen trainer."""
from copy import deepcopy
import numpy as np
import torch
from src.data.manifest_records import canonical, digest
from src.data.segmenter_native_inputs_v1 import OptimizerWindows
from src.data.segmenter_native_windows_v1 import POLICY, tiles, extract, orient, Reconstructor
from src.training.segmenter_augmentation_v1 import augmentation_identity
from src.training.segmenter_full_session_v1 import Session


class WindowSession:
    def __init__(self, raw):
        self.raw = raw
        self.identity = dict(version='native-window-session-1', raw=deepcopy(raw.identity),
                             policy=deepcopy(POLICY), augmentation=augmentation_identity())
        self.identity_pin = digest(canonical(self.identity))

    def __getattr__(self, key): return getattr(self.raw, key)

    def check(self):
        if digest(canonical(self.identity)) != self.identity_pin or self.identity['policy'] != POLICY:
            raise ValueError('Changed window identity')

    def update(self, provider):
        self.check(); adapter = OptimizerWindows(provider, self.raw)
        result = self.raw.update(adapter)
        return dict(result, input_view=adapter.trace)

    def state(self):
        self.check()
        return dict(version=1, identity=deepcopy(self.identity), identity_sha256=self.identity_pin,
                    raw=self.raw.state())

    @classmethod
    def restore(cls, state, identity):
        if state['version'] != 1 or state['identity'] != identity or state['identity_sha256'] != digest(canonical(identity)):
            raise ValueError('Window checkpoint identity mismatch')
        result = cls(Session.restore(state['raw'], identity['raw']))
        if result.identity != identity: raise ValueError('Window implementation changed')
        return result


@torch.no_grad()
def predict_native(session, image, geometry, *, progress=lambda completed, total: None):
    """CT-only signature: cannot use target/pancreas to choose inference windows."""
    if image.shape != tuple(geometry['shape']) or image.dtype != np.float32 or not np.isfinite(image).all():
        raise ValueError('Invalid native image')
    ts = tiles(image.shape); recon = Reconstructor(image.shape)
    session._clean()
    with session.rng_scope():
        session.model.eval()
        for i, origin in enumerate(ts):
            patch, _ = extract(image, origin)
            logits = session.model(torch.from_numpy(patch[None, None]).to(session.device))
            if not torch.isfinite(logits).all(): raise ValueError('Nonfinite prediction')
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()
            recon.add(origin, probabilities); progress(i+1, len(ts))
    codes = recon.finish(ts).argmax(0).astype(np.uint8)
    return orient(codes, geometry, inverse=True), dict(tiles=len(ts), minimum_blend_weight=float(recon.weight.min()),
                                                      gap_voxels=int((recon.weight == 0).sum()))
