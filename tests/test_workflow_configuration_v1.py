"""Configuration boundaries for existing CPU adapters; no new scientific dispatch."""
import copy
import json
from pathlib import Path
import pytest
from jsonschema import ValidationError
from src.operations.workflow_configuration_v1 import VERSION,validate_configuration
from src.operations.workflow_contracts_v1 import execute_registered,registry_for
from src.operations.workflow_plan_v1 import plan,Stage
from src.operations.saved_package_workflow_v1 import definition
from test_saved_package_workflow_v1 import setup


def config_for(setup):
    source,pin,e=setup;s,h,v=definition(source,pin);registry,_=registry_for('saved-package',s)
    return dict(schema=VERSION,plan=plan(s),registry=registry,workflow='saved-package',minimum_free_bytes=0,sensitivity='research-local')


def test_versioned_config_and_nonmutating_legacy_read(setup):
    config=config_for(setup);validate_configuration(config)
    legacy=copy.deepcopy(config);legacy.pop('schema');before=copy.deepcopy(legacy)
    with pytest.raises(ValidationError):validate_configuration(legacy)
    validate_configuration(legacy,allow_legacy=True)
    assert legacy==before
    legacy['schema']='unknown'
    with pytest.raises(ValidationError):validate_configuration(legacy,allow_legacy=True)


@pytest.mark.parametrize('fault',['extra','version','workflow','floor_negative','floor_bool','floor_float','sensitivity','row_extra','config','derivation','parents','order','registry','workflow_mismatch'])
def test_invalid_configuration_rejected(setup,fault):
    c=config_for(setup);rows=c['plan']['stages']
    if fault=='extra':c['command']='do not execute'
    if fault=='version':c['schema']='unknown'
    if fault=='workflow':c['workflow']='training'
    if fault=='floor_negative':c['minimum_free_bytes']=-1
    if fault=='floor_bool':c['minimum_free_bytes']=True
    if fault=='floor_float':c['minimum_free_bytes']=1.0
    if fault=='sensitivity':c['sensitivity']='public'
    if fault=='row_extra':rows[0]['command']='do not execute'
    if fault=='config':rows[0]['config']={'gpu':True}
    if fault=='derivation':rows[0]['derivation']='0'*64
    if fault=='parents':rows[1]['parents']['integrity']='0'*64
    if fault=='order':rows.reverse()
    if fault=='registry':c['registry']['workflows']['saved-package']['integrity']['resource_class']='gpu'
    if fault=='workflow_mismatch':c['workflow']='prepared-inputs'
    with pytest.raises((ValueError,ValidationError)):validate_configuration(c,allow_legacy=True)


def test_consistently_rehashed_plan_must_still_match_registry(setup):
    c=config_for(setup);rows=c['plan']['stages']
    stages=[Stage(r['id'],tuple(r['dependencies']),r['inputs'],r['config'],r['producer']) for r in rows]
    stages[0]=Stage('integrity',inputs={'wrong_input':'a'*64},producer=stages[0].producer)
    c['plan']=plan(stages)
    with pytest.raises(ValueError,match='registry'):validate_configuration(c)


@pytest.mark.parametrize('policy',['floor','sensitivity'])
def test_invalid_current_policy_fails_before_any_invocation_or_callback(setup,policy):
    source,pin,e=setup;s,h,v=definition(source,pin);calls=[]
    if policy=='floor':e.floor=-1
    else:e.sensitivity='unrecognized'
    with pytest.raises((ValueError,ValidationError)):
        execute_registered(e,'saved-package',s,{k:lambda p,c:calls.append(True) for k in h},v)
    assert not calls and not list(e.root.iterdir())


def test_new_invocation_persists_and_binds_versioned_configuration(setup):
    source,pin,e=setup;s,h,v=definition(source,pin)
    result=execute_registered(e,'saved-package',s,h,v)
    config=json.loads((e.root/'contracts'/result['run_id']/'resolved-config.json').read_bytes())
    assert config['schema']==VERSION;validate_configuration(config)
    assert e.inspect(result['run_id'])['lifecycle']['terminal']
