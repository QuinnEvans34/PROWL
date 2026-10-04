from copy import deepcopy
from io import BytesIO
import json
import numpy as np
import pytest
import torch
from src.training.localizer import LocalizerSession,patch_batch,foreground_dice,loss_value
from src.training.localizer_checkpoint import save,resume,decode
from src.operations.artifact_store import ArtifactStore
from src.data.manifest_records import canonical,digest


@pytest.fixture
def config():
    return dict(patch_size=[16]*3,seed=42,learning_rate=.003,weight_decay=.00001,max_steps=40)


@pytest.fixture
def fixture():
    y=torch.zeros(1,16,16,16);y[:,4:12,4:12,4:12]=1
    return y*.8+.1,y


@pytest.fixture
def identity(config):
    return dict(schema_version='1.0.0',run_id='localizer-synthetic-test',run_class='diagnostic',data_mode='synthetic',
        config=config,code_sha256='a'*64,environment_sha256='b'*64,cohort_sha256='c'*64,
        preprocessing_sha256='d'*64,device='cpu',precision='float32',workers=0,cache='none')


@pytest.fixture
def store(tmp_path):
    return ArtifactStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0)


def test_patch_padding_alignment_and_repeat(config,fixture):
    x,y=fixture;config['patch_size']=[96]*3
    a,b,trace=patch_batch(x,y,config,step=0,member_id='invented')
    assert a.shape==b.shape==(1,1,96,96,96)
    assert torch.equal(a[b.bool()],x[y.bool()])
    a2,b2,t2=patch_batch(x,y,config,step=0,member_id='invented')
    assert torch.equal(a,a2) and torch.equal(b,b2) and trace==t2
    assert y.sum()==512


def test_sampling_both_classes_and_empty(config,fixture):
    x,y=fixture
    classes={patch_batch(x,y,config,step=n,member_id='invented')[2]['center_class'] for n in range(40)}
    assert classes=={0,1}
    assert patch_batch(x,torch.zeros_like(y),config,step=0,member_id='empty')[2]['center_class']==0


@pytest.mark.parametrize('change',[{'patch_size':[17]*3},{'pretrained':'old.pt'},{'seed':-1},{'learning_rate':float('nan')}])
def test_bad_config(config,change):
    config.update(change)
    with pytest.raises(ValueError):LocalizerSession(config)


def test_bad_targets_and_image(config,fixture):
    x,y=fixture
    for image,target in ((x,y+1),(x+2,y),(x.double(),y),(x,y[:,:,:,:8])):
        with pytest.raises(ValueError):patch_batch(image,target,config,step=0,member_id='bad')


def test_metrics_oracles_and_empty():
    assert foreground_dice(torch.tensor([1,0,1]),torch.tensor([1,1,0]))['dice']==.5
    assert foreground_dice(torch.zeros(3),torch.zeros(3))==dict(dice=None,target_foreground=0,predicted_foreground=0)
    assert foreground_dice(torch.ones(3),torch.zeros(3))['predicted_foreground']==3
    logits=torch.zeros(1,2,2,2,2,requires_grad=True)
    loss=loss_value(logits,torch.zeros(1,1,2,2,2).long());loss.backward()
    assert loss.item()==pytest.approx(np.log(2)) and torch.isfinite(logits.grad).all()


def test_learning_and_exact_resume(config,fixture,identity,store):
    torch.set_num_threads(2)
    x,y=fixture;a=LocalizerSession(config)
    with torch.no_grad():initial=loss_value(a.model(x[None]),y[None].long()).item()
    original={k:v.clone() for k,v in a.model.state_dict().items()}
    for _ in range(4):a.update(x,y,'invented')
    ref=save(store,a,identity);b=resume(store,ref,identity)
    assert torch.equal(a.predict(x),b.predict(x))
    for _ in range(3):
        assert a.update(x,y,'invented')==b.update(x,y,'invented')
    assert all(torch.equal(v,b.model.state_dict()[k]) for k,v in a.model.state_dict().items())
    assert a.scheduler.state_dict()==b.scheduler.state_dict()
    for _ in range(13):a.update(x,y,'invented')
    with torch.no_grad():final=loss_value(a.model(x[None]),y[None].long()).item()
    assert final<initial*.8
    assert any(not torch.equal(v,original[k]) for k,v in a.model.state_dict().items())


def test_inference_odd_shape_source_restore(config):
    from src.data.localizer_preprocessing import preprocess,restore_to_source
    recipe=json.loads(open('configs/capstone/localizer-preprocessing-v1.json').read())
    recipe['minimum_shape']=[16]*3;recipe['spacing_mm']=[3]*3
    data=preprocess(np.zeros((19,21,23),np.float32),np.diag([3,3,3,1]),recipe)
    result=LocalizerSession(config).predict(data['image'])
    assert result.shape==(2,19,21,23) and torch.allclose(result.sum(0),torch.ones(19,21,23),atol=1e-6)
    native=restore_to_source(result,data['transform_record'],discrete=False)
    assert native.shape==result.shape and torch.isfinite(native).all()


def test_reject_corruption_and_wrong_identity(config,fixture,identity,store):
    a=LocalizerSession(config);a.update(*fixture,'invented');ref=save(store,a,identity)
    changed=deepcopy(identity);changed['cohort_sha256']='e'*64
    with pytest.raises(ValueError):resume(store,ref,changed)
    directory=store.root/digest(ref['artifact_id'].encode())
    (directory/'state.pt').write_bytes(b'corrupted')
    with pytest.raises(ValueError):resume(store,ref,identity)


def test_incomplete_attempt_and_failed_publication(config,fixture,identity,store,monkeypatch):
    a=LocalizerSession(config);a.update(*fixture,'invented');ref=save(store,a,identity)
    a.update(*fixture,'invented')
    import src.operations.artifact_store as module
    def interrupt(*args,**kwargs):raise InterruptedError('controlled before publish')
    with monkeypatch.context() as m:
        m.setattr(module.os,'rename',interrupt)
        with pytest.raises(InterruptedError):save(store,a,identity)
    assert len(list(store.root.glob('.attempt-*')))==1
    assert resume(store,ref,identity).step==1
    retry=save(store,a,identity)
    assert resume(store,retry,identity).step==2
    assert len(list(store.root.glob('.attempt-*')))==1


@pytest.mark.parametrize('fault',['missing_optimizer','scheduler','rng','nan','moment','step'])
def test_semantic_checkpoint_faults(config,fixture,identity,store,fault):
    a=LocalizerSession(config);a.update(*fixture,'invented');ref=save(store,a,identity)
    directory=store.root/digest(ref['artifact_id'].encode())
    state=torch.load(directory/'state.pt',weights_only=True)
    if fault=='missing_optimizer':state['optimizer']['state']={}
    if fault=='scheduler':state['scheduler']['last_epoch']=0
    if fault=='rng':state['cpu_rng']=torch.zeros(1)
    if fault=='nan':next(iter(state['model'].values())).fill_(float('nan'))
    if fault=='moment':next(iter(state['optimizer']['state'].values()))['exp_avg']=torch.zeros(1)
    if fault=='step':state['step']=1000
    b=BytesIO();torch.save(state,b)
    with pytest.raises(ValueError):decode({'identity.json':canonical(identity),'state.pt':b.getvalue()},identity)


def test_no_overwrite_and_step_budget(config,fixture,identity,store):
    config['max_steps']=1
    a=LocalizerSession(config);a.update(*fixture,'invented');ref=save(store,a,identity)
    with pytest.raises(ValueError,match='budget'):a.update(*fixture,'invented')
    with torch.no_grad():next(a.model.parameters()).add_(.01)
    with pytest.raises(ValueError,match='collision'):save(store,a,identity)
    assert resume(store,ref,identity).step==1


def test_scratch_seed_reproducibility(config):
    a=LocalizerSession(config);torch.manual_seed(998);b=LocalizerSession(config)
    assert all(torch.equal(v,b.model.state_dict()[k]) for k,v in a.model.state_dict().items())
    config['seed']+=1;c=LocalizerSession(config)
    assert not torch.equal(next(a.model.parameters()),next(c.model.parameters()))


def test_sample_varied_volume_preserves_voxel_pairs(config):
    x=torch.linspace(0,1,24*32*40).reshape(1,24,32,40);y=(x>.8).long()
    first=[]
    for step in range(10):
        a,b,trace=patch_batch(x,y,config,step=step,member_id='larger-fixture')
        assert torch.equal((a>.8).long(),b)
        assert y[(0,*trace['center'])].item()==trace['center_class']
        first.append(trace['origin_in_padded_grid'])
    assert len(set(map(tuple,first)))>1
