"""New event observations, strict binding, and unchanged legacy recovery."""
import json
import uuid
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator, FormatChecker
from src.operations.workflow_execution_v1 import read_record
from src.operations.workflow_plan_v1 import sha
from test_workflow_execution_v1 import setup
from test_workflow_resource_schema_v1 import replace_record

NEW_FIELDS = {'schema','event_id','run_id','attempt','observed_at'}
SCHEMA = json.loads((Path(__file__).parents[1]/'docs/capstone/contracts/offline-workflow-event-v2.schema.json').read_text())


def rewrite(folder, mutate, legacy=False):
    request = read_record(folder/'request.json')
    if legacy:
        request.pop('event_schema')
        replace_record(folder/'request.json', request)
    previous = None
    for i,p in enumerate(sorted(folder.glob('event-*.json'))):
        event = read_record(p)
        if legacy:
            for key in NEW_FIELDS: event.pop(key)
        mutate(i,event)
        event.update(previous=previous,request_sha256=sha(request))
        replace_record(p,event); previous=sha(event)


def test_new_records_validate_and_resume_has_fresh_event_ids(tmp_path):
    validator=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
    validator.check_schema(SCHEMA)
    e,s,h,v=setup(tmp_path); a=e.execute(s,h,v); b=e.execute(s,h,v,resume_of=a['run_id'])
    ids=[]
    for snapshot in (a,b):
        for p in (tmp_path/'runs'/snapshot['run_id']).glob('event-*.json'):
            event=json.loads(p.read_text()); validator.validate(event)
            assert event['attempt']==1  # Explicit resume creates a distinct run, no in-run retry.
            ids.append(event['event_id'])
    assert len(ids)==len(set(ids))
    assert set(b['stages'].values())=={'reused'}


@pytest.mark.parametrize('fault',['duplicate','run','timestamp','zone','attempt','bool','version','downgrade'])
def test_rehashed_invalid_event_identity_rejected(tmp_path,fault):
    e,s,h,v=setup(tmp_path); a=e.execute(s,h,v); folder=tmp_path/'runs'/a['run_id']; first=a['events'][0]['event_id']
    def mutate(i,event):
        if i!=1:return
        if fault=='duplicate':event['event_id']=first
        if fault=='run':event['run_id']=str(uuid.uuid4())
        if fault=='timestamp':event['observed_at']='invalid+00:00'
        if fault=='zone':event['observed_at']='2026-10-27T10:00:00'
        if fault=='attempt':event['attempt']=2
        if fault=='bool':event['attempt']=True
        if fault=='version':event['schema']='unknown'
        if fault=='downgrade':
            for k in NEW_FIELDS:event.pop(k)
    rewrite(folder,mutate)
    with pytest.raises(ValueError):e.inspect(a['run_id'])
    calls=[]
    with pytest.raises(ValueError):e.execute(s,{k:lambda p,c:calls.append(True) for k in h},v,resume_of=a['run_id'])
    assert not calls


def test_legacy_records_read_and_resume_without_inventing_observations(tmp_path):
    e,s,h,v=setup(tmp_path); a=e.execute(s,h,v); folder=tmp_path/'runs'/a['run_id']
    rewrite(folder,lambda i,e:None,legacy=True)
    old={p:p.read_bytes() for p in folder.iterdir()}
    snapshot=e.inspect(a['run_id'])
    assert all(not NEW_FIELDS.intersection(row) for row in snapshot['events'])
    resumed=e.execute(s,h,v,resume_of=a['run_id'])
    assert set(resumed['stages'].values())=={'reused'}
    assert all(row['schema']=='offline-workflow-event-v2' for row in resumed['events'])
    assert old=={p:p.read_bytes() for p in folder.iterdir()}


def test_failed_stage_schema_preserves_error_and_blocks_descendant(tmp_path):
    e,s,h,v=setup(tmp_path); identity=str(uuid.uuid4())
    h['source']=lambda p,c: (_ for _ in ()).throw(RuntimeError('invented failure'))
    with pytest.raises(RuntimeError):e.execute(s,h,v,identity=identity)
    snapshot=e.inspect(identity)
    assert snapshot['stages']=={'source':'failed','finish':'pending'}
    validator=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
    for p in (tmp_path/'runs'/identity).glob('event-*.json'):
        validator.validate(json.loads(p.read_text()))
    failed=json.loads((tmp_path/'runs'/identity/'event-0002.json').read_text())
    failed['reference']={'artifact_id':'fake','derivation':'a'*64,'receipt_sha256':'b'*64}
    assert list(validator.iter_errors(failed))
