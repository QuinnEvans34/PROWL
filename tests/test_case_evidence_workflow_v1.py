import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import pytest
from src.operations.case_evidence_workflow_v1 import definition, validate_bundle, validate_evidence
from src.operations.workflow_execution_v1 import Executor
from src.data.manifest_records import digest

REPO=Path(__file__).resolve().parents[1]
CLI=REPO/'scripts/diagnostics/qualify_case_evidence_workflow.py'
HELPER=REPO/'tests/helpers/workflow_fixture_process.py'


def env():return dict(os.environ,PYTHONPATH=str(REPO),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')


def test_connected_native_and_source_contracts(tmp_path):
    e=Executor(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    s,h,v=definition();a=e.execute(s,h,v)
    ref=a['events'][-1]['reference']
    files,_=e.store().resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=validate_bundle)
    assert validate_bundle(files)['review_decision'] is None
    changed=dict(files);answer=json.loads(changed['literature.json'])
    answer['answer']['extracts'][0]['quote']='unsupported invented assertion'
    changed['literature.json']=json.dumps(answer).encode()
    with pytest.raises(ValueError,match='Citation'):validate_bundle(changed)
    b=e.execute(s,h,v,resume_of=a['run_id'])
    assert set(b['stages'].values())=={'reused'}
    s,h,v=definition(evidence_version=2)
    c=e.execute(s,h,v,resume_of=b['run_id'])
    assert c['stages']=={'native':'reused','evidence':'completed','bundle':'completed'}


@pytest.mark.parametrize('mode',['hold','fail','orphan'])
def test_real_process_interruption_and_recovery(tmp_path,mode):
    identity=str(uuid.uuid4())
    child=subprocess.Popen([sys.executable,str(HELPER),str(tmp_path),identity,mode],env=env(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        if mode=='hold':
            deadline=time.monotonic()+15
            while not (tmp_path/'publication-ready').exists():
                assert child.poll() is None
                assert time.monotonic()<deadline
                time.sleep(.05)
            # The writer owns the lock in another process; no competing callbacks allowed.
            e=Executor(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
            s,h,v=definition()
            with pytest.raises(BlockingIOError):e.execute(s,h,v)
            child.kill()
        out,err=child.communicate(timeout=15)
        assert child.returncode in (-9,1,99),(out,err)
    finally:
        if child.poll() is None:child.kill();child.wait(5)
        child.stdout.close();child.stderr.close()
    e=Executor(tmp_path,check_root=lambda:None,minimum_free_bytes=0)
    before=e.inspect(identity)
    assert before['stages']['native']=='completed'
    assert before['stages']['bundle']=='pending'
    partials=list((tmp_path/'artifacts').glob('.attempt-*'))
    if mode!='orphan':assert partials
    s,h,v=definition();row=next(r for r in before['request']['plan']['stages'] if r['id']=='evidence')
    if mode!='orphan':assert not (tmp_path/'artifacts'/digest(row['artifact_id'].encode())).exists()
    result=e.execute(s,h,v,resume_of=identity)
    assert result['stages']=={'native':'reused','evidence':'completed','bundle':'completed'}
    assert e.inspect(identity)==before
    assert all(p.exists() for p in partials)


def test_cli_plan_status_and_resume(tmp_path):
    def call(*args):
        p=subprocess.run([sys.executable,str(CLI),*args,'--root',str(tmp_path),'--json'],
                         env=env(),capture_output=True,text=True,timeout=20)
        assert p.returncode==0,p.stderr
        return json.loads(p.stdout)
    call('plan');assert not list(tmp_path.iterdir())
    a=call('run');assert a['state']=='complete'
    b=call('resume','--resume-of',a['run_id']);assert set(b['stages'].values())=={'reused'}
    assert call('status','--run-id',b['run_id'])==b
    assert call('inspect','--run-id',a['run_id'])==a
