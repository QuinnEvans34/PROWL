import pytest
import torch
import torch.nn.functional as F
from src.training.midpoint_class_mean_loss import configured_loss, LOSS_ID
from src.training.localizer import configured_loss as legacy


@pytest.mark.parametrize('labels', [[0,0,0,0],[1,1,1,1],[0,0,0,1],[1,1,1,0]])
@pytest.mark.parametrize('values', [[-2.,-.5,1.2,2.],[-1000.,1000.,-100.,100.]])
def test_independent_binary_formula_values_and_gradients(labels, values):
    delta=torch.tensor(values,dtype=torch.float64,requires_grad=True)
    y=torch.tensor(labels,dtype=torch.long)
    z=torch.stack((torch.zeros_like(delta),delta)).reshape(1,2,1,1,4)
    t=y.reshape(1,1,1,1,4)
    actual=configured_loss(z,t,dict(loss_id=LOSS_ID))
    fg=y.bool();bg=~fg;p=delta.sigmoid()
    if fg.any() and bg.any():
        ce=.375*F.softplus(-delta[fg]).mean()+.625*F.softplus(delta[bg]).mean()
    else:ce=(F.softplus(-delta[fg]) if fg.any() else F.softplus(delta[bg])).mean()
    expected=ce+(1-(2*p[fg].sum()+1e-5)/(p.sum()+fg.sum()+1e-5) if fg.any() else p.sum()*0)
    ga,=torch.autograd.grad(actual,delta,retain_graph=True)
    ge,=torch.autograd.grad(expected,delta)
    assert torch.allclose(actual,expected,rtol=0,atol=1e-10)
    assert torch.allclose(ga,ge,rtol=0,atol=1e-10) and torch.isfinite(ga).all()


def test_batch_empty_sparse_and_dense_cases_have_independent_class_means():
    torch.manual_seed(42);z=torch.randn(3,2,2,2,2,dtype=torch.float64,requires_grad=True)
    t=torch.zeros(3,1,2,2,2,dtype=torch.long);t[1,0,0,0,0]=1;t[2]=1
    per=F.cross_entropy(z,t[:,0],reduction='none');p=z.softmax(1)[:,1]
    ce=(per[0].mean()+.375*per[1][t[1,0]==1].mean()+.625*per[1][t[1,0]==0].mean()+per[2].mean())/3
    truth=t[:,0];dice=1-(2*(p*truth).sum((1,2,3))+1e-5)/(p.sum((1,2,3))+truth.sum((1,2,3))+1e-5)
    loss=configured_loss(z,t,dict(loss_id=LOSS_ID));assert torch.allclose(loss,ce+dice[1:].mean())
    loss.backward();assert torch.isfinite(z.grad).all()


def test_class_means_are_not_fixed_voxel_weights_and_sole_class_is_full_strength():
    z=torch.zeros(1,2,1,1,100,dtype=torch.float64);z[:,1]=1
    t=torch.zeros(1,1,1,1,100,dtype=torch.long);t[...,0]=1
    per=F.cross_entropy(z,t[:,0],reduction='none');p=z.softmax(1)[:,1]
    dice=1-(2*p[...,0].sum()+1e-5)/(p.sum()+1+1e-5)
    loss=configured_loss(z,t,dict(loss_id=LOSS_ID))
    wrong=F.cross_entropy(z,t[:,0],weight=torch.tensor([.625,.375],dtype=torch.float64))+dice
    assert abs(float(loss-wrong))>.1
    t.zero_();assert torch.allclose(configured_loss(z,t,dict(loss_id=LOSS_ID)),F.cross_entropy(z,t[:,0]))


@pytest.mark.parametrize('fault',['loss','nonbinary','nan','shape','empty','classes'])
def test_invalid_objectives_and_inputs_refused(fault):
    z=torch.zeros(1,2,1,1,4);t=torch.zeros(1,1,1,1,4,dtype=torch.long);cfg=dict(loss_id=LOSS_ID)
    if fault=='loss':cfg['loss_id']='balanced_ce_dice_v1'
    if fault=='nonbinary':t[...,0]=2
    if fault=='nan':z[...,0]=float('nan')
    if fault=='shape':t=t[...,0:3]
    if fault=='empty':z=z[...,0:0];t=t[...,0:0]
    if fault=='classes':z=z[:,0:1]
    with pytest.raises(ValueError):configured_loss(z,t,cfg)


def test_legacy_dispatch_does_not_silently_adopt_new_loss():
    with pytest.raises(ValueError):legacy(torch.zeros(1,2,1,1,4),torch.zeros(1,1,1,1,4),dict(loss_id=LOSS_ID))


@pytest.mark.parametrize('empty',[False,True])
def test_sparse_and_empty_toy_learning_has_finite_parameter_gradients(empty):
    torch.set_num_threads(2);torch.manual_seed(42)
    t=torch.zeros(1,1,4,4,4,dtype=torch.long)
    if not empty:t[0,0,1,1,1]=1
    x=t.float();model=torch.nn.Conv3d(1,2,1);opt=torch.optim.AdamW(model.parameters(),lr=.1,weight_decay=0)
    initial=float(configured_loss(model(x),t,dict(loss_id=LOSS_ID)).detach())
    for _ in range(100):
        opt.zero_grad();loss=configured_loss(model(x),t,dict(loss_id=LOSS_ID));loss.backward()
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters());opt.step()
    with torch.no_grad():
        p=model(x).softmax(1)[:,1];end=float(configured_loss(model(x),t,dict(loss_id=LOSS_ID)))
    assert end<initial*.2 and p[t[:,0]==0].mean()<.05
    if not empty:assert p[t[:,0]==1].mean()>.95 and torch.equal(model(x).argmax(1),t[:,0])


def test_old_and_new_class_mean_dispatch_are_not_interchangeable():
    from src.training.class_mean_loss import configured_loss as v5, LOSS_ID as old_id
    z=torch.zeros(1,2,1,1,4);t=torch.zeros(1,1,1,1,4)
    with pytest.raises(ValueError):v5(z,t,dict(loss_id=LOSS_ID))
    with pytest.raises(ValueError):configured_loss(z,t,dict(loss_id=old_id))
