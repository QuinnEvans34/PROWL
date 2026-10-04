from copy import deepcopy
from io import BytesIO
import json
import numpy as np
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.training import twomm_training as m
from src.training import twomm_session as readiness
from src.training import twomm_training_executor as executor
from test_twomm_cache_adapter import fixture,make,config


def controls(binding,cp,*,steps=2):
    cfg=dict(config(),max_steps=steps)
    p=dict(schema_version='twomm-training-plan-1',config=cfg,checkpoint_steps=[0,steps],
        evaluations=[dict(step=s,roles=['optimizer','evaluator']) for s in (0,steps)],
        total_seconds=600,output_bytes=128*1024**2,reference_policy='fresh_native_references_each_stage_v1')
    c={'inputs.json':canonical(binding),'source.json':b'source','environment.json':b'env','plan.json':canonical(p)}
    i=dict(schema_version='twomm-training-1',run_id='twomm-training-test',purpose='synthetic-training-transaction',
        device='cpu',config=cfg,sampling_policy=m.POLICY,shuffle_policy=m.SHUFFLE,prediction_policy=m.PREDICTION,
        cache_receipt_sha256=cp,**{m.CONTROLS[n]:digest(v) for n,v in c.items()})
    a=dict(allowed=True,operation='synthetic_training_verification',authority='Codex synthetic verification',request_sha256=None,identity=deepcopy(i))
    c['authorization.json']=canonical(a);i['authorization_sha256']=digest(c['authorization.json'])
    return i,c

@pytest.fixture
def setup(tmp_path,fixture,monkeypatch):
    torch.set_num_threads(2)
    monkeypatch.setattr(readiness,'build_model',lambda _:torch.nn.Conv3d(1,2,1))
    path=tmp_path/'cache';path.mkdir();cache,cp,_=make(path,fixture)
    i,c=controls(fixture[1],cp);s=m.Session(i,c)
    return s,cache,i,c


def test_schedule_every_member_once_and_replay():
    b={'roles':{'optimizer':[{'descriptor':{'study_id':str(i)}} for i in range(113)]}}
    rows=[m.schedule(b,42,j)[0] for j in range(300)]
    assert set(rows[:113])==set(rows[113:226])==set(range(113))
    assert rows[:113]!=rows[113:226] and rows==[m.schedule(b,42,j)[0] for j in range(300)]
    assert all(rows.count(i) in (2,3) for i in range(113))


def test_training_roundtrip_and_next_update(setup):
    s,cache,i,c=setup;s.update(cache);f=m.payload(s);r=m.restore_payload(f,i)
    assert s.history==r.history and m.weight_digest(s)==m.weight_digest(r)
    assert s.update(cache)==r.update(cache) and m.weight_digest(s)==m.weight_digest(r)
    with pytest.raises(ValueError,match='exhausted'):s.update(cache)

@pytest.mark.parametrize('fault',['control','extra','identity','history_member','history_length','history_padding',
    'history_loss','history_rate','history_schedule','optimizer','scheduler','nan','version','step','rng'])
def test_checkpoint_faults(setup,fault):
    s,cache,i,c=setup;s.update(cache);f=m.payload(s)
    if fault=='control':f['authorization.json']=b'{}'
    elif fault=='extra':f['extra']=b''
    elif fault=='identity':f['identity.json']=b'{}'
    elif fault.startswith('history'):
        h=json.loads(f['progress.json'])
        if fault=='history_member':h[0]['sampling']['member_id']='evaluator-synthetic'
        if fault=='history_length':h=[]
        if fault=='history_padding':h[0]['sampling']['padding']['padding'][0]+=1
        if fault=='history_loss':h[0]['loss']=-1
        if fault=='history_rate':h[0]['learning_rate']=.5
        if fault=='history_schedule':h[0]['member_index']=1
        f['progress.json']=canonical(h)
    else:
        state=torch.load(BytesIO(f['state.pt']),weights_only=True)
        if fault=='optimizer':state['optimizer']['param_groups'][0]['maximize']=True
        if fault=='scheduler':state['scheduler']['T_max']=999
        if fault=='nan':next(iter(state['model'].values())).flatten()[0]=float('nan')
        if fault=='version':state['schema_version']='twomm-state-1'
        if fault=='step':state['step']=False
        if fault=='rng':state['cpu_rng']=torch.zeros(3,dtype=torch.uint8)
        stream=BytesIO();torch.save(state,stream);f['state.pt']=stream.getvalue()
    with pytest.raises((ValueError,RuntimeError)):m.decode(f,i)

@pytest.mark.parametrize('fault',['allowed','authority','plan','binding','cache','policy','real'])
def test_bad_controls_before_update(setup,fault):
    s,cache,i,c=setup;i=deepcopy(i);c=deepcopy(c)
    if fault in ('allowed','authority'):
        a=json.loads(c['authorization.json']);a[fault]=False if fault=='allowed' else 'other'
        c['authorization.json']=canonical(a);i['authorization_sha256']=digest(c['authorization.json'])
    if fault=='plan':c['plan.json']=b'{}'
    if fault=='binding':i['inputs_sha256']='f'*64
    if fault=='cache':i['cache_receipt_sha256']='f'*64
    if fault=='policy':i['prediction_policy']='threshold-tuned'
    if fault=='real':i['purpose']='qualified-twomm-training'
    with pytest.raises(ValueError):m.Session(i,c)


def test_cache_mutation_before_update(setup):
    s,cache,_,_=setup
    cache._manifest['binding']['roles']['optimizer'][0]['descriptor']['protected_role']='validation'
    with pytest.raises(ValueError):s.update(cache)
    assert s.step==0


def test_optimizer_interruption_poisoned_no_checkpoint(setup,monkeypatch):
    s,cache,_,_=setup;old=s.optimizer.step
    def interrupted():old();raise KeyboardInterrupt('after optimizer changed weights')
    monkeypatch.setattr(s.optimizer,'step',interrupted)
    with pytest.raises(KeyboardInterrupt):s.update(cache)
    with pytest.raises(ValueError,match='uncertain'):m.payload(s)
    with pytest.raises(ValueError,match='uncertain'):s.update(cache)


def references(s):
    class DS:
        def __init__(self,role):self.role=role;self.reads=set()
        def __len__(self):return 1
        def descriptor(self,i):return deepcopy(s.binding['roles'][self.role][i]['descriptor'])
        def load(self,i,*,operation):
            assert operation==self.role and i not in self.reads;self.reads.add(i)
            y=np.zeros((12,13,14),np.uint8);y[3:8,4:9,2:8]=1
            return y,np.diag([2.,2.,2.,1.]),{'descriptor':self.descriptor(i)}
    return {r:DS(r) for r in ('optimizer','evaluator')}


def transaction(setup,tmp_path,*,fail=None):
    s,cache,i,c=setup;dest=tmp_path/'attempt';dest.mkdir();saved=[]
    def save(files,identity):
        result=m.validate_payload(files,identity);saved.append(files)
        if fail=='checkpoint':raise KeyboardInterrupt('publication interruption')
        return dict(primary=dict(step=result['step'],receipt_sha256=digest(files['state.pt'])),backup=dict(receipt_sha256='b'*64))
    def open_refs(stage,guard):
        if fail=='evaluation':raise KeyboardInterrupt('evaluation interruption')
        return references(s)
    return dest,saved,lambda:executor.execute(s,cache,dest,open_references=open_refs,save_checkpoint=save)


def test_transaction_complete_native_exports_and_no_replay(setup,tmp_path):
    dest,saved,run=transaction(setup,tmp_path);result=run()
    assert result['completed_steps']==2 and len(saved)==2 and len(result['evaluations'])==2
    assert (dest/'complete.json').exists()
    events,pin=executor.verify_journal((dest/'events.jsonl').read_bytes(),setup[2])
    assert pin==result['last_event_sha256']
    assert [r['completed_step'] for r in events if r['state']=='update_complete']==[1,2]
    with pytest.raises(ValueError):run()

@pytest.mark.parametrize('fault',['checkpoint','evaluation'])
def test_transaction_interruption_retained_without_completion(setup,tmp_path,fault):
    dest,saved,run=transaction(setup,tmp_path,fail=fault)
    with pytest.raises(KeyboardInterrupt):run()
    assert not (dest/'complete.json').exists() and saved
    events,_=executor.verify_journal((dest/'events.jsonl').read_bytes(),setup[2])
    assert events[-1]['state']=='failed_or_interrupted'
    with pytest.raises(ValueError):run()


def test_journal_tamper(setup,tmp_path):
    dest,_,run=transaction(setup,tmp_path);run();raw=(dest/'events.jsonl').read_bytes()
    lines=raw.splitlines();lines[1]=lines[1].replace(b'checkpoint_started',b'checkpoint_skipped')
    with pytest.raises(ValueError):executor.verify_journal(b'\n'.join(lines),setup[2])


def test_wrong_reference_descriptor_no_read(setup,tmp_path):
    s,cache,_,_=setup;ds=references(s);ds['optimizer'].descriptor=lambda i:{'study_id':'held'}
    with pytest.raises(ValueError,match='qualification'):executor.evaluate(s,cache,ds,s.plan['evaluations'][0],tmp_path/'eval')
    assert all(not d.reads for d in ds.values())


def test_synthetic_authority_cannot_bind_real_descriptors(setup):
    s,cache,i,c=setup;b=deepcopy(s.binding)
    b['roles']['optimizer'][0]['descriptor']['rows']={'pancreas':{'uri':'real'}}
    i,c=controls(b,i['cache_receipt_sha256'])
    with pytest.raises(ValueError,match='invented descriptors'):m.Session(i,c)


def test_evaluation_record_keeper_refuses_metric_mutation(setup,tmp_path):
    from src.training import twomm_training_evidence as ev
    dest,_,run=transaction(setup,tmp_path);run();i=setup[2]
    files=ev.evaluation_files(dest/'evaluation-0002',i);assert ev.validate(files,i)['kind']=='evaluation'
    record=json.loads(files['record.json']);record['content']['cases'][0]['metrics']['dice']=.8
    with pytest.raises(ValueError):ev.validate({'record.json':canonical(record)},i)


def test_evaluation_record_requires_honest_mask_omissions(setup,tmp_path):
    from src.training import twomm_training_evidence as ev
    dest,_,run=transaction(setup,tmp_path);run();i=setup[2]
    files=ev.evaluation_files(dest/'evaluation-0002',i);record=json.loads(files['record.json'])
    record['content']['derived_masks_not_backed_up']={}
    with pytest.raises(ValueError,match='accounting'):ev.validate({'record.json':canonical(record)},i)


def test_transaction_time_cap_before_first_checkpoint(setup,tmp_path):
    s,cache,i,c=setup;dest=tmp_path/'timed';dest.mkdir();times=iter([0.,601.]);saved=[]
    with pytest.raises(ValueError,match='time cap'):
        executor.execute(s,cache,dest,open_references=lambda st,g:references(s),
            save_checkpoint=lambda f,i:saved.append(f),clock=lambda:next(times))
    assert not saved and not (dest/'complete.json').exists() and s.step==0


def test_missing_evaluation_keeper_fails_without_completion(setup,tmp_path):
    s,cache,i,c=setup;dest=tmp_path/'bad-keeper';dest.mkdir()
    def save(f,i):
        return {'primary':{'step':0,'receipt_sha256':'a'*64},'backup':{'receipt_sha256':'b'*64}}
    with pytest.raises(ValueError,match='keeper'):
        executor.execute(s,cache,dest,open_references=lambda st,g:references(s),
            save_checkpoint=save,keep_evaluation=lambda p,i:{})
    assert not (dest/'complete.json').exists() and (dest/'evaluation-0000/complete.json').exists()


def test_validation_sampling_never_used_for_updates(setup,monkeypatch):
    s,cache,_,_=setup;get=cache.get;calls=[]
    def checked(role,index):calls.append(role);return get(role,index)
    monkeypatch.setattr(cache,'get',checked);s.update(cache)
    assert calls==['optimizer']
