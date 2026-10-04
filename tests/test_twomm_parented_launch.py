from retained_diagnostic_metadata import metadata as retained_metadata
from copy import deepcopy
import json
from pathlib import Path
import pytest
from src.data.manifest_records import canonical,digest
from src.data import twomm_training_references as refs
from scripts.diagnostics import twomm_parented_launch as launch
from test_twomm_training_long_launch import items


def request(tmp_path,monkeypatch,zero):
    saved=retained_metadata();parent=saved['parent_reference'];probe=saved['parent_probe']
    monkeypatch.setattr(launch,'ROOT',tmp_path);monkeypatch.setattr(launch,'parent_reference',lambda:deepcopy(parent));monkeypatch.setattr(launch,'parent_probe',lambda:deepcopy(probe))
    monkeypatch.setattr(launch,'checked_qualification',lambda *a:dict(qualified=True))
    d=tmp_path/'twomm-training-test';d.mkdir();b={'roles':{r:[{'descriptor':x} for x in ds] for r,ds in items().items()}}
    binding=canonical(b);monkeypatch.setattr(launch,'REAL_BINDING',digest(binding));monkeypatch.setattr(launch,'capture',lambda:(b'src',b'env'))
    monkeypatch.setattr(refs,'mount_observation',lambda *a:dict(scope='invented'))
    files={'inputs.json':binding,'source.json':b'src','environment.json':b'env','plan.json':canonical(launch.plan(zero)),
        'reference-scope.json':canonical(refs.scope(b,launch.plan(zero))),'mount-observation.json':canonical(dict(scope='invented')),
        'parent-reference.json':canonical(parent),'parent-probe.json':canonical(probe),'parent-qualification.json':canonical(dict(path=str(tmp_path),sha256='a'*64)),
        'design.md':b'design','rehearsal.json':b'{}'}
    for n,v in files.items():(d/n).write_bytes(v)
    r=dict(zero_update=zero,schema_version='twomm-training-request-4',experiment='CAP-EXP-010',state='prepared_not_authorized',limits=launch.limits(zero),
        files={n:digest(v) for n,v in files.items()},cache_receipt_sha256=launch.REAL_CACHE,run_id=d.name)
    raw=canonical(r);(d/'request.json').write_bytes(raw);return d,digest(raw)

@pytest.mark.parametrize('zero',[True,False])
def test_distinct_profile_and_training_scope_and_approval(tmp_path,monkeypatch,zero):
    d,p=request(tmp_path,monkeypatch,zero);assert launch.checked_request(d,p)['zero_update']==zero
    op='qualify_CAP-EXP-010_parent' if zero else 'launch_CAP-EXP-010'
    a=canonical(dict(allowed=True,authority='Quinton Evans',operation=op,request_sha256=p));assert launch.checked_request(d,p,approval=a,approval_pin=digest(a))
    wrong=canonical(dict(allowed=True,authority='Quinton Evans',operation='wrong',request_sha256=p))
    with pytest.raises(ValueError):launch.checked_request(d,p,approval=wrong,approval_pin=digest(wrong))

@pytest.mark.parametrize('fault',['source','parent','probe','qualification','mode','limits','mount','plan','scope'])
def test_parented_request_drift_refused(tmp_path,monkeypatch,fault):
    d,p=request(tmp_path,monkeypatch,False)
    if fault=='source':monkeypatch.setattr(launch,'capture',lambda:(b'changed',b'env'))
    elif fault=='parent':(d/'parent-reference.json').write_text('{}')
    elif fault=='probe':(d/'parent-probe.json').write_text('{}')
    elif fault=='qualification':
        def reject(*a):raise ValueError('Unqualified')
        monkeypatch.setattr(launch,'checked_qualification',reject)
    elif fault=='mount':monkeypatch.setattr(refs,'mount_observation',lambda *a:dict(scope='changed'))
    elif fault=='plan':(d/'plan.json').write_text('{}')
    elif fault=='scope':(d/'reference-scope.json').write_text('{}')
    else:
        r=json.loads((d/'request.json').read_bytes())
        if fault=='mode':r['zero_update']=True
        else:r['limits']['seconds']=9999
        raw=canonical(r);(d/'request.json').write_bytes(raw);p=digest(raw)
    with pytest.raises(ValueError):launch.checked_request(d,p)


def test_real_reference_scopes_and_offsets():
    b=retained_metadata()['binding'];q=refs.scope(b,launch.plan(True));t=refs.scope(b,launch.plan(False))
    assert q['files']==40 and t['files']==233 and q['ct_files']==t['ct_files']==0
    assert [s['files'] for s in t['stages']]==[40,40,153]
    from src.training.twomm_parented_training import schedule
    chosen=[schedule(b,42,k)[0] for k in range(600)];assert sorted(chosen.count(j) for j in range(113))==[5]*78+[6]*35
