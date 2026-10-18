"""Generic policy regressions with invented evidence; no expected clinical answers."""
import json
from copy import deepcopy
import pytest
from src.retrieval.natural_answer import generate, AnswerFailure, NaturalAnswerService
from tests.retrieval.test_natural_answer import provider, DRAFT, EVIDENCE
from tests.retrieval.test_development_search import service
from tests.retrieval.test_literature_adapter import setup
from tests.retrieval.test_direct_ingestion import bundle


@pytest.mark.parametrize('strength', ['must compare','requires comparison','requiring comparison',
    'comparison is necessary','comparison is mandatory'])
def test_recommendation_cannot_become_mandatory_even_if_model_would_approve(strength):
    text='In this artificial pancreas study, comparison with earlier images is recommended.'
    evidence=[dict(rank=1,record=dict(text=text,citation=dict(title='Invented study')))]
    draft=deepcopy(DRAFT);draft['claims'][0]['text']='The study '+strength+' with earlier images.'
    call,calls=provider(draft)
    with pytest.raises(AnswerFailure) as failure: generate('Pancreas study recommendation?',evidence,call)
    assert failure.value.code=='qualifier_mismatch' and len(calls)==2


def test_expected_answer_and_internal_grounding_do_not_enter_review_claims():
    evidence=deepcopy(EVIDENCE)
    evidence[0]['expected_answer']='SECRET_EXPECTED_ANSWER'
    evidence[0]['record']['gold_concepts']=['SECRET_GOLD_LABEL']
    draft=deepcopy(DRAFT);draft['grounding']='INTERNAL_GROUNDING_CANARY'
    call,calls=provider(draft)
    result=generate('Pancreas size?',evidence,call)
    messages=str([p['messages'] for route,p in calls if route=='chat'])
    assert 'SECRET_EXPECTED_ANSWER' not in messages and 'SECRET_GOLD_LABEL' not in messages
    reviewed=json.loads(calls[2][1]['messages'][1]['content'])
    assert 'INTERNAL_GROUNDING_CANARY' not in str(reviewed) and 'grounding' not in result


@pytest.mark.parametrize('population',['healthy participants','healthy control group',
    'normal adults','control subjects','controls'])
def test_undefined_cohort_cannot_be_upgraded_to_health_or_control_status(population):
    text='In this invented pancreas study, the mean volume in group XYZ was 80 cm3.'
    evidence=[dict(rank=1,record=dict(text=text,citation=dict(title='Invented healthy controls title')))]
    draft=deepcopy(DRAFT);draft['claims'][0]['text']=f'The study reported 80 cm3 in {population}.'
    call,calls=provider(draft)
    with pytest.raises(AnswerFailure) as failure: generate('Pancreas volume?',evidence,call)
    assert failure.value.code=='qualifier_mismatch' and len(calls)==2


def test_explicit_source_population_descriptor_remains_usable():
    text='In this invented pancreas study, the healthy control group had a mean volume of 80 cm3.'
    evidence=[dict(rank=1,record=dict(text=text,citation=dict(title='Invented study')))]
    draft=deepcopy(DRAFT);draft['claims'][0]['text']='The study reported 80 cm3 in its healthy control group.'
    call,_=provider(draft)
    assert generate('Pancreas volume?',evidence,call)['status']=='summarized'


def test_controls_as_a_verb_is_not_a_population_descriptor():
    text='The invented study says the pancreas regulates energy use through hormones.'
    evidence=[dict(rank=1,record=dict(text=text,citation=dict(title='Invented study')))]
    draft=deepcopy(DRAFT);draft['claims'][0]['text']='The pancreas controls energy use through hormones.'
    call,_=provider(draft)
    assert generate('Pancreas function?',evidence,call)['status']=='summarized'


@pytest.mark.parametrize('code',['qualifier_mismatch'])
def test_rejected_quality_remains_failure_not_insufficient(service,code):
    search,request,_=service
    def fail(*args): raise AnswerFailure(code,'PRIVATE_DRAFT')
    result=NaturalAnswerService(search,fail).answer(request)
    assert result['generation']=='unavailable' and result['answer'] is None
    assert result['generation_failure']==code and result['evidence']
    assert 'PRIVATE_DRAFT' not in str(result)
