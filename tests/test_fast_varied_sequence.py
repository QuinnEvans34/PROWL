from copy import deepcopy
from types import SimpleNamespace
from src.training.segmenter_fast_varied_session_v1 import FastVariedSession,member_at
from src.training.segmenter_varied_region_session_v1 import VariedSession


def test_lookahead_counters_match_future_committed_state_across_epochs(monkeypatch):
    names=['a','b','c'];raw=SimpleNamespace(control={'train':names,'planned_focused_counts':dict.fromkeys(names,50)},
        config={'seed':42,'max_steps':40},identity={},exposure=dict.fromkeys(names,0),step=0)
    raw.next_member=lambda:member_at(names,raw.step,42)
    session=FastVariedSession(raw);pending=[];p=SimpleNamespace(plan_next=lambda request:pending.append(request))
    def update(self,provider):
        name=raw.next_member();step=raw.step
        if step%4!=3:self.focused[name]+=1
        raw.exposure[name]+=1;raw.step+=1
        return {'member_id':name}
    monkeypatch.setattr(VariedSession,'update',update)
    for step in range(40):
        session.update(p)
        if step==39:assert pending[-1] is None
        else:
            name=raw.next_member()
            assert pending[-1]==(name,raw.step,session.focused[name],42)
