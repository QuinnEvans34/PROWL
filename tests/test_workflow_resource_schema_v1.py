"""CPU fault checks: bounded records, capacity changes and downstream exclusion."""
import json
import uuid
import pytest
from src.operations.workflow_execution_v1 import read_record
from src.operations.workflow_plan_v1 import encoded, sha
from test_workflow_execution_v1 import setup


def replace_record(path, value):
    path.write_bytes(encoded(dict(value, content_sha256=sha(value))))


@pytest.mark.parametrize('fault', ['version', 'extra', 'parent'])
def test_invalid_run_contract_blocks_recovery(tmp_path, fault):
    e, stages, handlers, validators = setup(tmp_path)
    first = e.execute(stages, handlers, validators)
    path = tmp_path/'runs'/first['run_id']/'request.json'
    request = read_record(path)
    if fault == 'version': request['schema'] = 'workflow-run-v999'
    if fault == 'extra': request['execute_shell'] = 'not permitted'
    if fault == 'parent': request['resume_of'] = '../outside'
    replace_record(path, request)
    # Rebind event hashes too: validity must not depend solely on hash mismatches.
    previous = None
    for event_path in sorted(path.parent.glob('event-*.json')):
        event = read_record(event_path)
        event.update(request_sha256=sha(request), previous=previous)
        replace_record(event_path, event)
        previous = sha(event)
    with pytest.raises(ValueError): e.inspect(first['run_id'])
    calls = []
    with pytest.raises(ValueError):
        e.execute(stages, {k: lambda p,c: calls.append(k) for k in handlers}, validators, resume_of=first['run_id'])
    assert not calls


@pytest.mark.parametrize('fault', ['extra', 'error_on_complete', 'bad_receipt'])
def test_invalid_event_contract_blocks_inspection(tmp_path, fault):
    e,s,h,v = setup(tmp_path); first = e.execute(s,h,v)
    path = sorted((tmp_path/'runs'/first['run_id']).glob('event-*.json'))[-1]
    event = read_record(path)
    if fault == 'extra': event['execute_shell'] = 'not permitted'
    if fault == 'error_on_complete': event['error'] = 'contradictory result'
    if fault == 'bad_receipt': event['reference']['receipt_sha256'] = 'z'*64
    replace_record(path,event)
    with pytest.raises(ValueError): e.inspect(first['run_id'])


@pytest.mark.parametrize('floor', [-1, True, float('nan'), '50GB'])
def test_invalid_capacity_policy_rejected(tmp_path, floor):
    from src.operations.workflow_execution_v1 import Executor
    with pytest.raises(ValueError): Executor(tmp_path,check_root=lambda:None,minimum_free_bytes=floor)


def test_capacity_loss_after_compute_never_publishes_or_calls_descendant(tmp_path, monkeypatch):
    e,s,h,v = setup(tmp_path); identity = str(uuid.uuid4()); called = []
    from types import SimpleNamespace
    def source(p,c):
        monkeypatch.setattr('os.fstatvfs', lambda fd: SimpleNamespace(f_bavail=0, f_frsize=4096))
        return {'value.json': b'1'}
    h['source'] = source; h['finish'] = lambda p,c: called.append(True)
    with pytest.raises((ValueError,OSError),match='[Cc]apacity'): e.execute(s,h,v,identity=identity)
    assert not called
    assert not list((tmp_path/'artifacts').glob('*/complete.json'))
    assert e.inspect(identity)['state'] == 'incomplete'  # No space to journal failure safely.


def test_output_budget_rejects_without_downstream(tmp_path):
    e,s,h,v = setup(tmp_path); identity = str(uuid.uuid4()); called=[]
    h['source'] = lambda p,c: {'value.json': b'x'*(8*1024**2+1)}
    h['finish'] = lambda p,c: called.append(True)
    with pytest.raises(ValueError,match='budget'): e.execute(s,h,v,identity=identity)
    assert not called
    assert e.inspect(identity)['state']=='failed'
    assert not list((tmp_path/'artifacts').glob('*/complete.json'))
