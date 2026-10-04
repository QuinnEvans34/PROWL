from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.diagnostics import twomm_inference_continuation as c
from src.data.manifest_records import canonical,digest

@pytest.fixture
def binding():
    b={'roles':{role:[{'descriptor':dict(study_id=f'{role}-fixture-{i}',operation=role,
        protected_role='train' if role=='optimizer' else 'validation')} for i in range(n)]
        for role,n in [('optimizer',113),('evaluator',40)]}}
    for row in c.pilot.CASES:b['roles'][row['role']][row['index']]['descriptor']['study_id']=row['study_id']
    return b


def test_exact_complement_and_roles(binding):
    rows=c.cases(binding)
    assert len(rows)==145 and sum(r['role']=='optimizer' for r in rows)==107
    assert not any(r in c.pilot.CASES for r in rows)
    assert len({r['study_id'] for r in rows+c.pilot.CASES})==153

@pytest.mark.parametrize('fault',['missing','extra','duplicate','role','pilot_ancestry'])
def test_bad_full_binding_refused(binding,fault):
    rows=binding['roles']['optimizer']
    if fault=='missing':rows.pop()
    if fault=='extra':rows.append(deepcopy(rows[0]))
    if fault=='duplicate':rows[1]['descriptor']['study_id']=rows[0]['descriptor']['study_id']
    if fault=='role':rows[0]['descriptor']['protected_role']='validation'
    if fault=='pilot_ancestry':rows[76]['descriptor']['study_id']='changed'
    with pytest.raises(ValueError):c.cases(binding)

@pytest.fixture
def frozen(tmp_path,binding,monkeypatch):
    monkeypatch.setattr(c,'ROOT',tmp_path);monkeypatch.setattr(c,'check_pilot',lambda:None)
    dest=tmp_path/'twomm-session-continuation-fixture';dest.mkdir()
    raw=canonical(binding);pin=digest(raw);monkeypatch.setattr(c,'BINDING_PIN',pin)
    controls={'inputs.json':raw,'source.json':b'source','environment.json':b'env'}
    for n,v in controls.items():(dest/n).write_bytes(v)
    r=dict(schema_version='twomm-continuation-1',approval='D-303',operation='remaining145-zero-update-inference',
        cache=str(c.CACHE),cache_pin=c.CACHE_PIN,binding_pin=pin,cases=c.cases(binding),pilot_receipt_sha256=c.PILOT_PIN,
        limits=deepcopy(c.LIMITS),config=c.config(),files={n:digest(v) for n,v in controls.items()},
        storage_ceilings=[1,2],run_id=dest.name)
    (dest/'request.json').write_bytes(canonical(r));monkeypatch.setattr(c,'capture',lambda:(b'source',b'env'))
    return dest,r


def test_new_request_valid_and_consumed_once(frozen):
    dest,r=frozen;pin=digest(canonical(r));assert c.checked_request(dest,pin)==r
    c.claim(dest,pin)
    with pytest.raises(FileExistsError):c.claim(dest,pin)

@pytest.mark.parametrize('fault',['missing','duplicate','pilot_member','order','pilot_pin','budget','old_schema','cache','source'])
def test_wrong_continuation_request_refused(frozen,fault):
    dest,r=frozen
    if fault=='missing':r['cases'].pop()
    if fault=='duplicate':r['cases'][1]=r['cases'][0]
    if fault=='pilot_member':r['cases'][0]=c.pilot.CASES[0]
    if fault=='order':r['cases'].reverse()
    if fault=='pilot_pin':r['pilot_receipt_sha256']='0'*64
    if fault=='budget':r['limits']['seconds']*=2
    if fault=='old_schema':r['schema_version']='twomm-pilot-1'
    if fault=='cache':r['cache_pin']='0'*64
    if fault=='source':(dest/'source.json').write_bytes(b'changed')
    (dest/'request.json').write_bytes(canonical(r))
    with pytest.raises(ValueError):c.checked_request(dest,digest(canonical(r)))


def test_changed_pilot_evidence_refused(tmp_path,monkeypatch):
    p=tmp_path/'pilot';p.mkdir();b=b'evidence';(p/'profile.json').write_bytes(b)
    receipt=canonical(dict(state='complete',real_updates=0,files={'profile.json':dict(bytes=len(b),sha256=digest(b))}))
    (p/'receipt.json').write_bytes(receipt);monkeypatch.setattr(c,'PILOT',p);monkeypatch.setattr(c,'PILOT_PIN',digest(receipt))
    c.check_pilot();(p/'profile.json').write_bytes(b'changed')
    with pytest.raises(ValueError,match='evidence changed'):c.check_pilot()

@pytest.mark.parametrize('fault',[None,'duplicate','model','missing'])
def test_full153_reconciliation(frozen,tmp_path,monkeypatch,fault):
    dest,r=frozen;pilot=tmp_path/'pilot';pilot.mkdir();monkeypatch.setattr(c,'PILOT',pilot)
    def profile(rows):return dict(weights_sha256='a'*64,cases=[dict(x,transform_sha256='b'*64) for x in rows])
    prior=profile(c.pilot.CASES);current=profile(r['cases'])
    if fault=='duplicate':current['cases'][0]=prior['cases'][0]
    if fault=='model':current['weights_sha256']='c'*64
    if fault=='missing':current['cases'].pop()
    (pilot/'profile.json').write_bytes(canonical(prior));(dest/'profile.json').write_bytes(canonical(current))
    if fault:
        with pytest.raises(ValueError):c.reconcile(dest)
        assert not (dest/'aggregate.json').exists()
    else:
        record=c.reconcile(dest);assert record['counts']==dict(optimizer=113,evaluator=40)
        assert len(record['members'])==153


def test_continuation_keeps_memory_and_free_limits():
    assert c.LIMITS['rss_bytes']==c.pilot.LIMITS['rss_bytes']==16*1024**3
    assert c.LIMITS['free_bytes']==100*1024**3 and c.LIMITS['seconds']==1200
    assert c.stop_reason(0,0,5*1024**3,200*1024**3,True)=='output_cap'


def test_continuation_interruption_cleanup(tmp_path,monkeypatch):
    import test_twomm_inference_pilot as previous
    monkeypatch.setattr(previous,'pilot',c)
    previous.test_interrupted_supervisor_terminates_and_preserves_failure(tmp_path,monkeypatch)
