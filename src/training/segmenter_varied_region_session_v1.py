"""Versioned sampler identity and saved per-case focus counters; same optimizer/evaluator."""
from copy import deepcopy
from src.data.manifest_records import canonical, digest
from src.data.segmenter_varied_region_v1 import POLICY
from src.training.segmenter_full_session_v1 import Session
from src.training.segmenter_pancreas_region_session_v1 import RegionSession
from src.training.segmenter_augmentation_v1 import augmentation_identity


class VariedSession(RegionSession):
    def __init__(self, raw):
        self.raw = raw; self.focused = dict.fromkeys(raw.control['train'], 0)
        self.identity = dict(version='varied-region-session-1', raw=deepcopy(raw.identity),
                             policy=deepcopy(POLICY), augmentation=augmentation_identity())
        self.identity_pin = digest(canonical(self.identity))

    def check(self):
        if digest(canonical(self.identity)) != self.identity_pin or self.identity['policy'] != POLICY:
            raise ValueError('Varied region identity changed')
        if set(self.focused) != set(self.exposure) or any(type(v) != int or v < 0 or
                v > self.exposure[n] or v > self.control['planned_focused_counts'][n]
                for n,v in self.focused.items()): raise ValueError('Focus state invalid')
        if sum(self.focused.values()) != self.step-self.step//4: raise ValueError('Focus totals invalid')

    @classmethod
    def restore(cls, state, identity):
        if state['version'] != 1 or state['identity'] != identity or state['identity_sha256'] != digest(canonical(identity)):
            raise ValueError('Varied checkpoint identity mismatch')
        result = cls(Session.restore(state['raw'], identity['raw']))
        if result.identity != identity: raise ValueError('Expected implementation identity mismatch')
        result.focused = deepcopy(state['focused']); result.check()
        return result
