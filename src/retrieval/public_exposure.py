"""Consolidate named public exposure records without reading private questions.

Historical supplements retain their extracted wordings even when their producing UI/test
files have changed. Verify the supplement itself, not an obsolete producer against today's
checkout. Exact matching is conservative and cannot establish semantic independence.
"""
import json
from copy import deepcopy
from pathlib import Path

from .direct_ingestion import digest
from .query import normalize_question
from .records import sha256_hex

DIRECTORY = 'configs/evidence/evaluation/'
INPUT_NAMES = (
    'public-exposure-v1.json',
    'public-exposure-scan-supplement-v1.json',
    'public-exposure-live-search-v1.json',
    'public-exposure-natural-answers-v1.json',
    'public-exposure-natural-answers-v2.json',
    'public-exposure-answer-quality-v1.json',
)
LEGACY_DEVELOPMENT = {
    DIRECTORY + name for name in (
        'development-v1.json', 'development-v2-draft.json', 'development-v3-draft.json',
        'development-v4-draft.json', 'development-v5-draft.json')
}
DEMO = 'docs/capstone/retrieval/PLAIN-LANGUAGE-DEMO-PLAN.md'
LIMIT = 2 * 1024**2


def public_bytes(root, relative, expected_sha256=None):
    """Bounded ordinary repository file; reject path escapes and symlink aliases."""
    root = Path(root).resolve()
    path = root / relative
    if (Path(relative).is_absolute() or '..' in Path(relative).parts
            or path.resolve() != path.absolute() or not path.is_file()
            or not path.resolve().is_relative_to(root) or path.stat().st_size > LIMIT):
        raise ValueError('Expected bounded ordinary public repository file')
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT or (expected_sha256 is not None and sha256_hex(raw) != expected_sha256):
        raise ValueError('Public exposure input changed or exceeded bound')
    return raw


def _checked(root, pin):
    return json.loads(public_bytes(root, pin['path'], pin['sha256']))


def consolidate(root, inputs):
    """Derive complete wording/origin rows from the six explicitly named inventories."""
    expected = [DIRECTORY + name for name in INPUT_NAMES]
    if not isinstance(inputs, list) or [p['path'] for p in inputs] != expected:
        raise ValueError('All named public exposure inventories are required in order')
    rows = {}
    intents = set()
    records = 0

    def add(wording, origin, intent=None):
        nonlocal records
        normalized = normalize_question(wording).casefold()
        row = rows.setdefault(normalized, dict(normalized_wording=normalized, variants=[], origins=[]))
        if wording not in row['variants']:
            row['variants'].append(wording)
        row['origins'].append(origin)
        if intent:
            intents.add(intent)
        records += 1

    for pin in inputs:
        data = _checked(root, pin)
        if pin['path'] == expected[0]:
            files = data['files']
            if (len(files) != 6 or len({p['path'] for p in files}) != 6
                    or {p['path'] for p in files} != LEGACY_DEVELOPMENT | {DEMO}):
                raise ValueError('Legacy exposure membership mismatch')
            for item in files:
                raw = public_bytes(root, item['path'], item['sha256'])
                if item['path'] in LEGACY_DEVELOPMENT and item['kind'] == 'development':
                    cases = json.loads(raw)['cases']
                    if len(cases) > 60:
                        raise ValueError('Public development case bound exceeded')
                    for case in cases:
                        add(case['question'], dict(inventory=pin['path'], file=item['path'],
                            case_id=case['id']), case.get('intent_group'))
                elif item['path'] == DEMO and item['kind'] == 'demo_markdown':
                    table = {line.split('|')[1].strip() for line in raw.decode().splitlines()
                             if line.startswith('| ')}
                    if not set(data['demo_questions']).issubset(table):
                        raise ValueError('Demo exposure mismatch')
                    for index, wording in enumerate(data['demo_questions']):
                        add(wording, dict(inventory=pin['path'], file=item['path'], index=index))
                else:
                    raise ValueError('Unknown legacy exposure kind')
        else:
            wordings = data['wordings']
            if not isinstance(wordings, list) or len(wordings) > 256:
                raise ValueError('Supplement wording bound exceeded')
            for index, wording in enumerate(wordings):
                add(wording, dict(inventory=pin['path'], index=index))
    return dict(rows=[rows[k] for k in sorted(rows)], intent_groups=sorted(intents),
                record_count=records, distinct_wording_count=len(rows))


def load_public_exposure(root):
    """Validate both source pins and the materialized union; never load private paths."""
    data = json.loads(public_bytes(root, DIRECTORY + 'public-exposure-v2.json'))
    if (data['version'] != 'prowl-public-exposure-v2'
            or data['normalization'] != 'prowl-qnorm-v1+casefold'
            or data['content_sha256'] != digest({k: v for k, v in data.items() if k != 'content_sha256'})
            or data['inventory'] != consolidate(root, data['inputs'])):
        raise ValueError('Consolidated public exposure mismatch')
    return data


def public_preflight(root):
    """Current public reconciliation status. This version cannot admit private authoring."""
    exposure = load_public_exposure(root)
    state = json.loads(public_bytes(root, DIRECTORY + 'evaluation-reconciliation-v1.json'))
    if (state['version'] != 'prowl-evaluation-reconciliation-v1'
            or state['state'] != 'pending_expanded_scope_review'
            or state['ready_for_private_authoring'] is not False
            or state['ready_for_tuning'] is not False
            or state['final_development'] is not None
            or state['content_sha256'] != digest({k: v for k, v in state.items() if k != 'content_sha256'})):
        raise ValueError('A separately implemented and reviewed freeze is required')
    if state['exposure']['path'] != DIRECTORY + 'public-exposure-v2.json':
        raise ValueError('Current exposure binding mismatch')
    _checked(root, state['exposure'])
    if state['corpus']['path'] != 'configs/evidence/corpus-disease-v1.json':
        raise ValueError('Current corpus binding mismatch')
    corpus = _checked(root, state['corpus'])
    if state['prior_development']['path'] != DIRECTORY + 'development-v5-draft.json':
        raise ValueError('Prior development binding mismatch')
    prior = _checked(root, state['prior_development'])
    if state['disease_candidates']['path'] != DIRECTORY + 'development-disease-candidates-v2.json':
        raise ValueError('Disease candidate binding mismatch')
    candidates = _checked(root, state['disease_candidates'])
    return dict(state=state['state'], ready_for_private_authoring=False, ready_for_tuning=False,
                corpus_sources=corpus['inventory']['source_count'],
                corpus_passages=corpus['inventory']['passage_count'],
                prior_development_cases=len(prior['cases']), disease_candidates=len(candidates['cases']),
                exposed_records=exposure['inventory']['record_count'],
                distinct_exposed_wordings=exposure['inventory']['distinct_wording_count'],
                known_intent_groups=len(exposure['inventory']['intent_groups']),
                exposure_content_sha256=exposure['content_sha256'],
                pending=state['pending'], private_content_read=False)


def extend_with_development(root, parent_pin, development_pin):
    """Preserve v2 origins and add the revised public development wording and intents."""
    if (parent_pin['path'] != DIRECTORY + 'public-exposure-v2.json'
            or development_pin['path'] != DIRECTORY + 'development-v6-draft.json'):
        raise ValueError('Unexpected public exposure revision inputs')
    parent = _checked(root, parent_pin)
    if parent != load_public_exposure(root):
        raise ValueError('Public exposure parent mismatch')
    development = _checked(root, development_pin)
    if (development['schema_version'] != 'prowl-development-draft-v3'
            or development['status'] != 'draft_pending_human_review'
            or len(development['cases']) != 30
            or development['content_sha256'] != digest({k: v for k, v in development.items() if k != 'content_sha256'})):
        raise ValueError('Expected pinned public development draft')
    inventory = deepcopy(parent['inventory'])
    rows = {r['normalized_wording']: r for r in inventory['rows']}
    intents = set(inventory['intent_groups'])
    for case in development['cases']:
        if case['split'] != 'development' or case['authorship']['exposed'] is not True:
            raise ValueError('Only exposed development enters public inventory')
        wording = case['question']
        normalized = normalize_question(wording).casefold()
        row = rows.setdefault(normalized, dict(normalized_wording=normalized, variants=[], origins=[]))
        if wording not in row['variants']:
            row['variants'].append(wording)
        row['origins'].append(dict(inventory=DIRECTORY + 'public-exposure-v3.json',
                                  file=development_pin['path'], case_id=case['id']))
        intents.add(case['intent_group'])
    inventory.update(rows=[rows[k] for k in sorted(rows)], intent_groups=sorted(intents),
                     record_count=inventory['record_count'] + len(development['cases']),
                     distinct_wording_count=len(rows))
    return inventory


def load_current_exposure(root):
    data = json.loads(public_bytes(root, DIRECTORY + 'public-exposure-v3.json'))
    if (data['version'] != 'prowl-public-exposure-v3'
            or data['content_sha256'] != digest({k: v for k, v in data.items() if k != 'content_sha256'})
            or data['inventory'] != extend_with_development(root, data['parent'], data['development'])):
        raise ValueError('Current public exposure mismatch')
    return data


def current_public_preflight(root):
    """Reviewed engineering proposal is still not a human/protected evaluation freeze."""
    exposure = load_current_exposure(root)
    state = json.loads(public_bytes(root, DIRECTORY + 'evaluation-reconciliation-v2.json'))
    if (state['version'] != 'prowl-evaluation-reconciliation-v2'
            or state['state'] != 'engineering_review_complete_human_review_pending'
            or state['ready_for_private_authoring'] is not False
            or state['ready_for_tuning'] is not False or state['final_development'] is not None
            or state['content_sha256'] != digest({k: v for k, v in state.items() if k != 'content_sha256'})):
        raise ValueError('Human/protected evaluation admission remains unimplemented')
    if (state['exposure']['path'] != DIRECTORY + 'public-exposure-v3.json'
            or state['proposed_development']['path'] != DIRECTORY + 'development-v6-draft.json'
            or state['corpus']['path'] != 'configs/evidence/corpus-disease-v1.json'):
        raise ValueError('Current public proposal binding mismatch')
    if _checked(root, state['exposure']) != exposure:
        raise ValueError('Current exposure binding mismatch')
    corpus = _checked(root, state['corpus'])
    proposed = _checked(root, state['proposed_development'])
    if (state['proposed_development'] != exposure['development']
            or proposed['corpus_manifest_sha256'] != state['corpus']['sha256']
            or proposed['corpus_content_sha256'] != corpus['inventory']['content_sha256']):
        raise ValueError('Proposed development corpus/exposure mismatch')
    return dict(state=state['state'], ready_for_private_authoring=False, ready_for_tuning=False,
                corpus_sources=corpus['inventory']['source_count'],
                corpus_passages=corpus['inventory']['passage_count'],
                proposed_development_cases=len(proposed['cases']),
                exposed_records=exposure['inventory']['record_count'],
                distinct_exposed_wordings=exposure['inventory']['distinct_wording_count'],
                known_intent_groups=len(exposure['inventory']['intent_groups']),
                exposure_content_sha256=exposure['content_sha256'],
                pending=state['pending'], private_content_read=False)


def latest_public_preflight(root):
    """Include post-v3 exposed matrices; still cannot admit any private authoring."""
    from .evaluation_delta import extend_exposure
    report = current_public_preflight(root)
    parent = load_current_exposure(root)
    path = DIRECTORY + 'public-exposure-v4-preparation.json'
    data = json.loads(public_bytes(root, path))
    expected = ('configs/evidence/record-search-screen-v1.json',
                'configs/evidence/week3-quality-matrix-v1.json')
    if (data['version'] != 'prowl-public-exposure-v4-preparation'
            or data['status'] != 'preparation_not_private_admission'
            or data['parent']['path'] != DIRECTORY + 'public-exposure-v3.json'
            or _checked(root, data['parent']) != parent
            or tuple(p['path'] for p in data['sources']) != expected
            or data['content_sha256'] != digest({k:v for k,v in data.items() if k != 'content_sha256'})):
        raise ValueError('Post-v3 exposure preparation mismatch')
    for source in data['sources']:
        raw = _checked(root, source)
        if raw.get('scope', raw.get('exposure')) not in (
                'exposed_engineering_screen_not_independent_evaluation', 'development_only_not_independent'):
            raise ValueError('Unexpected public matrix scope')
        if source['cases'] != [dict(id=c['id'], question=c['question']) for c in raw['cases']]:
            raise ValueError('Exposed matrix wording was omitted or changed')
    inventory = extend_exposure(parent['inventory'], data['sources'])
    if inventory != data['inventory']:
        raise ValueError('Post-v3 exposure union mismatch')
    report.update(exposed_records=inventory['record_count'],
        distinct_exposed_wordings=inventory['distinct_wording_count'],
        exposure_content_sha256=data['content_sha256'], exposure_version=data['version'],
        exposure_limitations=data['limitations'])
    return report


def accepted_public_preflight(root):
    """Recognize the real delta acceptance without opening private admission."""
    from .development_review import validate_prepared_delta_review
    report = latest_public_preflight(root)
    receipt = json.loads(public_bytes(root, DIRECTORY+'development-v6-delta-acceptance-v1.json'))
    required = {'suite': DIRECTORY+'development-v6-draft.json',
        'review': DIRECTORY+'development-v6-delta-human-review.json',
        'packet': DIRECTORY+'review-packets/development-v6-changes-to-review.md',
        'appendix': DIRECTORY+'review-packets/development-v6-source-judgment-changes.md'}
    if (receipt['version'] != 'development-v6-delta-acceptance-v1'
            or receipt['ready_for_private_authoring'] is not False or receipt['ready_for_tuning'] is not False
            or any(receipt[k]['path'] != v for k,v in required.items())):
        raise ValueError('Unexpected public acceptance binding')
    for key in required:
        public_bytes(root, receipt[key]['path'], receipt[key]['sha256'])
    read = lambda path: json.loads(public_bytes(root, path))
    review = validate_prepared_delta_review(read(required['review']), read(required['suite']),
        packet_sha256=receipt['packet']['sha256'],
        prior_suite=read(DIRECTORY+'development-v5-draft.json'),
        prior_record=read(DIRECTORY+'development-v5-human-review.json'),
        prior_answers=public_bytes(root, 'docs/capstone/retrieval/DEVELOPMENT-QUESTIONS-AND-ANSWERS-V5.md').decode(),
        earlier_suite=read(DIRECTORY+'development-v4-draft.json'),
        earlier_record=read(DIRECTORY+'development-v4-human-review.json'),
        earlier_answers=public_bytes(root, 'docs/capstone/retrieval/DEVELOPMENT-QUESTIONS-AND-ANSWERS.md').decode())
    if receipt['report'] != review or not review['development_review_attested_complete']:
        raise ValueError('Accepted delta review does not verify')
    report.update(state='public_delta_accepted_private_preparation_pending',
        development_review_attested_complete=True, review_content_sha256=review['review_content_sha256'],
        pending=['Qualify the selected separate human-operated labeling assistant and revised role schema.',
                 'Resolve broader formal answer coverage without narrowing accepted evaluation to demo topics.',
                 'Complete private authoring, semantic independence, storage/backup and frozen admission.'])
    return report


V5_SOURCES = tuple(DIRECTORY + name for name in (
    'measurement-method-development-v1.json', 'rag-interpretation-development-v1.json',
    'rag-contour-development-v1.json', 'rag-study-coverage-development-v1.json',
    'public-exposure-measurement-method-v1.json', 'public-exposure-rag-quality-v1.json',
    'public-exposure-code-20261022.json'))


def load_prepared_exposure(root):
    """Verify v5 without opening protected content or changing historical v4 receipts."""
    from .evaluation_delta import extend_exposure
    latest_public_preflight(root)
    data = json.loads(public_bytes(root, DIRECTORY+'public-exposure-v5.json'))
    if (data['version'] != 'prowl-public-exposure-v5'
            or data['status'] != 'public_preparation_private_admission_pending'
            or data['parent']['path'] != DIRECTORY+'public-exposure-v4-preparation.json'
            or tuple(s['path'] for s in data['sources']) != V5_SOURCES
            or data['content_sha256'] != digest({k:v for k,v in data.items() if k!='content_sha256'})):
        raise ValueError('Current exposure preparation binding mismatch')
    parent = _checked(root, data['parent'])
    for index, source in enumerate(data['sources']):
        raw = _checked(root, source)
        if index in (4, 5):
            cases = [dict(id=f'wording-{i+1}', question=q) for i,q in enumerate(raw['wordings'])]
        else:
            cases = [dict(id=c['id'], question=c['question'])
                     for c in raw['questions' if index==0 else 'cases']]
        if source['exposure'] != 'development_only' or source['cases'] != cases:
            raise ValueError('Current exposed wording was omitted or changed')
        # Code producer pins describe the frozen extraction, not today's potentially
        # edited tests. The pinned inventory preserves those historical literal bytes.
    if data['inventory'] != extend_exposure(parent['inventory'], data['sources']):
        raise ValueError('Current public exposure union mismatch')
    return data


def prepared_public_preflight(root):
    """Current public preparation, including accepted development and v5 exclusions."""
    report = accepted_public_preflight(root)
    data = load_prepared_exposure(root)
    inventory = data['inventory']
    report.update(exposed_records=inventory['record_count'],
        distinct_exposed_wordings=inventory['distinct_wording_count'],
        exposure_content_sha256=data['content_sha256'], exposure_version=data['version'],
        known_intent_groups=len(inventory['intent_groups']), exposure_limitations=data['limitations'],
        ready_for_evaluation=False,
        pending=['Prepare the separately reviewed AI-authored set using exact frozen-source evidence.',
                 'Bind private review, storage/backup and single-run admission before evaluation.'])
    return report
