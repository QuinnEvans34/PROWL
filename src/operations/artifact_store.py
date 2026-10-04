"""Shared, bounded local artifact publication. Cooperative writers, POSIX filesystem.

The owning component supplies semantic validation; runtime roots need an independently
approved role/volume check. Not a scheduler, source reader, or automatic recovery service.
Incomplete attempts remain hidden from resolution. No deletion or stale-lock takeover.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import socket
import stat
from uuid import uuid4

from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require


def now():
    return datetime.now(timezone.utc).isoformat()


def directory(path):
    """Open every absolute directory component without following symlinks."""
    path=Path(path)
    require(path.is_absolute() and all(p not in ('.','..') for p in path.parts), 'Absolute canonical root required')
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=nxt
        return fd
    except BaseException:
        os.close(fd);raise


def member_name(name):
    require(isinstance(name,str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,159}',name)
            and name not in ('complete.json','events.jsonl'), 'Unsafe or reserved member name')


def read_file(fd,name,limit):
    child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
    with os.fdopen(child,'rb') as stream:
        s=os.fstat(stream.fileno())
        require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=limit, 'Unsafe or oversized artifact member')
        data=stream.read(limit+1)
        require(len(data)<=limit, 'Read budget exceeded')
        return data


class ArtifactStore:
    def __init__(self,root,*,check_root,max_bytes=96*1024**2,minimum_free_bytes=100*1024**3):
        self.root=Path(root);self.check_root=check_root
        self.max_bytes=max_bytes;self.minimum_free_bytes=minimum_free_bytes

    @contextmanager
    def opened(self):
        self.check_root()
        fd=directory(self.root)
        try:
            identity=os.fstat(fd)
            require(identity.st_dev==self.root.stat().st_dev and identity.st_ino==self.root.stat().st_ino,
                    'Root identity changed')
            yield fd
        finally:os.close(fd)

    def space(self,fd,remaining):
        s=os.fstatvfs(fd)
        require(s.f_bavail*s.f_frsize>=self.minimum_free_bytes+remaining, 'Capacity reserve would be crossed')

    @contextmanager
    def writer(self,fd):
        lock=os.open('.writer.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600,dir_fd=fd)
        try:
            require(stat.S_ISREG(os.fstat(lock).st_mode) and os.fstat(lock).st_nlink==1, 'Unsafe writer lock')
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield
        finally:os.close(lock)

    def _read(self,rootfd,artifact_id,receipt_sha256,validate,expected_derivation=None):
        name=digest(artifact_id.encode())
        fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=rootfd)
        try:
            payload=read_file(fd,'complete.json',1024**2)
            require(digest(payload)==receipt_sha256, 'Independent completion pin mismatch')
            receipt=json.loads(payload)
            require(receipt['schema_version']=='1.0.0' and receipt['state']=='complete' and
                    receipt['artifact_id']==artifact_id, 'Wrong completion identity/state')
            if expected_derivation is not None:
                require(receipt['derivation_sha256']==expected_derivation, 'Derivation conflict')
            inventory=receipt['members'];require(0<len(inventory)<=32, 'Invalid member inventory')
            require(set(os.listdir(fd))==set(inventory)|{'complete.json','events.jsonl'}, 'Artifact member inventory differs')
            data={};used=0
            for n,ref in inventory.items():
                member_name(n);value=read_file(fd,n,self.max_bytes-used);used+=len(value)
                require(ref==dict(bytes=len(value),sha256=digest(value)), 'Changed artifact member')
                data[n]=value
            event=read_file(fd,'events.jsonl',1024**2)
            require(receipt['events_sha256']==digest(event), 'Attempt evidence changed')
            require(validate(data)==receipt['validation'], 'Semantic validation differs')
            return data,receipt
        finally:os.close(fd)

    def resolve(self,artifact_id,*,receipt_sha256,validate,expected_derivation=None):
        with self.opened() as fd:
            return self._read(fd,artifact_id,receipt_sha256,validate,expected_derivation)

    def publish(self,artifact_id,*,derivation_sha256,files,metadata,validate):
        require(isinstance(artifact_id,str) and 0<len(artifact_id)<=256, 'Invalid artifact identity')
        require(re.fullmatch('[0-9a-f]{64}',derivation_sha256) is not None, 'Invalid derivation')
        require(0<len(files)<=32, 'Bounded member count required')
        for n,v in files.items():member_name(n);require(isinstance(v,bytes), 'Byte payloads required')
        size=sum(map(len,files.values()));require(size<=self.max_bytes, 'Output budget exceeded')
        required={'artifact_type','schema_version','component','code_sha256','parents','retention','sensitivity','run_id','stage_id'}
        require(isinstance(metadata,dict) and required<=set(metadata) and len(canonical(metadata))<=65536,
                'Bounded producing/retention metadata required')
        require(all(isinstance(metadata[k],str) and metadata[k] for k in required-{'parents'}) and
                isinstance(metadata['parents'],list), 'Invalid producing metadata')
        validation=validate(files)
        inventory={n:dict(bytes=len(v),sha256=digest(v)) for n,v in sorted(files.items())}
        final=digest(artifact_id.encode())
        with self.opened() as rootfd, self.writer(rootfd):
            self.space(rootfd,2*size+2*1024**2)  # candidate plus retry reserve, control allowance
            attempt='.attempt-'+str(uuid4());os.mkdir(attempt,0o700,dir_fd=rootfd)
            fd=os.open(attempt,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=rootfd)
            events=[]
            def write(n,payload):
                self.space(rootfd,len(payload))
                f=os.open(n,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
                with os.fdopen(f,'wb') as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
            def event(state):
                row=dict(schema_version='1.0.0',attempt_id=attempt,sequence=len(events),state=state,
                         artifact_id=artifact_id,stage_id='publish',run_id=metadata['run_id'],
                         process_id=os.getpid(),host=socket.gethostname(),timestamp=now())
                events.append(row)
                f=os.open('events.jsonl',os.O_WRONLY|os.O_APPEND|os.O_CREAT|os.O_NOFOLLOW,0o600,dir_fd=fd)
                with os.fdopen(f,'ab') as stream:stream.write(canonical(row));stream.flush();os.fsync(stream.fileno())
            try:
                event('writer_lock_acquired')
                for n,v in files.items():write(n,v)
                persisted={n:read_file(fd,n,self.max_bytes) for n in files}
                require(persisted==files and validate(persisted)==validation, 'Persisted semantic validation failed')
                if final in os.listdir(rootfd):
                    existing=os.open(final,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=rootfd)
                    try:existing_pin=digest(read_file(existing,'complete.json',1024**2))
                    finally:os.close(existing)
                    old,receipt=self._read(rootfd,artifact_id,existing_pin,validate,derivation_sha256)
                    require(old==files and receipt['metadata']==metadata, 'Artifact content/metadata collision')
                    event('verified_reuse');return existing_pin,'reused'
                event('validated_ready_to_publish')
                receipt=dict(schema_version='1.0.0',state='complete',artifact_id=artifact_id,
                             derivation_sha256=derivation_sha256,members=inventory,metadata=metadata,attempt_id=attempt,
                             validation=validation,completed_at=now(),
                             events_sha256=digest(read_file(fd,'events.jsonl',1024**2)))
                payload=canonical(receipt);write('complete.json',payload);os.fsync(fd)
                self.check_root()  # fail on changed volume before same-volume publication
                current=self.root.stat();held=os.fstat(rootfd)
                require((current.st_dev,current.st_ino)==(held.st_dev,held.st_ino), 'Root replaced during publication')
                # Every cooperating publisher holds this persistent family lock.
                require(final not in os.listdir(rootfd), 'Destination appeared during publication')
                os.rename(attempt,final,src_dir_fd=rootfd,dst_dir_fd=rootfd);os.fsync(rootfd)
                return digest(payload),'published'
            except BaseException:
                # Preserve the hidden attempt. Completion inside a hidden attempt is never discoverable.
                try:event('failed_or_interrupted')
                except OSError:pass
                raise
            finally:os.close(fd)
