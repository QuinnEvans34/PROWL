import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid
import pytest
from src.operations.workflow_execution_v1 import Executor,read_record
from src.operations.workflow_plan_v1 import encoded,sha
from test_workflow_execution_v1 import setup

REPO=Path(__file__).resolve().parents[1]


def rewrite(path,value):path.write_bytes(encoded(dict(value,content_sha256=sha(value))))


@pytest.mark.parametrize('signum',[signal.SIGINT,signal.SIGTERM])
def test_real_signal_stops_descendants_and_resume_reuses(tmp_path,signum):
    from src.operations.saved_package_workflow_v1 import definition
    from src.data.manifest_records import digest
    identity=str(uuid.uuid4())
    child=subprocess.Popen([sys.executable,str(REPO/'tests/helpers/workflow_cancel_fixture.py'),str(tmp_path),identity],
        cwd=REPO,env=dict(os.environ,PYTHONPATH=str(REPO)),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        deadline=time.monotonic()+5
        while not (tmp_path/'ready').exists():
            assert child.poll() is None
            assert time.monotonic()<deadline
            time.sleep(.02)
        child.send_signal(signum)
        # The handler finishes at its safe boundary after the request arrives.
        (tmp_path/'release').write_text('finish current stage')
        out,err=child.communicate(timeout=10)
        assert child.returncode==0,(out,err)
    finally:
        if child.poll() is None:child.kill();child.wait(5)
        child.stdout.close();child.stderr.close()
    e=Executor(tmp_path,check_root=lambda:None,minimum_free_bytes=0,sensitivity='research-local')
    first=e.inspect(identity)
    assert first['state']=='cancelled'
    assert first['stages']=={'integrity':'completed','handoff':'pending'}
    manifest=json.loads((tmp_path/'contracts'/identity/'run-manifest.json').read_bytes())
    assert manifest['status']=='cancelled'
    before={p.name:p.read_bytes() for p in (tmp_path/'runs'/identity).iterdir() if p.is_file()}
    source=tmp_path/'source';s,h,v=definition(source,digest((source/'manifest.json').read_bytes()))
    later=e.execute(s,h,v,resume_of=identity)
    assert later['stages']=={'integrity':'reused','handoff':'completed'}
    assert before=={p.name:p.read_bytes() for p in (tmp_path/'runs'/identity).iterdir() if p.is_file()}


def test_cancel_before_first_callback(tmp_path):
    e,s,h,v=setup(tmp_path);calls=[]
    a=e.execute(s,{k:lambda p,c:calls.append(1) for k in h},v,cancel_requested=lambda:'SIGINT')
    assert not calls and a['state']=='cancelled' and set(a['stages'].values())=={'pending'}


@pytest.mark.parametrize('fault',['sequence','previous','reason','time','extra'])
def test_forged_cancellation_rejected(tmp_path,fault):
    e,s,h,v=setup(tmp_path);a=e.execute(s,h,v,cancel_requested=lambda:'SIGTERM')
    path=tmp_path/'runs'/a['run_id']/'cancelled.json';c=read_record(path)
    if fault=='sequence':c['after_sequence']=1
    if fault=='previous':c['previous']='a'*64
    if fault=='reason':c['reason']='success'
    if fault=='time':c['observed_at']='2026-01-01T00:00:00'
    if fault=='extra':c['approved']=True
    rewrite(path,c)
    with pytest.raises(ValueError):e.inspect(a['run_id'])


@pytest.mark.parametrize('fault',['gap','dependency','transition','request'])
def test_rehashed_invalid_event_chain_rejected(tmp_path,fault):
    e,s,h,v=setup(tmp_path);a=e.execute(s,h,v)
    folder=tmp_path/'runs'/a['run_id'];paths=sorted(folder.glob('event-*.json'))
    if fault=='gap':paths[1].rename(folder/'event-0009.json')
    else:
        event=read_record(paths[0])
        if fault=='dependency':event['stage']='finish'
        if fault=='transition':event['state']='failed';event['error']='not started'
        if fault=='request':event['request_sha256']='0'*64
        rewrite(paths[0],event)
    with pytest.raises(ValueError):e.inspect(a['run_id'])


def test_stage_failure_wins_over_pending_cancellation(tmp_path):
    e,s,h,v=setup(tmp_path);requested=[];identity=str(uuid.uuid4())
    def fail(p,c):
        requested.append('SIGTERM')
        raise RuntimeError('real stage failure')
    h['source']=fail
    with pytest.raises(RuntimeError,match='real stage failure'):
        e.execute(s,h,v,identity=identity,cancel_requested=lambda:requested[0] if requested else None)
    assert e.inspect(identity)['state']=='failed'
    assert not (tmp_path/'runs'/identity/'cancelled.json').exists()


def test_last_stage_completion_wins_without_unstarted_work(tmp_path):
    e,s,h,v=setup(tmp_path);requested=[];original=h['finish']
    def finish(p,c):
        requested.append('SIGINT');return original(p,c)
    h['finish']=finish
    result=e.execute(s,h,v,cancel_requested=lambda:requested[0] if requested else None)
    assert result['state']=='complete'


def test_signal_handlers_are_restored():
    from src.operations.workflow_execution_v1 import cooperative_signals
    before={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    with cooperative_signals() as request:
        os.kill(os.getpid(),signal.SIGINT)
        assert request()=='SIGINT'
    assert before=={s:signal.getsignal(s) for s in before}
