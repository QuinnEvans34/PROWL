import copy
import hashlib
import json
from pathlib import Path
import shutil

import pytest
from src.operations.case_evidence_workflow_v1 import native_fixture
from src.operations.case_literature_workflow_v1 import definition,validate_capture
from src.operations.workflow_execution_v1 import Executor
from src.operations.workflow_plan_v1 import encoded

REPO=Path(__file__).resolve().parents[1]
NODE=shutil.which('node')
pytestmark=pytest.mark.skipif(not NODE,reason='Node required for exact UI validator')


def capture_fixture(kind='supported'):
    cfg=json.loads((REPO/'configs/evidence/development-search-v1.json').read_text())
    quote='The invented gland releases digestive enzymes.'
    request={'request_id':'invented-capture','question':'What does the invented gland do?'}
    response=dict(schema_version='prowl-general-extract-response-v1',**request,
        collection=cfg['collection'],target={'manifest_sha256':cfg['manifest']['sha256'],
        'inventory':{'content_sha256':cfg['corpus_content_sha256']}},state='evidence_unassessed',reason=None,
        generation='completed',answer_policy='general-source-extract-v1',retrieval_policy='source-linked-record-search-v1.1',
        record_selection={'policy':'source-linked-record-search-v1.1','status':'dense_fallback','reason':'unmatched','matches':[]},
        evidence=[{'rank':1,'score':1,'record':{'text':quote,'passage':{'passage_id':'psg:'+'a'*64},
            'citation':{'title':'Invented source','pmcid':'PMC123','pmid':'123','authors':['Example']},
            'rights':{'permissions':{'display_snippet':True}}}}],
        answer=dict(prompt_sha256='cb216828f532b41c3913f37c668ae25b8f96bd4ca287c476bcad37e601e545d6',
            policy='general-source-extract-v1',model='qwen3:8b',
            model_sha256='500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41',
            provenance='model_selected_source_sentences',validation='exact_source_sentences',coverage='supported',
            status='summarized',limitation='Invented test only.',claims=[{'text':quote,'citations':[{'rank':1,'quote':quote}]}]))
    if kind=='unavailable':response.update(generation='unavailable',answer=None,message='Invented timeout.')
    if kind=='insufficient':response['answer'].update(status='insufficient',coverage='none',claims=[])
    if kind=='refusal':
        for key in ('record_selection','retrieval_policy','answer_policy'):response.pop(key)
        response.update(schema_version='prowl-development-answer-response-v1',generation='not_called',answer=None,
                        state='not_searched',evidence=[],reason='out_of_scope')
    return {'request':request,'response':response}


@pytest.mark.parametrize('kind',['supported','insufficient','unavailable','refusal'])
def test_original_ui_validator_preserves_outcomes(kind):
    capture=capture_fixture(kind);before=copy.deepcopy(capture)
    result=validate_capture(encoded(capture),node=NODE)
    assert result['generation']==capture['response']['generation']
    assert result['answer_status']==(capture['response']['answer'] or {}).get('status')
    assert result['semantic_support_reassessed'] is False
    assert capture==before


@pytest.mark.parametrize('fault',['question','request_id','quote','rank','model','corpus','rights','duplicate'])
def test_reject_invalid_captured_response(fault):
    c=capture_fixture();r=c['response']
    if fault in ('question','request_id'):r[fault]='wrong'
    if fault=='quote':r['answer']['claims'][0]['citations'][0]['quote']='Changed quote'
    if fault=='rank':r['answer']['claims'][0]['citations'][0]['rank']=9
    if fault=='model':r['answer']['model']='unknown'
    if fault=='corpus':r['target']['manifest_sha256']='0'*64
    if fault=='rights':r['evidence'][0]['record']['rights']['permissions']['display_snippet']=False
    if fault=='duplicate':r['evidence']*=2
    with pytest.raises(ValueError):validate_capture(encoded(c),node=NODE)


@pytest.fixture
def setup(tmp_path):
    source=tmp_path/'source';source.mkdir()
    for k,v in native_fixture().items():(source/k).write_bytes(v)
    capture=tmp_path/'capture.json';capture.write_bytes(encoded(capture_fixture()))
    root=tmp_path/'workflow';root.mkdir()
    pin=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    e=Executor(root,check_root=lambda:None,minimum_free_bytes=0,sensitivity='research-local')
    return source,pin(source/'manifest.json'),capture,pin(capture),e


def test_link_and_reuse_keeps_original_capture_and_limits(setup):
    source,mp,capture,cp,e=setup;s,h,v=definition(source,mp,capture,cp)
    a=e.execute(s,h,v);ref=a['events'][-1]['reference']
    files,_=e.store().resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],validate=v['linked'])
    assert files['capture.json']==capture.read_bytes()
    value=json.loads(files['linked-handoff.json'])
    assert value['case']['manifest_sha256']==mp and value['review_decision'] is None
    assert value['patient_specific_interpretation'] is False
    assert value['measurement_qualification']=='not_evaluated'
    b=e.execute(s,h,v,resume_of=a['run_id']);assert set(b['stages'].values())=={'reused'}
    # Changed captured request creates a new literature branch; the case branch is reused.
    new=capture_fixture('insufficient');capture2=capture.with_name('capture2.json');capture2.write_bytes(encoded(new))
    s,h,v=definition(source,mp,capture2,hashlib.sha256(capture2.read_bytes()).hexdigest())
    c=e.execute(s,h,v,resume_of=b['run_id'])
    assert c['stages']=={'integrity':'reused','handoff':'reused','literature':'completed','linked':'completed'}


def test_changed_capture_rejected(setup):
    source,mp,capture,cp,e=setup;s,h,v=definition(source,mp,capture,cp)
    capture.write_bytes(encoded(capture_fixture('unavailable')))
    with pytest.raises(ValueError,match='pin'):e.execute(s,h,v)


def test_duplicate_json_rejected_without_node():
    with pytest.raises(ValueError,match='Duplicate'):validate_capture(b'{"request":1,"request":2}',node='not-used')
