import json
import pytest
from src.retrieval.repaired_answer import generate_repaired, MODEL, MODEL_SHA, check_draft
from src.retrieval.natural_answer import AnswerFailure
from tests.retrieval.test_natural_answer import EVIDENCE

DRAFT={'claims':[{'text':'The pancreas has a reported length range of 12 to 15 cm.','citations':[{'source':'P1'}]}]}
REVIEW={'checks':[{'claim':1,'explanation':'Supported.','supported':True}], 'safe':True,'relevant':True,'readable':True,'qualified':True,'feedback':''}


def run(responses):
    calls=[]
    def call(path,payload=None):
        if path=='tags':return {'models':[{'name':MODEL,'digest':MODEL_SHA}]}
        calls.append(payload)
        r=responses.pop(0)
        if isinstance(r,Exception):raise r
        return {'model':MODEL,'done':True,'done_reason':'stop','message':{'content':json.dumps(r)}}
    return call,calls


def test_valid_draft_needs_two_calls():
    call,calls=run([DRAFT,REVIEW]);result=generate_repaired('Pancreas size?',EVIDENCE,call)
    assert result['revisions']==0 and len(calls)==2
    assert all(c['think'] is False for c in calls)


def test_one_mechanical_revision_and_original_quote_binding():
    bad={'claims':[{'text':'The pancreas head is 12 cm.','citations':[{'source':'P1'}]}]}
    call,calls=run([bad,DRAFT,REVIEW]);result=generate_repaired('Pancreas size?',EVIDENCE,call)
    assert result['revisions']==1 and len(calls)==3
    feedback=json.loads(calls[1]['messages'][1]['content'])['feedback']
    assert 'anatomical narrowing' in feedback[0]
    assert result['claims'][0]['citations'][0]['quote']==EVIDENCE[0]['record']['text']


def test_review_feedback_gets_exactly_one_revision():
    bad=dict(REVIEW,readable=False,feedback='Explain specialist terminology.')
    call,calls=run([DRAFT,bad,DRAFT,REVIEW]);result=generate_repaired('Pancreas size?',EVIDENCE,call)
    assert result['revisions']==1 and len(calls)==4


def test_second_failure_stops_without_loop_or_draft():
    bad=dict(REVIEW,qualified=False,feedback='Missing qualifications.')
    call,calls=run([DRAFT,bad,DRAFT,bad])
    with pytest.raises(AnswerFailure):generate_repaired('Pancreas size?',EVIDENCE,call)
    assert len(calls)==4


def test_timeout_is_never_retried():
    call,calls=run([TimeoutError('expired')])
    with pytest.raises(TimeoutError):generate_repaired('Pancreas?',EVIDENCE,call)
    assert len(calls)==1


def test_gap_is_empty_not_a_cited_absence_claim():
    sources=[dict(source='P1',text=EVIDENCE[0]['record']['text'])]
    bad={'claims':[{'text':'The provided sources do not specify a policy.','citations':[{'source':'P1'}]}]}
    _,issues=check_draft(bad,sources,'Pancreas policy?')
    assert 'source absence' in issues[0]
    call,calls=run([{'claims':[]},dict(REVIEW,checks=[])])
    assert generate_repaired('Pancreas policy?',EVIDENCE,call)['status']=='insufficient'
    assert len(calls)==2
