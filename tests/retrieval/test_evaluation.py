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
