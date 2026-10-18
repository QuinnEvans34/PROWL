from copy import deepcopy
import pytest
from src.retrieval.natural_answer import validate_question_claims, AnswerFailure, generate, PLAIN_POLICY
from src.retrieval.source_context import with_source_context
from tests.retrieval.test_natural_answer import EVIDENCE, provider


def claim(text, quote):
    return {'claims':[{'text':text,'citations':[{'quote':quote}]}]}


def test_rejects_unrequested_incidence_even_when_number_in_source():
    with pytest.raises(AnswerFailure):
        validate_question_claims('Could pancreas size indicate disease?',claim('Occurs in 20% of cases.','Probably 20% in our experience.'))


def test_explicit_rate_question_can_use_percent():
    validate_question_claims('How often does this occur?',claim('One study reports 20%.','20%'))


@pytest.mark.parametrize('part',['head','body','tail'])
def test_does_not_narrow_whole_organ_statement(part):
    with pytest.raises(AnswerFailure):
        validate_question_claims('Pancreas size?',claim(f'The {part} shrinks with age.','The pancreas shrinks with age.'))


def test_subregion_requires_its_own_claim_citation():
    draft=claim('The head can enlarge.','The head can enlarge.')
    draft['claims']+=claim('The tail can enlarge.','The pancreas can enlarge.')['claims']
    with pytest.raises(AnswerFailure):validate_question_claims('Size?',draft)


def test_plain_profile_keeps_two_calls_and_new_policy():
    call,calls=provider()
    answer=generate('Pancreas size?',EVIDENCE,call,profile='section_plain')
    assert answer['policy']==PLAIN_POLICY
    chats=[p for path,p in calls if path=='chat']
    assert len(chats)==2
    assert chats[0]['format']['properties']['claims']['items']['properties']['citations']['maxItems']==3
    assert chats[0]['options']['num_ctx']==16384


def record(work,section,ordinal):
    return {'passage':dict(work_id=work,section_id=section,ordinal=ordinal,passage_id=f'{work}-{section}-{ordinal}'), 'text':'Context text', 'citation':{'title':'Study'}}


def test_context_adds_selected_paper_methods_and_abstract_without_duplicates():
    records=[record('a','body',0),record('a','abstract0',1),record('a','methods',2),record('b','abstract0',0)]
    bundles=[{'representation':{'work_id':w,'sections':[dict(section_id='abstract0',title='Abstract'),dict(section_id='methods',title='Data analysis')]}} for w in ('a','b')]
    hits=[dict(record=records[0],score=1),dict(record=records[1],score=.5)]
    result=with_source_context(hits,bundles,records)
    assert [h['record'] for h in result]==records[:3]
    assert len(hits)==2


def test_context_overflow_is_explicit():
    with pytest.raises(ValueError,match='budget'):
        with_source_context([dict(record=record('a','body',i),score=1) for i in range(51)],[],[])


def test_dense_model_comparison_changes_only_model_identity():
    from src.retrieval.natural_answer import DENSE_MODEL,DENSE_MODEL_SHA,DENSE_POLICY,PLAIN_SYSTEM
    call,calls=provider()
    def dense(path,payload=None):
        result=call(path,payload)
        if path=='tags':result['models']=[dict(name=DENSE_MODEL,digest=DENSE_MODEL_SHA)]
        else:result['model']=DENSE_MODEL
        return result
    result=generate('Pancreas size?',EVIDENCE,dense,profile='dense_plain')
    assert result['model']==DENSE_MODEL and result['policy']==DENSE_POLICY
    chats=[p for path,p in calls if path=='chat']
    assert len(chats)==2 and chats[0]['messages'][0]['content']==PLAIN_SYSTEM
    assert all(p['model']==DENSE_MODEL for p in chats)


def test_dense_profile_rejects_wrong_installed_digest_before_generation():
    call,calls=provider()
    with pytest.raises(OSError):generate('Pancreas?',EVIDENCE,call,profile='dense_plain')
    assert len(calls)==1


def test_sampled_profile_uses_publisher_options_and_keeps_seed():
    from src.retrieval.natural_answer import DENSE_MODEL,DENSE_MODEL_SHA,SAMPLED_POLICY
    call,calls=provider()
    def dense(path,payload=None):
        result=call(path,payload)
        if path=='tags':result['models']=[dict(name=DENSE_MODEL,digest=DENSE_MODEL_SHA)]
        else:result['model']=DENSE_MODEL
        return result
    result=generate('Pancreas size?',EVIDENCE,dense,profile='sampled_plain')
    assert result['policy']==SAMPLED_POLICY
    chats=[p for path,p in calls if path=='chat']
    assert [p['options']['temperature'] for p in chats]==[.6,.7]
    assert [p['options']['top_p'] for p in chats]==[.95,.8]
    assert all(p['options']['seed']==42 and p['options']['top_k']==20 and p['options']['min_p']==0 for p in chats)


def test_instruction_profile_uses_pinned_model_without_thinking_parameter():
    from src.retrieval.natural_answer import INSTRUCT_MODEL,INSTRUCT_MODEL_SHA,INSTRUCT_POLICY
    call,calls=provider()
    def instruct(path,payload=None):
        result=call(path,payload)
        if path=='tags':result['models']=[dict(name=INSTRUCT_MODEL,digest=INSTRUCT_MODEL_SHA)]
        else:result['model']=INSTRUCT_MODEL
        return result
    result=generate('Pancreas size?',EVIDENCE,instruct,profile='instruct_plain')
    assert result['policy']==INSTRUCT_POLICY
    chats=[p for path,p in calls if path=='chat']
    assert len(chats)==2 and all('think' not in p for p in chats)
    assert all(p['model']==INSTRUCT_MODEL and p['options']['num_predict']==1536 for p in chats)
