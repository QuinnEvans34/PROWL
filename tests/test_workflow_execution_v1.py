import json
import uuid
import pytest
from src.operations.workflow_plan_v1 import Stage, encoded, sha
from src.operations.workflow_execution_v1 import Executor


def setup(tmp_path):
    e=Executor(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    stages=[Stage('source',producer='a'*64),Stage('finish',('source',),producer='b'*64)]
    handlers={'source':lambda p,c:{'value.json':b'1'},'finish':lambda p,c:{'value.json':p['source']['value.json']}}
    def validate(f):
        if f!={'value.json':b'1'}:raise ValueError('Invalid fixture')
        return {'value':1}
    return e,stages,handlers,dict.fromkeys(handlers,validate)


def test_repeat_and_read_only_preview(tmp_path):
    e,s,h,v=setup(tmp_path)
    assert not list(tmp_path.iterdir())
    assert [r['action'] for r in e.preview(s,v)['decisions']]==['run','run']
    assert not list(tmp_path.iterdir())
    a=e.execute(s,h,v)
    b=e.execute(s,h,v,resume_of=a['run_id'])
    assert b['stages']=={'source':'reused','finish':'reused'}
    assert len(list((tmp_path/'artifacts').glob('[a-f0-9]'*64)))==2
    before={str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    e.inspect(b['run_id']);e.preview(s,v,resume_of=b['run_id'])
    assert before=={str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


def test_failed_stage_blocks_and_resume_preserves_attempt(tmp_path):
    e,s,h,v=setup(tmp_path);identity=str(uuid.uuid4());original=h['finish']
    h['finish']=lambda p,c:(_ for _ in ()).throw(RuntimeError('injected'))
    with pytest.raises(RuntimeError):e.execute(s,h,v,identity=identity)
    first=e.inspect(identity);assert first['state']=='failed'
    h['finish']=original
    result=e.execute(s,h,v,resume_of=identity)
    assert result['stages']=={'source':'reused','finish':'completed'}
    assert e.inspect(identity)==first


def test_corrupt_upstream_refuses_without_callback(tmp_path):
    e,s,h,v=setup(tmp_path);a=e.execute(s,h,v)
    row=a['request']['plan']['stages'][0]
    from src.data.manifest_records import digest
    (tmp_path/'artifacts'/digest(row['artifact_id'].encode())/'value.json').write_bytes(b'2')
    calls=[];h={k:lambda p,c:calls.append(1) for k in h}
    with pytest.raises(ValueError):e.execute(s,h,v,resume_of=a['run_id'])
    assert not calls


def test_changed_configuration_only_runs_descendant(tmp_path):
    e,s,h,v=setup(tmp_path);a=e.execute(s,h,v)
    s[1]=Stage('finish',('source',),config={'version':2},producer='b'*64)
    b=e.execute(s,h,v,resume_of=a['run_id'])
    assert b['stages']=={'source':'reused','finish':'completed'}


def test_parent_access_is_limited(tmp_path):
    e,s,h,v=setup(tmp_path)
    h['source']=lambda p,c: p['undeclared']
    with pytest.raises(KeyError):e.execute(s,h,v)


def test_missing_registry_and_capacity_no_calls(tmp_path):
    e,s,h,v=setup(tmp_path)
    with pytest.raises(ValueError):e.execute(s,{},v)
    e.floor=10**30
    with pytest.raises(OSError):e.execute(s,h,v)
    assert not list(tmp_path.iterdir())


def test_corrupt_event_and_run_id_rejected(tmp_path):
    e,s,h,v=setup(tmp_path);a=e.execute(s,h,v)
    with pytest.raises(ValueError):e.inspect('../escape')
    p=tmp_path/'runs'/a['run_id']/'event-0001.json'
    p.write_text('{}')
    with pytest.raises((KeyError,ValueError)):e.inspect(a['run_id'])


def test_missing_root(tmp_path):
    e,s,h,v=setup(tmp_path/'absent')
    with pytest.raises(FileNotFoundError):e.execute(s,h,v)


def test_same_id_never_overwrites(tmp_path):
    e,s,h,v=setup(tmp_path);a=e.execute(s,h,v)
    with pytest.raises(FileExistsError):e.execute(s,h,v,identity=a['run_id'])
    assert e.inspect(a['run_id'])==a


def test_root_replacement_rejected(tmp_path):
    root=tmp_path/'root';root.mkdir()
    e,s,h,v=setup(root)
    root.rename(tmp_path/'old');root.mkdir()
    with pytest.raises(OSError,match='identity'):e.execute(s,h,v)
    assert not list(root.iterdir())


def test_symlink_root_rejected(tmp_path):
    (tmp_path/'link').symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(OSError):setup(tmp_path/'link')


def test_unpublished_record_partial_is_not_an_event(tmp_path):
    e,s,h,v=setup(tmp_path);a=e.execute(s,h,v)
    (tmp_path/'runs'/a['run_id']/'.pending-invented').write_text('truncated')
    assert e.inspect(a['run_id'])==a
