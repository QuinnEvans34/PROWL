"""Contract bridge for the two registered offline CPU adapters, never training dispatch."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import uuid

from jsonschema import Draft202012Validator, FormatChecker
from .workflow_plan_v1 import encoded, sha, plan
from .workflow_execution_v1 import write_record, read_record, run_id, cooperative_signals
from .artifact_store import directory
from .workflow_lifecycle_v1 import Lifecycle, inspect_lifecycle
import os

REPO = Path(__file__).resolve().parents[2]
CONTRACTS = REPO/'docs/capstone/contracts'
REGISTRY = CONTRACTS/'offline-stage-registry-v1.json'


def validate(value, schema):
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)


def registry_for(kind, stages):
    registry = json.loads(REGISTRY.read_bytes())
    validate(registry, json.loads((CONTRACTS/'offline-stage-registry.schema.json').read_bytes()))
    if kind not in registry['workflows']:
        raise ValueError('Unregistered workflow; training dispatch is not supported')
    rows = plan(stages)['stages']
    declared = registry['workflows'][kind]
    if {r['id'] for r in rows} != set(declared):
        raise ValueError('Stage registry differs from plan')
    for row in rows:
        spec = declared[row['id']]
        if (row['dependencies'] != spec['dependencies'] or
            sorted(row['inputs']) != spec['input_pins'] or row['config'] != {}):
            raise ValueError('Stage dependencies, inputs or configuration differ from registry')
    return registry, declared


def now():
    return datetime.now(timezone.utc).isoformat()


def publish_summary(path, raw):
    """Publish only complete bytes; interruption leaves an ignored pending file."""
    temporary = path.parent/('.pending-summary-'+str(uuid.uuid4()))
    with temporary.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.link(temporary, path, follow_symlinks=False)
    temporary.unlink()
    fd = directory(path.parent)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def execute_registered(executor, kind, stages, handlers, validators, *, identity=None, resume_of=None):
    """Capture real invocation metadata before execution; validate a new summary afterward.

    Existing attempts without this context are not retroactively assigned timestamps
    or environments. Original executor records remain authoritative for recovery.
    """
    registry, declared = registry_for(kind, stages)
    ids = set(declared)
    if set(handlers) != ids or set(validators) != ids:
        raise ValueError('Exact registered callbacks required')
    identity = run_id(identity or str(uuid.uuid4()))
    if uuid.UUID(identity).version != 4:
        raise ValueError('Run-manifest requires a version-4 UUID')
    wrapped = {}
    for sid in ids:
        def check(files, sid=sid):
            if set(files) != set(declared[sid]['output_members']):
                raise ValueError('Registered output inventory differs')
            return validators[sid](files)
        wrapped[sid] = check
    executor.admit()
    parent = executor.root/'contracts'
    parent.mkdir(exist_ok=True)
    fd = directory(parent); os.close(fd)
    folder = parent/identity
    folder.mkdir()  # Never replace an earlier invocation, including preflight failure.
    deps = sorted((d.metadata['Name'], d.version) for d in importlib.metadata.distributions())
    def git(*args):
        return subprocess.run(['git', *args], cwd=REPO, capture_output=True,
                              text=True, check=True, timeout=5).stdout.strip()
    context = dict(created_at=now(), code=dict(git_commit=git('rev-parse','HEAD'),
        dirty=bool(git('status','--porcelain')), entry_point='offline-workflow-contracts-v1',
        component_version='1.0.0'), environment=dict(python=platform.python_version(),
        platform=platform.platform(), device='cpu', dependencies_sha256=sha(deps),
        environment_uri='environment.json'), registry_sha256=sha(registry))
    config = dict(plan=plan(stages), registry=registry, workflow=kind,
                  minimum_free_bytes=executor.floor, sensitivity=executor.sensitivity)
    context['resolved_config_sha256'] = sha(config)
    write_record(folder/'context.json', context)
    publish_summary(folder/'environment.json',encoded(deps))
    publish_summary(folder/'resolved-config.json',encoded(config))
    binding=dict(context_sha256=sha(context),registry_sha256=sha(registry),plan_sha256=sha(config['plan']))
    lifecycle=Lifecycle(executor,identity,binding)
    lifecycle.emit('run_planned')
    try:
        with cooperative_signals() as cancellation:
            observed=[]
            def cancel_requested():
                reason=cancellation()
                if reason and not observed:
                    lifecycle.emit('cancel_requested',reason=reason)
                    observed.append(reason)
                return reason
            result = executor.execute(stages, handlers, wrapped, identity=identity,
                                      resume_of=resume_of, cancel_requested=cancel_requested,
                                      provenance=binding, observe=lifecycle.emit)
        lifecycle.emit('run_cancelled' if result['state']=='cancelled' else 'run_completed')
        result=executor.inspect(identity)
    except Exception as original:
        # Preserve the original failure. Summary-generation failure cannot mask it.
        try:
            lifecycle.emit('run_failed',error=f'{type(original).__name__}: {original}'[:2000])
        except Exception as error:
            original.add_note('Lifecycle failure could not be recorded: '+str(error))
        try:
            export_summary(executor, identity, wrapped)
        except Exception as error:
            write_record(folder/'summary-unavailable.json', {'error':str(error)[:2000]})
        raise
    export_summary(executor, identity, wrapped)
    return result


def export_summary(executor, identity, validators):
    """Verify persisted outputs before describing a terminal attempt as completed."""
    snapshot = executor.inspect(identity)
    if snapshot['state'] not in ('complete','failed','cancelled'):
        raise ValueError('Incomplete attempt has no terminal run manifest')
    folder = executor.root/'contracts'/identity
    if 'provenance' in snapshot['request']:
        inspect_lifecycle(executor,identity,snapshot=snapshot,require_terminal=True)
    context = read_record(folder/'context.json')
    config_raw = (folder/'resolved-config.json').read_bytes()
    config = json.loads(config_raw)
    if hashlib.sha256(config_raw).hexdigest() != context['resolved_config_sha256']:
        raise ValueError('Resolved configuration changed')
    if config['plan'] != snapshot['request']['plan'] or sha(config['registry']) != context['registry_sha256']:
        raise ValueError('Run context differs from persisted request')
    if hashlib.sha256((folder/'environment.json').read_bytes()).hexdigest() != context['environment']['dependencies_sha256']:
        raise ValueError('Environment record changed')
    if set(validators) != set(snapshot['stages']):
        raise ValueError('Exact summary validator registry required')
    last = {event['stage']:event for event in snapshot['events']}
    refs = {}
    for row in snapshot['request']['plan']['stages']:
        event = last.get(row['id'], {})
        if event.get('state') not in ('completed','reused'): continue
        ref = event['reference']
        executor.store().resolve(ref['artifact_id'], receipt_sha256=ref['receipt_sha256'],
            expected_derivation=row['derivation'], validate=validators[row['id']])
        refs[row['id']] = dict(artifact_id=ref['artifact_id'],artifact_type='workflow-stage-receipt',
            uri='artifacts/'+hashlib.sha256(ref['artifact_id'].encode()).hexdigest()+'/complete.json',
            content_sha256=ref['receipt_sha256'],derivation_sha256=ref['derivation'])
    request_raw = (executor.root/'runs'/identity/'request.json').read_bytes()
    request_ref = dict(artifact_id='workflow-request:'+identity,artifact_type='workflow-request',
        uri='runs/'+identity+'/request.json',content_sha256=hashlib.sha256(request_raw).hexdigest())
    records=[]
    for row in snapshot['request']['plan']['stages']:
        sid=row['id']; event=last.get(sid,{})
        record=dict(stage_id=sid,component_version='1.0.0',status=snapshot['stages'][sid],
            attempt=1 if sid in last else 0,relevant_config_sha256=sha(row['config']),
            derivation_sha256=row['derivation'],inputs=[request_ref]+[refs[d] for d in row['dependencies'] if d in refs],
            outputs=[refs[sid]] if sid in refs else [])
        if event.get('state')=='failed':
            record['error']=dict(error_type='StageFailure',message=event['error'],retryable=False)
        started = next((e for e in snapshot['events'] if e['stage']==sid and e['state']=='running'), {})
        if 'observed_at' in started:
            record['started_at'] = started['observed_at']
        if event.get('state') in ('completed','reused') and 'observed_at' in event:
            record['completed_at'] = event['observed_at']
        records.append(record)
    stamp=now(); prefix='contracts/'+identity+'/'
    environment=dict(context['environment'],environment_uri=prefix+'environment.json')
    manifest=dict(schema_version='1.0.0',run_id='run:'+identity,run_name=config['workflow'],
        workflow_type='integration',status='completed' if snapshot['state']=='complete' else snapshot['state'],
        created_at=context['created_at'],updated_at=stamp,code=context['code'],environment=environment,
        resolved_config=dict(uri=prefix+'resolved-config.json',content_sha256=hashlib.sha256(config_raw).hexdigest()),
        stages=records,notes='Offline CPU handoff only. URIs are workflow-root relative. Summary time is observation time; stage durations are unmeasured. Input pins and dependency declarations are retained in the request. No training or measurement qualification.')
    validate(manifest,json.loads((CONTRACTS/'run-manifest.schema.json').read_bytes()))
    # Immutable per invocation; inspection never rewrites this summary.
    raw=encoded(manifest)
    publish_summary(folder/'run-manifest.json', raw)
    return manifest
