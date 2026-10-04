from copy import deepcopy
from pathlib import Path
import json
import numpy as np
import torch
import pytest
from src.data.localizer_preprocessing_v4 import preprocess
from src.data.manifest_records import canonical,digest
from src.training.twomm_cache import publish,DiskRoleCache,checked_binding
from src.training.twomm_adapter import patch_batch,pad_image,remove_padding,validate_config

@pytest.fixture
def fixture():
    torch.set_num_threads(2)
    recipe=json.loads(Path('configs/capstone/localizer-preprocessing-v4.json').read_text())
    y=np.zeros((12,13,14),np.uint8);y[3:8,4:9,2:8]=1
    base=preprocess(y.astype(np.float32)*300-100,np.diag([2.,2.,2.,1.]),recipe,target=y)
    class Dataset:
        def __init__(self,role):self.role=role;self.recipe=deepcopy(recipe);self.reads=0
        def __len__(self):return 1
        def descriptor(self,i):return dict(study_id=self.role+'-synthetic',operation=self.role,protected_role='train' if self.role=='optimizer' else 'validation',observations=['partial fixture'])
        def load(self,i,*,operation):
            assert operation==self.role;self.reads+=1;x=deepcopy(base);x['provenance']={'descriptor':self.descriptor(i)};return x
    ds={r:Dataset(r) for r in ('optimizer','evaluator')}
    b=dict(schema_version='twomm-cache-1',review_sha256='a'*64,bundle_sha256='b'*64,recipe=recipe,roles={r:[dict(descriptor=d.descriptor(0),transform_record=deepcopy(base['transform_record']))] for r,d in ds.items()})
    return ds,b

def make(tmp_path,fixture):
    ds,b=fixture;pin=digest(canonical(b));cp=publish(tmp_path,ds,b,pin);return DiskRoleCache(tmp_path,cp,b,pin),cp,pin

def config():return dict(schema_version='twomm-adapter-1',patch_size=[144]*3,seed=42,learning_rate=.0003,weight_decay=.00001,max_steps=4,loss_id='balanced_ce_dice_v1')

def test_complete_cache_roundtrip_and_copies(tmp_path,fixture):
    c,cp,pin=make(tmp_path,fixture);assert all(d.reads==1 for d in fixture[0].values())
    a=c.get('optimizer',0);a['image'].zero_();assert c.get('optimizer',0)['image'].sum()>0
    assert c.get('evaluator',0)['descriptor']['observations']==['partial fixture']
    assert DiskRoleCache(tmp_path,cp,fixture[1],pin).members('optimizer')==c.members('optimizer')

@pytest.mark.parametrize('fault',['role','member','recipe','transform','geometry','review'])
def test_bad_binding_refused_before_source(tmp_path,fixture,fault):
    ds,b=fixture;pin=digest(canonical(b))
    if fault=='role':b['roles']['optimizer'][0]['descriptor']['protected_role']='validation'
    if fault=='member':b['roles']['evaluator'][0]['descriptor']['study_id']=b['roles']['optimizer'][0]['descriptor']['study_id']
    if fault=='recipe':b['recipe']['spacing_mm']=[3.]*3
    if fault=='transform':b['roles']['optimizer'][0]['transform_record']['schema_version']='2.0.0'
    if fault=='geometry':b['roles']['optimizer'][0]['transform_record']['processed_affine'][0][0]=0
    if fault=='review':b['review_sha256']='c'*64
    with pytest.raises(ValueError):publish(tmp_path,ds,b,pin)
    assert not any(d.reads for d in ds.values())

@pytest.mark.parametrize('fault',['role','member','recipe','transform','geometry'])
def test_invalid_binding_even_with_recomputed_pin(tmp_path,fixture,fault):
    ds,b=fixture
    if fault=='role':b['roles']['optimizer'][0]['descriptor']['protected_role']='validation'
    if fault=='member':b['roles']['evaluator'][0]['descriptor']['study_id']=b['roles']['optimizer'][0]['descriptor']['study_id']
    if fault=='recipe':b['recipe']['spacing_mm']=[3.]*3
    if fault=='transform':b['roles']['optimizer'][0]['transform_record']['schema_version']='2.0.0'
    if fault=='geometry':b['roles']['optimizer'][0]['transform_record']['processed_affine'][0][0]=0
    with pytest.raises(ValueError):publish(tmp_path,ds,b,digest(canonical(b)))
    assert not any(d.reads for d in ds.values())

@pytest.mark.parametrize('fault',['bytes','missing','extra','symlink','completion','swap'])
def test_corrupted_persisted_cache_refused(tmp_path,fixture,fault):
    c,cp,pin=make(tmp_path,fixture);p=tmp_path/'optimizer-0000-image.npy'
    if fault=='bytes':p.write_bytes(b'bad')
    if fault=='missing':p.unlink()
    if fault=='extra':(tmp_path/'unexpected').write_text('x')
    if fault=='symlink':p.unlink();p.symlink_to(tmp_path/'evaluator-0000-image.npy')
    if fault=='completion':(tmp_path/'complete.json').write_text('{}')
    if fault=='swap':p.write_bytes((tmp_path/'optimizer-0000-label.npy').read_bytes())
    with pytest.raises(ValueError):DiskRoleCache(tmp_path,cp,fixture[1],pin)
    if fault in ('bytes','missing','symlink','swap'):
        with pytest.raises(ValueError):c.get('optimizer',0)

def test_interruption_never_publishes_or_implicitly_resumes(tmp_path,fixture):
    ds,b=fixture;pin=digest(canonical(b));n=0
    def guard():
        nonlocal n
        n+=1
        if n==4:raise RuntimeError('interrupted')
    with pytest.raises(RuntimeError):publish(tmp_path,ds,b,pin,guard=guard)
    assert not (tmp_path/'complete.json').exists()
    with pytest.raises(ValueError):DiskRoleCache(tmp_path,'c'*64,b,pin)
    with pytest.raises(ValueError):publish(tmp_path,ds,b,pin)

def test_free_floor_stops_before_write(tmp_path,fixture,monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr('src.training.twomm_cache.shutil.disk_usage',lambda p:SimpleNamespace(free=0))
    ds,b=fixture
    with pytest.raises(ValueError,match='free-space'):publish(tmp_path,ds,b,digest(canonical(b)))
    assert not (tmp_path/'complete.json').exists()

def test_sampler_resume_padding_and_validation_rejection(tmp_path,fixture):
    c,_,_=make(tmp_path,fixture);item=c.get('optimizer',0);cfg=config()
    a,b,t=patch_batch(item,cfg,step=2);aa,bb,tt=patch_batch(c.get('optimizer',0),cfg,step=2)
    assert torch.equal(a,aa) and torch.equal(b,bb) and t==tt and a.shape==(1,1,144,144,144)
    center=t['center_original_grid'];assert all(0<=n<s for n,s in zip(center,item['image'].shape[1:]))
    assert int(item['label'][(0,*center)])==t['center_class']
    padded,trace=pad_image(item['image'],cfg);assert torch.equal(remove_padding(padded,trace),item['image'])
    assert item['transform_record']==fixture[1]['roles']['optimizer'][0]['transform_record']
    with pytest.raises(ValueError,match='Validation'):patch_batch(c.get('evaluator',0),cfg,step=0)
    with pytest.raises(ValueError,match='budget'):patch_batch(item,cfg,step=4)

@pytest.mark.parametrize('shape',[(97,145,96),(145,147,149),(12,13,14)])
def test_asymmetric_padding_inverts(shape):
    x=torch.rand(1,*shape);p,t=pad_image(x,config());assert torch.equal(remove_padding(p,t),x)
    t['padding'][0]+=1
    with pytest.raises(ValueError):remove_padding(p,t)

@pytest.mark.parametrize('field,value',[('patch_size',[96]*3),('max_steps',301),('schema_version','unknown'),('loss_id','other')])
def test_adapter_config_refuses_unprepared_policy(field,value):
    c=config();c[field]=value
    with pytest.raises(ValueError):validate_config(c)

def test_payload_cap_before_source(tmp_path,fixture,monkeypatch):
    monkeypatch.setattr('src.training.twomm_cache.PAYLOAD_CAP',1)
    ds,b=fixture
    with pytest.raises(ValueError,match='payload cap'):publish(tmp_path,ds,b,digest(canonical(b)))
    assert not any(d.reads for d in ds.values())

def test_serialization_cap_does_not_publish(tmp_path,fixture,monkeypatch):
    ds,b=fixture
    # Allow binding metadata, but force oversized serializer output with bounded invented bytes.
    import src.training.twomm_cache as module
    original=module.np.save
    def bloated(stream,array,**kwargs):
        original(stream,array,**kwargs);stream.write(b'0'*(module.OVERHEAD_CAP+1))
    monkeypatch.setattr(module.np,'save',bloated)
    with pytest.raises(ValueError,match='serialization cap'):publish(tmp_path,ds,b,digest(canonical(b)))
    assert not (tmp_path/'complete.json').exists()

def test_loaded_transform_drift_refused(tmp_path,fixture):
    ds,b=fixture;original=ds['optimizer'].load
    def changed(*args,**kwargs):
        item=original(*args,**kwargs);item['transform_record']['processed_affine'][0][3]+=2;return item
    ds['optimizer'].load=changed
    with pytest.raises(ValueError,match='provenance/transform'):publish(tmp_path,ds,b,digest(canonical(b)))
    assert not (tmp_path/'complete.json').exists()

def test_missing_manifest_member_with_new_completion_pin_refused(tmp_path,fixture):
    _,cp,pin=make(tmp_path,fixture);p=tmp_path/'complete.json';m=json.loads(p.read_bytes());m['entries'].pop();raw=canonical(m);p.write_bytes(raw)
    with pytest.raises(ValueError,match='membership'):DiskRoleCache(tmp_path,digest(raw),fixture[1],pin)

def test_source_shape_not_silently_widened():
    from src.training.twomm_adapter import image_tensor
    x=torch.zeros(1,1,1,1).expand(1,257,257,257)
    with pytest.raises(ValueError,match='bounded'):image_tensor(x)
    x=torch.zeros(1,10,1000,1000)
    with pytest.raises(ValueError,match='padding voxel'):pad_image(x,config())

def test_read_only_role_api_and_mutation(tmp_path,fixture):
    c,_,_=make(tmp_path,fixture)
    with pytest.raises(ValueError):c.get('train',0)
    with pytest.raises(ValueError):c.get('optimizer',True)
    c._manifest['binding']['review_sha256']='e'*64
    with pytest.raises(ValueError,match='binding changed'):c.get('optimizer',0)
