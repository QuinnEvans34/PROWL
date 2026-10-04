from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.data.cohort_registry import COHORT_ID,MEMBERS
from src.data.localizer_preprocessing import preprocess
from src.training.localizer import LocalizerSession
from src.training.localizer_smoke import execute,probability_metrics,learning_observed,validate_terminal,validate_controls
from src.training.localizer_run import input_record,validate_payload
from src.operations.artifact_store import ArtifactStore


class FixtureDataset:
    def __init__(self,size=16):
        self.recipe=json.loads(Path('configs/capstone/localizer-preprocessing-v1.json').read_bytes())
        self.recipe['minimum_shape']=[size]*3
        self.descriptors=[dict(study_id=s,cohort_id=COHORT_ID) for s in MEMBERS]
        self.size=size;self.reads=[]
    def __getitem__(self,index):
        self.reads.append(index);s=self.size;y=np.zeros((s,s,s),np.uint8);y[s//3:2*s//3,s//3:2*s//3,s//3:2*s//3]=1
        value=preprocess((y*200).astype(np.float32),np.diag([3,3,3,1]),self.recipe,target=y)
        value['provenance']=deepcopy(self.descriptors[index]);return value
    def __len__(self):return 2


def bundle(size=16,steps=2,device='cpu'):
    data=FixtureDataset(size);cfg=dict(patch_size=[size]*3,seed=42,learning_rate=.003,weight_decay=.00001,max_steps=steps)
    plan=dict(schema_version='1.0.0',experiment_id='synthetic-executor',config=cfg,member_ids=MEMBERS,checkpoint_every=1,update_seconds=600,total_seconds=1200)
    controls={'inputs.json':canonical(input_record(data)),'source.json':b'{}','environment.json':b'{}','plan.json':canonical(plan)}
    identity=dict(schema_version='3.0.0',run_id='localizer-smoke-fixture',purpose='bounded-localizer-smoke',training_data='synthetic',device=device,config=cfg,
        **{key:digest(controls[name]) for name,key in [('inputs.json','inputs_sha256'),('source.json','source_sha256'),('environment.json','environment_sha256'),('plan.json','plan_sha256')]})
    authorization=dict(bindings={k:v for k,v in identity.items() if k.endswith('_sha256')},allowed=True,data_mode='synthetic',operation='synthetic_executor_check',authority='D-274')
    controls['authorization.json']=canonical(authorization);identity['authorization_sha256']=digest(controls['authorization.json'])
    return data,identity,controls


def test_full_executor_before_after_checkpoints_exports(tmp_path):
    torch.set_num_threads(2);data,identity,controls=bundle();session=LocalizerSession(identity['config']);events=[]
    store=ArtifactStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    result,ref=execute(session,data,identity,controls,store,event=events.append)
    files,_=store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=lambda f:validate_terminal(f,identity))
    assert result['completed_steps']==2 and data.reads==[0,1,0,1,0,1]
    assert [r['step'] for r in result['checkpoint_references']]==[0,1,2]
    assert set(k for k in files if k.endswith('.nii.gz'))=={f'{p}-PanTS_{i:08}.nii.gz' for p in ('before','after') for i in (3,26)}
    assert events[-1]['state']=='terminal_published'
    changed=dict(files);report=json.loads(changed['result.json']);report['completed_steps']=3;changed['result.json']=canonical(report)
    with pytest.raises(ValueError):validate_terminal(changed,identity)


def test_probability_metric_independent_oracle():
    p=torch.tensor([[[[.8,.3]]],[[[.2,.7]]]])
    target=torch.tensor([[[[0,1]]]])
    m=probability_metrics(p,target,np.diag([2,3,4,1]))
    ce=-(np.log(.8)+np.log(.7))/2
    soft=1-(2*.7+1e-5)/(.2+.7+1+1e-5)
    assert m['loss']==pytest.approx(ce+soft,abs=1e-6) and m['dice']==1 and m['predicted_volume_mm3']==pytest.approx(24)
    empty=probability_metrics(p,torch.zeros_like(target),np.eye(4))
    assert empty['dice'] is None and empty['predicted_foreground']==1


@pytest.mark.parametrize('value',[float('nan'),-1.,2.])
def test_bad_probabilities_refused(value):
    p=torch.zeros(2,2,2,2);p[0]=value
    with pytest.raises(ValueError):probability_metrics(p,torch.zeros(1,2,2,2),np.eye(4))


def test_authorization_refuses_before_reads(tmp_path):
    data,identity,controls=bundle();a=json.loads(controls['authorization.json']);a['allowed']=False
    controls['authorization.json']=canonical(a);identity['authorization_sha256']=digest(controls['authorization.json'])
    with pytest.raises(ValueError,match='Unapproved'):execute(LocalizerSession(identity['config']),data,identity,controls,None)
    assert data.reads==[]


def test_budget_failure_preserves_checkpoint_and_failure(tmp_path):
    data,identity,controls=bundle();events=[];store=ArtifactStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    times=iter([0,0,0,1300])
    with pytest.raises(ValueError,match='Total time'):execute(LocalizerSession(identity['config']),data,identity,controls,store,event=events.append,clock=lambda:next(times))
    assert events[-1]['state']=='failed_or_interrupted' and events[-1]['last_complete_checkpoint']['step']==0


def test_null_learning_is_not_execution_failure():
    assert not learning_observed(dict(mean_loss=1,mean_dice=.2),dict(mean_loss=1.2,mean_dice=.1))
    assert learning_observed(dict(mean_loss=1,mean_dice=.2),dict(mean_loss=.8,mean_dice=.4))
    assert not learning_observed(dict(mean_loss=1,mean_dice=None),dict(mean_loss=.5,mean_dice=.8))


def test_launch_pending_rejected_without_environment_or_payload_access(tmp_path,monkeypatch):
    import scripts.diagnostics.localizer_smoke_run as cli
    root=tmp_path/'output';root.mkdir();request=root/'request';request.mkdir();monkeypatch.setattr(cli,'OUTPUT',root)
    data,identity,controls=bundle()
    needed={n:v for n,v in controls.items() if n!='authorization.json'}
    for n,v in needed.items():(request/n).write_bytes(v)
    req=canonical(dict(files={n:digest(v) for n,v in needed.items()},bindings=json.loads(controls['authorization.json'])['bindings']))
    (request/'request.json').write_bytes(req)
    auth=json.loads(controls['authorization.json']);auth.update(allowed=False,operation='launch_CAP-EXP-001',authority='Quinton Evans',data_mode='qualified_cohort')
    approval=request/'pending.json';approval.write_bytes(canonical(auth))
    monkeypatch.setattr(cli,'capture',lambda:(_ for _ in ()).throw(AssertionError('early environment access')))
    with pytest.raises(ValueError,match='not authorized'):cli.checked_request(request,digest(req),approval,digest(approval.read_bytes()))


def test_failed_checkpoint_preserves_prior_complete_without_terminal(tmp_path):
    data,identity,controls=bundle();events=[]
    store=ArtifactStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    publish=store.publish
    calls=[]
    def failing_publish(*args,**kwargs):
        calls.append(args[0])
        if len(calls)==2:raise OSError('injected persistence failure')
        return publish(*args,**kwargs)
    store.publish=failing_publish
    with pytest.raises(OSError,match='persistence'):
        execute(LocalizerSession(identity['config']),data,identity,controls,store,event=events.append)
    failure=events[-1]
    assert failure['state']=='failed_or_interrupted' and failure['completed_steps']==1
    assert failure['last_complete_checkpoint']['step']==0
    assert not any(e['state']=='terminal_published' for e in events)
    ref=failure['last_complete_checkpoint']
    assert store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=lambda f:validate_payload(f,identity))[0]


def test_real_scope_cannot_inherit_synthetic_authorization():
    _,identity,controls=bundle(device='mps')
    identity['training_data']='qualified_cohort'
    with pytest.raises(ValueError,match='authorization'):validate_controls(controls,identity)
    auth=json.loads(controls['authorization.json']);auth['data_mode']='qualified_cohort'
    controls['authorization.json']=canonical(auth);identity['authorization_sha256']=digest(controls['authorization.json'])
    with pytest.raises(ValueError,match='Real launch scope'):validate_controls(controls,identity)


def test_slow_input_stops_before_optimizer_when_update_budget_expires(tmp_path):
    torch.set_num_threads(2);_,identity,controls=bundle();now=[0.];events=[]
    class SlowDataset(FixtureDataset):
        def __getitem__(self,index):
            item=super().__getitem__(index)
            if len(self.reads)==3:now[0]=601.
            return item
    data=SlowDataset();session=LocalizerSession(identity['config'])
    store=ArtifactStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    with pytest.raises(ValueError,match='Update time budget'):
        execute(session,data,identity,controls,store,clock=lambda:now[0],event=events.append)
    assert session.step==0 and data.reads==[0,1,0]
    assert events[-1]['last_complete_checkpoint']['step']==0
