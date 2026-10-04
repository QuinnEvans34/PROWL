from copy import deepcopy
from io import BytesIO
import json
import math
from pathlib import Path
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.training import twomm_training as m, twomm_training_executor as executor
from src.training import twomm_adapter as adapter, twomm_session as readiness
from src.training.twomm_coverage_guard import REAL_POLICY, review, validate_policy
from src.data.twomm_training_references import StagedReferences
from scripts.diagnostics import twomm_training_long_launch as launch
from test_twomm_cache_adapter import fixture, make
from test_twomm_training import controls, references
from test_twomm_training_launch import items


def long_controls(binding,cp,*,steps=3,guard=None):
    i,c=controls(binding,cp,steps=min(steps,300))
    cfg=dict(i['config'],schema_version='twomm-adapter-2',max_steps=steps)
    p=json.loads(c['plan.json']);boundaries=[0,2,3] if steps==3 else [0,steps]
    policy=guard or dict(REAL_POLICY,start_step=2,mean_recall_floor=0.,minimum_recall_floor=0.,
        box_pass_fraction_floor=0.,maximum_mean_recall_drop=1.)
    p.update(schema_version='twomm-training-plan-2',config=cfg,checkpoint_steps=boundaries,
        evaluations=[dict(step=s,roles=['optimizer','evaluator'] if s in (0,steps) else ['evaluator']) for s in boundaries],
        coverage_guard=policy)
    c['plan.json']=canonical(p);i.update(schema_version='twomm-training-2',config=cfg,plan_sha256=digest(c['plan.json']))
    auth=json.loads(c['authorization.json']);auth['identity']={k:v for k,v in i.items() if k!='authorization_sha256'}
    c['authorization.json']=canonical(auth);i['authorization_sha256']=digest(c['authorization.json']);return i,c


def tiny_batch(item,cfg,*,step):
    shape=list(item['image'].shape[1:]);pads=[max(0,144-n) for n in shape]
    trace=dict(member_id=item['study_id'],step=step,policy=m.POLICY,center_original_grid=[0]*3,center_class=0,
        origin_padded_grid=[0]*3,padding=dict(schema_version='twomm-padding-1',original_shape=shape,
        padding=[v for n in reversed(pads) for v in (n//2,n-n//2)],padded_shape=[s+n for s,n in zip(shape,pads)]))
    x=torch.full((1,1,8,8,8),.25);y=torch.zeros_like(x,dtype=torch.long);y[:,:,2:6,2:6,2:6]=1
    return x,y,trace


@pytest.fixture
def setup(tmp_path,fixture,monkeypatch):
    torch.set_num_threads(2)
    monkeypatch.setattr(readiness,'build_model',lambda _:torch.nn.Conv3d(1,2,1))
    monkeypatch.setattr(m,'patch_batch',tiny_batch)
    path=tmp_path/'cache';path.mkdir();cache,cp,_=make(path,fixture)
    i,c=long_controls(fixture[1],cp);return m.Session(i,c),cache,i,c


def row(sid,step,recall=1.,box=1.):
    tp=round(recall*1000)
    return dict(study_id=sid,role='evaluator',step=step,metrics=dict(reference_voxels=1000,
        true_positive=tp,recall=tp/1000,box_reference_coverage=box))


def test_original_adapter_and_readiness_caps_preserved(setup):
    i=deepcopy(setup[2]);cfg=dict(i['config'],schema_version='twomm-adapter-1',max_steps=301)
    with pytest.raises(ValueError):adapter.validate_config(cfg)
    adapter.validate_config(dict(cfg,schema_version='twomm-adapter-2',max_steps=1200))
    with pytest.raises(ValueError):adapter.validate_config(dict(cfg,schema_version='twomm-adapter-2',max_steps=1201))
    with pytest.raises(ValueError):m.validate_identity(dict(i,schema_version='twomm-training-1'))


def test_full_1200_toy_updates_reload_and_exact_exhaustion(setup):
    s,cache,_,_=setup;i,c=long_controls(s.binding,s.identity['cache_receipt_sha256'],steps=1200)
    s=m.Session(i,c)
    for _ in range(301):s.update(cache)
    saved=m.payload(s);r=m.restore_payload(saved,i)
    assert s.history==r.history and m.weight_digest(s)==m.weight_digest(r)
    assert s.update(cache)==r.update(cache) and m.weight_digest(s)==m.weight_digest(r)
    for _ in range(898):s.update(cache)
    assert s.step==1200 and abs(s.optimizer.param_groups[0]['lr'])<1e-12
    assert m.validate_payload(m.payload(s),i)['step']==1200
    with pytest.raises(ValueError,match='exhausted'):s.update(cache)
    state=torch.load(BytesIO(saved['state.pt']),weights_only=True);state['scheduler']['T_max']=300
    stream=BytesIO();torch.save(state,stream);saved['state.pt']=stream.getvalue()
    with pytest.raises(ValueError,match='Scheduler'):m.validate_payload(saved,i)


def test_extended_real_sampler_at_last_step_is_deterministic(setup):
    s,cache,_,_=setup;cfg=dict(s.config,max_steps=1200);item=cache.get('optimizer',0)
    x,y,a=adapter.patch_batch(item,cfg,step=1199);xx,yy,b=adapter.patch_batch(item,cfg,step=1199)
    assert torch.equal(x,xx) and torch.equal(y,yy) and a==b
    with pytest.raises(ValueError):adapter.patch_batch(item,cfg,step=1200)


@pytest.mark.parametrize('key,value', [('mean_recall_floor',float('nan')),('minimum_recall_floor',True),
    ('start_step',False),('box_pass_fraction_floor',1.01),('maximum_mean_recall_drop',-.1)])
def test_invalid_guard_policy(key,value):
    with pytest.raises(ValueError):validate_policy(dict(REAL_POLICY,**{key:value}))


@pytest.mark.parametrize('fault,reason',[('mean','mean_recall_below_floor'),('minimum','minimum_recall_below_floor'),
    ('box','box_coverage_below_floor'),('drop','mean_recall_drop_from_best_checkpoint')])
def test_each_numeric_coverage_stop(fault,reason):
    rows=[row(str(j),600) for j in range(40)];prior=[]
    if fault=='mean':rows=[row(str(j),600,.94) for j in range(40)]
    if fault=='minimum':rows[0]=row('0',600,.64)
    if fault=='box':rows[:3]=[row(str(j),600,box=.994) for j in range(3)]
    if fault=='drop':rows=[row(str(j),600,.96) for j in range(40)];prior=[review([row(str(j),300) for j in range(40)],REAL_POLICY,300,[])]
    d=review(rows,REAL_POLICY,600,prior);assert d['state']=='stop' and reason in d['reasons']
    assert review([row('a',0,0.,None)],REAL_POLICY,0,[])['state']=='warmup'


def test_guard_duplicate_stage_and_arithmetic_refused():
    a=row('a',300)
    for rows in ([a,a],[dict(a,step=299)],[dict(a,metrics=dict(a['metrics'],recall=.5))]):
        with pytest.raises(ValueError):review(rows,REAL_POLICY,300,[])


def test_coverage_stop_preserves_boundary_and_skips_future_reads(setup,tmp_path,monkeypatch):
    s,cache,_,_=setup;i,c=long_controls(s.binding,s.identity['cache_receipt_sha256'],guard=dict(REAL_POLICY,start_step=2))
    s=m.Session(i,c);opened=[];saved=[]
    def predict(image):
        padded,trace=adapter.pad_image(image,s.config)
        p=torch.zeros((2,*image.shape[1:]));p[0]=1;return p,trace
    monkeypatch.setattr(s,'predict',predict)
    def save(files,i):
        check=m.validate_payload(files,i);saved.append(check['step'])
        return dict(primary=dict(step=check['step'],receipt_sha256='a'*64),backup=dict(receipt_sha256='b'*64))
    def opened_refs(stage,guard):
        opened.append(stage['step']);all_refs=references(s)
        return {r:all_refs[r] for r in stage['roles']}
    dest=tmp_path/'attempt';dest.mkdir()
    result=executor.execute(s,cache,dest,open_references=opened_refs,save_checkpoint=save)
    assert result['state']=='stopped_coverage_guard' and result['completed_steps']==2 and result['planned_steps']==3
    assert opened==saved==[0,2] and not (dest/'evaluation-0003').exists()
    from src.training import twomm_training_evidence as evidence
    f=evidence.encode(i,'terminal',dict(result=result,journal=(dest/'events.jsonl').read_text(),probe_sha256='f'*64))
    assert evidence.validate(f,i)['kind']=='terminal'
    with pytest.raises(ValueError,match='uncertain'):s.update(cache)
    bad=json.loads(f['record.json']);bad['content']['result']['state']='complete'
    with pytest.raises(ValueError):evidence.validate({'record.json':canonical(bad)},i)


def test_explicit_stopped_reference_prefix_requires_every_read():
    p=dict(schema_version='twomm-training-plan-2',checkpoint_steps=[0,2,3],
        evaluations=[dict(step=s,roles=['optimizer','evaluator']) for s in (0,2,3)])
    scope=StagedReferences(items(),Path('/tmp'),lambda:None,p)
    for stage in p['evaluations'][:2]:
        scope.open(stage,lambda:None);b=scope.budgets[-1]
        for d in b.expected.values():b.remaining(d);b.record(dict(compressed_bytes=10,expanded_bytes=20))
    assert scope.completed(through_step=2)['files']==4
    with pytest.raises(ValueError):scope.completed()
    with pytest.raises(ValueError):scope.completed(through_step=1)


def test_proposed_membership_1200_exposures_and_cadence():
    b={'roles':{'optimizer':[{'descriptor':{'study_id':str(j)}} for j in range(113)]}}
    members=[m.schedule(b,42,j)[0] for j in range(1200)]
    assert sorted(members.count(j) for j in range(113))==[10]*43+[11]*70
    assert launch.plan()['checkpoint_steps']==[0,300,600,900,1200]
    assert launch.plan()['coverage_guard']==REAL_POLICY and launch.plan()['total_seconds']==5400
