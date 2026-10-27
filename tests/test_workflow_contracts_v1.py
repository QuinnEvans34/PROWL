import hashlib
import json
from pathlib import Path
import uuid

import pytest
from jsonschema import ValidationError
from src.operations.workflow_contracts_v1 import execute_registered, registry_for, validate, CONTRACTS
from src.operations.saved_package_workflow_v1 import definition
from src.operations.workflow_plan_v1 import Stage
from test_saved_package_workflow_v1 import setup


def verify_refs(root, manifest):
    refs=[manifest['resolved_config']]
    for stage in manifest['stages']:refs += stage['inputs']+stage['outputs']
    for ref in refs:
        path=root/ref['uri']
        assert path.is_relative_to(root)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==ref['content_sha256']
    env=manifest['environment']
    assert hashlib.sha256((root/env['environment_uri']).read_bytes()).hexdigest()==env['dependencies_sha256']


def test_actual_adapter_summary_and_reuse(setup):
    source,pin,e=setup;s,h,v=definition(source,pin)
    a=execute_registered(e,'saved-package',s,h,v)
    b=execute_registered(e,'saved-package',s,h,v,resume_of=a['run_id'])
    for result in [a,b]:
        raw=(e.root/'contracts'/result['run_id']/'run-manifest.json').read_bytes()
        m=json.loads(raw)
        validate(m,json.loads((CONTRACTS/'run-manifest.schema.json').read_bytes()))
        assert m['status']=='completed'
        assert m['run_id']=='run:'+result['run_id']
        for stage in m['stages']:
            events=[x for x in result['events'] if x['stage']==stage['stage_id']]
            assert stage['completed_at']==events[-1]['observed_at']
            if stage['status']=='reused':
                assert 'started_at' not in stage
            else:
                assert stage['started_at']==events[0]['observed_at']
            assert 'duration_seconds' not in stage
        verify_refs(e.root,m)
    assert set(b['stages'].values())=={'reused'}
    assert all(x['status']=='reused' for x in m['stages'])


@pytest.mark.parametrize('fault',['unknown','dependency','input','config','stage'])
def test_unregistered_contract_fails_before_run(setup,fault):
    source,pin,e=setup;s,h,v=definition(source,pin)
    kind='saved-package'
    if fault=='unknown':kind='training'
    if fault=='dependency':s[1]=Stage('handoff',producer='a'*64)
    if fault=='input':s[0]=Stage('integrity',inputs={'cohort':'a'*64},producer='a'*64)
    if fault=='config':s[0]=Stage('integrity',inputs={'saved_manifest':pin},config={'gpu':True},producer='a'*64)
    if fault=='stage':s.append(Stage('training',producer='a'*64))
    with pytest.raises(ValueError):execute_registered(e,kind,s,h,v)
    assert not list(e.root.iterdir())


def test_failed_stage_retains_failed_summary_and_no_output(setup):
    source,pin,e=setup;s,h,v=definition(source,pin);identity=str(uuid.uuid4())
    h['integrity']=lambda p,c: {'wrong.json':b'{}'}
    with pytest.raises(ValueError,match='inventory'):execute_registered(e,'saved-package',s,h,v,identity=identity)
    m=json.loads((e.root/'contracts'/identity/'run-manifest.json').read_bytes())
    assert m['status']=='failed'
    assert [r['status'] for r in m['stages']]==['failed','pending']
    assert m['stages'][0]['error']['retryable'] is False
    assert all(not r['outputs'] for r in m['stages'])
    verify_refs(e.root,m)


def test_run_manifest_schema_stays_strict(setup):
    source,pin,e=setup;s,h,v=definition(source,pin)
    a=execute_registered(e,'saved-package',s,h,v)
    m=json.loads((e.root/'contracts'/a['run_id']/'run-manifest.json').read_bytes())
    m['environment']['device']='gpu'  # Schema permits devices, registry does not dispatch one.
    m['created_at']='yesterday'
    with pytest.raises(ValidationError):validate(m,json.loads((CONTRACTS/'run-manifest.schema.json').read_bytes()))


def test_summary_failure_preserves_original_stage_error(setup,monkeypatch):
    import src.operations.workflow_contracts_v1 as module
    source,pin,e=setup;s,h,v=definition(source,pin);identity=str(uuid.uuid4())
    h['integrity']=lambda p,c: (_ for _ in ()).throw(RuntimeError('original failure'))
    monkeypatch.setattr(module,'export_summary',lambda *a: (_ for _ in ()).throw(ValueError('summary failure')))
    with pytest.raises(RuntimeError,match='original failure'):execute_registered(e,'saved-package',s,h,v,identity=identity)
    assert (e.root/'contracts'/identity/'summary-unavailable.json').exists()


def test_literature_adapter_uses_same_manifest_contract(setup,tmp_path):
    import shutil
    from test_case_literature_workflow_v1 import capture_fixture
    from src.operations.case_literature_workflow_v1 import definition as literature
    from src.operations.workflow_plan_v1 import encoded
    source,pin,e=setup
    capture=tmp_path/'capture.json';capture.write_bytes(encoded(capture_fixture()))
    node=shutil.which('node')
    assert node, 'Node24 required for production literature contract'
    s,h,v=literature(source,pin,capture,hashlib.sha256(capture.read_bytes()).hexdigest(),node=node)
    a=execute_registered(e,'case-literature',s,h,v)
    b=execute_registered(e,'case-literature',s,h,v,resume_of=a['run_id'])
    assert set(b['stages'].values())=={'reused'}
    m=json.loads((e.root/'contracts'/b['run_id']/'run-manifest.json').read_bytes())
    assert len(m['stages'])==4
    verify_refs(e.root,m)


def test_registry_rejects_gpu_resource_and_unknown_fields():
    from src.operations.workflow_contracts_v1 import REGISTRY
    schema=json.loads((CONTRACTS/'offline-stage-registry.schema.json').read_bytes())
    registry=json.loads(REGISTRY.read_bytes())
    registry['workflows']['saved-package']['integrity']['resource_class']='gpu'
    with pytest.raises(ValidationError):validate(registry,schema)


def test_context_change_cannot_be_exported_as_valid_summary(setup):
    from src.operations.workflow_contracts_v1 import export_summary
    source,pin,e=setup;s,h,v=definition(source,pin)
    a=execute_registered(e,'saved-package',s,h,v)
    p=e.root/'contracts'/a['run_id']/'resolved-config.json'
    original=(p.parent/'run-manifest.json').read_bytes()
    config=json.loads(p.read_bytes());config['minimum_free_bytes']=1;p.write_text(json.dumps(config))
    with pytest.raises(ValueError,match='configuration changed'):export_summary(e,a['run_id'],v)
    assert (p.parent/'run-manifest.json').read_bytes()==original


def test_summary_publication_failure_leaves_no_consumable_manifest(tmp_path,monkeypatch):
    from src.operations.workflow_contracts_v1 import publish_summary
    monkeypatch.setattr('os.link',lambda *a,**k: (_ for _ in ()).throw(OSError('injected publication failure')))
    with pytest.raises(OSError):publish_summary(tmp_path/'run-manifest.json',b'{"test":true}')
    assert not (tmp_path/'run-manifest.json').exists()
    assert len(list(tmp_path.glob('.pending-summary-*')))==1
