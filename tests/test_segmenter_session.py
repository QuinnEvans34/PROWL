from copy import deepcopy
from io import BytesIO
import json
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.operations.artifact_store import ArtifactStore
from src.training import segmenter_session_v1 as m

@pytest.fixture
def identity(monkeypatch):
    torch.set_num_threads(2)
    monkeypatch.setattr(m,'build_model',lambda c:torch.nn.Conv3d(1,3,1))
    context={n:canonical({'fixture':n}) for n in ('source.json','environment.json','geometry.json')}
    return m.make_identity(m.config(steps=10),context,run_id='segmenter-synthetic-test',device='cpu')

def test_independent_class_cues_and_boundaries():
    expected={'sparse':8,'multiple':16,'boundary':8,'outside_pancreas':12,'verified_negative':0}
    for n,count in expected.items():
        x,y=m.fixture(n);assert int((y==2).sum())==count
        assert x.dtype==torch.float32 and x.shape==(1,24,24,24)
        assert torch.all(x[0][y==2]==.9) and torch.all(x[0][y==1]==.5)
    _,a=m.fixture('outside_pancreas');assert torch.all(a[19:21,10:12,10:12]==2)
    _,a=m.fixture('boundary');assert (a[0]==2).any()
    _,a=m.fixture('multiple');assert len(m.metrics(a,a)['components'])==2
    assert m.metrics(a,a)['pancreas_lesion_union']['target_voxels']==int((a>0).sum())

@pytest.mark.parametrize('fault',['shape','dtype','values','nonfinite','channels','target_dtype','target_class'])
def test_bad_input_refused(fault):
    x,y=m.fixture('sparse')
    if fault=='shape':x=x[:,:23]
    elif fault=='dtype':x=x.double()
    elif fault=='values':x.fill_(1.1)
    elif fault=='nonfinite':x.flatten()[0]=float('nan')
    elif fault=='channels':x=x.repeat(2,1,1,1)
    elif fault=='target_dtype':y=y.float()
    elif fault=='target_class':y.flatten()[0]=3
    with pytest.raises(ValueError):m.checked_batch(x,y,m.config())

def test_objective_against_independent_scalar_and_gradient_oracle():
    logits=torch.tensor([[[[[.2, .7]]],[[[.4,-.1]]],[[[-.2,.3]]]]],requires_grad=True)
    y=torch.tensor([[[[1,2]]]],dtype=torch.long)
    p=torch.exp(logits)/torch.exp(logits).sum(1,keepdim=True)
    ce=-(p[0,1,0,0,0].log()+p[0,2,0,0,1].log())/2
    d1=1-(2*p[0,1,0,0,0]+1e-5)/(p[0,1].sum()+1+1e-5)
    d2=1-(2*p[0,2,0,0,1]+1e-5)/(p[0,2].sum()+1+1e-5)
    oracle=ce+(d1+d2)/2;actual=m.objective(logits,y)
    assert torch.allclose(actual,oracle,atol=1e-7)
    a=torch.autograd.grad(actual,logits,retain_graph=True)[0];b=torch.autograd.grad(oracle,logits)[0]
    assert torch.allclose(a,b,atol=1e-7) and a[0,1,0,0,0]<0 and a[0,2,0,0,1]<0
    assert torch.isfinite(a).all() and (a[:,0]>0).all()

def test_sparse_present_and_absent_class_gradients():
    for name in ('sparse','verified_negative'):
        _,y=m.fixture(name);z=torch.zeros((1,3,24,24,24),requires_grad=True);v=m.objective(z,y[None]);v.backward()
        assert torch.isfinite(z.grad).all() and z.grad[:,0].abs().sum()>0 and z.grad[:,1].abs().sum()>0
        if name=='sparse':assert (z.grad[0,2][y==2]<0).all()
        else:assert (z.grad[0,2]>0).all()  # CE actively suppresses absent lesions.

@pytest.mark.parametrize('fault',['task','mode','version','architecture','loss','policy','shape','steps','lr','bool_steps'])
def test_unsafe_identity_refused(identity,fault):
    i,c=deepcopy(identity)
    if fault=='task':i['task']='localizer'
    elif fault=='mode':i['data_mode']='qualified_real'
    elif fault=='version':i['schema_version']='twomm-session-1'
    else:
        f={'architecture':('architecture',{'out_channels':2}),'loss':('loss_id','balanced_ce_dice_v1'),'policy':('sampling_policy','lesion_centered'),'shape':('tensor_shape',[192]*3),'steps':('max_steps',121),'lr':('learning_rate',float('nan')),'bool_steps':('max_steps',True)}[fault]
        i['config'][f[0]]=f[1]
    with pytest.raises(ValueError):m.Session(i,c)

def test_sampler_full_epochs_and_evaluator_exclusion():
    c=m.config(steps=10);names=[m.next_member(c,k)[0] for k in range(10)]
    assert set(names[:5])==set(names[5:])==set(m.NAMES)
    assert names==[m.next_member(c,k)[0] for k in range(10)]
    assert 'synthetic_evaluator_not_optimizer' not in names
    with pytest.raises(ValueError):m.next_member(c,10)


def test_exact_resume_exposure_selection_and_foreign_input_denial(identity,tmp_path):
    i,c=identity;session=m.Session(i,c);session.evaluate();session.synthetic_update();session.evaluate()
    store=ArtifactStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    ref=m.publish_checkpoint(store,session);restored=m.resume(store,ref,i)
    assert m.progress(restored)==m.progress(session)
    assert torch.equal(session.predict(m.fixture('multiple')[0]),restored.predict(m.fixture('multiple')[0]))
    assert session.synthetic_update()==restored.synthetic_update()
    assert m.state_hash(session.model.state_dict())==m.state_hash(restored.model.state_dict())
    with pytest.raises(ValueError):session.update(m.fixture('sparse'))
    with pytest.raises(ValueError):session.import_weights(b'old checkpoint')
    with pytest.raises(TypeError):session.synthetic_update(m.fixture('sparse'))
    bad=deepcopy(ref);bad['receipt_sha256']='a'*64
    with pytest.raises(ValueError):m.resume(store,bad,i)


def test_partial_optimizer_failure_requires_reload(identity,monkeypatch):
    i,c=identity;s=m.Session(i,c);before=m.payload(s);old=s.optimizer.step
    def fail():old();raise RuntimeError('injected after optimizer but before commit')
    monkeypatch.setattr(s.optimizer,'step',fail)
    with pytest.raises(RuntimeError):s.synthetic_update()
    assert s.step==0 and s.dirty
    for call in (s.synthetic_update,lambda:m.payload(s),lambda:s.predict(m.fixture('sparse')[0])):
        with pytest.raises(ValueError,match='[Ii]nterrupt|[Ii]ncomplete|[Dd]irty'):call()
    restored=m.restore_payload(before,i);assert restored.synthetic_update()['completed_step']==1

@pytest.mark.parametrize('fault',['identity','extra','control','step0_weights','head','model_dtype','model_nan','opt_policy','opt_extra','opt_step','opt_variance','cpu_rng','mps_rng','state_step','history','exposure','sampler','best','eval_metric','negative_metric','component'])
def test_codec_semantic_faults_refused(identity,fault):
    i,c=identity;s=m.Session(i,c)
    if fault!='step0_weights':s.synthetic_update();s.evaluate()
    files=m.payload(s);files=deepcopy(files)
    if fault=='identity':files['identity.json']=b'{}'
    elif fault=='extra':files['old-localizer.pt']=b'x'
    elif fault=='control':files['inputs.json']=canonical({'real_case':'3'})
    elif fault in ('history','exposure','sampler','best','eval_metric','negative_metric','component'):
        p=json.loads(files['progress.json'])
        if fault=='history':p['history'][0]['member_id']='synthetic_evaluator_not_optimizer'
        elif fault=='exposure':p['exposure']['sparse']+=1
        elif fault=='sampler':p['sampler']['cursor']+=1
        elif fault=='best':p['best']=None
        elif fault=='eval_metric':p['evaluations'][0]['cases'][0]['metrics']['lesion']['dice']=.99
        elif fault=='negative_metric':p['evaluations'][0]['cases'][-1]['metrics']['lesion_false_positive_fraction']=0.99
        elif fault=='component':p['evaluations'][0]['cases'][0]['metrics']['components']=[]
        files['progress.json']=canonical(p)
    else:
        state=torch.load(BytesIO(files['state.pt']),weights_only=True)
        if fault=='step0_weights':next(iter(state['model'].values())).flatten()[0]+=1
        elif fault=='head':state['model']['weight']=state['model']['weight'][:2]
        elif fault=='model_dtype':state['model']['weight']=state['model']['weight'].double()
        elif fault=='model_nan':state['model']['weight'].flatten()[0]=float('nan')
        elif fault=='opt_policy':state['optimizer']['param_groups'][0]['lr']=.01
        elif fault=='opt_extra':state['optimizer']['state'][999]={}
        elif fault=='opt_step':next(iter(state['optimizer']['state'].values()))['step']+=1
        elif fault=='opt_variance':next(iter(state['optimizer']['state'].values()))['exp_avg_sq'].fill_(-1)
        elif fault=='cpu_rng':state['cpu_rng']=torch.zeros(3,dtype=torch.uint8)
        elif fault=='mps_rng':state['mps_rng']=torch.zeros(3,dtype=torch.uint8)
        elif fault=='state_step':state['step']=0
        st=BytesIO();torch.save(state,st);files['state.pt']=st.getvalue()
    with pytest.raises((ValueError,RuntimeError,KeyError)):m.decode(files,i)


def test_warm_start_rejected_even_with_refreshed_control_hash(identity):
    i,c=deepcopy(identity);init=json.loads(c['initialization.json']);init['mode']='prior_project';init['weight_imports']=['a'*64]
    c['initialization.json']=canonical(init);i['initialization_sha256']=digest(c['initialization.json'])
    with pytest.raises(ValueError,match='Warm'):m.Session(i,c)
    init['mode']='fresh_random_only';init['weight_imports']=[];init['initial_weights_sha256']='a'*64
    c['initialization.json']=canonical(init);i['initialization_sha256']=digest(c['initialization.json'])
    with pytest.raises(ValueError,match='scratch'):m.Session(i,c)


def test_rng_is_owned_and_external_rng_is_preserved(identity):
    i,c=identity;s=m.Session(i,c);s.synthetic_update();f=m.payload(s);r=m.restore_payload(f,i)
    external=torch.get_rng_state().clone();torch.rand(13);changed=torch.get_rng_state().clone()
    assert s.synthetic_update()==r.synthetic_update()
    assert torch.equal(torch.get_rng_state(),changed)
    assert torch.equal(s.cpu_rng,r.cpu_rng)


def test_failure_at_rng_commit_boundary_stays_dirty(identity,monkeypatch):
    from contextlib import contextmanager
    i,c=identity;s=m.Session(i,c)
    @contextmanager
    def bad():
        yield
        raise RuntimeError('injected RNG commit fault')
    monkeypatch.setattr(s,'rng_scope',bad)
    with pytest.raises(RuntimeError):s.synthetic_update()
    assert s.dirty and s.step==0 and s.history==[]
    with pytest.raises(ValueError):m.payload(s)


def test_weighted_candidate_independent_denominator_and_gradients():
    z=torch.zeros((1,3,1,1,3),requires_grad=True);y=torch.tensor([[[[0,1,2]]]])
    p=z.softmax(1)
    ce=-(p[0,0,0,0,0].log()+p[0,1,0,0,1].log()+16*p[0,2,0,0,2].log())/18
    dice=sum(1-(2*p[0,k,0,0,k]+1e-5)/(p[0,k].sum()+1+1e-5) for k in (1,2))/2
    oracle=ce+dice;actual=m.objective(z,y,m.LOSS_V2)
    assert torch.allclose(actual,oracle,atol=1e-7)
    assert torch.allclose(torch.autograd.grad(actual,z,retain_graph=True)[0],torch.autograd.grad(oracle,z)[0],atol=1e-7)
    neg=torch.zeros((1,3,1,1,3),requires_grad=True);target=torch.zeros((1,1,1,3),dtype=torch.long)
    assert torch.equal(m.objective(neg,target,m.LOSS),m.objective(neg,target,m.LOSS_V2))


def test_bool_exposure_refused(identity):
    i,c=identity;s=m.Session(i,c);s.synthetic_update();p=m.progress(s)
    n=s.history[0]['member_id'];p['exposure'][n]=True
    with pytest.raises(ValueError,match='types'):m.validate_progress(p,s.config)


def test_stronger_candidate_keeps_voxel_weight_denominator_and_finite_gradients():
    z=torch.zeros((1,3,1,1,3),requires_grad=True);y=torch.tensor([[[[0,1,2]]]])
    p=z.softmax(1);ce=-(p[0,0,0,0,0].log()+p[0,1,0,0,1].log()+256*p[0,2,0,0,2].log())/258
    dice=sum(1-(2*p[0,k,0,0,k]+1e-5)/(p[0,k].sum()+1+1e-5) for k in (1,2))/2
    assert torch.allclose(m.objective(z,y,m.LOSS_V3),ce+dice,atol=1e-7)
    grad=torch.autograd.grad(m.objective(z,y,m.LOSS_V3),z)[0]
    assert torch.isfinite(grad).all() and grad[0,2,0,0,2]<0


@pytest.mark.parametrize('size,steps,version',[(24,121,'segmenter-synthetic-config-1'),(24,361,'segmenter-synthetic-config-2'),(144,5,'segmenter-synthetic-config-1'),(144,360,'segmenter-synthetic-config-2')])
def test_extended_budget_cannot_widen_old_or_mps_envelope(size,steps,version):
    c=m.config(size=size,steps=steps);c['schema_version']=version
    with pytest.raises(ValueError):m.validate_config(c)
    m.validate_config(m.config(steps=360));m.validate_config(m.config(size=144,steps=4))


def test_final_cpu_duration_version_is_bounded():
    m.validate_config(m.config(steps=480))
    for size,steps,version in [(24,481,'segmenter-synthetic-config-3'),(24,480,'segmenter-synthetic-config-2'),(144,480,'segmenter-synthetic-config-3')]:
        c=m.config(size=size,steps=steps);c['schema_version']=version
        with pytest.raises(ValueError):m.validate_config(c)
