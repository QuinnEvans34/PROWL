import pytest
from src.inference.evaluation_summary import summarize


def row(case, state, dice, volume):
    return dict(case_id=case, inference_status='complete', scoring_status='complete',
        score=dict(lesion_reference_state=state, metrics=dict(
            lesion=dict(dice=dice, recall=dice, false_positive_ml=volume),
            pancreas_lesion_union=dict(dice=.5))))


def test_failures_and_empty_references_do_not_inflate_mean():
    rows=[row('a','positive',.2,1),row('b','positive',.8,2),
          row('c','reference_empty',None,8),
          dict(case_id='d',inference_status='failed',scoring_status='failed')]
    r=summarize(rows,['a','b','c','d'])
    assert r['fixed_cases']==4 and r['scored_cases']==3 and r['failed_or_unscored_cases']==1
    assert r['positive_lesion_macro_dice']==dict(value=.5,n=2)
    assert r['empty_reference_mean_predicted_lesion_ml']==dict(value=8,n=1)


def test_missing_duplicate_reordered_cases_refused():
    a=row('a','positive',.2,1);b=row('b','positive',.8,2)
    for rows,ids in [([a],['a','b']),([a,a],['a','b']),([b,a],['a','b']),([a,a],['a','a'])]:
        with pytest.raises(ValueError):summarize(rows,ids)


def test_all_failures_are_not_zero_dice():
    r=summarize([dict(case_id='a',inference_status='failed',scoring_status='failed')],['a'])
    assert r['positive_lesion_macro_dice']==dict(value=None,n=0)
    assert r['failed_or_unscored_cases']==1
