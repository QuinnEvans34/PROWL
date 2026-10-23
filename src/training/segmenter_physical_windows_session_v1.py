"""Physical-detail optimizer and native-grid inference, separately versioned."""
from copy import deepcopy
import numpy as np
import torch
from src.data.manifest_records import canonical,digest
from src.data.segmenter_native_windows_v1 import tiles,orient
from src.data.segmenter_physical_inputs_v1 import PhysicalOptimizerWindows
from src.data.segmenter_physical_windows_v1 import POLICY,physical_geometry,sample_window,PhysicalReconstructor
from src.training.segmenter_augmentation_v1 import augmentation_identity
from src.training.segmenter_full_session_v1 import Session


class PhysicalSession:
    def __init__(self,raw):
        self.raw=raw
        self.identity=dict(version='physical-detail-session-1',raw=deepcopy(raw.identity),
                           policy=deepcopy(POLICY),augmentation=augmentation_identity())
        self.identity_pin=digest(canonical(self.identity))

    def __getattr__(self,key):return getattr(self.raw,key)

    def check(self):
        if digest(canonical(self.identity))!=self.identity_pin or self.identity['policy']!=POLICY:raise ValueError('Physical policy changed')

    def update(self,provider):
        self.check();adapter=PhysicalOptimizerWindows(provider,self.raw)
        result=self.raw.update(adapter)
        return dict(result,input_view=adapter.trace)

    def state(self):
        self.check()
        return dict(version=1,identity=deepcopy(self.identity),identity_sha256=self.identity_pin,raw=self.raw.state())

    @classmethod
    def restore(cls,state,identity):
        if state['version']!=1 or state['identity']!=identity or state['identity_sha256']!=digest(canonical(identity)):
            raise ValueError('Physical checkpoint identity mismatch')
        result=cls(Session.restore(state['raw'],identity['raw']))
        if result.identity!=identity:raise ValueError('Physical implementation changed')
        return result


@torch.no_grad()
def predict_native(session,image,native_geometry,*,progress=lambda completed,total:None):
    if image.shape!=tuple(native_geometry['shape']) or image.dtype!=np.float32 or not np.isfinite(image).all():raise ValueError('Invalid CT')
    record=physical_geometry(native_geometry);ts=tiles(record['shape']);recon=PhysicalReconstructor(record)
    session._clean()
    with session.rng_scope():
        session.model.eval()
        for i,origin in enumerate(ts):
            patch,_=sample_window(image,record,origin,order=1)
            logits=session.model(torch.from_numpy(patch[None,None]).to(session.device))
            if not torch.isfinite(logits).all():raise ValueError('Nonfinite prediction')
            recon.add(origin,torch.softmax(logits,dim=1)[0].cpu().numpy());progress(i+1,len(ts))
    probabilities=recon.finish(ts)
    # Avoid NumPy argmax's possible large channel-contiguous temporary.
    codes=np.zeros(image.shape,np.uint8);best=probabilities[0].copy()
    for k in (1,2):
        take=probabilities[k]>best;codes[take]=k;best[take]=probabilities[k][take]
    return orient(codes,native_geometry,inverse=True),dict(tiles=len(ts),minimum_blend_weight=float(recon.weight.min()),
        gap_voxels=int((recon.weight==0).sum()),spacing_mm=record['spacing_mm'])
