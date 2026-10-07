from copy import deepcopy
import json
import pytest
from segmenter_duration_fixtures import request,approval,FakeSession,checkpoint,screen_pair,screen_record
from src.data.manifest_records import canonical,digest
from src.training import segmenter_duration_executor_v1 as e,segmenter_duration_session_v1 as core

@pytest.fixture(scope='module')
def unit():return request()
@pytest.fixture(scope='module')
def real():return request('scientific')[0]

@pytest.mark.parametrize('fault',['task','kind','domain','duration','cadence','limits','source','cache','imports','extension','calls','screen_mode','recovery','policy'])
def test_request_refuses_scope_drift(unit,fault):
    r=deepcopy(unit[0])
    if fault=='task':r['task']='other'
    if fault=='kind':r['kind']='scientific'
    if fault=='domain':r['identity']['domain']='qualified_real_cache'
    if fault=='duration':r['identity']['config']['max_steps']=192
    if fault=='cadence':r['checkpoint_steps']=[0,6]
    if fault=='limits':r['limits']['rss_bytes']+=1
    if fault=='source':r['source_pins']={}
    if fault=='cache':r['input_cache']={'area':'real'}
    if fault=='imports':r['imports_allowed']=True
    if fault=='extension':r['extension_allowed']=True
    if fault=='calls':r['model_calls']['producer']['optimizer_calls']=True
    if fault=='screen_mode':r['screen_mode']='engineering_native_counts'
    if fault=='recovery':r['recovery_policy']['real_optimizer_calls']=1
    if fault=='policy':r['policy_sha256']='0'*64
    with pytest.raises(ValueError):e.validate_request(r)

def test_unit_and_actual_authorities_separated(unit,real):
    e.validate_request(unit[0]);e.validate_request(real)
    with pytest.raises(ValueError):e.authorize(real)
    with pytest.raises(ValueError):e.authorize(unit[0],b'anything',trusted_approval_sha256='a'*64)
    raw=approval(real);g=e.authorize(real,raw,trusted_approval_sha256=digest(raw));e.checked_grant(real,g)
    changed=deepcopy(real);changed['identity']['run_id']+='-changed'
    with pytest.raises(ValueError):e.checked_grant(changed,g)

@pytest.mark.parametrize('fault',['request','author','screen_mode','calls','targets','ct','extension','restart','pin','unknown'])
def test_exact_authorization_refused(real,fault):
    a=json.loads(approval(real))
    if fault=='request':a['request_sha256']='0'*64
    if fault=='author':a['author']='Claude'
    if fault=='screen_mode':a['screen_mode']='engineering_native_counts'
    if fault=='calls':a['model_calls']['cold']['optimizer_calls']=1
    if fault=='targets':a['original_target_reads']=14
    if fault=='ct':a['original_ct_reads']=1
    if fault=='extension':a['extension']=True
    if fault=='restart':a['restart']=True
    if fault=='unknown':a['retry']=True
    raw=canonical(a)
    with pytest.raises(ValueError):e.authorize(real,raw,trusted_approval_sha256='0'*64 if fault=='pin' else digest(raw))

def drive(r,p,*,fp=100,fault=None):
    s=FakeSession(r['identity'],{n:v.encode() for n,v in r['controls'].items()});events=[]
    def save(s):
        ref=checkpoint(s)
        if fault=='keeper' and s.step==r['screen_steps'][0]:ref['backup']['receipt_sha256']=''
        return ref
    def screen(s,ref,tick):
        record,pair=screen_pair(r,s,fp)
        if fault=='screen_keeper':pair['backup']['receipt_sha256']=''
        if fault=='report_early':record['outcomes'].append(record['outcomes'][-1]|dict(role='report_only'))
        return record,pair
    out=e.drive(r,s,p,save_checkpoint=save,screen=screen,event=events.append,guard=lambda:None)
    return s,out,events

def test_192_full_loop_uses_mock_only_and_keeps_boundaries(unit):
    r,p=deepcopy(unit);r['identity']['config']=core.config();r['kind']='scientific';r['checkpoint_steps']=[0,48,96,144,192];r['screen_steps']=[48,96,144,192]
    s,(result,_,_),events=drive(r,p,fp=50)
    assert s.step==192 and result['state']=='complete' and set(result['exposure'].values())=={32}
    assert [v['step'] for v in result['checkpoints']]==[0,48,96,144,192] and result['terminal_decision']=='terminal_pass'
    assert s.evaluated==[(0,False),(48,False),(96,False),(144,False),(192,True)]
    assert [v['step'] for v in events if v['state']=='update_started']==list(range(192))

def test_coverage_and_fp_stop_before_next_update(unit):
    r,p=unit;s,(result,_,_),events=drive(r,p,fp=126)
    assert s.step==2 and result['state']=='stopped' and result['terminal_decision']=='stopped'
    assert len([v for v in events if v['state']=='update_complete'])==2

@pytest.mark.parametrize('fault',['keeper','screen_keeper'])
def test_cannot_advance_without_independent_durable_receipt(unit,fault):
    with pytest.raises(ValueError):drive(*unit,fault=fault)

@pytest.mark.parametrize('fault',['tuple','roles','control'])
def test_bad_provider_refused_before_factory(tmp_path,unit,fault):
    r,p=deepcopy(unit)
    if fault=='tuple':p=(None,None)
    else:p.control['train'][0]='held' if fault=='roles' else 'invented-validation'
    with pytest.raises(ValueError):e.execute(r,p,tmp_path,save_checkpoint=lambda s:None,screen=lambda *a:None,protect_summary=lambda *a:None,finish=lambda *a:None,session_factory=lambda *a:pytest.fail('Factory reached'))

def test_replay_refused_and_fault_preserves_last_keeper(tmp_path,unit):
    r,p=unit
    def save(s):
        if s.step==2:raise RuntimeError('invented backup failure')
        return checkpoint(s)
    kw=dict(save_checkpoint=save,screen=lambda s,ref,tick:screen_pair(r,s),protect_summary=lambda *a:None,finish=lambda *a:None,session_factory=FakeSession)
    with pytest.raises(RuntimeError):e.execute(r,p,tmp_path,**kw)
    failure=json.loads((tmp_path/'transaction-failure.json').read_bytes());assert failure['completed_steps']==2 and failure['last_durable_checkpoint']['step']==0
    before=(tmp_path/'journal.jsonl').read_bytes()
    with pytest.raises(FileExistsError):e.execute(r,p,tmp_path,**kw)
    assert (tmp_path/'journal.jsonl').read_bytes()==before

def test_call_counter_hard_stop_before_entry():
    counter=e.CallCounter(dict(forwards=1,optimizer_calls=0));counter.hit('forwards')
    with pytest.raises(ValueError):counter.hit('forwards')
    with pytest.raises(ValueError):counter.hit('optimizer_calls')
    assert counter.counts==dict(forwards=1,optimizer_calls=0)

def test_real_cannot_choose_engineering_mode(real):
    r=deepcopy(real);r['screen_mode']='engineering_native_counts'
    with pytest.raises(ValueError):e.validate_request(r)


def engineering_record(r,step):
    import numpy as np
    rows=[]
    for case in (r['targets']['cases'] if step==192 else r['targets']['cases'][:6]):
        p=case['fidelity']['metrics']['pancreas_parenchyma']['native_voxels'];les=case['fidelity']['metrics']['lesion']['native_voxels'];total=__import__('math').prod(case['descriptor']['geometry']['shape_xyz'])
        counts=dict(confusion_matrix=[[total-p-les,0,0],[0,p,0],[0,0,les]],components=[dict(component_id=v['component_id'],reference_voxels=v['native_voxels'],true_positive=v['native_voxels']) for v in case['reference_components']],voxel_volume_mm3=float(abs(np.linalg.det(np.asarray(case['descriptor']['geometry']['affine_ras']).reshape(4,4)[:3,:3]))),source_boundary_contact=any(v['source_boundary_contact'] for v in case['reference_components']))
        rows.append(dict(case_id=case['study_id'],role='train' if case['protected_role']=='train' else 'report_only',status='valid',reason=None,reported_metrics=None,counts=counts))
    return dict(schema_version='1.0.0',policy_sha256=r['policy_sha256'],baseline_sha256=r['policy']['baseline_sha256'],step=step,outcomes=rows)


def test_native_engineering_keeps_policy_failure_visible_without_quality_claim():
    r,p=request('native_rehearsal');e.validate_request(r)
    assessment=e.assess_stage(r,engineering_record(r,48))
    assert assessment['decision']=='continue' and assessment['engineering_only'] and not assessment['quality_acceptance']
    assert assessment['policy_result']['decision']=='stopped' # Baseline is deliberately different invented integer metadata.
    assert e.assess_stage(r,engineering_record(r,192))['decision']=='terminal_insufficient'

@pytest.mark.parametrize('fault',['missing','failed','count','boolean','volume','boundary','component'])
def test_engineering_never_skips_missing_or_corrupt_counts(fault):
    r,p=request('native_rehearsal');record=engineering_record(r,48)
    if fault=='missing':record['outcomes'].pop()
    if fault=='failed':record['outcomes'][0]['status']='failed'
    if fault=='count':record['outcomes'][0]['counts']['confusion_matrix'][0][0]-=1
    if fault=='boolean':record['outcomes'][0]['counts']['confusion_matrix'][0][0]=True
    if fault=='volume':record['outcomes'][0]['counts']['voxel_volume_mm3']+=1
    if fault=='boundary':record['outcomes'][0]['counts']['source_boundary_contact']=not record['outcomes'][0]['counts']['source_boundary_contact']
    if fault=='component':record['outcomes'][0]['counts']['components'][0]['true_positive']+=1
    with pytest.raises(ValueError):e.assess_stage(r,record)


def test_actual_request_requires_complete_new_code_test_contract_closure():
    r,p=request('scientific');e.validate_request(r)
    r['source_pins'].pop('scripts/diagnostics/segmenter_duration_launch.py')
    r['controls']['source.json']=canonical(r['source_pins']).decode();r['identity']['source_sha256']=digest(r['controls']['source.json'].encode())
    with pytest.raises(ValueError,match='closure'):e.validate_request(r)


def test_counter_attached_to_tiny_model_refuses_next_forward_before_update():
    import torch
    torch.set_num_threads(2);r,p=request();s=core.Session(r['identity'],{n:v.encode() for n,v in r['controls'].items()})
    budget=e.CallCounter(dict(forwards=1,optimizer_calls=0));budget.attach(s)
    s.predict(p.get(p.control['train'][0],role='train',operation='inference').image)
    with pytest.raises(ValueError,match='Model-call'):s.update(p)
    assert budget.counts==dict(forwards=1,optimizer_calls=0) and s.step==0 and s.dirty


def test_source_drift_stops_before_new_checkpoint_or_screen(tmp_path,unit):
    r,p=unit;calls=[]
    def verify():
        calls.append(True)
        if len(calls)==4:raise ValueError('invented source drift before step2 checkpoint')
    with pytest.raises(ValueError,match='source drift'):e.execute(r,p,tmp_path,save_checkpoint=checkpoint,screen=lambda *a:pytest.fail('Drift reached screen'),finish=lambda *a:None,protect_summary=lambda *a:None,session_factory=FakeSession,verify_source=verify)
    failure=json.loads((tmp_path/'transaction-failure.json').read_bytes());assert failure['completed_steps']==2 and failure['last_durable_checkpoint']['step']==0 and failure['dirty']
