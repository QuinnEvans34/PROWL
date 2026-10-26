import json
import pytest
from src.operations.case_evidence_workflow_v1 import native_fixture
from src.operations.saved_package_workflow_v1 import definition
from src.operations.workflow_execution_v1 import Executor
from src.review.store import ReviewStore,digest


@pytest.fixture
def setup(tmp_path):
    source=tmp_path/'source';source.mkdir()
    for name,data in native_fixture().items():(source/name).write_bytes(data)
    pin=digest((source/'manifest.json').read_bytes())
    root=tmp_path/'workflow';root.mkdir()
    e=Executor(root,check_root=lambda:None,minimum_free_bytes=0,sensitivity='research-local')
    return source,pin,e


def test_handoff_matches_existing_review_target_without_decision(setup,tmp_path):
    source,pin,e=setup;s,h,v=definition(source,pin)
    before={p.name:p.read_bytes() for p in source.iterdir()}
    first=e.execute(s,h,v);ref=first['events'][-1]['reference']
    files,receipt=e.store().resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=v['handoff'])
    handoff=json.loads(files['handoff.json'])
    target=ReviewStore(tmp_path/'test-only-review-store',source,floor_bytes=0).target('saved')
    for k in ('case_package_id','prediction_id','manifest_sha256'):assert target[k]==handoff[k]
    assert handoff['review_decision'] is None and not target['history']
    assert receipt['metadata']['sensitivity']=='research-local'
    assert before=={p.name:p.read_bytes() for p in source.iterdir()}
    second=e.execute(s,h,v,resume_of=first['run_id'])
    assert set(second['stages'].values())=={'reused'}


@pytest.mark.parametrize('member',['manifest.json','ct.nii.gz','prediction.nii.gz','result.json','evidence.json'])
def test_changed_source_blocks_reuse_and_handoff(setup,member):
    source,pin,e=setup;s,h,v=definition(source,pin);first=e.execute(s,h,v)
    (source/member).write_bytes(b'changed')
    with pytest.raises((ValueError,KeyError)):e.execute(s,h,v,resume_of=first['run_id'])
    assert e.inspect(first['run_id'])==first


def test_wrong_pin_blocks_before_downstream(setup):
    source,pin,e=setup;s,h,v=definition(source,'0'*64);called=[]
    h['handoff']=lambda p,c:called.append(True)
    with pytest.raises(ValueError,match='pin'):e.execute(s,h,v)
    assert not called


def test_replaced_source_directory_refused(setup):
    source,pin,e=setup;s,h,v=definition(source,pin)
    source.rename(source.with_name('old'));source.mkdir()
    with pytest.raises(OSError,match='replaced'):e.execute(s,h,v)
