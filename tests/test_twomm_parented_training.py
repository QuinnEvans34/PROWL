from copy import deepcopy
from io import BytesIO
import json
import pytest,torch
from src.data.manifest_records import canonical,digest
from src.training import twomm_training as old,twomm_parented_training as m,twomm_parented_executor as executor,twomm_parented_parity as parity,twomm_session as readiness
from test_twomm_cache_adapter import fixture,make
from test_twomm_training import controls as old_controls,references
from test_twomm_training_long import tiny_batch
from scripts.diagnostics.twomm_parented_rehearsal import controls


@pytest.fixture
def setup(tmp_path,fixture,monkeypatch):
    torch.set_num_threads(2);monkeypatch.setattr(readiness,'build_model',lambda _:torch.nn.Conv3d(1,2,1))
    monkeypatch.setattr(old,'patch_batch',tiny_batch);monkeypatch.setattr(m,'patch_batch',tiny_batch)
    path=tmp_path/'cache';path.mkdir();cache,cp,_=make(path,fixture)
    oi,oc=old_controls(fixture[1],cp,steps=2);parent=old.Session(oi,oc)
    for _ in range(2):parent.update(cache)
    f=old.payload(parent);r=m.reference(f,oi,dict(scope='invented'),dict(cases=[]))
    i,c=controls(fixture[1],cp,b'source',b'env','twomm-training-child-test',r);i['device']='cpu'
    a=json.loads(c['authorization.json']);a['identity']={k:v for k,v in i.items() if k!='authorization_sha256'}
    c['authorization.json']=canonical(a);i['authorization_sha256']=digest(c['authorization.json'])
    s=m.import_parent(f,i,c);return s,cache,i,c,f,parent


def test_import_preserves_exact_weights_moments_history_and_step(setup):
    s,cache,i,c,f,p=setup
    assert m.weight_digest(s)==old.weight_digest(p) and m.optimizer_digest(s.optimizer.state_dict())==m.optimizer_digest(p.optimizer.state_dict())
    assert s.parent_progress==f['progress.json'] and s.step==0 and s.history==[]
    assert s.optimizer.param_groups[0]['lr']==.00001 and s.optimizer.param_groups[0]['initial_lr']==p.optimizer.param_groups[0]['initial_lr']
    assert all(v['step']==2 for v in s.optimizer.state_dict()['state'].values())
    row=s.update(cache);assert row['absolute_completed_step']==3 and row['sampling']['step']==2
    assert (row['member_index'],row['pass_index'],row['pass_offset'])==old.schedule(s.binding,s.config['seed'],2)
    assert row['learning_rate_used']==row['learning_rate_next']==.00001
    assert all(v['step']==3 for v in s.optimizer.state_dict()['state'].values())


def test_child_reload_next_update_and_exhaustion(setup):
    s,cache,i,_,_,_=setup;s.update(cache);r=m.restore_payload(m.payload(s),i)
    assert s.update(cache)==r.update(cache) and m.weight_digest(s)==m.weight_digest(r)
    assert m.validate_payload(m.payload(s),i)['absolute_step']==4
    with pytest.raises(ValueError,match='exhausted'):s.update(cache)

@pytest.mark.parametrize('fault',['parent_bytes','parent_history','parent_pin','parent_step','parent_seed','rate','offset','optimizer_counter','moments','scheduler','absolute_step','rng'])
def test_parent_and_child_forgeries_refused(setup,fault):
    s,cache,i,c,f,p=setup
    if fault=='parent_bytes':
        f=deepcopy(f);f['state.pt']+=b'corrupt'
        with pytest.raises(ValueError):m.import_parent(f,i,c)
        return
    ck=m.payload(s)
    if fault=='parent_history':ck['parent-progress.json']=b'[]'
    elif fault in ('parent_pin','parent_step','parent_seed'):
        r=json.loads(ck['parent-reference.json'])
        if fault=='parent_pin':r['weight_sha256']='f'*64
        if fault=='parent_step':r['step']=1
        if fault=='parent_seed':r['identity']['config']['seed']+=1
        ck['parent-reference.json']=canonical(r)
    elif fault in ('rate','offset'):
        s.update(cache);ck=m.payload(s);h=json.loads(ck['progress.json']);h[0]['learning_rate_used' if fault=='rate' else 'absolute_completed_step']=.5 if fault=='rate' else 1
        ck['progress.json']=canonical(h)
    else:
        st=torch.load(BytesIO(ck['state.pt']),weights_only=True)
        if fault=='optimizer_counter':next(iter(st['optimizer']['state'].values()))['step']-=1
        if fault=='moments':next(iter(st['optimizer']['state'].values()))['exp_avg'].add_(1)
        if fault=='scheduler':st['scheduler']['factor']=.5
        if fault=='absolute_step':st['absolute_step']=99
        if fault=='rng':st['cpu_rng'][0]+=1
        out=BytesIO();torch.save(st,out);ck['state.pt']=out.getvalue()
    with pytest.raises(ValueError):m.validate_payload(ck,i)


def test_unimported_and_zero_update_sessions_cannot_train(setup):
    s,cache,i,c,f,p=setup
    bare=m.Session(i,c,f['progress.json'])
    with pytest.raises(ValueError,match='Unimported'):bare.update(cache)
    i=deepcopy(i);c=deepcopy(c);plan=json.loads(c['plan.json']);plan.update(execution_mode='zero_update_parent_check',checkpoint_steps=[0],evaluations=[dict(step=0,roles=['evaluator'])])
    c['plan.json']=canonical(plan);i['plan_sha256']=digest(c['plan.json']);a=json.loads(c['authorization.json']);a['identity']={k:v for k,v in i.items() if k!='authorization_sha256'}
    c['authorization.json']=canonical(a);i['authorization_sha256']=digest(c['authorization.json']);q=m.import_parent(f,i,c)
    with pytest.raises(ValueError,match='Zero-update'):q.update(cache)
    assert q.step==0

@pytest.mark.parametrize('mask_mismatch',[False,True])
def test_parent_inference_guard_retains_prefix_and_no_future_reads(setup,tmp_path,monkeypatch,mask_mismatch):
    s,cache,i,c,_,_=setup;opened=[];saved=[]
    def predict(image):
        from src.training.twomm_adapter import pad_image
        p=torch.zeros((2,*image.shape[1:]));p[1]=1;return p,pad_image(image,s.config)[1]
    monkeypatch.setattr(s,'predict',predict)
    def save(f,i):
        step=m.validate_payload(f,i)['step'];saved.append(step);return dict(primary=dict(step=step,receipt_sha256='a'*64),backup=dict(receipt_sha256='b'*64))
    def refs(stage,guard):opened.append(stage['step']);rs=references(s);return {r:rs[r] for r in stage['roles']}
    def check(s,p,h):
        return parity.decision(i,s.binding,weight_sha256=m.weight_digest(s),expected_weight_sha256=s.parent_reference['weight_sha256'],
            mismatched_masks=[s.binding['roles']['evaluator'][0]['descriptor']['study_id']] if mask_mismatch else [])
    dest=tmp_path/'attempt';dest.mkdir();r=executor.execute(s,cache,dest,open_references=refs,save_checkpoint=save,check_parent=check)
    assert r['state']==('stopped_parent_mismatch' if mask_mismatch else 'complete')
    assert opened==saved==([0] if mask_mismatch else [0,1,2])
    from src.training import twomm_parented_evidence as evidence
    f=evidence.encode(i,'terminal',dict(result=r,journal=(dest/'events.jsonl').read_text(),probe_sha256='f'*64));assert evidence.validate(f,i)
    assert r['absolute_completed_steps']==(2 if mask_mismatch else 4)


def test_real_absolute_sampler_budget_and_rejection_of_restart(setup):
    from src.training.twomm_adapter import patch_batch
    s,cache,_,_,_,_=setup;x,y,t=patch_batch(cache.get('optimizer',0),s.config,step=2)
    assert t['step']==2
    for j in (0,1,4):
        with pytest.raises(ValueError):patch_batch(cache.get('optimizer',0),s.config,step=j)


def test_legacy_codec_cannot_silently_accept_child(setup):
    s,_,i,_,_,_=setup
    with pytest.raises(ValueError):old.validate_payload(m.payload(s),i)
