"""Bounded local workflow execution; explicit recovery, no scheduling or shell dispatch.

Cooperating single-host POSIX writers. The registered callbacks own semantics;
this executor owns dependency ordering and validates artifacts before every reuse.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
import re
import signal
import stat
from pathlib import Path
import uuid

from src.operations.artifact_store import ArtifactStore, directory, read_file
from .workflow_plan_v1 import Stage, plan, encoded, sha


@contextmanager
def cooperative_signals():
    """CLI-only: stop at the next stage boundary, never interrupt publication."""
    requested = []
    old = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    def request(signum, frame):
        if not requested:
            requested.append(signal.Signals(signum).name)
    try:
        for s in old:
            signal.signal(s, request)
        yield lambda: requested[0] if requested else None
    finally:
        for s, handler in old.items():
            signal.signal(s, handler)


def run_id(value):
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ValueError('Invalid run ID')
    return value


def write_record(path, value):
    """Exclusive records; an interrupted record is rejected, never silently repaired."""
    data=encoded(dict(value, content_sha256=sha(value)))
    temporary=path.parent/('.pending-'+str(uuid.uuid4()))
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    # Atomic exclusive publication. A killed writer leaves an ignored partial, not a torn event.
    os.link(temporary,path,follow_symlinks=False)
    temporary.unlink()
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


def validate_request(value):
    """Exact workflow-run-v1 envelope; plan semantics are reconstructed separately."""
    if (not isinstance(value, dict) or
        set(value) != {'schema', 'run_id', 'resume_of', 'plan'} or
        value['schema'] != 'workflow-run-v1'):
        raise ValueError('Unsupported workflow run contract')
    run_id(value['run_id'])
    if value['resume_of'] is not None:
        run_id(value['resume_of'])


def validate_event(value):
    """State-specific v1 event envelope, before checking chain and dependencies."""
    if not isinstance(value, dict):
        raise ValueError('Invalid workflow event')
    state = value.get('state')
    fields = {'sequence', 'previous', 'request_sha256', 'stage', 'state'}
    if state in ('completed', 'reused'):
        fields.add('reference')
        ref = value.get('reference')
        if (not isinstance(ref, dict) or
            set(ref) != {'artifact_id', 'derivation', 'receipt_sha256'} or
            any(not isinstance(ref[k], str) or not re.fullmatch('[a-f0-9]{64}', ref[k])
                for k in ('derivation', 'receipt_sha256'))):
            raise ValueError('Invalid workflow output reference')
    elif state == 'failed':
        fields.add('error')
        if not isinstance(value.get('error'), str) or not 0 < len(value['error']) <= 2000:
            raise ValueError('Invalid workflow failure reason')
    elif state != 'running':
        raise ValueError('Invalid workflow event state')
    if set(value) != fields or type(value['sequence']) is not int or value['sequence'] < 1:
        raise ValueError('Invalid workflow event fields')


class Executor:
    def __init__(self, root, *, check_root, minimum_free_bytes=50_000_000_000, sensitivity='synthetic'):
        if type(minimum_free_bytes) is not int or minimum_free_bytes < 0:
            raise ValueError('Capacity reserve must be a nonnegative integer number of bytes')
        self.root=Path(root).absolute()
        self.check_root=check_root
        if sensitivity not in ('synthetic','research-local'):
            raise ValueError('Explicit supported sensitivity required')
        self.sensitivity=sensitivity
        self.floor=minimum_free_bytes
        self.root_identity=None
        if self.root.exists():
            fd=directory(self.root)
            try:
                st=os.fstat(fd);self.root_identity=(st.st_dev,st.st_ino)
            finally:os.close(fd)

    def verify_root(self):
        self.check_root()
        fd=directory(self.root)
        try:
            st=os.fstat(fd)
            if self.root_identity!=(st.st_dev,st.st_ino):
                raise OSError('Workflow root identity changed')
        finally:os.close(fd)

    def admit(self):
        self.verify_root()
        fd=directory(self.root)
        try:
            st=os.fstatvfs(fd)
            if st.f_bavail*st.f_frsize < self.floor+4*1024**2:
                raise OSError('Workflow capacity reserve would be crossed')
        finally: os.close(fd)

    @contextmanager
    def locked(self):
        self.admit()
        fd=os.open(self.root/'.workflow.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
        try:
            st=os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1:
                raise ValueError('Unsafe workflow lock')
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield
        finally: os.close(fd)

    def store(self):
        return ArtifactStore(self.root/'artifacts',check_root=self.verify_root,
                             max_bytes=8*1024**2,minimum_free_bytes=self.floor)

    def inspect(self, identity):
        """Read-only, including structural event validation. Does not claim artifact validity."""
        self.verify_root()
        folder=self.root/'runs'/run_id(identity)
        request=read_record(folder/'request.json')
        validate_request(request)
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
            validate_event(e)
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
        result=dict(run_id=identity,request=request,events=events,stages=states,
                    state='complete' if complete else 'failed' if terminal else 'incomplete')
        cancellation=folder/'cancelled.json'
        if cancellation.exists():
            c=read_record(cancellation)
            fields={'schema','run_id','request_sha256','after_sequence','previous','reason','observed_at'}
            if (set(c)!=fields or c['schema']!='workflow-cancellation-v1' or
                c['run_id']!=identity or c['request_sha256']!=sha(request) or
                type(c['after_sequence']) is not int or c['after_sequence']!=len(events) or
                c['previous']!=previous or c['reason'] not in ('SIGINT','SIGTERM') or
                terminal or complete or 'running' in states.values()):
                raise ValueError('Invalid cancellation boundary')
            stamp=datetime.fromisoformat(c['observed_at'])
            if stamp.utcoffset() is None:
                raise ValueError('Cancellation timestamp requires timezone')
            result.update(state='cancelled',cancellation=c)
        return result

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
                _,receipt=self.store().resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],
                    expected_derivation=row['derivation'],validate=validators[row['id']])
                if receipt['metadata']['sensitivity']!=self.sensitivity:
                    raise ValueError('Artifact sensitivity differs')
            decisions.append(dict(stage=row['id'],action='reuse' if ref else 'run',
                                  reason='verified identical derivation' if ref else 'no matching completed stage'))
        return dict(plan=p,decisions=decisions)

    def execute(self, stages, handlers, validators, *, resume_of=None, identity=None, cancel_requested=lambda:None):
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
                reason=cancel_requested()
                if reason is not None:
                    if reason not in ('SIGINT','SIGTERM'):
                        raise ValueError('Unsupported cancellation reason')
                    self.admit()
                    write_record(folder/'cancelled.json',dict(schema='workflow-cancellation-v1',
                        run_id=identity,request_sha256=sha(request),after_sequence=sequence,
                        previous=previous,reason=reason,observed_at=datetime.now(timezone.utc).isoformat()))
                    return self.inspect(identity)
                sid=row['id'];validator=validators[sid];ref=refs.get(row['derivation'])
                if ref:
                    # Revalidation failure is preserved as a failed attempt; never regenerate silently.
                    try:
                        data,receipt=store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],
                            expected_derivation=row['derivation'],validate=validator)
                        if receipt['metadata']['sensitivity']!=self.sensitivity:
                            raise ValueError('Artifact sensitivity differs')
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
                        retention='retain-until-reviewed',sensitivity=self.sensitivity,
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
