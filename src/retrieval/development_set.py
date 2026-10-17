"""Offline validation of exposed development drafts; never a held-out reader or tuning runner.

Exact provenance and concept coverage are mechanical checks. They cannot establish
entailment, exhaustive relevance, independent authorship or human adjudication.
"""
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError
from .records import CONTRACTS, sha256_hex
from .direct_ingestion import digest
from .corpus_inventory import frozen_inventory, verify_sources
from .labels import contains, gold_passages, gold_works, verify_label_set
from .query import make_query, normalize_question

FAMILIES = {'1': 'appearance', '2': 'measurement', '3': 'anatomy',
            '4': 'ai_limits', '5': 'review'}
NEEDS = {f'N{f}.{n}' for f, count in [(1, 5), (2, 4), (3, 4), (4, 6), (5, 6)]
         for n in range(1, count + 1)}
REFUSALS = {'RF1_diagnosis', 'RF2_case_malignancy_stage_subtype', 'RF3_treatment',
            'RF4_prognosis', 'RF6_hidden_patient_material', 'RF7_injection',
            'RF8_protected_system_information', 'RF9_contour_certification'}


def verify_hash(record):
    if record['content_sha256'] != digest({k: v for k, v in record.items() if k != 'content_sha256'}):
        raise ValueError('Draft content hash mismatch')


def validate_draft(suite, manifest, bundles, batches, *, manifest_sha256, regression_sha256):
    schema = json.loads((CONTRACTS / 'development-draft-v1.schema.json').read_text())
    try:
        Draft202012Validator(schema).validate(suite)
    except ValidationError:
        # Do not echo rejected fields or question text in routine error output.
        raise ValueError('Draft schema violation') from None
    verify_hash(suite)
    if (suite['corpus_manifest_sha256'] != manifest_sha256
            or suite['baseline_regression_sha256'] != regression_sha256
            or suite['corpus_content_sha256'] != manifest['inventory']['content_sha256']):
        raise ValueError('Draft corpus/regression binding mismatch')
    if frozen_inventory(batches) != manifest['inventory']:
        raise ValueError('Frozen corpus inventory mismatch')
    verify_sources(batches, bundles)
    reps = [b['representation'] for b in bundles]
    works = {b['work']['work_id'] for b in bundles}
    passages = [i['record']['passage'] for b in batches for i in b['items']]
    ids, wording = set(), set()
    reports, answerable_families = [], set()
    for case in suite['cases']:
        verify_hash(case)
        normalized = normalize_question(case['question']).casefold()
        if case['id'] in ids or normalized in wording:
            raise ValueError('Duplicate question ID or normalized wording')
        ids.add(case['id']); wording.add(normalized)
        if case['primary_need'] not in NEEDS or FAMILIES[case['primary_need'][1]] != case['family']:
            raise ValueError('Need/family mismatch')
        # Validate coarse input separately; do not use this keyword gate as the answer key.
        query = make_query(case['finding'], case['question'])
        label = verify_label_set(case['labels'], reps)
        if label['question_id'] != case['id']:
            raise ValueError('Label question identity mismatch')
        concepts = [c['id'] for c in case['concepts']]
        if len(set(concepts)) != len(concepts) or concepts != label['required_concepts']:
            raise ValueError('Concept identity mismatch')
        if any(s['grade'] == 'uncertain' for s in label['spans']):
            raise ValueError('Resolve uncertain spans before presenting a review-ready draft')
        expected = case['expected']
        if (expected['status'] == 'answered') != label['answerable']:
            raise ValueError('Expected status/answerability mismatch')
        reason = expected['reason']
        if ((expected['status'] == 'answered' and reason != 'supported')
                or (expected['status'] == 'insufficient_evidence' and reason != 'missing_evidence')
                or (expected['status'] == 'refused' and reason not in REFUSALS)):
            raise ValueError('Expected reason/status mismatch')
        direct = [s for s in label['spans'] if s['grade'] == 'direct']
        if any(not s['concept_ids'] for s in direct):
            raise ValueError('Direct span must identify a required concept')
        if {c for s in direct for c in s['concept_ids']} != set(concepts):
            raise ValueError('Every concept needs direct source support')
        # No silent trimming/relabeling when a frozen chunk cannot contain the gold span.
        if any(not any(contains(p, s) for p in passages) for s in direct):
            raise ValueError('Direct span not completely contained in any frozen passage')
        judgments = case['source_judgments']
        if len({j['work_id'] for j in judgments}) != len(judgments):
            raise ValueError('Duplicate source judgment')
        if any(j['work_id'] not in works for j in judgments):
            raise ValueError('Foreign source judgment')
        gold = gold_works(label, reps)
        if {j['work_id'] for j in judgments if j['grade'] == 'direct'} != gold:
            raise ValueError('Direct source judgments differ from span labels')
        if label['answerable']:
            answerable_families.add(case['family'])
            if {j['work_id'] for j in judgments} != works:
                raise ValueError('Answerable draft requires a judgment for every retained source')
        elif judgments:
            raise ValueError('Unsupported/refused question must not carry positive source judgments')
        reports.append(dict(id=case['id'],direct_spans=len(direct),gold_works=sorted(gold),
            gold_passages=sorted(gold_passages(passages, label)),
            keyword_gate_state=query['state'],keyword_gate_reasons=query['refusal_codes'],
            expected_status=expected['status']))
    counts = Counter(c['expected']['status'] for c in suite['cases'])
    if counts['answered'] != 20 or counts['refused'] + counts['insufficient_evidence'] != 10:
        raise ValueError('Require 20 answerable and 10 unsupported/out-of-scope cases')
    if answerable_families != set(FAMILIES.values()):
        raise ValueError('Answerable questions must cover all five families')
    ceilings = [min(5, len(r['gold_works'])) / len(r['gold_works']) for r in reports if r['gold_works']]
    return dict(state='draft_mechanically_valid',content_sha256=suite['content_sha256'],
        counts=dict(counts),families=dict(Counter(c['family'] for c in suite['cases'])),
        source_recall_at_5_ceiling=sum(ceilings)/len(ceilings),
        second_pass_pending=[c['id'] for c in suite['cases'] if c['review']['agent_second_pass'] != 'complete'],
        human_review_pending=[c['id'] for c in suite['cases']],
        ready_for_tuning=False,blockers=['Quinton semantic adjudication and second consistency pass',
            'Independent protected held-out authoring, cross-split duplicate review and freeze/backup receipts'],
        cases=reports)


def checked_json(pin, root):
    path = (root / pin['path']).resolve()
    if not path.is_relative_to(root.resolve()) or path.stat().st_size > 32 * 1024**2:
        raise ValueError('Expected bounded repository-local canonical input')
    raw = path.read_bytes()
    if sha256_hex(raw) != pin['sha256']:
        raise ValueError('Canonical input hash mismatch')
    return json.loads(raw)


def development_path(path, root):
    """Refuse external/protected locations before opening question content."""
    path = Path(path).resolve()
    allowed = (root / 'configs/evidence/evaluation').resolve()
    if not path.is_relative_to(allowed) or not path.name.startswith('development-'):
        raise ValueError('Only repository development-* evaluation files are accepted')
    return path


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--development', type=Path, required=True)
    parser.add_argument('--require-ready', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    development = development_path(args.development, root)
    path = root / 'configs/evidence/corpus-coverage-v1.json'
    manifest = json.loads(path.read_text())
    if len(manifest['sources']) > 32 or len(manifest['batches']) > 256:
        raise ValueError('Corpus input count exceeds draft bound')
    if development.stat().st_size > 2 * 1024**2:
        raise ValueError('Development draft exceeds 2 MiB')
    suite = json.loads(development.read_text())
    result = validate_draft(suite, manifest,
        [checked_json(s['bundle'], root) for s in manifest['sources']],
        [checked_json(b, root) for b in manifest['batches']],
        manifest_sha256=sha256_hex(path.read_bytes()),
        regression_sha256=sha256_hex((root/'configs/evidence/evaluation/development-v1.json').read_bytes()))
    print(json.dumps(result, indent=2))
    if args.require_ready:
        # This v1 reader accepts development DRAFTS only. No self-attested promotion switch.
        raise SystemExit('Draft is not released for tuning; complete the documented human/protected gates.')


if __name__ == '__main__':
    main()
