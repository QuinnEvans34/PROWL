import json
from types import SimpleNamespace
import pytest
from src.training.verifier_generator_executor_v1 import execute


def objects():
    c=dict(train=['a','b'],validation=['DO_NOT_READ'],restricted_generator=dict(selection='fixed_terminal_no_heldout_selection',evaluation_enabled=False))
    p=SimpleNamespace(control=c,pin='pin',closed=False)
    p.close=lambda:setattr(p,'closed',True)
    s=SimpleNamespace(control=c,control_pin='pin',step=0,config={'max_steps':4},identity={'test':True})
    def update(provider):s.step+=1;return dict(step=s.step,member_id='a',loss=1./s.step)
    s.update=update
    def forbidden(*a,**k):raise AssertionError('Development touched')
    s.evaluate_case=forbidden
    return s,p


def test_terminal_only(tmp_path):
    s,p=objects();saved=[];events=[]
    def checkpoint(path,session,**kwargs):
        assert kwargs['best_score'] is None
        saved.append((path.name,session.step));path.write_text('synthetic')
    result=execute(s,p,tmp_path/'run',checkpoint_every=2,checkpoint=checkpoint,track=events.append)
    assert saved==[('initial.pt',0),('last.pt',2),('last.pt',4),('terminal.pt',4)]
    assert result['selected_step']==4 and result['development_cases_evaluated']==0 and p.closed
    assert not any('validation' in x['event'] or 'native' in x['event'] for x in events)
    assert events[-1]['event']=='completed'


@pytest.mark.parametrize('bad',['identity','selection','resume'])
def test_admission(tmp_path,bad):
    s,p=objects()
    if bad=='identity':s.control_pin='wrong'
    if bad=='selection':p.control['restricted_generator']['evaluation_enabled']=True
    if bad=='resume':s.step=1
    with pytest.raises(ValueError):execute(s,p,tmp_path/'run')
    assert not (tmp_path/'run').exists()


@pytest.mark.parametrize('bad',['loss','member','step','backup'])
def test_failure_no_selected_checkpoint(tmp_path,bad):
    s,p=objects()
    def update(provider):
        s.step+=2 if bad=='step' else 1
        return dict(step=s.step,member_id='DO_NOT_READ' if bad=='member' else 'a',loss=float('nan') if bad=='loss' else 1.)
    s.update=update
    def checkpoint(path,session,**kw):path.write_text('synthetic')
    def hook(path):
        if bad=='backup':raise OSError('Backup failed')
    with pytest.raises((ValueError,OSError)):execute(s,p,tmp_path/'run',checkpoint=checkpoint,checkpoint_hook=hook)
    rows=[json.loads(x) for x in (tmp_path/'run/history.jsonl').read_text().splitlines()]
    assert rows[-1]['event']=='failed' and p.closed and not (tmp_path/'run/terminal.pt').exists()


def test_no_overwrite(tmp_path):
    s,p=objects();out=tmp_path/'run';out.mkdir()
    with pytest.raises(FileExistsError):execute(s,p,out)
