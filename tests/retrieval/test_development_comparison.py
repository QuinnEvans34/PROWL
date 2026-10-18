"""Hand-oracle guard: good source retrieval is not necessarily good passage retrieval."""
import importlib.util
from pathlib import Path
import sys

import pytest


@pytest.fixture
def scorer(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(root/'scripts'))
    spec = importlib.util.spec_from_file_location('development_comparison',
        root/'scripts/retrieval/compare_development_rankings.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.score


def fixture():
    records = {}
    for i in range(7):
        pid = f'p{i}'
        records[pid] = dict(passage=dict(passage_id=pid, work_id='w1' if i<6 else 'w2',
            representation_id='r1' if i<6 else 'r2', representation_sha256='h', start=i*10, end=i*10+10))
    span = dict(representation_id='r1', representation_sha256='h', start=51, end=59, grade='direct')
    case = dict(labels=dict(spans=[span]))
    reps = [dict(representation_id='r1',work_id='w1'),dict(representation_id='r2',work_id='w2')]
    return records, case, reps


def test_source_hit_does_not_count_as_direct_passage_or_span(scorer):
    records, case, reps = fixture()
    result = scorer([dict(passage_id=f'p{i}',score=1-i/10) for i in range(7)],case,records,reps)
    assert result['source_recall_at_1']==1
    assert result['passage_recall_at_5']==0 and result['passage_recall_at_10']==1
    assert result['passage_mrr']==1/6
    assert result['top5_source_coverage']==1 and result['top5_direct_hits']==0
    assert result['diagnostic_span_hit_at_5']==0


def test_empty_lexical_list_is_zero_not_perfect_or_filled(scorer):
    records, case, reps = fixture()
    result = scorer([],case,records,reps)
    assert all(value==0 for value in result.values())


@pytest.mark.parametrize('ids',[['p0','p0'],['foreign']])
def test_bad_membership_refuses_metrics(scorer,ids):
    records, case, reps = fixture()
    with pytest.raises(ValueError):
        scorer([dict(passage_id=p,score=.1) for p in ids],case,records,reps)
