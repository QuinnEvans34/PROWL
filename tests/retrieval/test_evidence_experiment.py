from copy import deepcopy
import pytest
from src.retrieval.evidence_experiment import body, curated_sources, review_body, sha


def sources():
    return [dict(source='P1', text='The study reports a result in this selected sample.',
                 title='Paper', work_id='w1', passage_id='a', expected_answer='must never enter prompt'),
            dict(source='P2', text='The sample used a particular measurement method.',
                 title='Paper', work_id='w1', passage_id='b')]


def test_matched_arms_preserve_exact_sources_and_only_add_relationships():
    s = sources()
    links = [dict(work_id='w1', roles=dict(finding=['P1'], method=['P2']))]
    flat, linked = body('Question?', s), body('Question?', s, links)
    assert flat['sources'] == linked['sources']
    assert flat['question'] == linked['question']
    assert flat['evidence_links'] == []
    assert 'expected_answer' not in str(linked)
    assert s[0]['expected_answer'] == 'must never enter prompt'


@pytest.mark.parametrize('role,ids,work', [('method', ['P9'], 'w1'), ('method', ['P1'], 'w2'),
                                       ('expected_answer', ['P1'], 'w1'), ('method', [], 'w1')])
def test_invalid_relationships_cannot_reassign_evidence(role, ids, work):
    with pytest.raises(ValueError):
        body('Q', sources(), [dict(work_id=work, roles={role: ids})])


def test_review_only_sees_citations_bound_to_each_claim():
    raw = dict(claims=[dict(text='A result.', citations=[dict(source='P1')])])
    result = review_body('Q', raw, sources())
    assert [c['source'] for c in result['claims'][0]['citations']] == ['P1']
    assert sources()[1]['text'] not in str(result)
    assert raw['claims'][0]['citations'] == [dict(source='P1')]


def test_changed_curated_text_is_rejected_before_model_call():
    s = sources()[0]
    recipe = dict(passages=[dict(work_id='w1', ordinal=0, passage_id='a', text_sha256=sha(s['text'].encode()))])
    lookup = {('w1', 0): s}
    assert curated_sources(recipe, lookup)[0] == s
    altered = deepcopy(s); altered['text'] += ' Changed.'
    with pytest.raises(ValueError):
        curated_sources(recipe, {('w1', 0): altered})


def test_duplicate_sources_rejected():
    with pytest.raises(ValueError):
        body('Q', [sources()[0], sources()[0]])
