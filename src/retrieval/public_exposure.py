"""Consolidate named public exposure records without reading private questions.

Historical supplements retain their extracted wordings even when their producing UI/test
files have changed. Verify the supplement itself, not an obsolete producer against today's
checkout. Exact matching is conservative and cannot establish semantic independence.
"""
import json
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
