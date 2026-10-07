from copy import deepcopy
from types import SimpleNamespace
import os
import pytest
from segmenter_duration_fixtures import request
from src.data import segmenter_duration_targets_v1 as t
from src.training import segmenter_duration_executor_v1 as e

@pytest.fixture(scope='module')
def real():return request('scientific')

def test_50_target_reads_separate_stages_no_ct(real):
    r,p=real;t.validate_scope(r['targets'],p.control)
    stages=[t.stage_scope(r['targets'],n) for n in t.STEPS]
    assert [len(v['files']) for v in stages]==[12,12,12,14]
    assert sum(len(v['files']) for v in stages)==r['targets']['logical_target_reads']==50
    assert all(v['kind'] in ('pancreas','lesion') for v in r['targets']['files'])
    assert all(r['targets']['limits'][k]==sum(v['limits'][k] for v in stages) for k in r['targets']['limits'])
    assert all([c['protected_role'] for c in v['cases']]==['train']*6 for v in stages[:-1])

@pytest.mark.parametrize('fault',['role','reads','bytes','stage','operation','write','pin','image'])
def test_source_scope_refuses_drift(real,fault):
    r,p=real;s=deepcopy(r['targets'])
    if fault=='role':s['cases'][0]['protected_role']='validation'
    if fault=='reads':s['logical_target_reads']=14
    if fault=='bytes':s['stage_limits']['48']['hash_bytes']+=1
    if fault=='stage':s['stage']='old_consumed_stage'
    if fault=='operation':s['capability']['operations'].append('ct_read')
    if fault=='write':s['capability']['source_writes']=True
    if fault=='pin':s['cases'][0]['transform_sha256']='0'*64
    if fault=='image':s['cases'][0]['image_sha256']='0'*64
    with pytest.raises(ValueError):t.validate_scope(s,p.control)

@pytest.mark.parametrize('step',[0,47,49,193,True])
def test_off_cadence_target_read_refused(real,step):
    with pytest.raises(ValueError):t.stage_scope(real[0]['targets'],step)

def test_refused_case_stays_consumed_and_bytes_are_retained(tmp_path,real,monkeypatch):
    r,p=deepcopy(real);r['targets']['capability']['source_root']=str(tmp_path)
    c=r['targets']['cases'][0];p._session=SimpleNamespace(select=lambda *a:c['descriptor'],records={});p._binding={'records':{}}
    reader=object.__new__(t.RealTargets);reader.provider=p;reader.request=r;reader.grant=None;reader.used=set();reader.counts={k:0 for k in r['targets']['limits']};reader.stage_counts={str(n):{k:0 for k in reader.counts} for n in t.STEPS};reader.mount_before=reader.mount_after=None
    st=tmp_path.stat();monkeypatch.setattr(e,'checked_grant',lambda *a:None)
    monkeypatch.setattr(t.source,'mount_guard',lambda cap:dict(root_device=st.st_dev,root_inode=st.st_ino))
    calls=[]
    def refuse(fd,d,rows,counts,limits,tick):
        calls.append('invented refused read');counts['hash_bytes']+=17;raise ValueError('invented content refusal')
    monkeypatch.setattr(t.scoring,'read_targets',refuse)
    session=SimpleNamespace(identity=r['identity'],step=48,dirty=False)
    with pytest.raises(ValueError,match='invented content refusal'):reader.read(session,c['study_id'])
    assert reader.used=={(48,c['study_id'])} and reader.counts['hash_bytes']==17
    with pytest.raises(ValueError,match='repeated'):reader.read(session,c['study_id'])
    assert len(calls)==1

def test_report_denied_before_source_observation(real,monkeypatch):
    r,p=real;reader=object.__new__(t.RealTargets);reader.request=r;reader.provider=p;reader.grant=None;reader.used=set()
    monkeypatch.setattr(e,'checked_grant',lambda *a:None);monkeypatch.setattr(t.source,'mount_guard',lambda *a:pytest.fail('Premature report touched source'))
    session=SimpleNamespace(identity=r['identity'],step=48,dirty=False)
    with pytest.raises(ValueError):reader.read(session,p.control['validation'][0])
