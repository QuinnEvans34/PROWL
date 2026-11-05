import hashlib
import json
from pathlib import Path
import uuid

import pytest

from tests.test_autonomous_baseline_review import fixture, REQUEST, READY
from src.operations.autonomous_baseline_workflow_v1 import definition
from src.operations.workflow_execution_v1 import Executor
from src.operations.workflow_contracts_v1 import execute_registered


@pytest.fixture
def setup(tmp_path):
    source=tmp_path/'export.json';source.write_text(json.dumps(fixture()))
    pin=hashlib.sha256(source.read_bytes()).hexdigest()
    root=tmp_path/'workflow';root.mkdir()
    executor=Executor(root,check_root=lambda:None,minimum_free_bytes=0)
    return source,pin,executor


def stages(setup):
    source,pin,executor=setup
    return definition(source,pin,REQUEST,READY)


def test_registered_run_then_reuse_keeps_all_failures_and_no_review_decision(setup):
    source,pin,e=setup;s,h,v=stages(setup);before=source.read_bytes()
    first=execute_registered(e,'autonomous-baseline',s,h,v)
    assert set(first['stages'].values())=={'completed'}
    ref=first['events'][-1]['reference']
    files,_=e.store().resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=v['handoff'])
    handoff=json.loads(files['handoff.json'])
    assert handoff['aggregate']['requested']==70 and handoff['aggregate']['failed']==7
    assert handoff['review_decision'] is None and not handoff['independent_acceptance']
    assert not handoff['inference_recovery_qualified']
    assert handoff['scope']['probability_equivalence']=='UNQUALIFIED'
    def forbidden(*a):pytest.fail('reused producer called')
    second=execute_registered(e,'autonomous-baseline',s,{key:forbidden for key in h},v,resume_of=first['run_id'])
    assert set(second['stages'].values())=={'reused'}
    assert source.read_bytes()==before and e.inspect(first['run_id'])==first


def test_explicit_recovery_after_analysis_failure_reuses_admission_and_preserves_failure(setup):
    _,_,e=setup;s,h,v=stages(setup);identity=str(uuid.uuid4());called=[]
    def fail(*args):raise RuntimeError('injected analysis failure')
    with pytest.raises(RuntimeError,match='injected'):
        execute_registered(e,'autonomous-baseline',s,dict(h,analysis=fail),v,identity=identity)
    old=e.inspect(identity)
    assert old['stages']==dict(admission='completed',analysis='failed',handoff='pending')
    def admission(*a):pytest.fail('valid admission rerun')
    recovered=execute_registered(e,'autonomous-baseline',s,dict(h,admission=admission),v,resume_of=identity)
    assert recovered['stages']==dict(admission='reused',analysis='completed',handoff='completed')
    assert e.inspect(identity)==old


def test_changed_source_cannot_reuse_old_outputs_even_when_plan_pin_is_unchanged(setup):
    source,_,e=setup;s,h,v=stages(setup)
    first=execute_registered(e,'autonomous-baseline',s,h,v)
    source.write_text('{}')
    with pytest.raises(ValueError,match='SHA256'):
        execute_registered(e,'autonomous-baseline',s,h,v,resume_of=first['run_id'])
    assert e.inspect(first['run_id'])==first


def test_fresh_source_identity_invalidates_descendants_but_never_claims_new_inference(setup):
    source,_,e=setup;s,h,v=stages(setup);first=execute_registered(e,'autonomous-baseline',s,h,v)
    document=fixture();document['identities']['completion_sha256']='1'*64
    source.write_text(json.dumps(document));new_pin=hashlib.sha256(source.read_bytes()).hexdigest()
    s,h,v=definition(source,new_pin,REQUEST,READY)
    result=execute_registered(e,'autonomous-baseline',s,h,v,resume_of=first['run_id'])
    assert set(result['stages'].values())=={'completed'}


def test_bad_request_pin_blocks_before_analysis(setup):
    source,pin,e=setup;s,h,v=definition(source,pin,'0'*64,READY)
    h['analysis']=lambda *args:pytest.fail('downstream must not execute')
    with pytest.raises(ValueError,match='identity'):
        execute_registered(e,'autonomous-baseline',s,h,v)


def test_corrupt_published_analysis_refuses_reuse_without_regeneration(setup):
    from src.data.manifest_records import digest
    _,_,e=setup;s,h,v=stages(setup);first=execute_registered(e,'autonomous-baseline',s,h,v)
    ref=next(x['reference'] for x in first['events'] if x['stage']=='analysis' and x['state']=='completed')
    (e.root/'artifacts'/digest(ref['artifact_id'].encode())/'analysis.json').write_bytes(b'{}')
    def forbidden(*args):pytest.fail('corrupt artifact must not be silently regenerated')
    with pytest.raises(ValueError):
        execute_registered(e,'autonomous-baseline',s,{key:forbidden for key in h},v,resume_of=first['run_id'])


def test_explicit_relocation_of_identical_pinned_export_reuses_outputs(setup,tmp_path):
    source,pin,e=setup;s,h,v=stages(setup);first=execute_registered(e,'autonomous-baseline',s,h,v)
    retained=tmp_path/'retained-export.json';source.rename(retained)
    s,h,v=definition(retained,pin,REQUEST,READY)
    result=execute_registered(e,'autonomous-baseline',s,h,v,resume_of=first['run_id'])
    assert set(result['stages'].values())=={'reused'}
