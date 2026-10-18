from copy import deepcopy
import json
import pytest
from src.retrieval.staged_answer import generate_staged, POLICY
from src.retrieval.natural_answer import MODEL, MODEL_SHA, AnswerFailure
from tests.retrieval.test_natural_answer import EVIDENCE


def provider(empty=False, reject=False):
    calls=[]
    draft={'grounding':'Source-bound fact','claims':[] if empty else [{'text':'The pancreas is reported as 12 to 15 cm long.','citations':[{'source':'P1'}]}]}
    def call(path,payload=None):
        if path=='tags':return {'models':[{'name':MODEL,'digest':MODEL_SHA}]}
        calls.append(payload)
        review='checks' in payload['format']['properties']
        content=({'checks':[] if empty else [{'claim':1,'explanation':'Supported in passage.','supported':not reject}], 'safe':True,'status_appropriate':True} if review else draft)
        return {'model':MODEL,'done':True,'done_reason':'stop','message':{'content':json.dumps(content)}}
    return call,calls


def test_three_stages_bind_original_sources():
    call,calls=provider()
    result=generate_staged('Pancreas size?',EVIDENCE,call)
    assert result['policy']==POLICY
    assert len(calls)==3
    assert [c['think'] for c in calls]==[True,False,True]
    assert result['claims'][0]['citations'][0]['quote']==EVIDENCE[0]['record']['text']


def test_empty_extraction_skips_writer_but_reviews_gap():
    call,calls=provider(empty=True)
    result=generate_staged('Pancreas?',EVIDENCE,call)
    assert result['status']=='insufficient' and len(calls)==2


def test_review_rejection_cannot_display_draft():
    call,_=provider(reject=True)
    with pytest.raises(AnswerFailure):generate_staged('Pancreas size?',EVIDENCE,call)


def test_expired_budget_does_not_call_provider():
    call,calls=provider()
    with pytest.raises(TimeoutError):generate_staged('Pancreas?',EVIDENCE,call,deadline=0)
    assert not calls
