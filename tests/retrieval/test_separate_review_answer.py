from copy import deepcopy
import json
import pytest
from src.retrieval import separate_review_answer as module
from src.retrieval.natural_answer import AnswerFailure
from tests.retrieval.test_readable_answer import EVIDENCE

DRAFT=dict(claims=[dict(text='The pancreas has a reported length range of 12 to 15 cm.', citations=[dict(source='P1')])])
SUPPORT=dict(checks=[dict(claim=1,decision='supported',reason='The attached quote supports this range.')],scope=dict(decision='pass',reason='General research claim within scope.'))
COMPLETE=dict(decision='pass',reason='The requested quantity and units are given.',missing=[])
READABLE=dict(decision='pass',reason='The text uses clear ordinary wording.')


def provider(responses):
    calls=[]
    def call(path,payload=None):
        calls.append((path,payload))
        if path=='tags':return dict(models=[dict(name=module.MODEL,digest=module.MODEL_SHA)])
        if path=='generate':return dict(done=True,model=module.MODEL)
        response=responses.pop(0)
        if isinstance(response,Exception):raise response
        return dict(model=module.MODEL,done=True,done_reason='stop',message=dict(content=json.dumps(response)))
    return call,calls


def test_complete_pipeline_has_three_separate_reviews_and_no_unchecked_rewrite():
    call,calls=provider([DRAFT,SUPPORT,COMPLETE,READABLE])
    result=module.generate_reviewed('Pancreas length?',EVIDENCE,call)
    assert result['status']=='summarized' and result['generation_calls']==4
    chats=[p for path,p in calls if path=='chat']
    assert [p['messages'][0]['content'] for p in chats]==[module.WRITE,module.SUPPORT,module.COMPLETENESS,module.READABILITY]
    assert 'citations' not in json.loads(chats[-1]['messages'][1]['content'])
    assert 'quote' not in chats[-1]['messages'][1]['content']
    assert calls[-1][0]=='generate'
    assert result['claims'][0]['text']==DRAFT['claims'][0]['text']


def test_all_mechanical_and_review_feedback_reaches_one_revision():
    evidence=deepcopy(EVIDENCE)
    evidence[0]['record']['text']='An invented study reports mean volume 80±4 cm³ (mean±SEM), 20% larger in the comparison.'
    raw=dict(claims=[dict(text='The mean is 80±4 cm³, 20% larger.',citations=[dict(source='P1')])])
    unsupported=deepcopy(SUPPORT);unsupported['checks'][0].update(decision='unsupported',reason='Study population omitted from the claim.')
    incomplete=dict(decision='revise',reason='The study method and sample are missing.',missing=['Study context'])
    unreadable=dict(decision='revise',reason='The uncertainty notation needs explanation.')
    fixed=dict(claims=[dict(text='One study reports a mean volume of 80 cm³.',citations=[dict(source='P1')])])
    call,calls=provider([raw,unsupported,incomplete,unreadable,fixed,SUPPORT,COMPLETE,READABLE])
    result=module.generate_reviewed('Pancreas volume?',evidence,call)
    chats=[p for path,p in calls if path=='chat']
    feedback=json.loads(chats[4]['messages'][1]['content'])['feedback']
    assert {i['criterion'] for i in feedback}=={'question_scope','study_qualifiers','factual_support','completeness','readability'}
    assert result['revisions']==1 and result['generation_calls']==8
    assert len([p for path,p in calls if path=='generate'])==1


@pytest.mark.parametrize('field',['factual_support','completeness','readability'])
def test_any_final_failed_criterion_withholds_draft(field):
    s,c,r=deepcopy(SUPPORT),deepcopy(COMPLETE),deepcopy(READABLE)
    if field=='factual_support':s['checks'][0]['decision']='unsupported'
    elif field=='completeness':c['decision']='revise'
    else:r['decision']='revise'
    call,calls=provider([DRAFT,s,c,r,DRAFT,s,c,r])
    with pytest.raises(AnswerFailure):module.generate_reviewed('Pancreas?',EVIDENCE,call)
    assert sum(path=='chat' for path,_ in calls)==8 and calls[-1][0]=='generate'


def test_empty_result_needs_no_reviews_and_makes_no_absence_claim():
    call,calls=provider([dict(claims=[])])
    result=module.generate_reviewed('Pancreas?',EVIDENCE,call)
    assert result['status']=='insufficient' and result['claims']==[] and result['reviews']==[]
    assert sum(path=='chat' for path,_ in calls)==1


def test_timeout_is_not_retried_and_cleanup_is_attempted():
    call,calls=provider([TimeoutError('expired')])
    with pytest.raises(TimeoutError):module.generate_reviewed('Pancreas?',EVIDENCE,call)
    assert [path for path,_ in calls]==['tags','chat','generate']


def test_expired_deadline_does_not_start_provider():
    call,calls=provider([])
    with pytest.raises(TimeoutError):module.generate_reviewed('Pancreas?',EVIDENCE,call,deadline=0)
    assert not calls


def test_support_reviewer_sees_only_bound_sources():
    sources=[dict(source='P1',text='This is the cited evidence.',title='Cited paper'),dict(source='P2',text='PRIVATE_UNCITED',title='Other')]
    body=module.bound_review_input('Question',DRAFT,sources)
    assert 'PRIVATE_UNCITED' not in json.dumps(body) and 'Other' not in json.dumps(body)


@pytest.mark.parametrize('bad',['identity','blank','contradictory'])
def test_malformed_reviews_fail_closed(bad):
    s,c,r=deepcopy(SUPPORT),deepcopy(COMPLETE),deepcopy(READABLE)
    if bad=='identity':s['checks'][0]['claim']=2
    elif bad=='blank':r['reason']=' '*10
    else:c['missing']=['A missing requirement']
    with pytest.raises(ValueError):module.review_findings(s,c,r,1)
