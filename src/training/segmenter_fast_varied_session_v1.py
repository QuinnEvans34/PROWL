"""Same scientific sequence with deterministic one-window lookahead."""
from copy import deepcopy
import hashlib
import torch
from src.data.manifest_records import canonical,digest
from src.data.segmenter_fast_varied_v1 import POLICY
from src.training.segmenter_full_session_v1 import POLICY as ORDER
from src.training.segmenter_varied_region_session_v1 import VariedSession


def member_at(names,step,seed):
    epoch,cursor=divmod(step,len(names))
    key=int.from_bytes(hashlib.sha256(f'{seed}:{epoch}:{ORDER}'.encode()).digest()[:8],'little')
    order=torch.randperm(len(names),generator=torch.Generator().manual_seed(key)).tolist()
    return names[order[cursor]]


class FastVariedSession(VariedSession):
    def __init__(self,raw):
        super().__init__(raw)
        self.identity['version']='fast-varied-session-1'
        self.identity['throughput']=deepcopy(POLICY)
        self.identity_pin=digest(canonical(self.identity))

    def update(self,provider):
        step=self.step;request=None
        if step+1<self.config['max_steps']:
            current=self.raw.next_member()
            following=member_at(self.control['train'],step+1,self.config['seed'])
            visit=self.focused[following]+int(following==current and step%4!=3)
            request=(following,step+1,visit,self.config['seed'])
        provider.plan_next(request)
        return super().update(provider)
