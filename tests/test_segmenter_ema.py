from copy import deepcopy
import json
import pytest
import torch
from test_segmenter_full import Invented,config
from src.training.segmenter_full_session_v1 import Session,learning_rate_factor
from src.training.segmenter_ema_v1 import EMASession
from src.training.segmenter_ema_executor_v1 import execute
from src.training.segmenter_live_tracking_v1 import Tracker
from scripts.diagnostics.profile_lenovo_real_segmenter import compare


def make():
    torch.set_num_threads(2);p=Invented()
    return p,EMASession(Session(config(4),p.control,device='cpu',initialization={'kind':'scratch'}),start_step=2)


def test_raw_updates_unaffected_and_ema_formula():
    p,s=make();other=Session(config(4),p.control,device='cpu',initialization={'kind':'scratch'})
    for step in range(1,5):
        old=deepcopy(s.ema);assert s.update(p)==other.update(p)
        compare(s.raw.state(),other.state(),exact=True)
        if step==1:assert s.ema is None
        if step==2:compare(s.ema,s.model.state_dict(),exact=True)
        if step>2:
            for k,v in s.ema.items():
                if v.is_floating_point():torch.testing.assert_close(v,old[k]*.99+s.model.state_dict()[k]*.01)
    assert s.ema_updates==2


@pytest.mark.parametrize('step',[0,1,2,3])
def test_restore_and_next_update(step):
    p,s=make()
    for _ in range(step):s.update(p)
    state=deepcopy(s.state());restored=EMASession.restore(state,s.identity)
    compare(state,restored.state(),exact=True)
    assert s.update(p)==restored.update(p);compare(s.state(),restored.state(),exact=True)


def test_eval_weights_restored_on_exception():
    p,s=make()
    for _ in range(3):s.update(p)
    original=deepcopy(s.state())
    with pytest.raises(RuntimeError):
        with s.weights('ema'):raise RuntimeError('evaluation fault')
    compare(s.state(),original,exact=True)


@pytest.mark.parametrize('bad',['count','missing','nan','identity'])
def test_corrupt_checkpoint_refused(bad):
    p,s=make();s.update(p);s.update(p);state=s.state()
    if bad=='count':state['ema_updates']=10
    if bad=='missing':state['ema']=None
    if bad=='nan':next(iter(state['ema'].values())).flatten()[0]=float('nan')
    if bad=='identity':state['identity']['alpha']=.9
    with pytest.raises(ValueError):EMASession.restore(state,s.identity)


def test_executor_preserves_both_weights_and_variant_events(tmp_path):
    p,s=make();seen=[]
    result=execute(s,p,tmp_path/'run',validate_every=2,checkpoint_every=2,retain_steps=[2,4],track=seen.append)
    assert result['completed_updates']==4
    assert {r['variant'] for r in seen if r['event']=='validation'}=={'raw','ema'}
    for name in ('initial.pt','last.pt','best-raw.pt','best-ema.pt','step-000002.pt','step-000004.pt'):
        state=torch.load(tmp_path/'run'/name,weights_only=True)['session'];EMASession.restore(state,s.identity)


def test_tracker_failure_preserves_training_path(tmp_path):
    class Broken:
        def log_batch(self,*a,**k):raise RuntimeError('tracking unavailable')
    t=Tracker('run',tmp_path,client=Broken())
    t(dict(event='update',step=1,loss=1,learning_rate=.01,elapsed_seconds=2,utc_ms=1000))
    assert t.disabled and json.loads((tmp_path/'tracking-warning.json').read_text())['step']==1
    t(dict(event='update',step=25))


def test_stretched_schedule_does_not_reuse_old_tail():
    c=dict(config(72000),warmup_steps=500,lr_horizon_steps=72000)
    assert learning_rate_factor(c,24000)>.7
    assert learning_rate_factor(c,71999)<1e-8
    assert learning_rate_factor(c,0)==.002
