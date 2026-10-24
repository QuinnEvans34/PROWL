"""Invented 144-cube actual-student KD check; no patient data or scientific run."""
from pathlib import Path
import json
import numpy as np
import torch
from src.data.manifest_records import canonical, digest
from src.data.segmenter_native_windows_v1 import geometry
from src.data.segmenter_teacher_cache_v1 import SCHEMA, identity_for, write_member, TeacherTargetStore
from src.training import segmenter_full_session_v1 as full
from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
from src.training.segmenter_distillation_session_v1 import DistillationSession
from src.training.segmenter_distillation_v1 import DistillationConfig

class Provider:
    def __init__(self):
        self.control=dict(train=['A','B'],validation=['V'],planned_focused_counts={'A':6,'B':6})
        self.pin=digest(canonical(self.control))
        native=geometry((144,)*3,np.eye(4))
        self.small=dict(geometry=native,parent_geometry=native,region_low=[0]*3,region_high=[144]*3,
            source_sha256=dict(ct='a'*64))
    def plan_next(self, request): pass
    def training_window(self,name,**kwargs):
        x=np.linspace(0,1,144**3,dtype=np.float32).reshape(1,144,144,144)
        y=np.zeros((144,)*3,np.uint8);y[30:110,30:110,30:110]=1;y[60:80,60:80,60:80]=2
        return x,y,dict(pad_low=[0]*3,normalized_shape=[144]*3),dict(origin=[0]*3,
            region_low=[0]*3,region_high=[144]*3,kind='synthetic',**kwargs)
    def cache_member(self,name): return None,self.small

def student(p):
    c=dict(max_steps=8,tensor_shape=[144]*3,seed=42,learning_rate=1e-4,weight_decay=1e-5,
        warmup_steps=0,lr_schedule='constant',loss_id=full.DICE_FOCAL)
    return FastVariedSession(full.Session(c,p.control,device='mps',initialization={'kind':'scratch'}))

def store(folder,p,create):
    common={k:'a'*64 for k in ('teacher_sha256','teacher_config_sha256','teacher_mapping_sha256','preprocessing_sha256')}
    common['control_sha256']=p.pin
    if create:
        folder.mkdir();members={}
        for name in p.control['train']:
            _,y,_,_=p.training_window(name)
            q=np.where(y==2,.9,.1).astype(np.float32)
            members[name]=write_member(folder,name,q,identity_for(name,p.small,common))
        (folder/'manifest.json').write_bytes(canonical(dict(schema=SCHEMA,complete=True,control_sha256=p.pin,members=members)))
    manifest=(folder/'manifest.json').read_bytes()
    return TeacherTargetStore(folder,digest(manifest),control=p.control,common_identity=common)

def compare(a,b):
    if isinstance(a,torch.Tensor):
        torch.testing.assert_close(a.cpu(),b.cpu(),rtol=1.3e-6,atol=1e-5);return
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:compare(a[k],b[k])
    elif isinstance(a,(list,tuple)):
        assert len(a)==len(b)
        for x,y in zip(a,b):compare(x,y)
    elif isinstance(a,float):assert abs(a-b)<=1e-5+1.3e-6*abs(b)
    else:assert a==b

def run(stage,destination,base):
    torch.set_num_threads(1);p=Provider()
    from scripts.diagnostics.qualify_distillation_mac import write
    if stage=='student':
        targets=store(destination/'targets',p,True)
        control=student(p)
        zero=DistillationSession(student(p),teacher_identity={'weights':{'sha256':'a'*64}},
            loss_config=DistillationConfig(max_weight=0),target_manifest_sha256=targets.pin)
        control.update(p);z=zero.update(p)
        compare(control.state(),zero.student.state())
        assert not z['teacher_accessed']
        del control,zero;torch.mps.empty_cache()
        s=DistillationSession(student(p),teacher_identity={'weights':{'sha256':'a'*64}},
            loss_config=DistillationConfig(ramp_updates=2),target_manifest_sha256=targets.pin)
        rows=[s.update(p,targets)]
        torch.save(s.state(),destination/'saved.pt')
        rows.append(s.update(p,targets));torch.save(s.state(),destination/'expected.pt')
        write(destination/'updates.json',rows)
        write(destination/'identity.json',s.identity)
        updates=4
    else:
        producer=base/'student-01';targets=store(producer/'targets',p,False)
        checkpoint=torch.load(producer/'saved.pt',weights_only=True,map_location='cpu')
        identity=checkpoint['identity']
        s=DistillationSession.restore(checkpoint,identity)
        row=s.update(p,targets)
        expected=torch.load(producer/'expected.pt',weights_only=True,map_location='cpu')
        compare(s.state(),expected);updates=1
        write(destination/'updates.json',[row])
    torch.mps.synchronize()
    write(destination/'result.json',dict(success=True,stage=stage,synthetic_updates=updates,
        actual_model='production SegResNet',device='mps',shape=[144]*3,patient_reads=0,
        scientific_updates=0,comparison_rtol=1.3e-6,comparison_atol=1e-5,
        comparison_scope='engineering tolerance; not bit-exact or long-run drift qualification',
        mps_driver_bytes=torch.mps.driver_allocated_memory(),training_ready=False))
