from types import SimpleNamespace
import torch
import pytest
from src.retrieval.section_ranking import SectionRanker


class Tokenizer:
    def __init__(self):self.seen=[]
    def __call__(self,query,text,**kwargs):
        if isinstance(text,str):
            self.seen.append(text)
            return dict(input_ids=list(range(len(text)//2+1)))
        return dict(input_ids=torch.zeros((len(text),max(len(t)//2+1 for t in text)),dtype=torch.long))


def setup(count=1):
    tokenizer=Tokenizer()
    model=SimpleNamespace(tokenizer=tokenizer,model=lambda **kw:SimpleNamespace(logits=torch.zeros((len(kw['input_ids']),1))))
    text='abcdefghij'*140
    bundle=dict(work=dict(work_id='w'),citation=dict(title='Study'),representation=dict(work_id='w',text=text,
        sections=[dict(section_id='s',title='Methods',start=0,end=len(text))]))
    records=[dict(text='Original canonical passage',citation=dict(title='Study'),passage=dict(
        passage_id=str(i),work_id='w',ordinal=i,section_id='s')) for i in range(count)]
    return SectionRanker(model,[bundle],records),records,tokenizer


def test_scoring_windows_split_but_returned_records_stay_canonical():
    ranker,records,tokenizer=setup()
    result=ranker.search('Pancreas')
    assert result['window_count']==3  # first1200characters split; final400 also retained
    assert [h['record'] for h in result['hits']]==records
    assert result['hits'][0]['record'] is records[0]
    assert all(len(t)//2+1<=512 for t in tokenizer.seen if len(t)<1200)


def test_large_package_fails_instead_of_clipping():
    ranker,_,_=setup(51)
    with pytest.raises(ValueError,match='budget exceeded'):ranker.search('Pancreas')


def test_deadline_prevents_partial_ranking(monkeypatch):
    ranker,_,_=setup();clock=iter([0,46])
    monkeypatch.setattr('src.retrieval.section_ranking.monotonic',lambda:next(clock))
    with pytest.raises(TimeoutError):ranker.search('Pancreas')


def test_nonfinite_scores_fail():
    ranker,_,_=setup()
    ranker.model.model=lambda **kw:SimpleNamespace(logits=torch.full((len(kw['input_ids']),1),float('nan')))
    with pytest.raises(ValueError,match='scores'):ranker.search('Pancreas')
