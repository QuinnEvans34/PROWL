"""Pure, tool-neutral plans for explicitly registered bounded workflows."""
from dataclasses import dataclass, field
import hashlib
import json
import re


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', value):
        raise ValueError('Invalid stage identifier')
    return value


@dataclass(frozen=True)
class Stage:
    id: str
    dependencies: tuple = ()
    inputs: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)
    producer: str = ''


def plan(stages):
    """Return a JSON snapshot; the caller cannot mutate a planned stage via its inputs."""
    stages = list(stages)
    if not 0 < len(stages) <= 32:
        raise ValueError('Expected 1–32 stages')
    registry = {}
    for s in stages:
        name(s.id)
        if s.id in registry:
            raise ValueError('Duplicate stage')
        if not isinstance(s.producer, str) or not re.fullmatch('[a-f0-9]{64}', s.producer):
            raise ValueError('Explicit producer hash required')
        if len(set(s.dependencies)) != len(s.dependencies):
            raise ValueError('Duplicate dependency')
        for dep in s.dependencies: name(dep)
        if not isinstance(s.inputs, dict) or not isinstance(s.config, dict):
            raise ValueError('Explicit input/config maps required')
        if any(not isinstance(k, str) or not isinstance(v, str) or
               not re.fullmatch('[a-f0-9]{64}', v) for k, v in s.inputs.items()):
            raise ValueError('Inputs must have content hashes')
        registry[s.id] = s
    if any(d not in registry for s in stages for d in s.dependencies):
        raise ValueError('Missing dependency')
    rows, keys = [], {}
    while len(rows) < len(stages):
        ready = sorted(k for k, s in registry.items() if k not in keys and
                       all(d in keys for d in s.dependencies))
        if not ready:
            raise ValueError('Dependency cycle')
        for k in ready:
            s = registry[k]
            row = dict(id=k, dependencies=sorted(s.dependencies), inputs=s.inputs,
                       config=s.config, producer=s.producer,
                       parents={d:keys[d] for d in sorted(s.dependencies)})
            key = sha(row)
            keys[k] = key
            rows.append(dict(row, derivation=key, artifact_id='workflow-v1:'+key))
    result = dict(schema='workflow-plan-v1', stages=rows)
    if len(encoded(result)) > 65536:
        raise ValueError('Plan exceeds budget')
    return json.loads(encoded(result))
