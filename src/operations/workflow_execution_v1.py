"""Bounded local workflow execution; explicit recovery, no scheduling or shell dispatch.

Cooperating single-host POSIX writers. The registered callbacks own semantics;
this executor owns dependency ordering and validates artifacts before every reuse.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import uuid

from src.operations.artifact_store import ArtifactStore, directory, read_file
from .workflow_plan_v1 import Stage, plan, encoded, sha


def run_id(value):
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ValueError('Invalid run ID')
    return value


def write_record(path, value):
    """Exclusive records; an interrupted record is rejected, never silently repaired."""
    data=encoded(dict(value, content_sha256=sha(value)))
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def read_record(path):
    fd=directory(path.parent)
    try: value=json.loads(read_file(fd,path.name,1024**2))
    finally: os.close(fd)
    pin=value.pop('content_sha256')
    if pin!=sha(value): raise ValueError('Workflow record integrity failed')
    return value


class Executor:
    def __init__(self, root, *, check_root, minimum_free_bytes=50_000_000_000):
        self.root=Path(root).absolute()
        self.check_root=check_root
        self.floor=minimum_free_bytes

    def admit(self):
        self.check_root()
        fd=directory(self.root)
        try:
            st=os.fstatvfs(fd)
            if st.f_bavail*st.f_frsize < self.floor+4*1024**2:
                raise OSError('Workflow capacity reserve would be crossed')
        finally: os.close(fd)

    @contextmanager
    def locked(self):
        self.admit()
        fd=os.open(self.root/'.workflow.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield
        finally: os.close(fd)

    def store(self):
        return ArtifactStore(self.root/'artifacts',check_root=self.check_root,
                             max_bytes=8*1024**2,minimum_free_bytes=self.floor)

    def inspect(self, identity):
        """Read-only, including structural event validation. Does not claim artifact validity."""
        folder=self.root/'runs'/run_id(identity)
        request=read_record(folder/'request.json')
        if request['run_id']!=identity: raise ValueError('Run identity mismatch')
        rows=request['plan']['stages']
        reconstructed=plan([Stage(r['id'],tuple(r['dependencies']),r['inputs'],r['config'],r['producer']) for r in rows])
        if reconstructed!=request['plan']: raise ValueError('Invalid persisted plan')
        known={r['id']:r for r in rows}
        states={k:'pending' for k in known};events=[];previous=None;terminal=False
        paths=sorted(folder.glob('event-*.json'))
        if len(paths)>128: raise ValueError('Event count exceeds budget')
        for index,path in enumerate(paths,1):
            e=read_record(path)
            if (terminal or path.name!=f'event-{index:04d}.json' or e['sequence']!=index or
                e['previous']!=previous or e['request_sha256']!=sha(request)):
                raise ValueError('Invalid workflow event chain')
            stage=e['stage'];state=e['state']
            if stage not in known or any(states[d] not in ('completed','reused') for d in known[stage]['dependencies']):
                raise ValueError('Invalid event dependency')
            before=states[stage]
            if not ((before=='pending' and state in ('running','reused')) or
                    (before=='running' and state in ('completed','failed'))):
                raise ValueError('Invalid stage transition')
            if state in ('completed','reused'):
                ref=e['reference'];row=known[stage]
                if (ref['artifact_id']!=row['artifact_id'] or ref['derivation']!=row['derivation'] or
                    len(ref['receipt_sha256'])!=64): raise ValueError('Invalid output reference')
            states[stage]=state;terminal=state=='failed';previous=sha(e);events.append(e)
        complete=all(s in ('completed','reused') for s in states.values())
        return dict(run_id=identity,request=request,events=events,stages=states,
                    state='complete' if complete else 'failed' if terminal else 'incomplete')

    def history(self, parent):
        refs={};seen=set();current=parent
        while current:
            if current in seen or len(seen)>=32: raise ValueError('Invalid recovery lineage')
            seen.add(current);snapshot=self.inspect(current)
            for event in reversed(snapshot['events']):
                if event['state'] in ('completed','reused'):
                    ref=event['reference'];refs.setdefault(ref['derivation'],ref)
            current=snapshot['request']['resume_of']
        return refs

    def preview(self, stages, validators, *, resume_of=None):
        p=plan(stages)
        if set(validators)!={r['id'] for r in p['stages']}:
            raise ValueError('Exact validator registry required')
        refs=self.history(resume_of) if resume_of else {}
        decisions=[]
        for row in p['stages']:
            ref=refs.get(row['derivation'])
            if ref:
                self.store().resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],
                    expected_derivation=row['derivation'],validate=validators[row['id']])
            decisions.append(dict(stage=row['id'],action='reuse' if ref else 'run',
                                  reason='verified identical derivation' if ref else 'no matching completed stage'))
        return dict(plan=p,decisions=decisions)

    def execute(self, stages, handlers, validators, *, resume_of=None, identity=None):
        p=plan(stages);ids={r['id'] for r in p['stages']}
        if set(handlers)!=ids or set(validators)!=ids:
            raise ValueError('Exact handler and validator registries required')
        identity=run_id(identity or str(uuid.uuid4()))
        with self.locked():
            for name in ('runs','artifacts'):
                (self.root/name).mkdir(exist_ok=True)
                fd=directory(self.root/name);os.close(fd)
            refs=self.history(resume_of) if resume_of else {}
            folder=self.root/'runs'/identity;folder.mkdir()
            request=dict(schema='workflow-run-v1',run_id=identity,resume_of=resume_of,plan=p)
            write_record(folder/'request.json',request)
            sequence=0;previous=None;outputs={}
            def event(stage,state,**fields):
                nonlocal sequence,previous
                self.admit();sequence+=1
                value=dict(sequence=sequence,previous=previous,request_sha256=sha(request),
                           stage=stage,state=state,**fields)
                write_record(folder/f'event-{sequence:04d}.json',value);previous=sha(value)
            store=self.store()
            for row in p['stages']:
                sid=row['id'];validator=validators[sid];ref=refs.get(row['derivation'])
                if ref:
                    # Revalidation failure is preserved as a failed attempt; never regenerate silently.
                    try:
                        data,_=store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],
                            expected_derivation=row['derivation'],validate=validator)
                    except Exception as exc:
                        event(sid,'running');event(sid,'failed',error=f'{type(exc).__name__}: {exc}'[:2000]);raise
                    event(sid,'reused',reference=ref);outputs[sid]=data;continue
                event(sid,'running')
                try:
                    self.admit()
                    # Callbacks receive only declared parents and a detached relevant config snapshot.
                    parents={d:dict(outputs[d]) for d in row['dependencies']}
                    data=handlers[sid](parents,json.loads(encoded(row['config'])))
                    metadata=dict(artifact_type='workflow-stage',schema_version='1.0.0',component=sid,
                        code_sha256=row['producer'],parents=list(row['parents'].values()),
                        retention='retain-until-reviewed',sensitivity='synthetic',
                        run_id=row['derivation'],stage_id=sid)
                    pin,_=store.publish(row['artifact_id'],derivation_sha256=row['derivation'],
                                        files=data,metadata=metadata,validate=validator)
                    ref=dict(artifact_id=row['artifact_id'],derivation=row['derivation'],receipt_sha256=pin)
                    outputs[sid],_=store.resolve(row['artifact_id'],receipt_sha256=pin,
                        expected_derivation=row['derivation'],validate=validator)
                    event(sid,'completed',reference=ref)
                except Exception as exc:
                    event(sid,'failed',error=f'{type(exc).__name__}: {exc}'[:2000]);raise
            return self.inspect(identity)
