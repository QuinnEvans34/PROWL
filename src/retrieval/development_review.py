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
                'prowl-development-draft-v2': 'development-draft-v2.schema.json',
                'prowl-development-draft-v3': 'development-draft-v3.schema.json'}
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
    version = 'v2' if suite['schema_version'] == 'prowl-development-draft-v3' else 'v1'
    record = dict(schema_version=f'prowl-development-review-{version}',
                  development_content_sha256=suite['content_sha256'],
                  answers_sha256=answers_sha256, events=[])
    record['content_sha256'] = digest(record)
    validate_review(record, suite, answers_sha256=answers_sha256)
    return record


def validate_review(record, suite, *, answers_sha256):
    return _validate_review(record, suite, answers_sha256=answers_sha256)


def _validate_review(record, suite, *, answers_sha256, inherited=None):
    verify_development(suite)
    version = 'v2' if suite['schema_version'] == 'prowl-development-draft-v3' else 'v1'
    schema = json.loads((CONTRACTS / f'development-review-{version}.schema.json').read_text())
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
    if inherited is not None:
        for stage in STAGES[:2]:
            for case_id in inherited[stage]:
                states[stage][case_id] = 'accept'
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


def answer_blocks(text, suite):
    """Compare actual answer prose, independently of changed introductions/source links."""
    import re
    sections = re.findall(r'^### (\d+)\. (.*?)\n(.*?)(?=^### |^## |\Z)', text, re.M | re.S)
    if ([int(n) for n, _, _ in sections] != list(range(1, len(suite['cases']) + 1))
            or [q for _, q, _ in sections] != [c['question'] for c in suite['cases']]):
        raise ValueError('Readable answer question/order mismatch')
    result = {}
    for (_, _, body), case in zip(sections, suite['cases']):
        match = re.search(r'\*\*Expected (?:answer|response)\*\*\s*\n(.*?)(?=\n\*\*(?:Source|Sources|Basis):)', body, re.S)
        if match is None:
            raise ValueError('Readable expected answer missing')
        result[case['id']] = match.group(1).strip()
    return result


def validate_delta_review(record, suite, answers, *, prior_suite, prior_record, prior_answers):
    """Carry only proven unchanged accepted parts; never invent review events.

    New corpus judgments reopen evidence review. Corpus-gap cases always reopen when
    the corpus changes, even if their wording and empty labels are identical.
    Set-wide consistency never carries across versions.
    """
    prior = validate_review(prior_record, prior_suite,
                            answers_sha256=sha256_hex(prior_answers.encode()))
    verify_development(suite)
    before = {c['id']: c for c in prior_suite['cases']}
    old_answers = answer_blocks(prior_answers, prior_suite)
    new_answers = answer_blocks(answers, suite)
    inherited = {s: [] for s in STAGES[:2]}
    core = ('id', 'split', 'primary_need', 'family', 'intent_group', 'question',
            'finding', 'expected', 'concepts')
    corpus_changed = suite['corpus_content_sha256'] != prior_suite['corpus_content_sha256']
    for case in suite['cases']:
        ident = case['id']; old = before.get(ident)
        if old is None:
            continue
        same = (all(case[k] == old[k] for k in core)
                and new_answers[ident] == old_answers[ident])
        if same and ident not in prior['pending']['wording_and_answer']:
            inherited['wording_and_answer'].append(ident)
        if (same and case['labels'] == old['labels']
                and case['source_judgments'] == old['source_judgments']
                and not (corpus_changed and case['expected']['status'] == 'insufficient_evidence')
                and ident not in prior['pending']['evidence_labels']):
            inherited['evidence_labels'].append(ident)
    result = _validate_review(record, suite, answers_sha256=sha256_hex(answers.encode()),
                              inherited=inherited)
    result.update(inherited_acceptances=inherited,
                  prior_development_content_sha256=prior_suite['content_sha256'],
                  prior_review_content_sha256=prior_record['content_sha256'])
    return result


def read_public_json(path, root):
    path = development_path(path, root)
    if path.stat().st_size > 2 * 1024**2:
        raise ValueError('Development review input exceeds 2 MiB')
    return json.loads(path.read_text())


def validate_prepared_delta_review(record, suite, *, packet_sha256, prior_suite,
                                  prior_record, prior_answers, earlier_suite,
                                  earlier_record, earlier_answers):
    """Validate change-only concept review against the actual accepted two-step chain.

    The packet preserves prior prose; unchanged core/labels may inherit, never new
    evidence or consistency. No new events are manufactured by this validator.
    """
    from .evaluation_delta import CORE
    prior = validate_delta_review(prior_record, prior_suite, prior_answers,
        prior_suite=earlier_suite, prior_record=earlier_record, prior_answers=earlier_answers)
    if not prior['development_review_attested_complete']:
        raise ValueError('Prior acceptance chain is incomplete')
    verify_development(suite)
    old = {c['id']: c for c in prior_suite['cases']}
    inherited = {s: [] for s in STAGES[:2]}
    changed_corpus = suite['corpus_content_sha256'] != prior_suite['corpus_content_sha256']
    for case in suite['cases']:
        previous = old.get(case['id'])
        same = previous is not None and all(case[k] == previous[k] for k in CORE)
        if same:
            inherited['wording_and_answer'].append(case['id'])
        # The new label-set version is provenance, not a new semantic judgment.
        label_meaning = lambda labels: {k:v for k,v in labels.items() if k != 'label_version'}
        if (same and label_meaning(case['labels']) == label_meaning(previous['labels'])
                and case['source_judgments'] == previous['source_judgments']
                and not (changed_corpus and case['expected']['status'] == 'insufficient_evidence')):
            inherited['evidence_labels'].append(case['id'])
    result = _validate_review(record, suite, answers_sha256=packet_sha256, inherited=inherited)
    result.update(inherited_acceptances=inherited,
        prior_review_content_sha256=prior_record['content_sha256'],
        prior_development_content_sha256=prior_suite['content_sha256'])
    return result


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
        if suite['schema_version'] == 'prowl-development-draft-v3':
            answers = root / 'outputs/prowl/development-v6-review-20261017/all-questions.md'
        report = validate_review(record, suite, answers_sha256=sha256_hex(answers.read_bytes()))
    except (ValueError, OSError):
        # Do not echo rejected input content or private paths in routine CLI failures.
        raise SystemExit('Development review validation failed.') from None
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
