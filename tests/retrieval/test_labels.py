"""Span labels: validation, staleness, complete containment and grade mapping."""
from copy import deepcopy

import pytest

from src.retrieval.labels import (contains, direct_spans, gold_passages, gold_works, make_label_set,
                                  passage_grade, verify_label_set)
from src.retrieval.passages import chunk_config, make_passages, make_representation
from src.retrieval.records import RecordError

pytestmark = pytest.mark.unit
W, R = 'work:synthetic:x', 'rev:' + 'b' * 64


def rep():
    # Sentences: [0,6) 'Aa bb.' [7,13) 'Cc dd.' [14,20) 'Ee ff.'
    return make_representation(work_id=W, revision_id=R, kind='abstract',
                               sections=[dict(section_id='s0', title='', paragraphs=['Aa bb. Cc dd. Ee ff.'])])


def span(r, start, end, grade='direct', concepts=('c:one',)):
    return dict(representation_id=r['representation_id'], representation_sha256=r['text_sha256'],
                start=start, end=end, grade=grade, concept_ids=list(concepts))


def labels(r, spans, answerable=True, concepts=('c:one', 'c:two')):
    return make_label_set(question_id='q:syn-1', label_version='labels-syn-v1', answerable=answerable,
                          required_concepts=concepts if answerable else (), spans=spans)


def test_complete_containment_is_direct_partial_overlap_is_not():
    r = rep()
    one_sentence = make_passages(r, chunk_config(max_chars=6, overlap_sentences=0))  # [0,6) [7,13) [14,20)
    ls = labels(r, [span(r, 4, 10)])  # crosses the first two sentences
    verify_label_set(ls, [r])
    assert [passage_grade(p, ls) for p in one_sentence] == ['partial', 'partial', 'none']
    assert gold_passages(one_sentence, ls) == set()  # no passage fully contains the span
    two_sentence = make_passages(r, chunk_config(max_chars=13, overlap_sentences=1))  # [0,13) [7,20)
    assert [passage_grade(p, ls) for p in two_sentence] == ['direct', 'partial']
    assert gold_passages(two_sentence, ls) == {two_sentence[0]['passage_id']}


def test_uncertain_excluded_from_gold_and_duplicates_count_once():
    r = rep()
    ls = labels(r, [span(r, 0, 6), span(r, 7, 13, grade='uncertain'), span(r, 14, 20, grade='partial_context')])
    assert [(s['start'], s['end']) for s in direct_spans(ls)] == [(0, 6)]
    assert gold_works(ls, [r]) == {W}
    overlapping = make_passages(r, chunk_config(max_chars=13, overlap_sentences=1))  # both contain [7,13)
    assert sum(contains(p, span(r, 7, 13)) for p in overlapping) == 2  # counted once by metrics
    with pytest.raises(RecordError, match='duplicate'):
        verify_label_set(labels(r, [span(r, 0, 6), span(r, 0, 6)]), [r])


@pytest.mark.failure_injection
def test_stale_representation_hash_invalidates_labels():
    r = rep()
    ls = labels(r, [span(r, 0, 6)])
    changed = make_representation(work_id=W, revision_id=R, kind='abstract',
                                  sections=[dict(section_id='s0', title='', paragraphs=['Aa bb. Cc dd. Ee fg.'])])
    stale = deepcopy(ls)
    stale['spans'][0]['representation_id'] = changed['representation_id']
    with pytest.raises(RecordError, match='stale'):
        verify_label_set(stale, [changed])


@pytest.mark.parametrize('mutate,match', [
    (lambda ls: ls['spans'][0].update(end=21), 'outside'),
    (lambda ls: ls['spans'][0].update(representation_id='repr:' + 'f' * 64), 'unknown representation'),
    (lambda ls: ls['spans'][0].update(concept_ids=['c:undeclared']), 'undeclared'),
    (lambda ls: ls['spans'][0].update(grade='uncertain'), 'no direct span'),
    (lambda ls: (ls.update(required_concepts=[]), ls['spans'][0].update(concept_ids=[])), 'no required concepts'),
])
def test_invalid_label_sets_rejected(mutate, match):
    r = rep()
    ls = deepcopy(labels(r, [span(r, 0, 6)]))
    mutate(ls)
    with pytest.raises(RecordError, match=match):
        verify_label_set(ls, [r])


def test_refusal_questions_carry_no_spans_and_start_must_precede_end():
    r = rep()
    verify_label_set(labels(r, [], answerable=False), [r])
    bad = labels(r, [], answerable=False)
    bad['spans'] = [span(r, 0, 6, concepts=())]
    with pytest.raises(RecordError, match='must not carry'):
        verify_label_set(bad, [r])
    with pytest.raises(RecordError):
        verify_label_set(labels(r, [span(r, 6, 6)]), [r])
