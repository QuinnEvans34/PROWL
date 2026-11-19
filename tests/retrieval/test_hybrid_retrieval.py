"""Synthetic retrieval checks, not a medical answer-accuracy benchmark."""
from copy import deepcopy
import math
import pytest

from src.retrieval.hybrid_retrieval import HybridPassageIndex, LIMITS, terms


def record(pid, text, title='Synthetic gland research'):
    return dict(passage=dict(passage_id=pid), citation=dict(title=title), text=text)


def hit(row, score=.8):
    return dict(record=deepcopy(row), score=score)


def test_complementary_lexical_facts_survive_tangential_dense_results():
    direct = record('fact', 'The gland secretes invented hormone quasinin.')
    studies = [record(f'study{i}', f'Quasinin concentrations correlate with organ size in study {i}.') for i in range(8)]
    index = HybridPassageIndex([direct] + studies, LIMITS)
    hits = index.rank('Does the gland produce quasinin?', [hit(r) for r in studies])
    assert direct in [h['record'] for h in hits]
    assert len(hits) == 5 and len({h['record']['passage']['passage_id'] for h in hits}) == 5


def test_biological_dysfunction_does_not_match_machine_learning_loss_function():
    clinical = record('clinical', 'Gland dysfunction interferes with its usual function.')
    ml = record('ml', 'The gland segmentation uses a Dice loss function and focal loss function.')
    index = HybridPassageIndex([clinical, ml], LIMITS)
    assert index.lexical('What happens if the gland loses function?')[0][0] == 'clinical'
    assert 'optimizationobjective' in terms(ml['text'])
    assert terms('loss of function') == ['dysfunction', 'function']


def test_morphology_normalization_preserves_organ_word_and_negation():
    assert terms('pancreatic pancreas') == ['pancreas', 'pancreas']
    assert terms('The pancreas does not secrete quasinin.') == ['pancreas', 'not', 'secrete', 'quasinin']
    assert 'function' in terms('What does the gland do?', question=True)


def test_source_title_is_searchable_but_never_added_to_original_passage():
    row = record('source', 'Cells secrete quasinin.', 'Anatomy of the invented gland')
    index = HybridPassageIndex([row], LIMITS)
    assert index.lexical('Where is the invented gland?')
    result = index.rank('Where is the invented gland?', [])
    assert result[0]['record'] == row
    result[0]['record']['text'] = 'changed'
    assert index.rank('Where is the invented gland?', [])[0]['record'] == row


def test_input_records_are_detached_and_canonical_candidates_are_required():
    row = record('source', 'An invented gland releases a hormone.')
    original = deepcopy(row)
    index = HybridPassageIndex([row], LIMITS)
    row['text'] = 'modified after admission'
    assert index.rank('gland', [hit(original)])[0]['record'] == original
    with pytest.raises(ValueError):
        index.rank('gland', [hit(row)])


@pytest.mark.parametrize('dense', ['bad', [hit(record('foreign', 'gland'))],
    [hit(record('source', 'gland'))] * 2,
    [hit(record('source', 'gland'), math.nan)],
    [hit(record('source', 'gland'))] * 21])
def test_invalid_dense_candidates_fail_closed(dense):
    with pytest.raises(ValueError):
        HybridPassageIndex([record('source', 'gland')], LIMITS).rank('gland', dense)


def test_empty_channels_and_sparse_matches_do_not_invent_results():
    index = HybridPassageIndex([record('source', 'An invented gland.')], LIMITS)
    assert index.rank('quasinin', []) == []
    assert len(index.rank('gland', [])) == 1


@pytest.mark.parametrize('question', ['', ' ', None, 'a' * 501])
def test_question_budget(question):
    with pytest.raises(ValueError):
        HybridPassageIndex([record('source', 'gland')], LIMITS).rank(question, [])


def test_configuration_and_corpus_limits_are_explicit():
    with pytest.raises(ValueError):
        HybridPassageIndex([record('source', 'gland')], dict(LIMITS, top_k=10))
    with pytest.raises(ValueError):
        HybridPassageIndex([], LIMITS)
    with pytest.raises(ValueError):
        HybridPassageIndex([record('same', 'gland')] * 2, LIMITS)


def test_dense_complement_retains_two_distinct_results_and_stable_order():
    rows = [record(f'lex{i}', f'Quasinin gland secretion {i}') for i in range(4)]
    other = [record(f'dense{i}', f'A different semantic description {i}.') for i in range(3)]
    index = HybridPassageIndex(rows + other, LIMITS)
    result = index.rank('quasinin', [hit(r) for r in other])
    assert [h['record']['passage']['passage_id'] for h in result][-2:] == ['dense0', 'dense1']
    assert [h['score'] for h in result] == [1, .5, 1/3, .25, .2]
