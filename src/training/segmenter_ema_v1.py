"""Additive EMA state; historical full-session identities and numerics remain unchanged."""
from contextlib import contextmanager
from copy import deepcopy
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training.segmenter_full_session_v1 import Session
from src.training.segmenter_session_v1 import cpu_tree,finite


class EMASession:
    def __init__(self,raw,alpha=.99,start_step=500):
        require(type(alpha) in (int,float) and 0<alpha<1,'Invalid EMA alpha')
        require(type(start_step) is int and 0<start_step<=raw.config['max_steps'],'Invalid EMA start')
        self.raw=raw;self.alpha=alpha;self.start_step=start_step
        self.ema=None;self.ema_updates=0
        self.identity=dict(version='segmenter-ema-1',raw=deepcopy(raw.identity),alpha=alpha,start_step=start_step)
        self.identity_pin=digest(canonical(self.identity))

    def __getattr__(self,key):return getattr(self.raw,key)

    def update(self,provider):
        result=self.raw.update(provider)
        if self.step>=self.start_step:
            with torch.no_grad():
                values=self.raw.model.state_dict()
                if self.ema is None:self.ema={k:v.detach().clone() for k,v in values.items()}
                else:
                    for k,v in values.items():
                        if v.is_floating_point():self.ema[k].mul_(self.alpha).add_(v,alpha=1-self.alpha)
                        else:self.ema[k].copy_(v)
                    self.ema_updates+=1
                require(finite(self.ema),'Nonfinite EMA')
        return result

    @contextmanager
    def weights(self,kind):
        require(kind in ('raw','ema'),'Unknown weight variant')
        if kind=='raw':yield;return
        require(self.ema is not None,'EMA not initialized')
        original={k:v.detach().clone() for k,v in self.raw.model.state_dict().items()}
        try:
            self.raw.model.load_state_dict(self.ema,strict=True);yield
        finally:self.raw.model.load_state_dict(original,strict=True)

    def state(self):
        require(digest(canonical(self.identity))==self.identity_pin,'EMA identity changed')
        return dict(version=1,identity=deepcopy(self.identity),identity_sha256=self.identity_pin,
            raw=self.raw.state(),ema=cpu_tree(self.ema),ema_updates=self.ema_updates)

    @classmethod
    def restore(cls,state,identity):
        require(state['version']==1 and state['identity']==identity and state['identity_sha256']==digest(canonical(identity)), 'EMA checkpoint identity mismatch')
        raw=Session.restore(state['raw'],identity['raw']);s=cls(raw,identity['alpha'],identity['start_step'])
        expected=max(0,raw.step-s.start_step)
        require(type(state['ema_updates']) is int and state['ema_updates']==expected,'EMA count mismatch')
        if raw.step<s.start_step:require(state['ema'] is None,'Premature EMA state')
        else:
            values=raw.model.state_dict();ema=state['ema']
            require(isinstance(ema,dict) and set(ema)==set(values) and finite(ema),'Missing/nonfinite EMA')
            require(all(isinstance(ema[k],torch.Tensor) and ema[k].shape==v.shape and ema[k].dtype==v.dtype for k,v in values.items()),'EMA signature mismatch')
            s.ema={k:v.to(raw.device).clone() for k,v in ema.items()}
        s.ema_updates=expected;return s
