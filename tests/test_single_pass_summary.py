import json
import pytest
from src.retrieval.single_pass_summary import generate,SinglePassAnswers,MODEL,MODEL_SHA
E=[dict(rank=1,record=dict(text='The invented gland releases digestive enzymes.',citation=dict(title='Synthetic source')))]
A=dict(coverage='supported',limitation='',claims=[dict(text='It releases enzymes that help digestion.',citations=[dict(rank=1,quote=E[0]['record']['text'])])])
def run(answer=A):
    calls=[]
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        calls.append(payload)
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(answer)))
    return generate('What does it do?',E,call),calls

def test_one_call_question_evidence_and_no_thinking():
    answer,calls=run();assert len(calls)==1 and calls[0]['think'] is False
    body=json.loads(calls[0]['messages'][1]['content'])
    assert body['question']=='What does it do?' and body['passages'][0]['text']==E[0]['record']['text']
    assert answer['validation']=='citation_binding_only'

@pytest.mark.parametrize('kind',['rank','quote','coverage','duplicate'])
def test_bad_binding_rejected(kind):
    a=json.loads(json.dumps(A));c=a['claims'][0]['citations'][0]
    if kind=='rank':c['rank']=2
    if kind=='quote':c['quote']='This supporting text is entirely invented.'
    if kind=='coverage':a['coverage']='none'
    if kind=='duplicate':a['claims'][0]['citations'].append(c.copy())
    with pytest.raises(Exception):run(a)

def test_gap_and_partial():
    assert run(dict(coverage='none',claims=[],limitation='No supporting evidence.'))[0]['status']=='insufficient'
    a=json.loads(json.dumps(A));a.update(coverage='partial',limitation='No measurement range was found.')
    assert run(a)[0]['coverage']=='partial'

def test_boundary_never_calls_model():
    class Search:
        def search(self,r):return dict(state='not_searched',answer=None,generation='not_called')
    def forbidden(*a):raise AssertionError('Model must not run')
    assert SinglePassAnswers(Search(),forbidden).answer(dict(question='Diagnose me'))['generation']=='not_called'

def test_failure_preserves_evidence_and_releases_lock():
    class Search:
        def search(self,r):return dict(state='evidence_unassessed',record_selection=dict(status='dense_fallback'),evidence=E)
    def fail(*a):raise TimeoutError()
    service=SinglePassAnswers(Search(),fail)
    for _ in range(2):
        result=service.answer(dict(question='What does it do?'))
        assert result['generation']=='unavailable' and result['evidence']==E

def test_clarification_never_calls_model():
    class Search:
        def search(self,r):return dict(state='evidence_unassessed',record_selection=dict(status='dense_fallback',reason='comparison_groups_unspecified'),evidence=E,generation='not_called')
    def forbidden(*a):raise AssertionError('Model must not run')
    assert SinglePassAnswers(Search(),forbidden).answer(dict(question='Which is bigger?'))['generation']=='not_called'
