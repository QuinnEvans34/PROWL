import pytest
from src.retrieval.direct_ingestion import digest
from src.retrieval.evaluation import score


def fixture():
    suite = {'cases': [dict(id='one', question='question', expected_status='excerpts',
                            aspects=['fact'], reference_passage_ids=['p1'])]}
    quote = 'An exact quotation may still discuss an unrelated research task.'
    receipt = dict(case_id='one', question='question', suite_sha256=digest(suite),
                   passages=[{'record': {'passage': {'passage_id': 'p1'}, 'text': quote}}],
                   generation=dict(validation='exact_quotes_verified', answer=dict(status='excerpts',
                       extracts=[dict(passage_id='p1', quote=quote)])), total_seconds=1)
    review = dict(receipt_sha256=digest(receipt), extract_relevance=['mixed'],
                  aspects_covered=[True], rationale='Contains the fact and unrelated material.')
    return suite, {'one': receipt}, {'one': review}


def test_exact_citation_does_not_imply_relevance():
    result = score(*fixture())['totals']
    assert result['reference_hits'] == result['exact_extracts'] == result['covered_aspects'] == 1
    assert result['relevant_extracts'] == result['clean_supported_answers'] == 0


def test_changed_receipt_cannot_reuse_review():
    suite, receipts, reviews = fixture()
    receipts['one']['total_seconds'] = 2
    with pytest.raises(ValueError, match='identity'):
        score(suite, receipts, reviews)


@pytest.mark.parametrize('mutation', ['missing_review', 'missing_extract', 'nonboolean'])
def test_incomplete_judgments_refused(mutation):
    suite, receipts, reviews = fixture()
    if mutation == 'missing_review':
        reviews.clear()
    elif mutation == 'missing_extract':
        reviews['one']['extract_relevance'] = []
    else:
        reviews['one']['aspects_covered'] = ['yes']
    with pytest.raises(ValueError):
        score(suite, receipts, reviews)


def test_rejected_generation_is_not_successful_abstention():
    suite, receipts, reviews = fixture()
    suite['cases'][0].update(expected_status='insufficient_evidence', aspects=[], reference_passage_ids=[])
    receipt = receipts['one']
    receipt.update(suite_sha256=digest(suite), generation=dict(validation='generation_rejected',
                   answer=dict(status='insufficient_evidence', extracts=[])))
    reviews['one'].update(receipt_sha256=digest(receipt), extract_relevance=[], aspects_covered=[])
    assert score(suite, receipts, reviews)['totals']['correct_abstentions'] == 0
    receipt['generation']['validation'] = 'exact_quotes_verified'
    reviews['one']['receipt_sha256'] = digest(receipt)
    assert score(suite, receipts, reviews)['totals']['correct_abstentions'] == 1


def test_runner_does_not_send_gold_labels_to_model():
    from scripts.retrieval.evaluate_answers import run_case
    suite, receipts, _ = fixture()
    calls = []
    def generate(question, passages):
        calls.append((question, passages))
        return receipts['one']['generation']
    result = run_case(suite['cases'][0], lambda q: receipts['one']['passages'], generate)
    assert calls == [('question', receipts['one']['passages'])]
    assert 'reference_passage_ids' not in result
    assert 'aspects' not in result


def test_generation_failure_preserves_retrieval_without_earning_answer_credit():
    from scripts.retrieval.evaluate_answers import reuse_passages, run_case
    suite, receipts, reviews = fixture()
    passages = receipts['one']['passages']

    def unavailable(question, received):
        assert received == passages
        raise TimeoutError('Test timeout')

    receipt = run_case(suite['cases'][0], lambda _: passages, unavailable)
    assert receipt['passages'] == passages
    assert receipt['total_seconds'] >= receipt['retrieval_seconds']
    receipt['suite_sha256'] = digest(suite)
    reviews['one']['receipt_sha256'] = digest(receipt)
    result = score(suite, {'one': receipt}, reviews)
    assert result['totals']['reference_hits'] == result['totals']['errors'] == 1
    assert result['totals']['supported_answers'] == result['totals']['correct_abstentions'] == 0
    assert result['cases'][0]['error_stage'] == 'generation'
    assert reuse_passages(receipt, suite['cases'][0], digest(suite)) == passages


@pytest.mark.parametrize('change', [dict(error='TimeoutError'), dict(passages=None), dict(case_id='other'),
                                    dict(question='different'), dict(suite_sha256='wrong')])
def test_retrieval_reuse_rejects_failed_search_or_mismatched_receipt(change):
    from scripts.retrieval.evaluate_answers import reuse_passages
    suite, receipts, _ = fixture()
    with pytest.raises(ValueError, match='Invalid retrieval reuse'):
        reuse_passages(dict(receipts['one'], **change), suite['cases'][0], digest(suite))


def test_receipts_are_immutable_and_hash_checked(tmp_path):
    from scripts.retrieval.evaluate_answers import save, checked_read
    path = tmp_path/'receipt.json'
    save(path, {'value': 1})
    assert checked_read(path) == {'value': 1}
    with pytest.raises(ValueError, match='Existing artifact differs'):
        save(path, {'value': 2})
    path.write_text(path.read_text().replace('"value":1', '"value":2'))
    with pytest.raises(ValueError, match='hash'):
        checked_read(path)


def test_saved_rankings_preserve_generation_failure_and_search_denominator():
    from src.retrieval.evaluation import score_saved_rankings
    suite = dict(split='development', cases=[
        dict(id='ranked', question='First', expected_status='excerpts', reference_passage_ids=['a', 'b']),
        dict(id='failed', question='Second', expected_status='excerpts', reference_passage_ids=['c']),
        dict(id='boundary', question='Third', expected_status='insufficient_evidence', reference_passage_ids=[]),
    ])
    receipts = {case['id']: dict(case_id=case['id'], question=case['question'], suite_sha256=digest(suite))
                for case in suite['cases']}
    receipts['ranked'].update(error='TimeoutError', error_stage='generation', passages=[
        dict(record=dict(passage=dict(passage_id=pid))) for pid in ('x', 'a', 'b')])
    receipts['failed']['error'] = 'TimeoutError'
    result = score_saved_rankings(suite, receipts)
    assert result['answerable_cases'] == 2 and result['other_cases'] == result['search_errors'] == 1
    assert result['recall_at'] == {1: 0, 3: .5, 5: .5}
    assert result['mrr_at_5'] == .25
    receipts['ranked']['question'] = 'Wrong'
    with pytest.raises(ValueError, match='identity'):
        score_saved_rankings(suite, receipts)
