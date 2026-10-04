from copy import deepcopy
from io import BytesIO
import json
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.training import segmenter_balanced_session_v1 as m,segmenter_session_v1 as old
from src.training.segmenter_balanced_loss_v1 import objective,LOSS

@pytest.mark.parametrize('codes',[[0]*8,[1]*8,[2]*8,[0,1,1,1,1,1,1,2],[2,1,0,0,0,0,0,0],[0,0,0,2,0,0,0,0]])
def test_independent_scalar_and_gradient(codes):
    z=torch.randn(1,3,2,2,2,generator=torch.Generator().manual_seed(3),dtype=torch.float64,requires_grad=True)
    y=torch.tensor(codes).reshape(1,2,2,2);p=z.softmax(1);weight=torch.tensor([1.,64.,256.],dtype=z.dtype)
    truth=torch.nn.functional.one_hot(y,3).movedim(-1,1);selected=(p*truth).sum(1)
    ce=-(weight[y]*selected.log()).sum()/weight[y].sum();ds=[]
    for k in (1,2):
        t=(y==k).double()
        if t.any():ds.append(1-(2*(p[:,k]*t).sum()+1e-5)/(p[:,k].sum()+t.sum()+1e-5))
    expected=ce+(torch.stack(ds).mean() if ds else p.sum()*0);actual=objective(z,y)
    assert torch.allclose(actual,expected,atol=1e-12,rtol=0)
    assert torch.allclose(torch.autograd.grad(actual,z,retain_graph=True)[0],torch.autograd.grad(expected,z)[0],atol=1e-12,rtol=0)

def test_batch_present_class_reduction_and_old_loss_difference():
    z=torch.zeros(2,3,2,2,2,requires_grad=True);y=torch.zeros(2,2,2,2,dtype=torch.long);y[1,0,0,0]=1;y[1,1,1,1]=2
    expected=(objective(z[:1],y[:1])-torch.nn.functional.cross_entropy(z[:1],y[:1])+objective(z[1:],y[1:])-torch.nn.functional.cross_entropy(z[1:],y[1:],weight=z.new_tensor([1,64,256])))/2
    ce=torch.nn.functional.cross_entropy(z,y,weight=z.new_tensor([1,64,256]))
    assert torch.allclose(objective(z,y),ce+expected,atol=1e-6)
    z2=z.detach().clone();z2[:,1]=1.7
    assert not torch.allclose(objective(z2,y),old.objective(z2,y,old.LOSS_V3))

@pytest.fixture
def identity(monkeypatch):
    torch.set_num_threads(2);monkeypatch.setattr(m,'build_model',lambda c:torch.nn.Conv3d(1,3,1))
    return m.make_identity(m.config(steps=10),{n:canonical({'fixture':n}) for n in ('source.json','environment.json','geometry.json')},run_id='segmenter-balanced-synthetic-test',device='cpu')

@pytest.mark.parametrize('fault',['old_loss','old_task','old_schema','real_mode','shape','steps','nonfinite_rate','bool_steps','warm_init'])
def test_identity_isolation(identity,fault):
    i,c=deepcopy(identity)
    if fault=='old_loss':i['config']['loss_id']=old.LOSS_V3
    elif fault=='old_task':i['task']=old.TASK
    elif fault=='old_schema':i['schema_version']='segmenter-synthetic-session-1'
    elif fault=='real_mode':i['data_mode']='qualified_real_cache'
    elif fault=='shape':i['config']['tensor_shape']=[192]*3
    elif fault=='steps':i['config']['max_steps']=481
    elif fault=='nonfinite_rate':i['config']['learning_rate']=float('nan')
    elif fault=='bool_steps':i['config']['max_steps']=True
    else:
        init=json.loads(c['initialization.json']);init['mode']='old_project';c['initialization.json']=canonical(init);i['initialization_sha256']=digest(c['initialization.json'])
    with pytest.raises(ValueError):m.Session(i,c)


def test_exact_restart_and_old_codec_isolation(identity):
    i,c=identity;s=m.Session(i,c);s.evaluate();s.synthetic_update();files=m.payload(s);r=m.restore_payload(files,i)
    assert s.synthetic_update()==r.synthetic_update()
    assert m.state_hash(s.model.state_dict())==m.state_hash(r.model.state_dict())
    assert m.progress(s)==m.progress(r)
    with pytest.raises(ValueError):old.decode(files,i)
    oldi,oldc=old.make_identity(old.config(steps=10),{n:canonical({'fixture':n}) for n in ('source.json','environment.json','geometry.json')},run_id='segmenter-synthetic-legacy-test',device='cpu')
    oldmodel=old.Session(oldi,oldc);legacy=old.payload(oldmodel)
    assert old.decode(legacy,oldi).step==0
    with pytest.raises(ValueError):m.decode(legacy,oldi)
    for call in (lambda:s.update(m.fixture('sparse')),lambda:s.import_weights(b'weights')):
        with pytest.raises(ValueError):call()


def test_dirty_step_and_checkpoint_refusal(identity,monkeypatch):
    i,c=identity;s=m.Session(i,c);before=m.payload(s);step=s.optimizer.step
    def fail():step();raise RuntimeError('injected post-mutation')
    monkeypatch.setattr(s.optimizer,'step',fail)
    with pytest.raises(RuntimeError):s.synthetic_update()
    assert s.dirty and s.step==0
    for f in (s.synthetic_update,lambda:m.payload(s),lambda:s.predict(m.fixture('sparse')[0])):
        with pytest.raises(ValueError):f()
    assert m.restore_payload(before,i).synthetic_update()['completed_step']==1

@pytest.mark.parametrize('fault',['loss','nonfinite','code','dtype','channels','empty'])
def test_bad_objective_refused(fault):
    z=torch.ones(1,3,2,2,2);y=torch.zeros(1,2,2,2,dtype=torch.long);loss=LOSS
    if fault=='loss':loss=old.LOSS_V3
    if fault=='nonfinite':z[0,0,0,0,0]=float('inf')
    if fault=='code':y[0,0,0,0]=3
    if fault=='dtype':y=y.float()
    if fault=='channels':z=z[:,:2]
    if fault=='empty':z=z[:0];y=y[:0]
    with pytest.raises(ValueError):objective(z,y,loss)

@pytest.mark.parametrize('fault',['optimizer_step','rng','target_role','state_identity','variance','extra_payload'])
def test_checkpoint_faults_refused(identity,fault):
    i,c=identity;s=m.Session(i,c);s.synthetic_update();files=m.payload(s)
    if fault=='extra_payload':files['external.pt']=b'extra'
    elif fault=='target_role':files['inputs.json']=canonical({'evaluator':'optimizer'})
    else:
        state=torch.load(BytesIO(files['state.pt']),weights_only=True)
        if fault=='optimizer_step':next(iter(state['optimizer']['state'].values()))['step']+=1
        elif fault=='variance':next(iter(state['optimizer']['state'].values()))['exp_avg_sq'].fill_(-1)
        elif fault=='rng':state['cpu_rng']=torch.zeros(3,dtype=torch.uint8)
        elif fault=='state_identity':state['identity_sha256']='a'*64
        b=BytesIO();torch.save(state,b);files['state.pt']=b.getvalue()
    with pytest.raises((ValueError,RuntimeError)):m.decode(files,i)

@pytest.fixture
def cli(monkeypatch,tmp_path):
    from scripts.diagnostics import segmenter_balanced_qualification as q
    monkeypatch.setattr(m,'build_model',lambda c:torch.nn.Conv3d(1,3,1))
    monkeypatch.setattr(q,'DEST',tmp_path/'diagnostic')
    monkeypatch.setattr(q,'context',lambda:{n:canonical({'fixture':n}) for n in ('source.json','environment.json','geometry.json')})
    monkeypatch.setattr(q,'pins',lambda:{'code':'a'*64})
    monkeypatch.setattr(q.a.c,'runtime',lambda:{'invented':'runtime'})
    return q


def test_request_persisted_pin_and_exclusive_creation(cli,capsys):
    cli.prepare();pin=capsys.readouterr().out.strip()
    assert pin==digest((cli.DEST/'request.json').read_bytes())
    assert cli.checked(pin)['total_synthetic_optimizer_calls']==960
    with pytest.raises(FileExistsError):cli.prepare()

@pytest.mark.parametrize('field',['bars','limits','loss','real','code','calls'])
def test_request_envelope_tampering(cli,field):
    cli.DEST.mkdir();r=cli.request()
    if field=='bars':r['bars']=dict(r['bars'],positive_lesion_dice=0)
    elif field=='limits':r['limits']=dict(r['limits'],trajectory_seconds=1000)
    elif field=='loss':r['identity']['config']['loss_id']=old.LOSS_V3
    elif field=='real':r['real_inputs_allowed']=True
    elif field=='code':r['source_pins']={'code':'b'*64}
    else:r['total_synthetic_optimizer_calls']=961
    from scripts.diagnostics.segmenter_source_verification import put
    put(cli.DEST/'request.json',r)
    with pytest.raises(ValueError):cli.checked(digest((cli.DEST/'request.json').read_bytes()))


def test_saved_payload_refuses_changed_bytes(cli):
    cli.DEST.mkdir();r=cli.request();s=m.Session(r['identity'],{n:v.encode() for n,v in r['controls'].items()});s.synthetic_update()
    ref=cli.save(s,'test');assert cli.load(ref,r['identity']).step==1
    p=cli.DEST/'test--state.pt';raw=p.read_bytes();p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
    with pytest.raises(ValueError):cli.load(ref,r['identity'])
