from copy import deepcopy
import json
import numpy as np
import pytest
import torch
from tests.test_expanded_localizer_runner import fixture,identity
from src.training.expanded_localizer import RoleCache
from src.training.expanded_executor import execute,metrics,validate_terminal,validate_controls,validate_checkpoint
from src.training.localizer import LocalizerSession
from src.data.manifest_records import canonical,digest
from src.operations.artifact_store import ArtifactStore


def setup(tmp_path):
    torch.set_num_threads(2);cache=RoleCache(fixture());ident=identity(cache)
    ident.update(schema_version='2.0.0',purpose='synthetic-expanded-executor')
    plan=dict(experiment_id='synthetic',config=ident['config'],evaluation_steps=[0,2,4],checkpoint_steps=[0,2,4],total_seconds=1200,update_seconds=600,margin_mm=10,export_final=True)
    ident['plan_sha256']=digest(canonical(plan))
    approval=dict(allowed=True,operation='synthetic_executor_verification',bindings={k:ident[k] for k in ('inputs_sha256','source_sha256','environment_sha256','plan_sha256')})
    return cache,ident,plan,approval,ArtifactStore(tmp_path,check_root=lambda:None,minimum_free_bytes=0)


def test_complete_cpu_transaction_and_corrupt_export(tmp_path):
    c,i,p,a,s=setup(tmp_path);result,ref=execute(LocalizerSession(i['config']),c,i,p,a,s)
    assert result['completed_steps']==4 and len(result['exports'])==4
    files,_=s.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=lambda f:validate_terminal(f,i,s))
    assert [t['step'] for t in json.loads(files['trajectory.json'])]==[0,2,4]
    for t in json.loads(files['trajectory.json']):
        for role in ('optimizer','evaluator'):
            for row in t['metrics'][role]['cases']:
                assert row['source_crop_geometry']['schema_version']=='source-crop-geometry-v1'
                assert row['source_size_diagnostic_pass']==(row['source_crop_geometry']['scan_fraction'] is not None and 0<row['source_crop_geometry']['scan_fraction']<=.25)
                assert row['scan_fraction_scope'].startswith('padded_processed_tensor')
    case=result['exports'][0]['reference'];(tmp_path/digest(case['artifact_id'].encode())/'prediction.nii.gz').write_bytes(b'broken')
    with pytest.raises(ValueError):validate_terminal(files,i,s)


def test_interrupt_preserves_last_checkpoint_no_terminal(tmp_path):
    c,i,p,a,s=setup(tmp_path);events=[]
    def event(row):
        events.append(row)
        if row['state']=='update_complete' and row['completed_step']==3:raise KeyboardInterrupt('injected')
    with pytest.raises(KeyboardInterrupt):execute(LocalizerSession(i['config']),c,i,p,a,s,event=event)
    fail=events[-1];assert fail['state']=='failed_or_interrupted' and fail['completed_steps']==3
    cp=fail['last_complete_checkpoint'];files,_=s.resolve(cp['artifact_id'],receipt_sha256=cp['receipt_sha256'],validate=lambda f:validate_checkpoint(f,i))
    assert validate_checkpoint(files,i)['step']==2
    assert not (tmp_path/digest((i['run_id']+':terminal').encode())).exists()

@pytest.mark.parametrize('fault',['denied','binding','plan','real','resume'])
def test_refusal_before_updates(tmp_path,fault):
    c,i,p,a,s=setup(tmp_path);session=LocalizerSession(i['config'])
    if fault=='denied':a['allowed']=False
    if fault=='binding':a['bindings']['inputs_sha256']='0'*64
    if fault=='plan':p['margin_mm']=9
    if fault=='real':i['purpose']='qualified-expanded-executor'
    if fault=='resume':session.step=1
    with pytest.raises(ValueError):execute(session,c,i,p,a,s)
    assert not list(tmp_path.glob('*/complete.json'))


def test_empty_exact_and_fragmented_metrics():
    y=np.zeros((32,32,32),np.uint8);y[8:16,8:16,8:16]=1
    empty=metrics(np.zeros_like(y),y,np.eye(4));assert empty['localization_state']=='failed_empty_localization' and empty['box'] is None and empty['recall']==0
    exact=metrics(y,y,np.eye(4));assert exact['dice']==exact['precision']==exact['recall']==1
    # Fragmentation must not lose the case or prevent all-component box reporting.
    p=np.zeros((48,48,48),np.uint8);p[::2,::2,::2]=1
    large=metrics(p,np.ones_like(p),np.eye(4));assert large['component_count']>4096 and large['box'] is not None and large['component_detail_state']=='budget_exceeded'


def test_time_stop_has_no_success_terminal(tmp_path):
    c,i,p,a,s=setup(tmp_path);events=[];ticks=iter([0,0,1300])
    with pytest.raises(ValueError,match='budget'):execute(LocalizerSession(i['config']),c,i,p,a,s,event=events.append,clock=lambda:next(ticks))
    assert events[-1]['state']=='failed_or_interrupted'


def test_nonbinary_metrics_refused():
    with pytest.raises(ValueError,match='Binary'):metrics(np.full((8,8,8),.5),np.ones((8,8,8)),np.eye(4))


def test_export_failure_preserves_checkpoint_and_refuses_terminal(tmp_path):
    c,i,p,a,s=setup(tmp_path);events=[];original=s.publish
    def fail(artifact_id,**kwargs):
        if artifact_id.endswith('case:optimizer:1'):raise OSError('injected export failure')
        return original(artifact_id,**kwargs)
    s.publish=fail
    with pytest.raises(OSError,match='injected'):execute(LocalizerSession(i['config']),c,i,p,a,s,event=events.append)
    last=events[-1]['last_complete_checkpoint'];assert last['artifact_id'].endswith('checkpoint:4')
    assert not (tmp_path/digest((i['run_id']+':terminal').encode())).exists()
    assert (tmp_path/digest((i['run_id']+':case:optimizer:0').encode())/'complete.json').exists()

@pytest.mark.parametrize('fault',['missing_checkpoint','missing_case','metric'])
def test_terminal_refuses_incomplete_or_inconsistent_manifest(tmp_path,fault):
    c,i,p,a,s=setup(tmp_path);result,ref=execute(LocalizerSession(i['config']),c,i,p,a,s)
    f,_=s.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=lambda x:validate_terminal(x,i,s))
    if fault=='missing_checkpoint':result['checkpoints'].pop(0)
    if fault=='missing_case':result['exports'].pop()
    if fault=='metric':
        trajectory=json.loads(f['trajectory.json']);trajectory[-1]['metrics']['optimizer']['cases'][0]['recall']=42
        f['trajectory.json']=canonical(trajectory)
    f['result.json']=canonical(result)
    with pytest.raises(ValueError):validate_terminal(f,i,s)


def test_restore_reuses_original_combined_storage_ceiling(monkeypatch):
    from scripts.diagnostics import expanded_localizer_launch as launch
    class Store:
        def __init__(self,q):self.quota_bytes=q
    monkeypatch.setattr(launch,'stores',lambda recovery_only=False:(None,Store(200),Store(200)) if recovery_only else (Store(100),Store(200),Store(200)))
    invocation={'storage_quota_ceilings':[80,90]}
    primary,backup,target=launch.capped_stores(invocation)
    assert [x.quota_bytes for x in (primary,backup,target)]==[80,90,90]
    _,backup,target=launch.capped_stores(invocation,recovery_only=True)
    assert backup.quota_bytes==target.quota_bytes==90


def test_sustained_budget_is_explicit_and_legacy_cap_stays():
    from src.training.localizer import validate_config
    from src.training.expanded_executor import CONFIG,SUSTAINED_CONFIG
    validate_config(SUSTAINED_CONFIG)
    for config in (dict(CONFIG,max_steps=301),dict(SUSTAINED_CONFIG,max_steps=2401),dict(SUSTAINED_CONFIG,budget_id='unbounded'),dict(SUSTAINED_CONFIG,loss_id='voxel_ce_dice_v1')):
        with pytest.raises(ValueError):validate_config(config)


def test_sustained_cpu_transaction_and_evaluation_journal(tmp_path):
    c,i,p,a,s=setup(tmp_path)
    i['config']['budget_id']='sustained_localizer_v1'
    i['plan_sha256']=digest(canonical(p));a['bindings']['plan_sha256']=i['plan_sha256']
    events=[]
    result,ref=execute(LocalizerSession(i['config']),c,i,p,a,s,event=events.append)
    assert result['completed_steps']==4
    assert [e['step'] for e in events if e['state']=='evaluation_complete']==[0,2,4]
    f,_=s.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=lambda f:validate_terminal(f,i,s))
    assert json.loads(f['trajectory.json'])==[{k:v for k,v in e.items() if k!='state'} for e in events if e['state']=='evaluation_complete']


def test_backup_callback_failure_prevents_updates(tmp_path):
    c,i,p,a,s=setup(tmp_path);session=LocalizerSession(i['config']);events=[]
    def event(row):
        events.append(row)
        if row['state']=='checkpoint_complete':raise OSError('injected backup failure')
    with pytest.raises(OSError,match='backup'):execute(session,c,i,p,a,s,event=event)
    assert session.step==0 and events[-1]['state']=='failed_or_interrupted'
    assert events[-1]['last_complete_checkpoint']['artifact_id'].endswith('checkpoint:0')


@pytest.mark.parametrize('fault',[None,'config','cadence','budget','approval','scope'])
def test_real_sustained_controls_are_exact(tmp_path,monkeypatch,fault):
    from src.training.expanded_executor import SUSTAINED_CONFIG
    from scripts.diagnostics.expanded_localizer_launch import plan
    import src.training.expanded_executor as executor
    c,i,_,_,_=setup(tmp_path)
    inputs=deepcopy(c.inputs)
    for role,count in [('optimizer',16),('evaluator',11)]:
        prototype=inputs['roles'][role][0]
        inputs['roles'][role]=[dict(prototype,study_id=f'{role}-{j}') for j in range(count)]
    pin=digest(canonical(inputs));monkeypatch.setattr(executor,'REAL_INPUT_PIN',pin)
    i.update(device='mps',purpose='qualified-expanded-executor',config=deepcopy(SUSTAINED_CONFIG),inputs_sha256=pin)
    p=plan(i['config'],experiment='CAP-EXP-006')
    if fault=='config':p['config']=dict(p['config'],learning_rate=.0002);i['config']=p['config']
    if fault=='cadence':p['evaluation_steps']=[0,2400]
    if fault=='budget':p['total_seconds']=3601
    if fault=='scope':p['experiment_id']='CAP-EXP-005'
    i['plan_sha256']=digest(canonical(p))
    a=dict(allowed=True,authority='Quinton Evans',operation='launch_CAP-EXP-005' if fault=='approval' else 'launch_CAP-EXP-006',bindings={k:i[k] for k in ('inputs_sha256','source_sha256','environment_sha256','plan_sha256')})
    if fault:
        with pytest.raises(ValueError):validate_controls(i,inputs,p,a)
    else:validate_controls(i,inputs,p,a)


def test_sustained_checkpoint_beyond_old_cap_continues_exactly():
    from src.training.expanded_localizer import synthetic_update,checkpoint,restore
    torch.set_num_threads(2);c=RoleCache(fixture());i=identity(c)
    i['config'].update(max_steps=2400,budget_id='sustained_localizer_v1')
    session=LocalizerSession(i['config'])
    history=[synthetic_update(session,c,i) for _ in range(301)]
    restored=restore(checkpoint(session,c,i,history),i)
    assert restored.step==301 and restored.scheduler.T_max==2400
    a=synthetic_update(session,c,i);b=synthetic_update(restored,c,i)
    assert a==b
    assert all(torch.equal(x,y) for x,y in zip(session.model.parameters(),restored.model.parameters()))
