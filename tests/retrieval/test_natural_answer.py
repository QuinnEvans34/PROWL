import json
from copy import deepcopy
import pytest
from src.retrieval.natural_answer import (MODEL,MODEL_SHA,generate,validate_draft,NaturalAnswerService)
from tests.retrieval.test_development_search import service
from tests.retrieval.test_literature_adapter import setup
from tests.retrieval.test_direct_ingestion import bundle

TEXT='In this artificial study, the pancreas length ranged from 12 to 15 cm in adults.'
EVIDENCE=[dict(rank=1,record=dict(text=TEXT,citation=dict(title='Artificial source')))]
DRAFT=dict(grounding='An artificial adult cohort reports a length range.',claims=[dict(text='The study reported an adult pancreas length of 12–15 cm.',
    citations=[dict(source='P1',quote=TEXT)])])

def provider(draft=None,review=None):
    calls=[]
    def call(path,payload=None):
        calls.append((path,payload))
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        content=(DRAFT if draft is None else draft) if len(calls)==2 else (dict(checks=[dict(claim=i,explanation='Supported by the artificial cohort.',supported=True) for i,_ in enumerate((DRAFT if draft is None else draft)['claims'],1)],safe=True,status_appropriate=True) if review is None else review)
        return dict(model=MODEL,done=True,done_reason='stop',message=dict(content=json.dumps(content)))
    return call,calls

def test_real_protocol_preserves_claim_and_exact_quote():
    call,calls=provider();r=generate('Pancreas size?',EVIDENCE,call)
    assert r['claims'][0]['text']==DRAFT['claims'][0]['text']
    assert r['claims'][0]['citations']==[dict(rank=1,quote=TEXT)]
    assert r['quality']=='development_unvalidated' and len(calls)==3
    assert all('request_id' not in str(p) for _,p in calls)

@pytest.mark.parametrize('kind',['foreign','fabricated','empty','duplicate','no_citation','unknown','too_many','wrong_state'])
def test_invalid_drafts_fail_before_review(kind):
    draft=deepcopy(DRAFT);c=draft['claims'][0]
    if kind=='foreign':c['citations'][0]['source']='P9'
    if kind=='fabricated':c['citations'][0]['quote']='This quote does not occur in the source.'
    if kind=='empty':c['text']=' '
    if kind=='duplicate':c['citations']*=2
    if kind=='no_citation':c['citations']=[]
    if kind=='unknown':draft['answer']='hidden'
    if kind=='too_many':draft['claims']*=4
    if kind=='wrong_state':draft['status']='insufficient'
    call,calls=provider(draft)
    with pytest.raises(ValueError):generate('Pancreas size?',EVIDENCE,call)
    assert len(calls)==2

@pytest.mark.parametrize('review',[{'acceptable':False},{'acceptable':1},{'acceptable':True,'extra':'x'},{}])
def test_review_rejection_does_not_publish(review):
    call,_=provider(review=review)
    with pytest.raises(ValueError):generate('Pancreas size?',EVIDENCE,call)

def test_insufficient_is_checked_and_contains_no_claims():
    call,calls=provider(dict(grounding='No direct evidence.',claims=[]))
    assert generate('Pancreas size?',EVIDENCE,call)['status']=='insufficient'
    assert len(calls)==3

def test_missing_model_and_truncation_fail():
    call,calls=provider()
    def wrong(path,payload=None):
        r=call(path,payload)
        if path=='tags':r['models'][0]['digest']='wrong'
        return r
    with pytest.raises(OSError):generate('Pancreas size?',EVIDENCE,wrong)
    assert len(calls)==1
    call,_=provider()
    def truncated(path,payload=None):
        r=call(path,payload)
        if path=='chat':r['done_reason']='length'
        return r
    with pytest.raises(ValueError):generate('Pancreas size?',EVIDENCE,truncated)

def test_scope_failure_and_busy_keep_sources_separate(service):
    s,r,_=service;calls=[]
    def fail(*args):calls.append(args);raise OSError('PRIVATE_MODEL_ERROR')
    a=NaturalAnswerService(s,fail)
    result=a.answer(r)
    assert result['generation']=='unavailable' and result['evidence'] and result['answer'] is None
    assert 'PRIVATE_MODEL_ERROR' not in str(result)
    r['question']='Measure this pancreas'
    assert a.answer(r)['generation']=='not_called' and len(calls)==1
    a.lock.acquire()
    with pytest.raises(OSError):a.answer(r)
    a.lock.release()


def test_range_cannot_be_called_average_even_with_exact_quote():
    draft=deepcopy(DRAFT);draft['claims'][0]['text']='The average pancreas is 12–15 cm long.'
    call,calls=provider(draft)
    with pytest.raises(ValueError,match='average'):generate('Pancreas size?',EVIDENCE,call)
    assert len(calls)==2


def test_number_requires_its_own_cited_quote():
    draft=deepcopy(DRAFT);draft['claims'][0]['text']='The pancreas was 33% smaller in that cohort.'
    call,calls=provider(draft)
    with pytest.raises(ValueError,match='Number'):generate('Pancreas size?',EVIDENCE,call)
    assert len(calls)==2
