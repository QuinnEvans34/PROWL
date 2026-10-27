"""CPU lifecycle observation, provenance tampering and recovery boundaries."""
import json
import fcntl
import uuid
import pytest
from src.operations.workflow_contracts_v1 import execute_registered
from src.operations.workflow_execution_v1 import read_record
from src.operations.workflow_lifecycle_v1 import inspect_lifecycle
from src.operations.workflow_plan_v1 import sha,encoded
from src.operations.saved_package_workflow_v1 import definition
from test_saved_package_workflow_v1 import setup
from test_workflow_resource_schema_v1 import replace_record


def test_completed_reused_runs_have_actual_lock_and_terminal_observations(setup):
    source,pin,e=setup;s,h,v=definition(source,pin)
    first=execute_registered(e,'saved-package',s,h,v)
    before={p:p.read_bytes() for p in (e.root/'contracts'/first['run_id']).iterdir()}
    second=execute_registered(e,'saved-package',s,h,v,resume_of=first['run_id'])
    for result in (first,second):
        seen=inspect_lifecycle(e,result['run_id'],snapshot=e.inspect(result['run_id']),require_terminal=True)
        assert [x['event_type'] for x in seen['events']]==['run_planned','lock_acquired','run_started','lock_released','run_completed']
        assert seen['lock_release_observed']
        assert result['request']['provenance']==seen['provenance']
    assert before=={p:p.read_bytes() for p in before}


@pytest.mark.parametrize('target',['registry','environment','context'])
def test_provenance_tampering_blocks_resume_before_callbacks(setup,target):
    source,pin,e=setup;s,h,v=definition(source,pin);a=execute_registered(e,'saved-package',s,h,v)
    folder=e.root/'contracts'/a['run_id']
    if target=='context':
        p=folder/'context.json';c=read_record(p);c['code']['git_commit']='0'*40;replace_record(p,c)
    elif target=='environment':(folder/'environment.json').write_bytes(encoded([]))
    else:
        p=folder/'resolved-config.json';c=json.loads(p.read_bytes());c['registry']['workflows']['saved-package']['integrity']['output_members']=['other.json']
        p.write_bytes(encoded(c))
        # Rehash the context too; the immutable run request must still reject it.
        context=read_record(folder/'context.json');context['resolved_config_sha256']=sha(c);context['registry_sha256']=sha(c['registry']);replace_record(folder/'context.json',context)
    calls=[]
    with pytest.raises(ValueError):e.execute(s,{k:lambda p,c:calls.append(True) for k in h},v,resume_of=a['run_id'])
    assert not calls


@pytest.mark.parametrize('fault',['release_before_acquire','duplicate_id','wrong_run','terminal','extra','process','binding'])
def test_rehashed_lifecycle_corruption_rejected(setup,fault):
    source,pin,e=setup;s,h,v=definition(source,pin);a=execute_registered(e,'saved-package',s,h,v)
    paths=sorted((e.root/'contracts'/a['run_id']).glob('lifecycle-*.json'))
    first=read_record(paths[0]);previous=None
    for index,p in enumerate(paths):
        x=read_record(p)
        if index==1:
            if fault=='release_before_acquire':x['event_type']='lock_released'
            if fault=='duplicate_id':x['event_id']=first['event_id']
            if fault=='wrong_run':x['run_id']=str(uuid.uuid4())
            if fault=='terminal':x['event_type']='run_completed'
            if fault=='extra':x['shell']='no'
            if fault=='process':x['process']['pid']+=1
            if fault=='binding':x['provenance']['registry_sha256']='0'*64
        x['previous']=previous;replace_record(p,x);previous=sha(x)
    with pytest.raises(ValueError):e.inspect(a['run_id'])


def test_lock_conflict_records_failure_without_claiming_acquisition(setup):
    source,pin,e=setup;s,h,v=definition(source,pin);identity=str(uuid.uuid4())
    with e.locked():
        with pytest.raises(BlockingIOError):execute_registered(e,'saved-package',s,h,v,identity=identity)
    seen=inspect_lifecycle(e,identity,require_terminal=True)
    assert [x['event_type'] for x in seen['events']]==['run_planned','run_failed']
    assert not seen['lock_release_observed']
    assert not (e.root/'runs'/identity).exists()


def test_stage_failure_records_release_and_preserves_error(setup):
    source,pin,e=setup;s,h,v=definition(source,pin);identity=str(uuid.uuid4())
    h['integrity']=lambda p,c: (_ for _ in ()).throw(RuntimeError('original error'))
    with pytest.raises(RuntimeError,match='original error'):execute_registered(e,'saved-package',s,h,v,identity=identity)
    seen=inspect_lifecycle(e,identity,snapshot=e.inspect(identity),require_terminal=True)
    assert [x['event_type'] for x in seen['events']][-2:]==['lock_released','run_failed']
    assert seen['events'][-1]['details']['error']=='RuntimeError: original error'


def test_missing_terminal_is_incomplete_not_invented_cleanup(setup):
    source,pin,e=setup;s,h,v=definition(source,pin);a=execute_registered(e,'saved-package',s,h,v)
    folder=e.root/'contracts'/a['run_id']
    (folder/'lifecycle-0005.json').unlink();(folder/'lifecycle-0004.json').unlink()
    seen=inspect_lifecycle(e,a['run_id'],snapshot=e.inspect(a['run_id']))
    assert not seen['terminal'] and not seen['lock_release_observed']
    with pytest.raises(ValueError,match='incomplete'):inspect_lifecycle(e,a['run_id'],require_terminal=True)


def test_lifecycle_schema_matches_success_and_failed_records(setup):
    from pathlib import Path
    from jsonschema import Draft202012Validator,FormatChecker
    schema=json.loads((Path(__file__).parents[1]/'docs/capstone/contracts/offline-workflow-lifecycle-v1.schema.json').read_text())
    check=Draft202012Validator(schema,format_checker=FormatChecker());check.check_schema(schema)
    source,pin,e=setup;s,h,v=definition(source,pin);execute_registered(e,'saved-package',s,h,v)
    h['integrity']=lambda p,c: (_ for _ in ()).throw(RuntimeError('synthetic failure'))
    with pytest.raises(RuntimeError):execute_registered(e,'saved-package',s,h,v)
    for path in (e.root/'contracts').glob('*/lifecycle-*.json'):
        event=json.loads(path.read_bytes());check.validate(event)
        event['details']={'reason':'SIGTERM','error':'incompatible'}
        assert list(check.iter_errors(event))


def test_release_log_failure_does_not_mask_stage_error_or_hold_lock(setup,monkeypatch):
    from src.operations.workflow_lifecycle_v1 import Lifecycle
    source,pin,e=setup;s,h,v=definition(source,pin);identity=str(uuid.uuid4())
    original=Lifecycle.emit
    def emit(self,event,**details):
        if event=='lock_released':raise OSError('synthetic journal failure')
        return original(self,event,**details)
    monkeypatch.setattr(Lifecycle,'emit',emit)
    h['integrity']=lambda p,c: (_ for _ in ()).throw(RuntimeError('original stage error'))
    with pytest.raises(RuntimeError,match='original stage error') as error:
        execute_registered(e,'saved-package',s,h,v,identity=identity)
    assert any('Lock released' in n for n in error.value.__notes__)
    with e.locked():pass
    folder=e.root/'contracts'/identity
    assert (folder/'summary-unavailable.json').exists()
    assert not (folder/'run-manifest.json').exists()


def test_lost_summary_does_not_destroy_artifact_reuse_or_rewrite_attempt(setup):
    """The projection is disposable; authoritative request/events/receipts are not."""
    source,pin,e=setup;s,h,v=definition(source,pin)
    first=execute_registered(e,'saved-package',s,h,v)
    folder=e.root/'contracts'/first['run_id']
    (folder/'run-manifest.json').unlink()  # Fault injection only in a temporary invented run.
    before={p:p.read_bytes() for p in folder.iterdir()}
    assert e.inspect(first['run_id'])['lifecycle']['terminal']
    calls=[]
    later=execute_registered(e,'saved-package',s,{k:lambda p,c:calls.append(True) for k in h},v,resume_of=first['run_id'])
    assert not calls and set(later['stages'].values())=={'reused'}
    assert before=={p:p.read_bytes() for p in folder.iterdir()}
    assert (e.root/'contracts'/later['run_id']/'run-manifest.json').exists()
