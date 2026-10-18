import math
import pytest
from src.retrieval.cross_encoder import ordered_hits, PassageReranker


def records(*ids):
    return [dict(passage=dict(passage_id=i),text='Invented evidence') for i in ids]


def test_logits_can_be_negative_and_ties_are_stable():
    r=records('b','a','c')
    assert [h['record']['passage']['passage_id'] for h in ordered_hits(r,[-1,-1,-3],2)]==['a','b']


@pytest.mark.parametrize('scores',[[math.nan,1],[math.inf,1],[1]])
def test_nonfinite_or_missing_scores_fail(scores):
    with pytest.raises(ValueError):ordered_hits(records('a','b'),scores,5)


def test_duplicate_identity_fails():
    with pytest.raises(ValueError):ordered_hits(records('a','a'),[1,2],5)


@pytest.mark.parametrize('k',[0,51,True,1.5])
def test_invalid_limit(k):
    with pytest.raises(ValueError):ordered_hits(records('a'),[1],k)


@pytest.mark.parametrize('question',['',' ',None,'a'*501])
def test_invalid_question_never_loads_model(question):
    scorer=PassageReranker.__new__(PassageReranker)
    with pytest.raises(ValueError):scorer.rank(question,records('a'))


def fake_scorer(tokens=10):
    import torch
    scorer=PassageReranker.__new__(PassageReranker)
    scorer.descriptor=dict(max_passages=1179,seconds=30,batch_size=32,max_tokens=512)
    scorer.tokenizer=lambda *a,**kw:dict(input_ids=torch.ones((1,tokens),dtype=torch.long))
    scorer.model=lambda **kw:(_ for _ in ()).throw(AssertionError('Model must not run'))
    return scorer


def test_overlong_pair_rejected_before_model_not_silently_truncated():
    with pytest.raises(ValueError,match='no truncation'):
        fake_scorer(513).rank('pancreas',records('a'))


def test_expired_deadline_returns_no_partial_ranking(monkeypatch):
    scorer=fake_scorer()
    times=iter([0,31])
    monkeypatch.setattr('src.retrieval.cross_encoder.monotonic',lambda:next(times))
    with pytest.raises(TimeoutError):scorer.rank('pancreas',records('a'))


def test_corpus_bound_rejects_before_model():
    with pytest.raises(ValueError,match='Candidate count'):
        fake_scorer().rank('pancreas',records(*map(str,range(1180))))
