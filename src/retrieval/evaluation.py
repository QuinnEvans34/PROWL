"""Score hash-bound human/agent judgments without using a model as its own judge."""
from .direct_ingestion import digest
from .grounded_answer import validate_answer
from .metrics import mean_or_none, recall_at_k, reciprocal_rank


def score_saved_rankings(suite, receipts):
    """Score the ordered top-five passage lists saved by the development runner."""
    cases = suite['cases']
    ids = {case['id'] for case in cases}
    if suite.get('split') != 'development' or len(ids) != len(cases) or receipts.keys() != ids:
        raise ValueError('A complete development suite with unique case IDs is required')
    suite_sha = digest(suite)
    cutoffs = (1, 3, 5)
    rows = []
    search_errors = 0
    for case in cases:
        receipt = receipts[case['id']]
        if (receipt['suite_sha256'] != suite_sha or receipt['case_id'] != case['id']
                or receipt['question'] != case['question']):
            raise ValueError('Ranking receipt identity mismatch')
        search_failed = 'error' in receipt and receipt.get('error_stage') != 'generation'
        search_errors += int(search_failed)
        if case['expected_status'] != 'excerpts':
            continue
        ranked = [] if search_failed else [p['record']['passage']['passage_id'] for p in receipt['passages']]
        if len(ranked) > cutoffs[-1]:
            raise ValueError('Saved ranking exceeds the development runner depth')
        gold = case['reference_passage_ids']
        rows.append(dict(id=case['id'], search_failed=search_failed,
                         recall_at={k: recall_at_k(ranked, gold, k) for k in cutoffs},
                         reciprocal_rank=reciprocal_rank(ranked, gold)))
    return dict(scope='saved_development_passage_rankings', max_depth=cutoffs[-1],
                answerable_cases=len(rows), other_cases=len(cases)-len(rows), search_errors=search_errors,
                recall_at={k: mean_or_none(row['recall_at'][k] for row in rows) for k in cutoffs},
                mrr_at_5=mean_or_none(row['reciprocal_rank'] for row in rows), cases=rows)


def score(suite, receipts, reviews):
    expected_ids = {c['id'] for c in suite['cases']}
    if set(receipts) != expected_ids or set(reviews) != expected_ids:
        raise ValueError('Exactly one receipt and review required per case')
    totals = dict(supported_cases=0, missing_cases=0, reference_hits=0, supported_answers=0,
                  clean_supported_answers=0, correct_abstentions=0, errors=0,
                  extracts=0, exact_extracts=0, relevant_extracts=0, covered_aspects=0, aspects=0)
    rows = []
    for case in suite['cases']:
        receipt, review = receipts[case['id']], reviews[case['id']]
        if (receipt['suite_sha256'] != digest(suite) or receipt['question'] != case['question']
                or receipt['case_id'] != case['id'] or review['receipt_sha256'] != digest(receipt)):
            raise ValueError('Judgment/receipt identity mismatch')
        supported = case['expected_status'] == 'excerpts'
        totals['supported_cases' if supported else 'missing_cases'] += 1
        totals['aspects'] += len(case['aspects'])
        # A failed answer does not erase a successful retrieval.
        retrieved = {p['record']['passage']['passage_id'] for p in receipt.get('passages', [])}
        hit = supported and bool(retrieved & set(case['reference_passage_ids']))
        totals['reference_hits'] += int(hit)
        if 'error' in receipt:
            totals['errors'] += 1
            row = dict(id=case['id'], error=receipt['error'])
            if receipt.get('error_stage') == 'generation':
                row.update(error_stage='generation', reference_hit=hit, total_seconds=receipt['total_seconds'])
            rows.append(row)
            continue
        answer = receipt['generation']['answer']
        relevance, covered = review['extract_relevance'], review['aspects_covered']
        if (len(relevance) != len(answer['extracts']) or len(covered) != len(case['aspects'])
                or any(r not in ('relevant', 'mixed', 'irrelevant') for r in relevance)
                or any(type(c) is not bool for c in covered) or not review['rationale']):
            raise ValueError('Incomplete or invalid judgment')
        if answer['status'] != 'excerpts' and any(covered):
            raise ValueError('Abstention cannot cover answer aspects')
        exact = True
        try:
            validate_answer(answer, receipt['passages'])
        except ValueError:
            exact = False
        valid = exact and receipt['generation']['validation'] != 'generation_rejected'
        nonempty = valid and answer['status'] == 'excerpts'
        clean = supported and nonempty and all(covered) and all(r == 'relevant' for r in relevance)
        abstained = not supported and valid and answer['status'] == 'insufficient_evidence'
        totals['supported_answers'] += int(supported and nonempty)
        totals['clean_supported_answers'] += int(clean)
        totals['correct_abstentions'] += int(abstained)
        totals['extracts'] += len(relevance)
        totals['exact_extracts'] += len(relevance) if exact else 0
        totals['relevant_extracts'] += relevance.count('relevant')
        totals['covered_aspects'] += sum(covered) if valid else 0
        rows.append(dict(id=case['id'], reference_hit=hit, status=answer['status'],
                         validation=receipt['generation']['validation'], relevance=relevance,
                         covered=sum(covered), aspects=len(covered), clean=bool(clean),
                         total_seconds=receipt['total_seconds']))
    return dict(totals=totals, cases=rows)


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    from scripts.retrieval.evaluate_answers import checked_read
    parser = argparse.ArgumentParser(description='Recompute a development score from immutable receipts and recorded judgments')
    parser.add_argument('--run', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--review', type=Path)
    mode.add_argument('--rankings-only', action='store_true', help='Score saved passage ranks on a development suite')
    args = parser.parse_args()
    manifest = checked_read(args.run/'manifest.json')
    suite = manifest['suite']
    if args.rankings_only:
        if suite.get('split') != 'development':
            raise ValueError('Saved-ranking review requires a development suite')
        receipts = {c['id']: checked_read(args.run/(c['id']+'.json')) for c in suite['cases']}
        print(json.dumps(score_saved_rankings(suite, receipts), indent=2))
        raise SystemExit(0)
    review = json.loads(args.review.read_text())
    if review['manifest_sha256'] != digest(manifest) or review['suite_sha256'] != digest(suite):
        raise ValueError('Review belongs to another run/suite')
    receipts = {c['id']: checked_read(args.run/(c['id']+'.json')) for c in suite['cases']}
    result = score(suite, receipts, review['reviews'])
    if result != review['score']:
        raise ValueError('Recorded score differs from recomputed result')
    print(json.dumps(result, indent=2))
