from copy import deepcopy
import json
from pathlib import Path
import pytest
from src.data.manifest_records import canonical,digest
from src.data import twomm_training_references as refs
from scripts.diagnostics import twomm_training_long_launch as launch


def items():
    return {role:[dict(study_id='synthetic-'+role,operation=role,protected_role='train' if role=='optimizer' else 'validation',
        target_scope='visible_reference_not_whole_organ',rows={'pancreas':dict(uri=role,bytes=10,expanded_bytes=20)})]
        for role in ('optimizer','evaluator')}


def test_stage_scope_counts_repeated_uses_separately():
    ds=items();binding={'roles':{r:[{'descriptor':d} for d in rows] for r,rows in ds.items()}}
    s=refs.scope(binding,launch.plan());assert s['files']==7 and s['compressed_bytes']==70 and s['expanded_bytes']==140


def test_stage_claim_no_replay_and_no_incomplete_advance():
    p={'evaluations':[dict(step=0,roles=['optimizer','evaluator']),dict(step=2,roles=['evaluator'])]}
    scope=refs.StagedReferences(items(),Path('/tmp'),lambda:None,p)
    ds=scope.open(p['evaluations'][0],lambda:None);assert set(ds)=={'optimizer','evaluator'}
    with pytest.raises(ValueError,match='order'):scope.open(p['evaluations'][0],lambda:None)
    with pytest.raises(ValueError,match='Incomplete'):scope.open(p['evaluations'][1],lambda:None)
    with pytest.raises(ValueError,match='Incomplete'):scope.completed()


def test_stage_completed_counts_and_mutation():
    p={'evaluations':[dict(step=0,roles=['optimizer','evaluator']),dict(step=2,roles=['evaluator'])]}
    scope=refs.StagedReferences(items(),Path('/tmp'),lambda:None,p)
    for stage in p['evaluations']:
        scope.open(stage,lambda:None);b=scope.budgets[-1]
        for row in b.expected.values():b.remaining(row);b.record(dict(compressed_bytes=10,expanded_bytes=20))
    assert scope.completed()==dict(files=3,compressed_bytes=30,expanded_bytes=60,ct_files=0)
    with pytest.raises(ValueError):scope.open(p['evaluations'][-1],lambda:None)
    other=refs.StagedReferences(items(),Path('/tmp'),lambda:None,p);other._plan['evaluations'][0]['step']=1
    with pytest.raises(ValueError,match='changed'):other.open(p['evaluations'][0],lambda:None)


def request(tmp_path,monkeypatch):
    monkeypatch.setattr(launch,'ROOT',tmp_path)
    d=tmp_path/'twomm-training-fixture';d.mkdir()
    binding={'roles':{r:[{'descriptor':x} for x in ds] for r,ds in items().items()}}
    raw=canonical(binding);monkeypatch.setattr(launch,'REAL_BINDING',digest(raw))
    monkeypatch.setattr(refs,'mount_observation',lambda repo,b:dict(scope='synthetic mount observation'))
    files={'inputs.json':raw,'source.json':b'source','environment.json':b'environment',
        'plan.json':canonical(launch.plan()),'reference-scope.json':canonical(refs.scope(binding,launch.plan())),
        'design.md':b'design','rehearsal.json':b'{}','mount-observation.json':canonical(dict(scope='synthetic mount observation'))}
    for n,v in files.items():(d/n).write_bytes(v)
    r=dict(schema_version='twomm-training-request-2',experiment='CAP-EXP-008',state='prepared_not_authorized',
        limits=launch.LIMITS,files={n:digest(v) for n,v in files.items()},cache_receipt_sha256=launch.REAL_CACHE,run_id=d.name)
    raw=canonical(r);(d/'request.json').write_bytes(raw);monkeypatch.setattr(launch,'capture',lambda:(b'source',b'environment'))
    return d,digest(raw)


def test_request_is_prepared_and_separate_exact_approval_required(tmp_path,monkeypatch):
    d,p=request(tmp_path,monkeypatch);assert launch.checked_request(d,p)['state']=='prepared_not_authorized'
    a=canonical(dict(allowed=True,authority='Quinton Evans',operation='launch_CAP-EXP-008',request_sha256=p))
    assert launch.checked_request(d,p,approval=a,approval_pin=digest(a))
    for key,value in [('allowed',False),('authority','Codex'),('request_sha256','a'*64),('operation','other')]:
        bad=json.loads(a);bad[key]=value;raw=canonical(bad)
        with pytest.raises(ValueError,match='approval'):launch.checked_request(d,p,approval=raw,approval_pin=digest(raw))

@pytest.mark.parametrize('fault',['source','plan','cap','file','symlink','pin','reference','mount'])
def test_request_faults(tmp_path,monkeypatch,fault):
    d,p=request(tmp_path,monkeypatch)
    if fault=='source':monkeypatch.setattr(launch,'capture',lambda:(b'changed',b'environment'))
    elif fault=='pin':p='0'*64
    elif fault=='symlink':(d/'design.md').unlink();(d/'design.md').symlink_to(d/'source.json')
    elif fault=='reference':(d/'reference-scope.json').write_text('{}')
    elif fault=='mount':monkeypatch.setattr(refs,'mount_observation',lambda repo,b:dict(scope='changed device'))
    elif fault=='plan':(d/'plan.json').write_text('{}')
    elif fault=='file':(d/'inputs.json').write_text('{}')
    else:
        r=json.loads((d/'request.json').read_bytes());r['limits']=dict(r['limits'],seconds=99999)
        raw=canonical(r);(d/'request.json').write_bytes(raw);p=digest(raw)
    with pytest.raises(ValueError):launch.checked_request(d,p)
