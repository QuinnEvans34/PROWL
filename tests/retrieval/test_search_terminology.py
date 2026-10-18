import pytest
from src.retrieval.search_terminology import normalize_search_terms


@pytest.mark.parametrize('question',[
    'Could the size of the pancreas body be associated with disease?',
    'Does abnormal pancreatic tail size have a meaning?',
    'Which conditions change pancreatic dimensions?',
])
def test_general_size_disease_intent_expands_without_changing_anatomy(question):
    result=normalize_search_terms(question)
    assert 'enlargement, swelling or atrophy' in result
    for anatomy in ['body','tail']:
        assert (anatomy in question)==(anatomy in result)


@pytest.mark.parametrize('question',['How large is the average pancreas?',
    'What is the pancreas size?', 'Does liver size indicate disease?',
    'What CT limitations did the TAGS pancreas study report?'])
def test_unrelated_intents_unchanged(question):
    assert normalize_search_terms(question)==question


def test_negation_comparison_and_original_clause_preserved():
    q='Why does pancreatic inflammation not always imply a tumor?'
    assert normalize_search_terms(q)=='Why does pancreatic inflammation (pancreatitis) not always imply a tumor?'


def test_expansion_over_budget_preserves_original():
    q='Pancreatic size disease '+ 'a'*470
    assert normalize_search_terms(q)==q
