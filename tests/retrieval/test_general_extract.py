import json
import pytest
from jsonschema import ValidationError
from src.retrieval.general_extract import generate, MODEL, MODEL_SHA
EVIDENCE=[dict(rank=1,record=dict(text='The invented gland releases enzymes. Its location is behind the invented organ.',citation=dict(title='Synthetic source')))]

def fake(selections):
    calls=[]
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        calls.append(payload)
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(selections[len(calls)-1])))
    return call,calls

def test_audit_can_remove_unrelated_sentence_and_exact_text_is_copied():
    call,calls=fake([dict(coverage='supported',sentence_ids=['P1S1','P1S2']),dict(coverage='supported',sentence_ids=['P1S1'])])
    r=generate('What does the invented gland do?',EVIDENCE,call)
    assert r['claims']==[dict(text='The invented gland releases enzymes.',citations=[dict(rank=1,quote='The invented gland releases enzymes.')])]
    assert len(calls)==2 and json.loads(calls[1]['messages'][1]['content'])['proposed']['sentence_ids']==['P1S1','P1S2']

@pytest.mark.parametrize('selection',[dict(coverage='supported',sentence_ids=['P9S9']),dict(coverage='none',sentence_ids=['P1S1']),dict(coverage='supported',sentence_ids=[])])
def test_invalid_or_inconsistent_selection_cannot_publish(selection):
    call,_=fake([selection])
    with pytest.raises((ValueError,ValidationError)):generate('Question',EVIDENCE,call)

def test_gap_keeps_no_claims():
    call,_=fake([dict(coverage='none',sentence_ids=[])]*2)
    r=generate('What is the numerical range?',EVIDENCE,call)
    assert r['status']=='insufficient' and r['claims']==[]

@pytest.mark.parametrize('result',[dict(answer={'status':'summarized'},state='evidence_unassessed'),dict(answer=None,state='not_searched'),dict(answer=None,state='evidence_unassessed',record_selection=dict(status='dense_fallback',reason='diabetes_population_unspecified'))])
def test_wrapper_preserves_reviewed_answers_boundaries_and_clarifications(result):
    from src.retrieval.general_extract import GeneralExtractAnswers
    class Reviewed:
        def answer(self,r):return result
    def unexpected(*args):raise AssertionError('No fallback call')
    assert GeneralExtractAnswers(Reviewed(),unexpected).answer({'question':'test'}) is result

def test_wrapper_keeps_evidence_on_model_failure():
    from src.retrieval.general_extract import GeneralExtractAnswers
    class Reviewed:
        def answer(self,r):return dict(answer=None,state='evidence_unassessed',record_selection=dict(status='dense_fallback'),evidence=EVIDENCE)
    def fail(*args):raise TimeoutError()
    r=GeneralExtractAnswers(Reviewed(),fail).answer({'question':'test'})
    assert r['generation']=='unavailable' and r['evidence']==EVIDENCE and r['answer'] is None


def test_unrepresented_volume_population_does_not_start_slow_selection():
    from src.retrieval.general_extract import GeneralExtractAnswers
    result=dict(answer=None,state='evidence_unassessed',record_selection=dict(policy='source-linked-volume-search-v1',status='dense_fallback',reason='unrepresented_population'))
    class Reviewed:
        def answer(self,r):return result
    def unexpected(*args):raise AssertionError('No fallback for existing volume boundary')
    assert GeneralExtractAnswers(Reviewed(),unexpected).answer({'question':'Pancreas volume in children?'}) is result

def test_cache_reuses_only_same_question_evidence_and_returns_independent_copy():
    from copy import deepcopy
    from src.retrieval.general_extract import GeneralExtractAnswers
    class Reviewed:
        evidence = deepcopy(EVIDENCE)
        def answer(self,r):
            return dict(answer=None,state='evidence_unassessed',record_selection=dict(status='dense_fallback'),evidence=self.evidence)
    calls=[]
    def produce(q,e):
        calls.append(q)
        return dict(status='summarized',claims=[dict(text=e[0]['record']['text'])])
    reviewed=Reviewed(); service=GeneralExtractAnswers(reviewed,produce)
    first=service.answer({'question':'function?'})
    first['answer']['claims'].clear()
    second=service.answer({'question':'function?'})
    assert second['answer']['claims'] and len(calls)==1
    assert second['timing']['checked_answer_cache_hit'] is True
    service.answer({'question':'location?'})
    reviewed.evidence[0]['record']['text']='Changed source.'
    service.answer({'question':'function?'})
    assert len(calls)==3

def test_cache_has_a_bounded_lifetime(monkeypatch):
    import src.retrieval.general_extract as module
    clock=[0]; monkeypatch.setattr(module,'monotonic',lambda:clock[0])
    class Reviewed:
        def answer(self,r):
            return dict(answer=None,state='evidence_unassessed',record_selection=dict(status='dense_fallback'),evidence=EVIDENCE)
    calls=[]
    def produce(q,e): calls.append(q); return dict(claims=[])
    service=module.GeneralExtractAnswers(Reviewed(),produce)
    service.answer({'question':'test'});clock[0]=601
    service.answer({'question':'test'})
    assert len(calls)==2
