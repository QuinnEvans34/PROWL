import copy
import types
import numpy as np
import pytest
import torch
from src.training.stunet_session_20261106 import Session as Parent, compare
from src.training.stunet_continuation_session_20261108 import Session, PARENT_SHA, loss_diagnostics
from src.training.stunet_transfer_20261106 import deep_supervision_loss


class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.body=torch.nn.Conv3d(1,2,1)
        self.seg_outputs=torch.nn.ModuleList([torch.nn.Conv3d(2,3,1) for _ in range(5)])
        self.decoder=types.SimpleNamespace(deep_supervision=True)
    def forward(self,x):
        return [h(self.body(x)) for h in self.seg_outputs]


class Provider:
    identity='new-input'
    def training(self,step):
        return np.ones((1,2,2,2),np.float32),np.ones((2,2,2),np.uint8),dict(case_id='fit',step=step)


def states():
    identity=dict(input_sha256='old-input',train=['fit'],nonpromotable=False,precision='fp32')
    old=Parent(Tiny(),identity,device='cpu')
    # Exercise real optimizer moments before synthesizing ancestry bookkeeping.
    old.optimizer.zero_grad();sum(x.sum() for x in old.model(torch.ones(1,1,2,2,2))).backward();old.optimizer.step()
    old.step=12000;old.exposure={'fit':12000}
    new=Session(Tiny(),dict(identity,input_sha256='new-input',nonpromotable=True,parent_checkpoint_sha256=PARENT_SHA,phase='corrected-12k-20261108'),device='cpu')
    return old.state(),identity,new


def test_parent_full_state_and_cold_next_update():
    state,identity,new=states()
    proof=new.import_parent(state,identity,PARENT_SHA)
    assert all(p['max_abs_difference']==0 for p in proof.values())
    result=new.update(Provider());assert result['step']==12001 and result['phase_step']==1
    assert result['lr']==pytest.approx(4e-8)
    assert set(result['diagnostics']['gradient_l2'])=={'body','heads'}
    saved=new.state();expected=new.update(Provider());end=new.state()
    _,_,cold=states();cold.restore(saved)
    assert cold.update(Provider())==expected
    compare(end,cold.state())
    with pytest.raises(ValueError):new.import_parent(state,identity,PARENT_SHA)


@pytest.mark.parametrize('mutation',['hash','step','head','identity','rng_role','exposure','precision'])
def test_parent_import_fails_closed(mutation):
    state,identity,new=states();digest=PARENT_SHA
    if mutation=='hash':digest='bad'
    elif mutation=='step':state['step']=11999
    elif mutation=='head':state['model'].pop('seg_outputs.0.weight')
    elif mutation=='identity':state['identity_sha256']='bad'
    elif mutation=='rng_role':identity=dict(identity,nonpromotable=True)
    elif mutation=='exposure':state['exposure']={'fit':11999}
    elif mutation=='precision':state['scaler']={}
    with pytest.raises((ValueError,RuntimeError)):new.import_parent(state,identity,digest)


def test_diagnostics_do_not_change_objective_or_gradients():
    model=Tiny();target=torch.ones(1,2,2,2,dtype=torch.long)
    outputs=model(torch.ones(1,1,2,2,2));loss=deep_supervision_loss(outputs,target)
    before=float(loss.detach());diag=loss_diagnostics(outputs,target);loss.backward()
    gradients={n:p.grad.clone() for n,p in model.named_parameters()}
    model.zero_grad();loss2=deep_supervision_loss(model(torch.ones(1,1,2,2,2)),target);loss2.backward()
    assert float(loss2.detach())==before and len(diag['scales'])==5
    for n,p in model.named_parameters():assert torch.equal(gradients[n],p.grad)
    assert diag['scales'][0]['classes'][2]['ce_mean'] is None


def test_original_restore_does_not_accept_continuation():
    state,identity,new=states();new.import_parent(state,identity,PARENT_SHA)
    with pytest.raises(ValueError):Parent(Tiny(),identity,device='cpu').restore(new.state())
    with pytest.raises(ValueError):new.restore(state)
