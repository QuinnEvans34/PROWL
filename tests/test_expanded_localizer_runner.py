from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest
import torch
from src.data.localizer_preprocessing_v2 import preprocess
from src.data.manifest_records import canonical,digest
from src.training.expanded_localizer import RoleCache,scheduled_member,synthetic_update,evaluate_role,checkpoint,restore
from src.training.localizer import LocalizerSession

class Fixtures:
    def __init__(self,role,n=2,shape=16):
        self.role=role;self.n=n;self.shape=shape;self.reads=0
        self.recipe=json.loads(Path('configs/capstone/localizer-preprocessing-v2.json').read_bytes())
        self.recipe.update(spacing_mm=[1.]*3,minimum_shape=[16]*3)
    def __len__(self):return self.n
    def descriptor(self,i):return dict(study_id=f'{self.role}-{i}',operation=self.role,protected_role='train' if self.role=='optimizer' else 'validation')
    def load(self,i,*,operation):
        assert operation==self.role;self.reads+=1
        y=np.zeros((self.shape,)*3,np.uint8);y[3:9,4:10,2:8]=1
        item=preprocess(y.astype(np.float32)*300-100,np.eye(4),self.recipe,target=y)
        item['provenance']={'descriptor':self.descriptor(i)};return item

def fixture(n=2):return {r:Fixtures(r,n) for r in ('optimizer','evaluator')}
def identity(cache):return dict(schema_version='1.0.0',purpose='synthetic-expanded-verification',run_id='expanded-test',device='cpu',
    config=dict(patch_size=[16]*3,seed=42,learning_rate=.0003,weight_decay=.00001,max_steps=4,loss_id='balanced_ce_dice_v1'),
    inputs_sha256=digest(canonical(cache.inputs)),source_sha256='a'*64,environment_sha256='b'*64)

def test_cache_once_copies_and_schedule():
    ds=fixture(16);c=RoleCache(ds)
    assert ds['optimizer'].reads==ds['evaluator'].reads==16
    assert c.bytes==32*16**3*5
    assert [scheduled_member(c.inputs,i) for i in range(32)]==c.members('optimizer')*2
    x=c.get('optimizer',0);x['image'].zero_();assert c.get('optimizer',0)['image'].sum()>0
    with pytest.raises(ValueError):c.get('validation',0)
    c._items['optimizer'][0]['label'].zero_()
    with pytest.raises(ValueError,match='Cached input'):c.get('optimizer',0)

def test_cache_refuses_limit_role_and_provenance():
    with pytest.raises(ValueError,match='byte cap'):RoleCache(fixture(),max_bytes=1)
    ds=fixture();ds['evaluator']=ds['optimizer']
    with pytest.raises(ValueError,match='Wrong role'):RoleCache(ds)
    ds=fixture();old=ds['optimizer'].load
    def changed(*a,**kw):
        x=old(*a,**kw);x['provenance']['descriptor']['study_id']='wrong';return x
    ds['optimizer'].load=changed
    with pytest.raises(ValueError,match='Loaded member'):RoleCache(ds)

def test_resume_matches_uninterrupted_next_member_and_parameters():
    torch.set_num_threads(2);c=RoleCache(fixture());i=identity(c);s=LocalizerSession(i['config'])
    history=[synthetic_update(s,c,i)];files=checkpoint(s,c,i,history);resumed=restore(files,i)
    a=synthetic_update(s,c,i);b=synthetic_update(resumed,c,i)
    assert a==b and a['sampling']['member_id']=='optimizer-1'
    assert all(torch.equal(x,y) for x,y in zip(s.model.parameters(),resumed.model.parameters()))
    before=s.step;metrics=evaluate_role(s,c,i,'evaluator');assert s.step==before and len(metrics['cases'])==2
    assert all(r['study_id'].startswith('evaluator') for r in metrics['cases'])

@pytest.mark.parametrize('fault',['identity','inputs','history','missing','real_updates'])
def test_checkpoint_refuses_tampering(fault):
    torch.set_num_threads(2);c=RoleCache(fixture());i=identity(c);s=LocalizerSession(i['config'])
    h=[synthetic_update(s,c,i)];f=checkpoint(s,c,i,h)
    if fault=='identity':i['environment_sha256']='c'*64
    if fault=='inputs':f['inputs.json']=canonical({'roles':{}})
    if fault=='history':h[0]['sampling']['member_id']='evaluator-0';f['progress.json']=canonical(h)
    if fault=='missing':del f['state.pt']
    if fault=='real_updates':
        i['purpose']='qualified-expanded-forward-profile'
        with pytest.raises(ValueError,match='Real updates'):synthetic_update(s,c,i)
        with pytest.raises(ValueError,match='Real profile'):checkpoint(s,c,i,h)
        return
    with pytest.raises(ValueError):restore(f,i)

def test_expanded_checkpoint_artifact_roundtrip_and_corruption(tmp_path):
    from src.operations.artifact_store import ArtifactStore
    torch.set_num_threads(2);c=RoleCache(fixture());i=identity(c);s=LocalizerSession(i['config'])
    h=[synthetic_update(s,c,i)];files=checkpoint(s,c,i,h)
    store=ArtifactStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    def validate(f):return dict(step=restore(f,i).step,inputs_sha256=i['inputs_sha256'])
    metadata=dict(run_id=i['run_id'],stage_id='checkpoint',artifact_type='expanded-localizer-checkpoint',schema_version='1.0.0',component='expanded-localizer-v1',code_sha256=i['source_sha256'],parents=[i['inputs_sha256']],retention='verification',sensitivity='synthetic')
    pin,state=store.publish('expanded-checkpoint',derivation_sha256=digest(canonical(i)),files=files,metadata=metadata,validate=validate)
    loaded,_=store.resolve('expanded-checkpoint',receipt_sha256=pin,validate=validate)
    assert state=='published' and restore(loaded,i).step==1
    (tmp_path/digest(b'expanded-checkpoint')/'state.pt').write_bytes(b'interrupted-or-corrupt')
    with pytest.raises(ValueError):store.resolve('expanded-checkpoint',receipt_sha256=pin,validate=validate)
