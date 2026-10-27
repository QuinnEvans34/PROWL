"""Strict configuration for the existing registered CPU adapters, with legacy reads."""
import json
from pathlib import Path
from functools import lru_cache
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from .workflow_plan_v1 import Stage, plan, encoded

CONTRACTS=Path(__file__).resolve().parents[2]/'docs/capstone/contracts'
VERSION='offline-workflow-configuration-v1'


@lru_cache(maxsize=1)
def configuration_validator():
    schema=json.loads((CONTRACTS/'offline-workflow-configuration-v1.schema.json').read_bytes())
    registry=json.loads((CONTRACTS/'offline-stage-registry.schema.json').read_bytes())
    Draft202012Validator.check_schema(schema);Draft202012Validator.check_schema(registry)
    resources=Registry().with_resource('https://prowl.local/contracts/offline-stage-registry.schema.json',Resource.from_contents(registry))
    return Draft202012Validator(schema,registry=resources)


def validate_registry_plan(registry,kind,rows):
    """Registry strings are declarations, never dynamically executed code."""
    Draft202012Validator(json.loads((CONTRACTS/'offline-stage-registry.schema.json').read_bytes())).validate(registry)
    if kind not in registry['workflows']:
        raise ValueError('Unregistered workflow; training dispatch is not supported')
    declared=registry['workflows'][kind]
    if {r['id'] for r in rows}!=set(declared):
        raise ValueError('Stage registry differs from plan')
    for row in rows:
        spec=declared[row['id']]
        if (row['dependencies']!=spec['dependencies'] or
            sorted(row['inputs'])!=spec['input_pins'] or row['config']!={}):
            raise ValueError('Stage dependencies, inputs or configuration differ from registry')
    return declared


def validate_configuration(value, *, allow_legacy=False):
    """Read legacy bytes without mutation; new invocations require an explicit version."""
    if not isinstance(value,dict): raise ValueError('Configuration object required')
    checked=value
    if allow_legacy and 'schema' not in value:
        checked=dict(value,schema=VERSION)
    configuration_validator().validate(checked)
    if type(checked['minimum_free_bytes']) is not int:
        raise ValueError('Capacity reserve must be integer bytes')
    if len(encoded(checked))>4*1024**2:
        raise ValueError('Configuration exceeds budget')
    rows=checked['plan']['stages']
    stages=[Stage(r['id'],tuple(r['dependencies']),r['inputs'],r['config'],r['producer']) for r in rows]
    if plan(stages)!=checked['plan']:
        raise ValueError('Configuration plan derivations or ordering differ')
    validate_registry_plan(checked['registry'],checked['workflow'],rows)
