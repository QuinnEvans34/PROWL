from copy import deepcopy
from dataclasses import replace
import json

import numpy as np
import pytest
import torch

from src.data.manifest_records import canonical,digest
from src.data.segmenter_native_windows_v1 import geometry
from src.data.segmenter_physical_windows_v1 import physical_geometry,sample_window
from src.data.segmenter_teacher_cache_v1 import (
    SCHEMA,QUANTIZATION_ERROR,encode,identity_for,write_member,sample_field,TeacherTargetStore,
)
from src.training import segmenter_full_session_v1 as full
from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
from src.training.segmenter_distillation_v1 import DistillationConfig
from src.training.segmenter_distillation_session_v1 import DistillationSession,BoundDistillationSession,live_metrics


@pytest.fixture(autouse=True)
def isolated_cpu(monkeypatch):
    old=torch.get_num_threads();torch.set_num_threads(1)
    # Synthetic optimizer-path test; not a claim of real SegResNet qualification.
    monkeypatch.setattr(full,'build_model',lambda _:torch.nn.Conv3d(1,3,1))
    yield
    torch.set_num_threads(old)


def same(a,b):
    if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
    if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b


class Provider:
    def __init__(self):
        self.control=dict(train=['A','B'],validation=['V'],planned_focused_counts={'A':6,'B':6})
        self.pin=digest(canonical(self.control));self.requests=[]
        native=geometry((16,16,16),np.eye(4))
        self.small=dict(geometry=native,parent_geometry=native,region_low=[0,0,0],region_high=[16,16,16],
            source_sha256=dict(ct='a'*64))
    def plan_next(self,request):self.requests.append(request)
    def training_window(self,name,**kwargs):
        x=np.linspace(0,1,16**3,dtype=np.float32).reshape(1,16,16,16)
        y=np.zeros((16,)*3,np.uint8);y[3:13,3:13,3:13]=1;y[6:10,6:10,6:10]=2
        return x,y,dict(pad_low=[0]*3,normalized_shape=[16]*3),dict(origin=[0]*3,
            region_low=[0]*3,region_high=[16]*3,kind='synthetic',**kwargs)
    def cache_member(self,name):return None,self.small


def student(p):
    config=dict(max_steps=8,tensor_shape=[16]*3,seed=42,learning_rate=1e-4,weight_decay=1e-5,
        warmup_steps=0,lr_schedule='constant',loss_id=full.DICE_FOCAL)
    return FastVariedSession(full.Session(config,p.control,device='cpu',initialization={'kind':'scratch'}))


def store(tmp_path,p):
    common={k:'a'*64 for k in ('teacher_sha256','teacher_config_sha256','teacher_mapping_sha256','preprocessing_sha256')}
    common['control_sha256']=p.pin;members={}
    for name in p.control['train']:
        _,y,_,_=p.training_window(name)
        q=np.where(y==2,.9,.1).astype(np.float32)
        members[name]=write_member(tmp_path,name,q,identity_for(name,p.small,common))
    manifest=dict(schema=SCHEMA,complete=True,control_sha256=p.pin,members=members)
    (tmp_path/'manifest.json').write_bytes(canonical(manifest))
    return TeacherTargetStore(tmp_path,digest(canonical(manifest)),control=p.control,common_identity=common)


def kd(s,pin,weight=.1):
    return DistillationSession(s,teacher_identity={'weights':{'sha256':'a'*64}},
        loss_config=DistillationConfig(max_weight=weight,ramp_updates=2),target_manifest_sha256=pin)


def test_zero_kd_exact_optimizer_path_without_any_teacher(tmp_path):
    a,b=Provider(),Provider();control=student(a);candidate=kd(student(b),'0'*64,0)
    before=torch.get_rng_state().clone()
    for _ in range(3):
        x=control.update(a);y=candidate.update(b)
        assert x['loss']==y['loss'] and x['batch_sha256']==y['batch_sha256']
        assert not y['teacher_accessed'] and same(control.state(),candidate.student.state())
    assert a.requests==b.requests and torch.equal(before,torch.get_rng_state())


def test_positive_kd_checkpoint_cold_restore_next_update_exact(tmp_path):
    p=Provider();targets=store(tmp_path,p);s=kd(student(p),targets.pin)
    for _ in range(4):
        row=s.update(p,targets)
        assert row['loss']==pytest.approx(row['supervised_loss']+row['kd_weight']*row['kd_loss'],abs=2e-7)
        assert row['eligible_voxels']==16**3 and row['teacher_accessed']
    saved=tmp_path/'student.pt';torch.save(s.state(),saved)
    restored=DistillationSession.restore(torch.load(saved,weights_only=True),s.identity)
    assert same(s.state(),restored.state())
    a=s.update(p,targets);b=restored.update(Provider(),targets)
    assert a==b and same(s.state(),restored.state())
    facade=BoundDistillationSession(restored,targets)
    assert facade.raw is restored.raw and facade.control==p.control
    assert live_metrics(dict(event='update',utc_ms=1,**dict(a,step=25)))['train/kd_loss']==a['kd_loss']
    assert live_metrics(dict(event='native_case'))=={}


def test_wrong_target_pin_or_teacher_and_changed_loss_are_rejected(tmp_path):
    p=Provider();targets=store(tmp_path,p);s=kd(student(p),'0'*64)
    with pytest.raises(ValueError,match='Bound'):s.update(p,targets)
    assert s.step==0
    s=kd(student(p),targets.pin);targets.common['teacher_sha256']='b'*64
    with pytest.raises(ValueError,match='teacher differs'):s.update(p,targets)
    s.loss_config=replace(s.loss_config,max_weight=.2)
    with pytest.raises(ValueError,match='recipe'):s.state()


def test_restore_rejects_changed_teacher_target_or_ramp(tmp_path):
    p=Provider();s=kd(student(p),'0'*64);state=s.state()
    for field in ('teacher','target_manifest_sha256','loss'):
        changed=deepcopy(s.identity);changed[field]='changed'
        with pytest.raises(ValueError,match='identity'):DistillationSession.restore(state,changed)


def test_quantization_bound_and_no_binary_threshold():
    q=np.random.default_rng(42).random((16,16,16)).astype(np.float32)
    q[0,0,:3]=[0,.5,1]
    values,error=encode(q)
    assert error<=QUANTIZATION_ERROR and len(np.unique(values))>3000
    assert values[0,0,0]==0 and values[0,0,2]==65535
    for bad in (-.1,1.1,np.nan):
        q[0,0,0]=bad
        with pytest.raises(ValueError):encode(q)


@pytest.mark.parametrize('spacing',[(1,1,1),(.7,.8,2.3),(.5,3,4)])
@pytest.mark.parametrize('origin',[[0,0,0],[1,2,3]])
def test_local_teacher_sampling_matches_full_float_reference(spacing,origin):
    affine=np.diag([*spacing,1.]);native=geometry((20,24,32),affine);record=physical_geometry(native)
    values=np.random.default_rng(2).integers(0,65536,size=tuple(record['native_shape']),dtype=np.uint16)
    actual,valid=sample_field(values,record,origin,window=16)
    expected,_=sample_window(values.astype(np.float32)/65535.,record,origin,order=1,window=16)
    np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-7);assert valid.all()


def test_padding_and_invalid_origins_are_explicit():
    native=geometry((4,5,6),np.eye(4));record=physical_geometry(native)
    q,valid=sample_field(np.full((4,5,6),65535,np.uint16),record,[0,0,0],window=16)
    assert valid.sum()==120 and np.all(q[valid]==1) and np.all(q[~valid]==0)
    with pytest.raises(ValueError):sample_field(np.zeros((4,5,6),np.uint16),record,[-1,0,0])


def test_cache_rejects_protected_roles_missing_cases_and_mutation(tmp_path):
    p=Provider();targets=store(tmp_path,p);record=physical_geometry(p.small['geometry'])
    with pytest.raises(ValueError,match='Training'):targets.window('V',p.small,record,[0]*3)
    changed=deepcopy(p.small);changed['source_sha256']['ct']='b'*64
    with pytest.raises(ValueError,match='mismatch'):targets.window('A',changed,record,[0]*3)
    values,valid,_=targets.window('A',p.small,record,[0]*3,window=16);assert valid.all()
    with (tmp_path/'A.npz').open('ab') as stream:stream.write(b'changed')
    with pytest.raises(ValueError,match='payload'):targets.window('A',p.small,record,[0]*3)
    manifest=deepcopy(targets.manifest);manifest['members'].pop('B')
    (tmp_path/'manifest.json').write_bytes(canonical(manifest))
    with pytest.raises(ValueError,match='Incomplete'):
        TeacherTargetStore(tmp_path,digest(canonical(manifest)),control=p.control,common_identity=targets.common)


def test_no_cuda_context():assert not torch.cuda.is_initialized()


@pytest.mark.parametrize('field',['manifest','common','control','train'])
def test_mutated_in_memory_admission_cannot_bypass_disk_pin(tmp_path,field):
    p=Provider();targets=store(tmp_path,p)
    if field=='manifest':targets.manifest['members']['A']['max_quantization_error']=0
    elif field=='common':targets.common['preprocessing_sha256']='b'*64
    elif field=='control':targets.control['train'].append('V')
    else:targets.train.add('V')
    with pytest.raises(ValueError,match='in-memory'):
        targets.window('A',p.small,physical_geometry(p.small['geometry']),[0]*3,window=16)


def test_quantized_half_is_not_mistaken_for_confident_agreement(tmp_path):
    p=Provider();common={k:'a'*64 for k in ('teacher_sha256','teacher_config_sha256','teacher_mapping_sha256','preprocessing_sha256')}
    common['control_sha256']=p.pin;members={}
    for name in p.control['train']:
        members[name]=write_member(tmp_path,name,np.full((16,)*3,.5,np.float32),identity_for(name,p.small,common))
    manifest=dict(schema=SCHEMA,complete=True,control_sha256=p.pin,members=members)
    (tmp_path/'manifest.json').write_bytes(canonical(manifest))
    targets=TeacherTargetStore(tmp_path,digest(canonical(manifest)),control=p.control,common_identity=common)
    q,valid,info=targets.window('A',p.small,physical_geometry(p.small['geometry']),[0]*3,window=16)
    assert np.all(q==.5) and valid.all() and info['quantization_uncertain_voxels']==16**3
    row=kd(student(p),targets.pin).update(p,targets)
    assert row['eligible_voxels']==0 and row['kd_loss']==0
