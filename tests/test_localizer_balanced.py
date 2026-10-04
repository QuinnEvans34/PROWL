import json
import math
from io import BytesIO
import pytest
import torch
import torch.nn.functional as F
from src.training.localizer import configured_loss,balanced_cross_entropy,loss_value,LocalizerSession
from src.training.localizer_run import validate_identity,payload,validate_payload
from src.training.localizer_smoke import execute,validate_terminal
from src.data.manifest_records import canonical,digest
from src.operations.artifact_store import ArtifactStore
from tests.test_localizer_smoke import bundle


def balanced_bundle():
    data,identity,controls=bundle();identity['schema_version']='4.0.0';identity['config']['loss_id']='balanced_ce_dice_v1'
    plan=json.loads(controls['plan.json']);plan.update(config=identity['config'],evaluation_policy='balanced_and_legacy_v1')
    controls['plan.json']=canonical(plan);identity['plan_sha256']=digest(controls['plan.json'])
    auth=json.loads(controls['authorization.json']);auth['bindings']['plan_sha256']=identity['plan_sha256']
    controls['authorization.json']=canonical(auth);identity['authorization_sha256']=digest(controls['authorization.json'])
    return data,identity,controls


def test_balanced_ce_oracle_and_class_duplication():
    p=torch.tensor([.2,.2,.7]);z=torch.stack([(1-p).log(),p.log()])[None,:,None,None,:];y=torch.tensor([0,0,1])[None,None,None,:]
    actual=balanced_cross_entropy(z,y)
    assert actual.item()==pytest.approx(( -math.log(.8)-math.log(.7))/2,abs=1e-6)
    assert balanced_cross_entropy(z[:,:,:,:,[0,2]],y[:,:,:,[0,2]]).item()==pytest.approx(actual.item())


@pytest.mark.parametrize('label',[0,1])
def test_single_class_and_extreme_logits_finite(label):
    z=torch.tensor([1000.,-1000.]).reshape(1,2,1,1,1).requires_grad_();y=torch.full((1,1,1,1,1),label)
    value=configured_loss(z,y,{'loss_id':'balanced_ce_dice_v1'});value.backward()
    assert torch.isfinite(value) and torch.isfinite(z.grad).all()
    assert balanced_cross_entropy(z,y[:,0])==F.cross_entropy(z,y[:,0])


def test_legacy_exact_and_balanced_gradient():
    z=torch.linspace(-1,1,16,dtype=torch.float64).reshape(1,2,2,2,2).requires_grad_();y=torch.zeros(1,1,2,2,2,dtype=torch.long);y[...,0,0,0]=1
    assert torch.equal(configured_loss(z,y,{}),loss_value(z,y))
    v=configured_loss(z,y,{'loss_id':'balanced_ce_dice_v1'});g=torch.autograd.grad(v,z)[0]
    eps=1e-5;plus=z.detach().clone();minus=plus.clone();plus[0,1,0,0,0]+=eps;minus[0,1,0,0,0]-=eps
    fd=(configured_loss(plus,y,{'loss_id':'balanced_ce_dice_v1'})-configured_loss(minus,y,{'loss_id':'balanced_ce_dice_v1'}))/(2*eps)
    assert g[0,1,0,0,0].item()==pytest.approx(fd.item(),abs=1e-7)


def test_objective_identity_mismatch_and_end_to_end(tmp_path):
    torch.set_num_threads(2);data,identity,controls=balanced_bundle();session=LocalizerSession(identity['config'])
    store=ArtifactStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    result,ref=execute(session,data,identity,controls,store)
    files,_=store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=lambda f:validate_terminal(f,identity))
    trajectory=json.loads(files['trajectory.json']);assert [r['step'] for r in trajectory]==[0,1,2]
    assert all('legacy_loss' in c for r in trajectory for c in r['metrics']['cases'])
    wrong=dict(identity,schema_version='3.0.0')
    with pytest.raises(ValueError,match='Legacy'):validate_identity(wrong)
    wrong=dict(identity,config=dict(identity['config'],loss_id='voxel_ce_dice_v1'))
    with pytest.raises(ValueError,match='Version4'):validate_identity(wrong)
    changed=dict(files);t=json.loads(changed['trajectory.json']);t[1]['step']=99;changed['trajectory.json']=canonical(t)
    with pytest.raises(ValueError,match='trajectory'):validate_terminal(changed,identity)


def test_balanced_logit_probe_matches_balanced_ce():
    from src.training.localizer_diagnostics import logit_diagnostics
    z=torch.linspace(-1,1,16).reshape(1,2,2,2,2).requires_grad_();y=torch.zeros(1,1,2,2,2,dtype=torch.long);y[...,0,0,0]=1
    probe=logit_diagnostics(z,y,include_balanced=True)['terms']['balanced_ce']
    loss=balanced_cross_entropy(z,y[:,0]);g=torch.autograd.grad(loss,z)[0]
    assert probe['value']==pytest.approx(loss.item(),abs=1e-6)
    assert probe['uniform_logit_shift_derivative']==pytest.approx(g[:,1].sum().item(),abs=1e-6)


def test_real_experiment_configuration_is_bound_to_registered_id():
    from src.training.localizer_smoke import BALANCED_EXPERIMENTS,validate_controls
    _,identity,controls=balanced_bundle();identity.update(training_data='qualified_cohort',device='mps',config=BALANCED_EXPERIMENTS['CAP-EXP-003'])
    plan=json.loads(controls['plan.json']);plan.update(experiment_id='CAP-EXP-003',config=identity['config'],checkpoint_every=25)
    auth=json.loads(controls['authorization.json']);auth.update(data_mode='qualified_cohort',authority='Quinton Evans',operation='launch_CAP-EXP-003')
    def bind():
        controls['plan.json']=canonical(plan);identity['plan_sha256']=digest(controls['plan.json'])
        auth['bindings']['plan_sha256']=identity['plan_sha256'];controls['authorization.json']=canonical(auth);identity['authorization_sha256']=digest(controls['authorization.json'])
    bind();validate_controls(controls,identity)
    plan['experiment_id']='CAP-EXP-002';auth['operation']='launch_CAP-EXP-002';bind()
    with pytest.raises(ValueError,match='Real launch scope'):validate_controls(controls,identity)


def test_bounded300_scheduler_checkpoint_and_legacy_ceiling():
    from src.training.localizer import validate_config
    data,identity,controls=balanced_bundle();identity['config'].update(max_steps=300,learning_rate=.0003)
    plan=json.loads(controls['plan.json']);plan['config']=identity['config'];controls['plan.json']=canonical(plan);identity['plan_sha256']=digest(controls['plan.json'])
    auth=json.loads(controls['authorization.json']);auth['bindings']['plan_sha256']=identity['plan_sha256'];controls['authorization.json']=canonical(auth);identity['authorization_sha256']=digest(controls['authorization.json'])
    validate_config(identity['config'])
    with pytest.raises(ValueError,match='step budget'):validate_config(dict(identity['config'],max_steps=301))
    legacy={k:v for k,v in identity['config'].items() if k!='loss_id'}
    with pytest.raises(ValueError,match='step budget'):validate_config(dict(legacy,max_steps=101))
    session=LocalizerSession(identity['config']);item=data[0];row=session.update(item['image'],item['label'],data.descriptors[0]['study_id'])
    files=payload(session,identity,dict(controls,**{'progress.json':canonical(dict(updates=[row]))}))
    assert validate_payload(files,identity)['step']==1
    assert session.optimizer.param_groups[0]['lr']==pytest.approx(.0003*(1+math.cos(math.pi/300))/2)


def test_long_real_recipe_requires_registered_cadence():
    from src.training.localizer_smoke import BALANCED_EXPERIMENTS,validate_controls
    _,identity,controls=balanced_bundle();identity.update(training_data='qualified_cohort',device='mps',config=BALANCED_EXPERIMENTS['CAP-EXP-004'])
    plan=json.loads(controls['plan.json']);plan.update(experiment_id='CAP-EXP-004',config=identity['config'],checkpoint_every=75)
    auth=json.loads(controls['authorization.json']);auth.update(data_mode='qualified_cohort',authority='Quinton Evans',operation='launch_CAP-EXP-004')
    def bind():
        controls['plan.json']=canonical(plan);identity['plan_sha256']=digest(controls['plan.json']);auth['bindings']['plan_sha256']=identity['plan_sha256']
        controls['authorization.json']=canonical(auth);identity['authorization_sha256']=digest(controls['authorization.json'])
    bind();validate_controls(controls,identity)
    plan['checkpoint_every']=25;bind()
    with pytest.raises(ValueError,match='Real launch scope'):validate_controls(controls,identity)
