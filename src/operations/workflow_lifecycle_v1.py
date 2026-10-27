"""Observed lifecycle for registered CPU invocations; never a scheduler or GPU owner."""
from datetime import datetime, timezone
import json
import os
import platform
import uuid
from .artifact_store import directory, read_file
from .workflow_plan_v1 import sha
from .workflow_execution_v1 import read_record, write_record, run_id
from .workflow_configuration_v1 import validate_configuration


def bounded_json(folder, name):
    fd=directory(folder)
    try: return json.loads(read_file(fd,name,4*1024**2))
    finally: os.close(fd)


def verify_provenance(root, identity, request):
    folder=root/'contracts'/run_id(identity)
    context=read_record(folder/'context.json')
    config=bounded_json(folder,'resolved-config.json')
    environment=bounded_json(folder,'environment.json')
    binding=dict(context_sha256=sha(context),registry_sha256=sha(config['registry']),
                 plan_sha256=sha(request['plan']))
    if sha(config)!=context['resolved_config_sha256']:
        raise ValueError('Resolved configuration changed')
    validate_configuration(config,allow_legacy=True)
    if (binding!=request['provenance'] or config['plan']!=request['plan'] or
        sha(environment)!=context['environment']['dependencies_sha256'] or
        binding['registry_sha256']!=context['registry_sha256']):
        raise ValueError('Workflow provenance differs from immutable request')
    return binding


class Lifecycle:
    def __init__(self, executor, identity, binding):
        self.executor=executor; self.identity=identity; self.binding=binding
        self.folder=executor.root/'contracts'/identity
        self.sequence=0; self.previous=None
        self.process=dict(host=platform.node(),pid=os.getpid(),adapter='offline-workflow-contracts-v1')

    def emit(self, event, **details):
        self.executor.admit()
        value=dict(schema='offline-workflow-lifecycle-v1',event_id=str(uuid.uuid4()),
            run_id=self.identity,sequence=self.sequence+1,previous=self.previous,
            observed_at=datetime.now(timezone.utc).isoformat(),event_type=event,
            provenance=self.binding,process=self.process,details=details)
        write_record(self.folder/f'lifecycle-{self.sequence+1:04d}.json',value)
        self.sequence+=1; self.previous=sha(value)


def inspect_lifecycle(executor, identity, *, snapshot=None, require_terminal=False):
    """Validate observed transitions; absence of a release is never inferred as cleanup."""
    folder=executor.root/'contracts'/run_id(identity)
    context=read_record(folder/'context.json'); config=bounded_json(folder,'resolved-config.json')
    binding=dict(context_sha256=sha(context),registry_sha256=sha(config['registry']),plan_sha256=sha(config['plan']))
    if sha(config)!=context['resolved_config_sha256'] or binding['registry_sha256']!=context['registry_sha256']:
        raise ValueError('Lifecycle context mismatch')
    validate_configuration(config,allow_legacy=True)
    if snapshot is not None:
        if snapshot['request'].get('provenance')!=binding:
            raise ValueError('Lifecycle request binding mismatch')
        verify_provenance(executor.root,identity,snapshot['request'])
    paths=sorted(folder.glob('lifecycle-*.json'))
    if not paths or len(paths)>8: raise ValueError('Lifecycle event count invalid')
    previous=None; ids=set(); events=[]; acquired=False; released=False; started=False; cancelled=False; terminal=False; process=None
    for index,path in enumerate(paths,1):
        e=read_record(path)
        fields={'schema','event_id','run_id','sequence','previous','observed_at','event_type','provenance','process','details'}
        if (set(e)!=fields or e['schema']!='offline-workflow-lifecycle-v1' or
            e['run_id']!=identity or type(e['sequence']) is not int or e['sequence']!=index or
            path.name!=f'lifecycle-{index:04d}.json' or e['previous']!=previous or
            e['provenance']!=binding or terminal): raise ValueError('Invalid lifecycle chain')
        run_id(e['event_id'])
        if e['event_id'] in ids: raise ValueError('Duplicate lifecycle identity')
        ids.add(e['event_id'])
        stamp=e['observed_at']
        if not isinstance(stamp,str) or not stamp.endswith('+00:00'): raise ValueError('Lifecycle time requires UTC')
        datetime.fromisoformat(stamp)
        p=e['process']
        if (not isinstance(p,dict) or set(p)!= {'host','pid','adapter'} or
            type(p['pid']) is not int or p['pid']<=0 or not isinstance(p['host'],str) or
            p['adapter']!='offline-workflow-contracts-v1' or (process is not None and p!=process)):
            raise ValueError('Invalid lifecycle process')
        process=p; kind=e['event_type']; detail=e['details']
        if not isinstance(detail,dict): raise ValueError('Invalid lifecycle details')
        if kind=='run_planned':
            valid=index==1 and detail=={}
        elif kind=='lock_acquired':
            valid=index==2 and not acquired and detail=={}; acquired=True
        elif kind=='run_started':
            valid=acquired and not released and not started and detail=={}; started=True
        elif kind=='cancel_requested':
            valid=started and not released and not cancelled and set(detail)=={'reason'} and detail['reason'] in ('SIGINT','SIGTERM'); cancelled=True
        elif kind=='lock_released':
            valid=acquired and not released and detail=={}; released=True
        elif kind in ('run_completed','run_cancelled','run_failed'):
            valid=index>1 and (not acquired or released)
            if kind=='run_failed':
                valid=valid and set(detail)=={'error'} and isinstance(detail['error'],str) and 0<len(detail['error'])<=2000
            else:
                valid=valid and started and detail=={} and (kind!='run_cancelled' or cancelled)
            if snapshot is not None:
                expected={'run_completed':('complete',),'run_cancelled':('cancelled',),'run_failed':('failed','incomplete')}[kind]
                valid=valid and snapshot['state'] in expected
                if kind=='run_cancelled':
                    request=next((x for x in events if x['event_type']=='cancel_requested'),None)
                    valid=valid and request is not None and request['details']['reason']==snapshot['cancellation']['reason']
            terminal=True
        else: valid=False
        if index==1 and kind!='run_planned': valid=False
        if not valid: raise ValueError('Invalid lifecycle transition')
        previous=sha(e); events.append(e)
    if require_terminal and not terminal: raise ValueError('Lifecycle is incomplete')
    if snapshot is not None and snapshot['events'] and not started:
        raise ValueError('Stage events lack observed run start')
    return dict(events=events,terminal=terminal,lock_release_observed=released,provenance=binding)
