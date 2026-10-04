import json
import os
from pathlib import Path
import pytest
from src.operations.artifact_store import ArtifactStore
from src.data.manifest_records import digest


def validate(files):
    assert files=={'value.json':b'{"value":1}'}
    return {'records':1}


def store(tmp_path):return ArtifactStore(tmp_path,check_root=lambda:None,max_bytes=1024,minimum_free_bytes=0)


def publish(s,**changes):
    args=dict(derivation_sha256='a'*64,files={'value.json':b'{"value":1}'},metadata=dict(run_id='synthetic',stage_id='publish',artifact_type='test',schema_version='1.0.0',component='test',code_sha256='a'*64,parents=[],retention='test',sensitivity='synthetic'),validate=validate)
    args.update(changes)
    return s.publish('synthetic:one',**args)


def test_publish_resolve_and_verified_reuse(tmp_path):
    s=store(tmp_path);pin,state=publish(s)
    assert state=='published'
    data,receipt=s.resolve('synthetic:one',receipt_sha256=pin,validate=validate)
    assert receipt['state']=='complete' and data['value.json']==b'{"value":1}'
    assert publish(s)==(pin,'reused')


@pytest.mark.parametrize('fault',['corrupt','missing','extra','link','receipt','events'])
def test_consumer_rejects_damaged_publication(tmp_path,fault):
    s=store(tmp_path);pin,_=publish(s);p=tmp_path/digest(b'synthetic:one')
    if fault=='corrupt':(p/'value.json').write_bytes(b'changed')
    if fault=='missing':(p/'complete.json').unlink()
    if fault=='extra':(p/'unexpected').write_bytes(b'x')
    if fault=='link':
        (p/'value.json').unlink();(p/'value.json').symlink_to(tmp_path/'elsewhere')
    if fault=='receipt':pin='0'*64
    if fault=='events':(p/'events.jsonl').write_bytes(b'changed')
    with pytest.raises((ValueError,OSError)):s.resolve('synthetic:one',receipt_sha256=pin,validate=validate)


def test_conflict_preserves_original_and_hidden_attempt(tmp_path):
    s=store(tmp_path);pin,_=publish(s)
    with pytest.raises(ValueError,match='Derivation'):publish(s,derivation_sha256='b'*64)
    assert len(list(tmp_path.glob('.attempt-*')))==1
    s.resolve('synthetic:one',receipt_sha256=pin,validate=validate)


def test_incomplete_never_resolves(tmp_path):
    s=store(tmp_path);calls=[]
    def fails_on_persisted(files):
        calls.append(1)
        if len(calls)==2:raise RuntimeError('injected interruption')
        return validate(files)
    with pytest.raises(RuntimeError):publish(s,validate=fails_on_persisted)
    with pytest.raises(FileNotFoundError):s.resolve('synthetic:one',receipt_sha256='a'*64,validate=validate)
    assert list(tmp_path.glob('.attempt-*'))


def test_writer_contention_and_os_release(tmp_path):
    s=store(tmp_path)
    with s.opened() as fd,s.writer(fd):
        with pytest.raises(BlockingIOError):publish(s)
    assert publish(s)[1]=='published'


@pytest.mark.parametrize('name',['../escape','/absolute','sub/file','complete.json','events.jsonl'])
def test_member_paths_refused(tmp_path,name):
    with pytest.raises(ValueError):publish(store(tmp_path),files={name:b'x'},validate=lambda f:{})


def test_missing_root_and_symlink_refused(tmp_path):
    with pytest.raises(FileNotFoundError):publish(store(tmp_path/'missing'))
    (tmp_path/'link').symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(OSError):publish(store(tmp_path/'link'))


def test_capacity_stops_before_attempt(tmp_path):
    s=store(tmp_path);s.minimum_free_bytes=10**30
    with pytest.raises(ValueError,match='reserve'):publish(s)
    assert not list(tmp_path.glob('.attempt-*'))


def test_changed_volume_blocks_final_publication(tmp_path):
    calls=[]
    def check():
        calls.append(1)
        if len(calls)>1:raise ValueError('volume changed')
    s=ArtifactStore(tmp_path,check_root=check,minimum_free_bytes=0)
    with pytest.raises(ValueError,match='volume'):publish(s)
    assert not (tmp_path/digest(b'synthetic:one')).exists()


def test_separate_process_cannot_take_writer_lock(tmp_path):
    import subprocess
    import sys
    s=store(tmp_path)
    probe="""import fcntl,sys
f=open(sys.argv[1],'rb')
try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError: sys.exit(23)
sys.exit(0)
"""
    with s.opened() as fd,s.writer(fd):
        child=subprocess.run([sys.executable,'-c',probe,str(tmp_path/'.writer.lock')],timeout=10)
        assert child.returncode==23
    assert subprocess.run([sys.executable,'-c',probe,str(tmp_path/'.writer.lock')],timeout=10).returncode==0


def test_hardlinked_member_is_not_an_immutable_artifact(tmp_path):
    s=store(tmp_path);pin,_=publish(s);p=tmp_path/digest(b'synthetic:one')
    os.link(p/'value.json',tmp_path/'alias')
    with pytest.raises(ValueError,match='Unsafe'):
        s.resolve('synthetic:one',receipt_sha256=pin,validate=validate)
