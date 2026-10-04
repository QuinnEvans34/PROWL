from copy import deepcopy
from io import BytesIO
import pytest
import torch
from src.data.manifest_records import canonical, digest
from src.training import twomm_session as module
from src.training.twomm_session import Session, payload, decode, restore_payload, weight_digest
from test_twomm_cache_adapter import fixture, make, config


def identity(purpose='synthetic-recovery'):
    controls={n:canonical({'fixture':n}) for n in module.CONTROLS}
    i=dict(schema_version='twomm-session-1',run_id='twomm-session-test',purpose=purpose,
        device='cpu',config=config(),sampling_policy=module.POLICY,cache_receipt_sha256='a'*64,
        **{k:digest(controls[n]) for n,k in module.CONTROLS.items()})
    return i,controls

@pytest.fixture
def checkpoint():
    torch.set_num_threads(2)
    i,c=identity();s=Session(i)
    return i,payload(s,i,c)


def test_zero_checkpoint_exact_and_rng_preserved(checkpoint):
    i,f=checkpoint;before=torch.get_rng_state().clone()
    a,_=decode(f,i);b=restore_payload(f,i)
    assert weight_digest(a)==weight_digest(b) and a.step==0
    assert torch.equal(before,torch.get_rng_state())

@pytest.mark.parametrize('fault',['identity','control','extra','version','step','bool_step','scheduler',
    'optimizer','state_extra','model_dtype','model_nan','rng','history'])
def test_bad_checkpoint_refused(checkpoint,fault):
    i,f=checkpoint;f=deepcopy(f)
    if fault=='identity':f['identity.json']=b'{}'
    elif fault=='control':f['source.json']=b'changed'
    elif fault=='extra':f['extra']=b'x'
    else:
        state=torch.load(BytesIO(f['state.pt']),weights_only=True)
        if fault=='version':state['schema_version']='1.0.0'
        if fault=='step':state['step']=5
        if fault=='bool_step':state['step']=False
        if fault=='scheduler':state['scheduler']['T_max']=5
        if fault=='optimizer':state['optimizer']['param_groups'][0]['maximize']=True
        if fault=='state_extra':state['optimizer']['state'][999]={}
        if fault=='model_dtype':
            k=next(iter(state['model']));state['model'][k]=state['model'][k].double()
        if fault=='model_nan':next(iter(state['model'].values())).flatten()[0]=float('nan')
        if fault=='rng':state['cpu_rng']=torch.zeros(3,dtype=torch.uint8)
        if fault=='history':state['step']=1
        stream=BytesIO();torch.save(state,stream);f['state.pt']=stream.getvalue()
    with pytest.raises((ValueError,RuntimeError)):decode(f,i)


def test_real_updates_and_external_synthetic_inputs_refused():
    i,_=identity('qualified-cache-inference');s=Session(i)
    with pytest.raises(ValueError):s.synthetic_update()
    with pytest.raises(ValueError):s.update(None)
    with pytest.raises(TypeError):s.synthetic_update(torch.zeros(1))


def test_unpadding_prediction_has_original_grid(monkeypatch):
    i,_=identity();s=Session(i)
    seen=[]
    def fake(x,roi,batch,model,**kw):
        seen.append((x.shape,roi,kw));return torch.cat([x,x+1],dim=1)
    monkeypatch.setattr(module,'sliding_window_inference',fake)
    p,t=s.predict(torch.ones((1,96,150,100),dtype=torch.float32))
    assert p.shape==(2,96,150,100) and seen[0][0]==(1,1,144,150,144)
    assert torch.allclose(p.sum(0),torch.ones_like(p[0]))


def test_cache_exact_binding_and_roles(tmp_path,fixture,monkeypatch):
    cache,cp,pin=make(tmp_path,fixture);i,_=identity('qualified-cache-inference')
    i.update(inputs_sha256=pin,cache_receipt_sha256=cp);s=Session(i)
    monkeypatch.setattr(s,'predict',lambda x:(x,{}))
    assert s.predict_cache(cache,'evaluator',0)[2]['operation']=='evaluator'
    s.identity['inputs_sha256']='b'*64
    with pytest.raises(ValueError,match='binding'):s.predict_cache(cache,'optimizer',0)
    s.identity['inputs_sha256']=pin;(tmp_path/'complete.json').write_bytes(b'{}')
    with pytest.raises(ValueError,match='completion'):s.predict_cache(cache,'optimizer',0)


def test_nonzero_checkpoint_next_update_replay_with_small_test_model(monkeypatch):
    # Codec/scheduler/optimizer continuation test; native rehearsal uses the actual network and144³.
    monkeypatch.setattr(module,'build_model',lambda c:torch.nn.Conv3d(1,2,1))
    monkeypatch.setattr(module,'patch_batch',lambda item,c,step:(torch.ones(1,1,8,8,8),
        torch.ones(1,1,8,8,8,dtype=torch.long),{'step':step}))
    i,c=identity();s=Session(i);s.synthetic_update();f=payload(s,i,c)
    restored=restore_payload(f,i);a=s.synthetic_update();b=restored.synthetic_update()
    assert a==b and weight_digest(s)==weight_digest(restored)
    bad=deepcopy(i);bad['purpose']='qualified-cache-inference'
    state=torch.load(BytesIO(f['state.pt']),weights_only=True);state['identity_sha256']=digest(canonical(bad))
    stream=BytesIO();torch.save(state,stream);f.update({'state.pt':stream.getvalue(),'identity.json':canonical(bad)})
    with pytest.raises(ValueError,match='has updates'):decode(f,bad)
