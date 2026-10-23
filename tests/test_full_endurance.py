import json
from types import SimpleNamespace
import pytest
from src.training import segmenter_full_executor_v1 as executor
from src.training.segmenter_full_session_v1 import learning_rate_factor, validate_config


def test_schedule_horizon_keeps_old_rates_and_holds_final():
    c = dict(max_steps=24000,tensor_shape=[144]*3,seed=42,learning_rate=1e-4,
             weight_decay=1e-5,warmup_steps=500,lr_schedule='warmup_cosine')
    long = dict(c,max_steps=1000000,lr_horizon_steps=24000)
    validate_config(c); validate_config(long)
    for step in (0,499,500,23999):
        assert learning_rate_factor(c,step) == learning_rate_factor(long,step)
    assert learning_rate_factor(long,999999) == learning_rate_factor(c,23999)
    for horizon in (0,500,1000001,True):
        with pytest.raises(ValueError): validate_config(dict(long,lr_horizon_steps=horizon))


def run_fake(tmp_path, monkeypatch, *, ceiling=100, target=8, fail=False):
    now = [0.]; saves = []; backup = []
    monkeypatch.setattr(executor.time,'monotonic',lambda:now[0])
    def checkpoint(path, session, **kwargs): saves.append((path.name,session.step))
    monkeypatch.setattr(executor,'atomic_checkpoint',checkpoint)
    s=SimpleNamespace(step=0,config={'max_steps':ceiling},identity={},dirty=False,control={'validation':['dev']})
    def update(provider):
        if fail: raise RuntimeError('injected failure')
        s.step += 1; now[0] += 2
        return dict(step=s.step)
    s.update=update
    s.evaluate_case=lambda *a:dict(metrics={'lesion':dict(target_voxels=1,dice=.5)})
    result=executor.execute(s,None,tmp_path/'run',validate_every=2,checkpoint_every=3,
        checkpoint_hook=lambda p:backup.append(p.name),target_seconds=target)
    return result,saves,backup


def test_duration_saves_and_backs_up_terminal_state(tmp_path,monkeypatch):
    result,saves,backup=run_fake(tmp_path,monkeypatch)
    assert result['completed_updates']==4 and result['training_seconds']==8
    assert result['stop_reason']=='duration_target'
    assert saves[-1]==('last.pt',4) and backup[-1]=='last.pt'
    rows=[json.loads(s) for s in (tmp_path/'run/history.jsonl').read_text().splitlines()]
    assert rows[-1]['event']=='completed'


def test_short_ceiling_is_not_endurance_success(tmp_path,monkeypatch):
    with pytest.raises(ValueError,match='ceiling'):run_fake(tmp_path,monkeypatch,ceiling=2)
    assert json.loads((tmp_path/'run/history.jsonl').read_text().splitlines()[-1])['event']=='failed'


def test_failure_remains_failure(tmp_path,monkeypatch):
    with pytest.raises(RuntimeError,match='injected'):run_fake(tmp_path,monkeypatch,fail=True)
