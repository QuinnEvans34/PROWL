from src.retrieval.guided_retrieval import merge, plan, CATALOG


def hit(pid, text):
    return dict(record=dict(passage=dict(passage_id=pid), text=text), score=.5)


def test_facet_coverage_duplicates_and_provenance():
    a=hit('a','definition feature extraction workflow')
    b=hit('b','EUS clinical study morphology cyst')
    result=merge([('first',[a,b]),('second',[b,a])],2)
    assert [r['record']['passage']['passage_id'] for r in result]==['a','b']
    assert len(result[0]['retrieval']['matches'])==2
    assert result==merge([('first',[a,b]),('second',[b,a])],2)


def test_near_duplicates_do_not_displace_distinct_evidence():
    result=merge([('q',[hit('a','one two three four five six'),hit('b','one two three four five six seven'),hit('c','different study text')])],2)
    assert [r['record']['passage']['passage_id'] for r in result]==['a','c']
    assert merge([],5)==[]


def test_expansion_is_only_for_known_guided_question():
    assert len(plan(CATALOG[0]['label']))==3
    assert plan('unknown question')==['unknown question']
