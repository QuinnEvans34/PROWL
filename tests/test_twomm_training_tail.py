from retained_diagnostic_metadata import metadata as retained_metadata
from copy import deepcopy
from io import BytesIO
import json
import math
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.training import twomm_training as m,twomm_training_executor as executor,twomm_session as readiness,twomm_adapter as adapter
from src.training.twomm_tail_schedule import CosineThenConstantLR,REAL_SCHEDULE
from src.training.twomm_prefix_parity import decision,validate_decision,validate_reference
from src.training.twomm_coverage_guard import REAL_POLICY
from test_twomm_cache_adapter import fixture,make
from test_twomm_training import controls,references
from test_twomm_training_long import long_controls,tiny_batch


def tail_controls(binding,cp,steps=3,prefix=2):
    i,c=long_controls(binding,cp,steps=steps,guard=dict(REAL_POLICY,start_step=prefix,mean_recall_floor=0.,minimum_recall_floor=0.,box_pass_fraction_floor=0.,maximum_mean_recall_drop=1.))
    cfg=dict(i['config'],schema_version='twomm-adapter-3',schedule=dict(REAL_SCHEDULE,prefix_steps=prefix))
    p=json.loads(c['plan.json']);cadence=[0,prefix,steps]
    p.update(schema_version='twomm-training-plan-3',config=cfg,checkpoint_steps=cadence,
        evaluations=[dict(step=s,roles=['optimizer','evaluator'] if s in (0,steps) else ['evaluator']) for s in cadence],
        prefix_reference=dict(scope='invented_prefix',step=prefix))
    c['plan.json']=canonical(p);i.update(schema_version='twomm-training-3',config=cfg,plan_sha256=digest(c['plan.json']))
    a=json.loads(c['authorization.json']);a['identity']={k:v for k,v in i.items() if k!='authorization_sha256'}
    c['authorization.json']=canonical(a);i['authorization_sha256']=digest(c['authorization.json']);return i,c

@pytest.fixture
def setup(tmp_path,fixture,monkeypatch):
    torch.set_num_threads(2);monkeypatch.setattr(readiness,'build_model',lambda _:torch.nn.Conv3d(1,2,1));monkeypatch.setattr(m,'patch_batch',tiny_batch)
    path=tmp_path/'cache';path.mkdir();cache,cp,_=make(path,fixture)
    i,c=tail_controls(fixture[1],cp);return m.Session(i,c),cache,i,c


def test_installed_scheduler_matches_all_applied_prefix_rates_and_flat_tail():
    old=torch.nn.Parameter(torch.tensor(1.));new=torch.nn.Parameter(torch.tensor(1.))
    a=torch.optim.AdamW([old],lr=.0003);b=torch.optim.AdamW([new],lr=.0003)
    x=torch.optim.lr_scheduler.CosineAnnealingLR(a,T_max=300,eta_min=0)
    y=CosineThenConstantLR(b,prefix_steps=300,tail_learning_rate=.00001)
    rates=[]
    for j in range(600):
        used=b.param_groups[0]['lr'];rates.append(used)
        if j<300:assert used==a.param_groups[0]['lr']
        else:assert used==.00001
        old.grad=torch.ones_like(old);new.grad=torch.ones_like(new);a.step();b.step();x.step();y.step()
    assert rates[299]<1e-8 and b.param_groups[0]['lr']==.00001
    assert a.param_groups[0]['lr']>.00029


def test_600_toy_updates_match_original_300_weights_and_transition_reload(setup):
    s,cache,_,_=setup;i,c=tail_controls(s.binding,s.identity['cache_receipt_sha256'],steps=600,prefix=300);s=m.Session(i,c)
    oi,oc=controls(s.binding,s.identity['cache_receipt_sha256'],steps=300);old=m.Session(oi,oc)
    for j in range(300):
        a=s.update(cache);b=old.update(cache)
        assert a['sampling']==b['sampling'] and a['loss']==b['loss']
        if j==298:
            restored=m.restore_payload(m.payload(s),i);assert restored.update(cache)==s.update(cache)
            # Complete the original update matching the extra step above.
            b=old.update(cache);assert restored.step==s.step==old.step==300
            break
    assert m.weight_digest(s)==m.weight_digest(old)
    assert s.history[-1]['learning_rate_used']<1e-8 and s.history[-1]['learning_rate_next']==.00001
    restored=m.restore_payload(m.payload(s),i)
    assert s.update(cache)==restored.update(cache) and m.weight_digest(s)==m.weight_digest(restored)
    assert s.history[-1]['learning_rate_used']==.00001
    while s.step<599:s.update(cache)
    restored=m.restore_payload(m.payload(s),i);assert s.update(cache)==restored.update(cache)
    assert m.validate_payload(m.payload(s),i)['step']==600
    with pytest.raises(ValueError,match='exhausted'):s.update(cache)

@pytest.mark.parametrize('fault',['used','next','scheduler_tail','scheduler_prefix'])
def test_tail_checkpoint_rate_and_scheduler_forgery_refused(setup,fault):
    s,cache,i,c=setup;s.update(cache);f=m.payload(s)
    if fault in ('used','next'):
        h=json.loads(f['progress.json']);h[0]['learning_rate_'+fault]=.5;f['progress.json']=canonical(h)
    else:
        state=torch.load(BytesIO(f['state.pt']),weights_only=True)
        state['scheduler']['tail_learning_rate' if fault=='scheduler_tail' else 'T_max']=.05
        stream=BytesIO();torch.save(state,stream);f['state.pt']=stream.getvalue()
    with pytest.raises(ValueError):m.validate_payload(f,i)

@pytest.mark.parametrize('key,value',[('prefix_steps',0),('prefix_steps',600),('prefix_steps',True),('tail_learning_rate',0.),('tail_learning_rate',float('nan')),('tail_learning_rate',.01),('schema_version','unknown')])
def test_invalid_tail_schedule(setup,key,value):
    cfg=deepcopy(setup[0].config);cfg['schedule'][key]=value
    with pytest.raises(ValueError):adapter.validate_config(cfg)


def test_versions_caps_and_readiness_preserved(setup):
    cfg=setup[0].config
    adapter.validate_config(dict(cfg,max_steps=600,schedule=REAL_SCHEDULE))
    with pytest.raises(ValueError):adapter.validate_config(dict(cfg,max_steps=601,schedule=REAL_SCHEDULE))
    with pytest.raises(ValueError):adapter.validate_config(dict(cfg,schema_version='twomm-adapter-2'))


def check(s,*,fault=None):
    return decision(step=2,reference_sha256='a'*64,weight_difference=2e-6 if fault=='weights' else 0.,weight_tolerance=1e-6,
        history_matches=fault!='history',expected_masks=1,mismatched_masks=['evaluator-synthetic'] if fault=='mask' else [],
        baseline_weight_sha256='b'*64,candidate_weight_sha256=m.weight_digest(s))

@pytest.mark.parametrize('fault',[None,'weights','history','mask'])
def test_prefix_failures_stop_before_tail_and_preserve_terminal(setup,tmp_path,monkeypatch,fault):
    s,cache,i,c=setup;opened=[];saved=[]
    def predict(image):
        p=torch.zeros((2,*image.shape[1:]));p[1]=1;return p,adapter.pad_image(image,s.config)[1]
    monkeypatch.setattr(s,'predict',predict)
    def save(files,i):
        step=m.validate_payload(files,i)['step'];saved.append(step)
        return dict(primary=dict(step=step,receipt_sha256='a'*64),backup=dict(receipt_sha256='b'*64))
    def refs(stage,guard):
        opened.append(stage['step']);all_refs=references(s);return {r:all_refs[r] for r in stage['roles']}
    dest=tmp_path/'attempt';dest.mkdir()
    result=executor.execute(s,cache,dest,open_references=refs,save_checkpoint=save,check_prefix=lambda s,p,h:check(s,fault=fault))
    assert s.step==(2 if fault else 3) and opened==saved==([0,2] if fault else [0,2,3])
    assert result['state']==('stopped_prefix_mismatch' if fault else 'complete')
    from src.training import twomm_training_evidence as evidence
    f=evidence.encode(i,'terminal',dict(result=result,journal=(dest/'events.jsonl').read_text(),probe_sha256='f'*64));assert evidence.validate(f,i)['kind']=='terminal'
    bad=json.loads(f['record.json']);bad['content']['result']['prefix_reviews'][0]['state']='forged'
    with pytest.raises(ValueError):evidence.validate({'record.json':canonical(bad)},i)
    if fault:
        assert not (dest/'evaluation-0003').exists()
        with pytest.raises(ValueError):s.update(cache)


def test_missing_callback_refused_before_updates(setup,tmp_path):
    s,cache,_,_=setup;dest=tmp_path/'attempt';dest.mkdir()
    with pytest.raises(ValueError,match='prefix verifier'):executor.execute(s,cache,dest,open_references=lambda *a:None,save_checkpoint=lambda *a:None)
    assert s.step==0 and not list(dest.iterdir())

@pytest.mark.parametrize('fault',['state','count','difference','history_type','duplicate_mask','pin'])
def test_prefix_decision_forgery_refused(setup,fault):
    r=check(setup[0])
    if fault=='state':r['state']='stop'
    if fault=='count':r['matched_masks']=0
    if fault=='difference':r['model_max_abs_difference']=float('nan')
    if fault=='history_type':r['history_matches']=1
    if fault=='duplicate_mask':r['mismatched_masks']=['x','x']
    if fault=='pin':r['reference_sha256']='wrong'
    with pytest.raises(ValueError):validate_decision(r)


def test_real_prefix_reference_pinned_and_membership_bound(monkeypatch):
    from scripts.diagnostics import twomm_training_tail_launch as launch
    monkeypatch.setattr(launch,'prefix_reference',lambda:retained_metadata()['prefix_reference'])
    from scripts.diagnostics.twomm_training_tail_launch import prefix_reference,BINDING,plan
    r=prefix_reference();b=retained_metadata()['binding'];validate_reference(r,b)
    r['cases'][0]['native_mask_sha256']='f'*64
    with pytest.raises(ValueError):validate_reference(r,b)
    p=plan();assert p['checkpoint_steps']==[0,300,450,600] and p['total_seconds']==3600
    members=[m.schedule(b,42,j)[0] for j in range(600)]
    assert sorted(members.count(j) for j in range(113))==[5]*78+[6]*35

@pytest.mark.parametrize('fault',['stage','candidate','members'])
def test_prefix_verifier_context_drift_refused(setup,tmp_path,monkeypatch,fault):
    s,cache,i,c=setup
    def predict(image):
        p=torch.zeros((2,*image.shape[1:]));p[1]=1;return p,adapter.pad_image(image,s.config)[1]
    monkeypatch.setattr(s,'predict',predict)
    def save(files,i):
        step=m.validate_payload(files,i)['step'];return dict(primary=dict(step=step,receipt_sha256='a'*64),backup=dict(receipt_sha256='b'*64))
    def callback(s,p,h):
        r=check(s)
        if fault=='stage':r['step']=1
        if fault=='candidate':r['candidate_weight_sha256']='f'*64
        if fault=='members':r.update(expected_masks=2,matched_masks=2)
        return r
    def refs(stage,guard):return {r:references(s)[r] for r in stage['roles']}
    dest=tmp_path/'attempt';dest.mkdir()
    with pytest.raises(ValueError,match='stage/model/membership'):executor.execute(s,cache,dest,open_references=refs,save_checkpoint=save,check_prefix=callback)
    assert s.step==2 and s.poisoned and not (dest/'evaluation-0003').exists()


def test_coverage_cannot_prevent_required_prefix_review(setup):
    s,_,i,c=setup;i=deepcopy(i);c=deepcopy(c);p=json.loads(c['plan.json']);p['coverage_guard']['start_step']=1
    c['plan.json']=canonical(p);i['plan_sha256']=digest(c['plan.json']);a=json.loads(c['authorization.json']);a['identity']={k:v for k,v in i.items() if k!='authorization_sha256'}
    c['authorization.json']=canonical(a);i['authorization_sha256']=digest(c['authorization.json'])
    with pytest.raises(ValueError,match='early coverage'):m.Session(i,c)
