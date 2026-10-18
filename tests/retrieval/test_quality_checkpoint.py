from copy import deepcopy
import pytest
from src.retrieval.direct_ingestion import digest
from src.retrieval.quality_checkpoint import request_for, observe, verify_response


def fixture():
    search={'collection':'artificial'}
    answer={'version':'test','model':'test','model_sha256':'a'*64,'prompt_sha256':'b'*64}
    target={'manifest_sha256':'c'*64}
    record={'passage':{'passage_id':'psg:test'},'text':'An artificial passage for testing source identity.'}
    bindings=dict(search=search,answer=answer,target=target,records={'psg:test':record})
    request=request_for({'question':'Artificial question'})
    result=dict(schema_version='prowl-development-answer-response-v1',**{k:request[k] for k in ('request_id','question')},
        collection='artificial',target=target,configuration_sha256=digest(search),
        evidence=[dict(rank=1,score=.5,record=record)],state='evidence_unassessed',reason=None,
        generation='completed',answer=dict(status='summarized',claims=[dict(text='An artificial claim.',
            citations=[dict(rank=1,quote=record['text'])])],policy='test',model='test',
            model_sha256=answer['model_sha256'],prompt_sha256=answer['prompt_sha256'],
            validation='exact_quotes_and_model_review',quality='development_unvalidated'))
    return request,result,bindings


def test_gold_and_expected_text_never_enter_request():
    case=dict(id='a',question='Artificial question',expected='GOLD_CANARY',labels={'gold':'SECRET'})
    request=request_for(case)
    assert set(request)=={'schema_version','request_id','question'}
    assert request['question']==case['question'] and 'CANARY' not in str(request) and 'SECRET' not in str(request)


@pytest.mark.parametrize('field',['question','request_id','collection','target','configuration_sha256'])
def test_rejects_wrong_run_identity(field):
    request,result,bindings=fixture();result[field]='wrong'
    with pytest.raises(ValueError):verify_response(result,request,**bindings)


@pytest.mark.parametrize('mutation',['record','duplicate','nan','quote','model','prompt','state'])
def test_rejects_invalid_evidence_or_answer(mutation):
    request,result,bindings=fixture();result=deepcopy(result)
    if mutation=='record':result['evidence'][0]['record']['text']='Invented'
    if mutation=='duplicate':result['evidence']*=2
    if mutation=='nan':result['evidence'][0]['score']=float('nan')
    if mutation=='quote':result['answer']['claims'][0]['citations'][0]['quote']='Invented quote'
    if mutation=='model':result['answer']['model_sha256']='wrong'
    if mutation=='prompt':result['answer']['prompt_sha256']='wrong'
    if mutation=='state':result['state']='no_results'
    with pytest.raises(ValueError):verify_response(result,request,**bindings)


def test_retains_invalid_observation_without_retry_or_acceptance():
    _,result,bindings=fixture();calls=[]
    def post(request):calls.append(request);return result
    receipt=observe(dict(id='a',question='Artificial question',expected='CANARY'),post,**bindings)
    assert len(calls)==1 and receipt['transport_validation']=='failed' and receipt['response']==result
    assert 'CANARY' not in str(calls)


def test_valid_refusal_failure_and_insufficiency_stay_distinct():
    request,result,bindings=fixture()
    assert verify_response(result,request,**bindings)==result
    failed=deepcopy(result);failed.update(generation='unavailable',generation_failure='timeout',answer=None)
    assert verify_response(failed,request,**bindings)['generation']=='unavailable'
    empty=deepcopy(result);empty['answer'].update(status='insufficient',claims=[])
    assert verify_response(empty,request,**bindings)['answer']['status']=='insufficient'
    refused=deepcopy(result);refused.update(state='not_searched',reason='out_of_scope',evidence=[],answer=None,generation='not_called')
    assert verify_response(refused,request,**bindings)['state']=='not_searched'
