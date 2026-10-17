"""Score hash-bound human/agent judgments without using a model as its own judge."""
from .direct_ingestion import digest
from .grounded_answer import validate_answer


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
        if 'error' in receipt:
            totals['errors'] += 1
            rows.append(dict(id=case['id'], error=receipt['error']))
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
        retrieved = {p['record']['passage']['passage_id'] for p in receipt['passages']}
        hit = supported and bool(retrieved & set(case['reference_passage_ids']))
        valid = exact and receipt['generation']['validation'] != 'generation_rejected'
        nonempty = valid and answer['status'] == 'excerpts'
        clean = supported and nonempty and all(covered) and all(r == 'relevant' for r in relevance)
        abstained = not supported and valid and answer['status'] == 'insufficient_evidence'
        totals['reference_hits'] += int(hit)
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
    parser.add_argument('--review', type=Path, required=True)
    args = parser.parse_args()
    manifest = checked_read(args.run/'manifest.json')
    review = json.loads(args.review.read_text())
    suite = manifest['suite']
    if review['manifest_sha256'] != digest(manifest) or review['suite_sha256'] != digest(suite):
        raise ValueError('Review belongs to another run/suite')
    receipts = {c['id']: checked_read(args.run/(c['id']+'.json')) for c in suite['cases']}
    result = score(suite, receipts, review['reviews'])
    if result != review['score']:
        raise ValueError('Recorded score differs from recomputed result')
    print(json.dumps(result, indent=2))
