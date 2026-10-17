"""Track explicit human review of exposed drafts; never authorize tuning or read held-out data.

Recorded statements are attestations, not authenticated proof of human review.
Corpus/span validation remains the responsibility of development_set.
"""
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from .development_set import development_path, verify_hash
from .direct_ingestion import digest
from .records import CONTRACTS, sha256_hex

STAGES = ('wording_and_answer', 'evidence_labels', 'second_consistency')


def verify_development(suite):
    versions = {'prowl-development-draft-v1': 'development-draft-v1.schema.json',
                'prowl-development-draft-v2': 'development-draft-v2.schema.json'}
    version = suite.get('schema_version') if isinstance(suite, dict) else None
    if not isinstance(version, str) or version not in versions:
        raise ValueError('Expected exposed development draft')
    try:
        Draft202012Validator(json.loads((CONTRACTS / versions[version]).read_text())).validate(suite)
    except ValidationError:
        raise ValueError('Development draft schema violation') from None
    verify_hash(suite)
    for case in suite['cases']:
        verify_hash(case)
    if len({c['id'] for c in suite['cases']}) != len(suite['cases']):
        raise ValueError('Duplicate development case identity')


def new_record(suite, answers_sha256):
    """Create an empty record. No user decisions can be inferred by this function."""
    verify_development(suite)
    record = dict(schema_version='prowl-development-review-v1',
                  development_content_sha256=suite['content_sha256'],
                  answers_sha256=answers_sha256, events=[])
    record['content_sha256'] = digest(record)
    validate_review(record, suite, answers_sha256=answers_sha256)
    return record


def validate_review(record, suite, *, answers_sha256):
    verify_development(suite)
    schema = json.loads((CONTRACTS / 'development-review-v1.schema.json').read_text())
    try:
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)
    except ValidationError:
        raise ValueError('Development review schema violation') from None
    verify_hash(record)
    if (record['development_content_sha256'] != suite['content_sha256']
            or record['answers_sha256'] != answers_sha256):
        raise ValueError('Review content binding mismatch')
    cases = {c['id']: c['content_sha256'] for c in suite['cases']}
    states = {stage: dict.fromkeys(cases, 'pending') for stage in STAGES}
    for sequence, event in enumerate(record['events'], 1):
        if event['sequence'] != sequence:
            raise ValueError('Review events must retain contiguous append order')
        targets = event['targets']
        ids = [t['id'] for t in targets]
        if len(ids) != len(set(ids)) or any(cases.get(t['id']) != t['content_sha256'] for t in targets):
            raise ValueError('Review case binding mismatch')
        stage = event['stage']
        if stage == 'second_consistency':
            if set(ids) != set(cases):
                raise ValueError('Second consistency pass must cover the complete development set')
            if any(v != 'accept' for s in STAGES[:2] for v in states[s].values()):
                raise ValueError('Resolve wording and evidence decisions before second consistency pass')
        else:
            # New decisions reopen set-wide consistency, including corrections after acceptance.
            states['second_consistency'] = dict.fromkeys(cases, 'pending')
        for case_id in ids:
            states[stage][case_id] = event['decision']
    pending = {s: [k for k, v in states[s].items() if v != 'accept'] for s in STAGES}
    return dict(state='review_record_valid',
                development_content_sha256=suite['content_sha256'],
                review_content_sha256=record['content_sha256'],
                event_count=len(record['events']),
                decision_counts={s: dict(Counter(states[s].values())) for s in STAGES},
                pending=pending,
                development_review_attested_complete=not any(pending.values()),
                ready_for_tuning=False,
                limitation='Attestations only; corpus validation, protected authoring and split freeze remain separate.')


def read_public_json(path, root):
    path = development_path(path, root)
    if path.stat().st_size > 2 * 1024**2:
        raise ValueError('Development review input exceeds 2 MiB')
    return json.loads(path.read_text())


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--development', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        suite = read_public_json(args.development, root)
        record = read_public_json(args.review, root)
        answers = root / 'docs/capstone/retrieval/DEVELOPMENT-QUESTIONS-AND-ANSWERS.md'
        report = validate_review(record, suite, answers_sha256=sha256_hex(answers.read_bytes()))
    except (ValueError, OSError):
        # Do not echo rejected input content or private paths in routine CLI failures.
        raise SystemExit('Development review validation failed.') from None
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
