from copy import deepcopy
import pytest
from src.retrieval.answer_feedback import collect_claim_feedback, review_feedback
from src.retrieval.natural_answer import AnswerFailure
from tests.retrieval.test_isolated_answer import REVIEW

SOURCES=[dict(source='P1', title='Invented study', text='One study reported a mean volume of 80±4 cm³ (mean±SEM), 20% larger than its comparison group.')]


def draft(text):
    return dict(claims=[dict(text=text,citations=[dict(source='P1')])])


def test_percentage_does_not_hide_missing_study_context_and_uncertainty():
    claims, issues=collect_claim_feedback(draft('The mean is 80±4 cm³, 20% larger.'),SOURCES,'What is the average volume?')
    assert not claims
    assert {i['criterion'] for i in issues}=={'question_scope','study_qualifiers'}
    reasons=' '.join(i['reason'] for i in issues)
    assert 'specific study' in reasons and 'statistical meaning' in reasons and 'sample size' in reasons


def test_rejected_draft_never_returns_partial_claims():
    raw=draft('One study reported a mean volume of 80 cm³.')
    raw['claims']+=draft('The mean is 80±4 cm³.')['claims']
    claims, issues=collect_claim_feedback(raw,SOURCES,'Volume?')
    assert not claims and issues


def test_passed_mechanical_checks_preserve_canonical_quote_without_mutating_input():
    raw=draft('One study reported a mean volume of 80 cm³.')
    original=deepcopy(raw)
    claims,issues=collect_claim_feedback(raw,SOURCES,'Volume?')
    assert not issues and claims[0]['citations'][0]['quote']==SOURCES[0]['text']
    assert raw==original


def test_blank_model_rejection_stays_rejected_instead_of_becoming_revision_feedback():
    with pytest.raises(AnswerFailure,match='no explanation'):
        review_feedback(dict(REVIEW,qualified=False,feedback=' '),1)


def test_nonempty_rejection_preserves_failed_criterion():
    issues=review_feedback(dict(REVIEW,qualified=False,feedback='Missing measurement method.'),1)
    assert issues==[dict(claim=None,criterion='qualified',reason='Missing measurement method.')]


def test_support_rejection_cannot_be_lost_in_other_positive_flags():
    review=deepcopy(REVIEW);review['checks'][0].update(supported=False,explanation='Population differs.')
    assert review_feedback(review,1)[0]['criterion']=='support'


def test_review_cannot_duplicate_or_omit_claim_identity():
    review=deepcopy(REVIEW);review['checks']*=2
    with pytest.raises(AnswerFailure,match='identity'):review_feedback(review,2)
