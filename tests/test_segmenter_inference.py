from copy import deepcopy
from io import BytesIO
import json
import numpy as np
import pytest
import torch
from src.training import segmenter_inference_v1 as c
from src.data import segmenter_geometry_v1 as g
from src.data.source_inventory_records import content_hash
from src.data.manifest_records import digest,canonical

@pytest.fixture(scope='module')
def bundle():
    torch.set_num_threads(2)
    t=g.plan_geometry([24,24,24],np.eye(4),[[4,4,4],[20,20,20]],g.recipe(),source_identity=dict(study_id='invented',ct_sha256=digest(b'x')),roi_origin='provided_pancreas_reference')
    x=np.full((1,144,144,144),.5,np.float32);e=dict(study_id='invented',protected_role='train',transform=t,transform_sha256=content_hash(t),image_sha256=digest(c.array_bytes(x)))
    identity=c.make_identity([e],dict(source={'invented':'control'},environment={'device':'CPU test'},ancestry={'domain':'invented'}),run_id='test',domain='invented_profile')
    s=c.Session(identity);p=np.zeros((3,144,144,144),np.float32);p[0]=1;a,r=c.export(p,e);f=c.payload(s,x,p,[(a,r)])
    return identity,s,x,e,p,f

@pytest.mark.parametrize('field,value',[('task','pancreas_lesion_segmenter_synthetic_v1'),('domain','training'),('initial_weight_sha256','0'*64),('config',{'optimizer_allowed':True})])
def test_identity_cannot_relabel(bundle,field,value):
    v=deepcopy(bundle[0]);v[field]=value
    with pytest.raises((ValueError,KeyError)):c.checked_identity(v)

@pytest.mark.parametrize('extra',['optimizer','sampler','synthetic_controls','rng'])
def test_checkpoint_rejects_other_task_states(bundle,extra):
    f=dict(bundle[-1]);state=torch.load(BytesIO(f['state.pt']),weights_only=True);state[extra]={};b=BytesIO();torch.save(state,b);f['state.pt']=b.getvalue()
    with pytest.raises(ValueError):c.validate_payload(f,bundle[0])

def test_changed_weights_refused(bundle):
    f=dict(bundle[-1]);state=torch.load(BytesIO(f['state.pt']),weights_only=True);next(iter(state['weights'].values())).add_(.01);b=BytesIO();torch.save(state,b);f['state.pt']=b.getvalue()
    with pytest.raises(ValueError):c.validate_payload(f,bundle[0])

@pytest.mark.parametrize('fault',['target','role','held','image','transform','shape','dtype'])
def test_image_only_input_rejects_fault_before_forward(bundle,fault):
    identity,s,x,e,*_=bundle;v={k:deepcopy(z) for k,z in e.items() if k!='image_sha256'};v['image']=x.copy()
    if fault=='target':v['target']=np.zeros((144,)*3,np.uint8)
    if fault=='role':v['protected_role']='validation'
    if fault=='held':v['study_id']='held'
    if fault=='image':v['image'][0,0,0,0]=.1
    if fault=='transform':v['transform']['source_affine'][0][0]=2
    if fault=='shape':v['image']=x[:,:,:,:143]
    if fault=='dtype':v['image']=x.astype(np.float64)
    with pytest.raises(ValueError):s.predict(v)

@pytest.mark.parametrize('method',['step','import_weights'])
def test_training_import_closed(bundle,method):
    with pytest.raises(ValueError):getattr(bundle[1],method)()

@pytest.mark.parametrize('fault',['channels','nan','sum','negative','float64'])
def test_probabilities_reject_head_or_values(bundle,fault):
    p=bundle[4].copy()
    if fault=='channels':p=p[:2]
    if fault=='nan':p[0,0,0,0]=np.nan
    if fault=='sum':p[1]=.1
    if fault=='negative':p[1,0,0,0]=-.1
    if fault=='float64':p=p.astype(np.float64)
    with pytest.raises(ValueError):c.probabilities(p)

@pytest.mark.parametrize('pattern',['empty','dense','sparse','fragmented'])
def test_native_grid_and_outside_roi_independent_oracle(bundle,pattern):
    e=bundle[3];p=np.zeros((3,144,144,144),np.float32);p[0]=1
    if pattern=='dense':p[0]=0;p[2]=1
    if pattern=='sparse':p[:,60:84,60:84,60:84]=0;p[2,60:84,60:84,60:84]=1
    if pattern=='fragmented':p[:,::4,::4,::4]=0;p[2,::4,::4,::4]=1
    a,r=c.export(p,e)
    assert a.shape==(24,24,24) and a.dtype==np.uint8
    assert not a[:4].any() and not a[20:].any() and not a[:,:4].any() and not a[:,:,20:].any()
    if pattern=='empty':assert np.all(a==0)
    if pattern=='dense':assert np.all(a[4:20,4:20,4:20]==2)
    assert sum(r['class_counts'])==24**3

@pytest.mark.parametrize('name',['identity.json','state.pt','probe-image.npy','probe-probabilities.npy','exports.json','case-00-native.npy'])
def test_each_required_member_missing_refused(bundle,name):
    f=dict(bundle[-1]);f.pop(name)
    with pytest.raises(ValueError):c.validate_payload(f,bundle[0])

@pytest.mark.parametrize('fault',['truncated','trailing','dtype','shape'])
def test_header_first_refuses_bad_arrays(fault):
    raw=c.array_bytes(np.zeros((8,8,8),np.uint8))
    if fault=='truncated':raw=raw[:-1]
    if fault=='trailing':raw+=b'x'
    if fault=='dtype':raw=c.array_bytes(np.zeros((8,8,8),np.float32))
    if fault=='shape':raw=c.array_bytes(np.zeros((8,8,9),np.uint8))
    with pytest.raises(ValueError):c.decode_array(raw,[8,8,8],'uint8')

@pytest.mark.parametrize('fault',['role','affine','counts','outside','inverse'])
def test_export_control_and_outside_faults(bundle,fault):
    e=bundle[3];r=json.loads(bundle[-1]['exports.json'])[0];raw=bundle[-1]['case-00-native.npy']
    if fault=='role':r['protected_role']='validation'
    if fault=='affine':r['source_affine'][0][0]=2
    if fault=='counts':r['class_counts'][0]-=1
    if fault=='inverse':r['inverse']='nearest_before_argmax'
    if fault=='outside':
        a=np.zeros((24,24,24),np.uint8);a[0,0,0]=2;raw=c.array_bytes(a);r['native_sha256']=digest(raw);r['class_counts']=[24**3-1,0,1]
    with pytest.raises(ValueError):c.validate_export(raw,r,e)

def test_checkpoint_valid(bundle):
    assert c.validate_payload(bundle[-1],bundle[0])['completed_updates']==0

@pytest.mark.parametrize('fault',['two_channels','nan','mutating'])
def test_actual_forward_result_checks(bundle,monkeypatch,fault):
    identity,_,x,e,*_=bundle;s=c.Session(identity)
    def forward(v):
        if fault=='mutating':next(iter(s.model.parameters())).data.add_(.01)
        shape=(1,2 if fault=='two_channels' else 3,144,144,144)
        out=torch.zeros(shape)
        if fault=='nan':out[0,0,0,0,0]=float('nan')
        return out
    monkeypatch.setattr(s.model,'forward',forward);item={k:v for k,v in e.items() if k!='image_sha256'}|dict(image=x)
    with pytest.raises(ValueError):s.predict(item)

def test_forward_probability_and_weight_invariance(bundle,monkeypatch):
    identity,_,x,e,*_=bundle;s=c.Session(identity);before=c.state_hash(s.model.state_dict())
    monkeypatch.setattr(s.model,'forward',lambda v:torch.zeros((1,3,144,144,144)))
    p=s.predict({k:v for k,v in e.items() if k!='image_sha256'}|dict(image=x))
    np.testing.assert_allclose(p,np.full((3,144,144,144),1/3,np.float32),rtol=0,atol=0)
    assert c.state_hash(s.model.state_dict())==before
