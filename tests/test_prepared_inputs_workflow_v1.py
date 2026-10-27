import hashlib
import json
import uuid
import pytest
from src.operations.prepared_inputs_workflow_v1 import definition
from src.operations.workflow_execution_v1 import Executor
from src.operations.workflow_contracts_v1 import execute_registered
from src.data.manifest_records import canonical,digest


@pytest.fixture
def fixture(tmp_path):
    raw={'train':b'A\nB\n','development':b'V\n'}
    c=dict(train=['A','B'],validation=['V'],bindings={k:hashlib.sha256(raw[n]).hexdigest() for k,n in [('train_file','train'),('dev_file','development')]},
        kd_native_metadata={'pins':{'A':'a'*64,'B':'b'*64}},planned_focused_counts={'A':3,'B':3},
        label_revision={'corrected_cases':['A']},throughput={'version':'errata-kd-on-demand-1','prefetch':False,'ct':'original_full_decode_per_visit','labels':'original_with_explicit_errata_overlay'})
    r=dict(provider_sha256=digest(canonical(c)),success=True,scientific_ready=False,ct_voxel_reads=0,optimizer_updates=0,
        train=2,development=1,rows=[dict(case_id=n,focused_visits=3,total_visits=4,coverage_windows=2,positive=n=='B',corrected=n=='A') for n in ['A','B']],
        focused_updates=6,context_updates=2,planned_updates=8,positive_train=1)
    raw.update(control=canonical(c),result=canonical(r),resources=canonical(dict(success=True,workers_reaped=True,exit_code=0)))
    source=tmp_path/'source';source.mkdir();refs={}
    for key,value in raw.items():
        path=source/key;path.write_bytes(value);refs[key]=dict(path=str(path),sha256=hashlib.sha256(value).hexdigest())
    root=tmp_path/'workflow';root.mkdir()
    return refs,Executor(root,check_root=lambda:None,minimum_free_bytes=0,sensitivity='research-local')


def test_link_reuse_and_no_source_mutation(fixture):
    refs,e=fixture;s,h,v=definition(refs)
    a=execute_registered(e,'prepared-inputs',s,h,v)
    b=execute_registered(e,'prepared-inputs',s,h,v,resume_of=a['run_id'])
    assert set(b['stages'].values())=={'reused'}
    ref=b['events'][-1]['reference'];files,_=e.store().resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=v['prepared'])
    value=json.loads(files['prepared.json'])
    assert value['training_authorized'] is False and value['cache_payloads_revalidated'] is False
    for ref in refs.values():assert hashlib.sha256(__import__('pathlib').Path(ref['path']).read_bytes()).hexdigest()==ref['sha256']


@pytest.mark.parametrize('fault',['overlap','order','metadata','visits','totals','not_reaped','ready','payload_reads','provider','rows','policy','changed_pin'])
def test_invalid_saved_evidence_blocks_handoff(fixture,fault):
    from pathlib import Path
    refs,e=fixture
    key='control' if fault in ('overlap','order','metadata','policy') else 'resources' if fault=='not_reaped' else 'result'
    path=Path(refs[key]['path']);value=json.loads(path.read_bytes())
    if fault=='overlap':value['validation']=['A']
    if fault=='order':value['train'].reverse()
    if fault=='metadata':value['kd_native_metadata']['pins'].pop('B')
    if fault=='visits':value['rows'][0]['coverage_windows']=4
    if fault=='totals':value['planned_updates']=9
    if fault=='not_reaped':value['workers_reaped']=False
    if fault=='ready':value['scientific_ready']=True
    if fault=='payload_reads':value['ct_voxel_reads']=1
    if fault=='provider':value['provider_sha256']='0'*64
    if fault=='rows':value['rows'].reverse()
    if fault=='policy':value['throughput']['prefetch']=True
    if fault=='changed_pin':value['planned_updates']=123
    path.write_bytes(canonical(value))
    if fault!='changed_pin':refs[key]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    s,h,v=definition(refs);identity=str(uuid.uuid4())
    with pytest.raises(ValueError):e.execute(s,h,v,identity=identity)
    assert e.inspect(identity)['stages']['prepared'] in ('pending','failed')
