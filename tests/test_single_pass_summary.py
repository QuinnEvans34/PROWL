import json
import pytest
from jsonschema import ValidationError
from src.retrieval.single_pass_summary import generate,SinglePassAnswers,MODEL,MODEL_SHA
E=[dict(rank=1,record=dict(text='The invented gland releases digestive enzymes.',citation=dict(title='Synthetic source')))]
A=dict(coverage='supported',limitation='',claims=[dict(text='It releases enzymes that help digestion.',sentence_ids=['P1S1'])])
def run(answer=A):
    calls=[]
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        calls.append(payload)
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(answer)))
    return generate('What does it do?',E,call),calls

def test_one_call_question_evidence_and_bounded_thinking():
    answer,calls=run();assert len(calls)==1 and calls[0]['think'] is True
    assert calls[0]['options']['num_predict']==1536
    body=json.loads(calls[0]['messages'][1]['content'])
    assert body['question']=='What does it do?' and body['passages'][0]['sentences'][0]['text']==E[0]['record']['text']
    assert answer['validation']=='citation_binding_only'

@pytest.mark.parametrize('kind',['unknown','quote','coverage','duplicate'])
def test_bad_binding_rejected(kind):
    a=json.loads(json.dumps(A));c=a['claims'][0]
    if kind=='unknown':c['sentence_ids']=['P2S1']
    if kind=='quote':c['quote']='This supporting text is entirely invented.'
    if kind=='coverage':a['coverage']='none'
    if kind=='duplicate':c['sentence_ids'].append('P1S1')
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


def test_resolves_exact_contiguous_span_including_qualification():
    from src.retrieval.single_pass_summary import source_sentences
    evidence=[dict(rank=2,record=dict(text='The organ is visible [1]. However, the boundary can be uncertain. This study used CT [2].',citation=dict(title='Invented')))]
    sources, lookup=source_sentences(evidence)
    assert [x['id'] for x in sources[0]['sentences']]==['P2S1','P2S2','P2S3']
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        answer=dict(claims=[dict(text='The organ is visible in this CT study.',sentence_ids=['P2S1','P2S3'])],coverage='supported',limitation='')
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(answer)))
    result=generate('What was visible?',evidence,call)
    assert result['claims'][0]['citations']==[dict(rank=2,quote=evidence[0]['record']['text'])]
    assert 'sentence_ids' not in result['claims'][0]


def test_supported_answer_cannot_include_spurious_limitation():
    a=json.loads(json.dumps(A));a['limitation']='The wording differs.'
    with pytest.raises(ValidationError):run(a)
