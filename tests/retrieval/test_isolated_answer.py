import json
import pytest
from src.retrieval.isolated_answer import generate_isolated, MODEL, MODEL_SHA, check_draft
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
    call,calls=run([DRAFT,REVIEW]);result=generate_isolated('Pancreas size?',EVIDENCE,call)
    assert result['revisions']==0 and len(calls)==2
    assert all('think' not in c for c in calls)


def test_one_mechanical_revision_and_original_quote_binding():
    bad={'claims':[{'text':'The pancreas head is 12 cm.','citations':[{'source':'P1'}]}]}
    call,calls=run([bad,DRAFT,REVIEW]);result=generate_isolated('Pancreas size?',EVIDENCE,call)
    assert result['revisions']==1 and len(calls)==3
    feedback=json.loads(calls[1]['messages'][1]['content'])['feedback']
    assert 'anatomical narrowing' in feedback[0]
    assert result['claims'][0]['citations'][0]['quote']==EVIDENCE[0]['record']['text']


def test_review_feedback_gets_exactly_one_revision():
    bad=dict(REVIEW,readable=False,feedback='Explain specialist terminology.')
    call,calls=run([DRAFT,bad,DRAFT,REVIEW]);result=generate_isolated('Pancreas size?',EVIDENCE,call)
    assert result['revisions']==1 and len(calls)==4


def test_second_failure_stops_without_loop_or_draft():
    bad=dict(REVIEW,qualified=False,feedback='Missing qualifications.')
    call,calls=run([DRAFT,bad,DRAFT,bad])
    with pytest.raises(AnswerFailure):generate_isolated('Pancreas size?',EVIDENCE,call)
    assert len(calls)==4


def test_timeout_is_never_retried():
    call,calls=run([TimeoutError('expired')])
    with pytest.raises(TimeoutError):generate_isolated('Pancreas?',EVIDENCE,call)
    assert len(calls)==1


def test_gap_is_empty_not_a_cited_absence_claim():
    sources=[dict(source='P1',text=EVIDENCE[0]['record']['text'])]
    bad={'claims':[{'text':'The provided sources do not specify a policy.','citations':[{'source':'P1'}]}]}
    _,issues=check_draft(bad,sources,'Pancreas policy?')
    assert 'source absence' in issues[0]
    call,calls=run([{'claims':[]},dict(REVIEW,checks=[])])
    assert generate_isolated('Pancreas policy?',EVIDENCE,call)['status']=='insufficient'
    assert len(calls)==2


def test_review_cannot_see_uncited_evidence():
    from src.retrieval.isolated_answer import isolated_review_body
    sources=[dict(source='P1',title='Cited',text='Supported quote'),dict(source='P2',title='Uncited title',text='UNRELATED_INSTRUCTION')]
    claims=[dict(text='A claim.',citations=[dict(source='P1',quote='Supported quote')])]
    body=isolated_review_body('Pancreas?',claims,sources)
    assert 'sources' not in body
    assert 'UNRELATED_INSTRUCTION' not in json.dumps(body)
    assert 'Uncited title' not in json.dumps(body)
    assert body['claims'][0]['citations'][0]['title']=='Cited'


def test_mean_requires_study_boundary_and_uncertainty_definition():
    from src.retrieval.isolated_answer import study_guards
    def c(text,quote):return dict(text=text,citations=[dict(quote=quote)])
    with pytest.raises(ValueError):study_guards(c('The average volume is 80 cm³.','Study mean volume 80 cm³.'))
    with pytest.raises(ValueError):study_guards(c('One study reported 80±4 cm³.','Mean±SEM was 80±4 cm³.'))
    study_guards(c('One study reported 80±4 cm³ (mean ± standard error).','Mean±SEM was 80±4 cm³.'))
