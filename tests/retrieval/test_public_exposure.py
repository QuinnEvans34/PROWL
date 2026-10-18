"""Invented public inventories; no actual protected paths, questions or labels."""
import json

import pytest

from src.retrieval.direct_ingestion import digest
from src.retrieval.records import sha256_hex
from src.retrieval.public_exposure import (
    DIRECTORY, INPUT_NAMES, LEGACY_DEVELOPMENT, DEMO, LIMIT,
    consolidate, load_public_exposure, public_bytes, public_preflight,
)


def write(root, path, value):
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = value.encode() if isinstance(value, str) else json.dumps(value).encode()
    p.write_bytes(raw)
    return dict(path=path, sha256=sha256_hex(raw))


def sealed(value):
    value.pop('content_sha256', None)
    return dict(value, content_sha256=digest(value))


@pytest.fixture
def public_fixture(tmp_path):
    files = []
    for index, path in enumerate(sorted(LEGACY_DEVELOPMENT)):
        p = write(tmp_path, path, dict(cases=[dict(id=f'q:{index}',
            question='Invented reference question?', intent_group='invented-intent')]))
        files.append(dict(p, kind='development'))
    files.append(dict(write(tmp_path, DEMO, '| Invented demo question? | example |'), kind='demo_markdown'))
    inputs = [write(tmp_path, DIRECTORY + INPUT_NAMES[0],
                    dict(files=files, demo_questions=['Invented demo question?']))]
    for index, name in enumerate(INPUT_NAMES[1:]):
        inputs.append(write(tmp_path, DIRECTORY + name, dict(
            wordings=['  INVENTED   reference question?  ', f'Invented supplement {index}?'],
            files=[dict(path='/never/read/a/private/producer', sha256='obsolete')])))
    union = dict(version='prowl-public-exposure-v2', normalization='prowl-qnorm-v1+casefold',
                 inputs=inputs, inventory=consolidate(tmp_path, inputs))
    exposure_pin = write(tmp_path, DIRECTORY + 'public-exposure-v2.json', sealed(union))
    state = dict(version='prowl-evaluation-reconciliation-v1', state='pending_expanded_scope_review',
        ready_for_private_authoring=False, ready_for_tuning=False, final_development=None,
        exposure=exposure_pin,
        corpus=write(tmp_path, 'configs/evidence/corpus-disease-v1.json',
                     dict(inventory=dict(source_count=14, passage_count=1179))),
        prior_development=next(p for p in files if p['path'].endswith('development-v5-draft.json')),
        disease_candidates=write(tmp_path, DIRECTORY + 'development-disease-candidates-v2.json', dict(cases=[{}, {}])),
        pending=['Invented uncompleted review'])
    write(tmp_path, DIRECTORY + 'evaluation-reconciliation-v1.json', sealed(state))
    return tmp_path, union, state


def test_union_retains_every_origin_and_normalizes_exact_matches(public_fixture):
    root, _, _ = public_fixture
    data = load_public_exposure(root)['inventory']
    assert data['record_count'] == 16 and data['distinct_wording_count'] == 7
    row = next(r for r in data['rows'] if r['normalized_wording'] == 'invented reference question?')
    assert len(row['origins']) == 10 and len(row['variants']) == 2
    assert data['intent_groups'] == ['invented-intent']
    # Obsolete producer references in historical supplements are not traversed.
    assert public_preflight(root)['ready_for_private_authoring'] is False


def test_missing_inventory_cannot_silently_drop_exposures(public_fixture):
    root, union, _ = public_fixture
    with pytest.raises(ValueError, match='All named'):
        consolidate(root, union['inputs'][:-1])


def test_changed_pinned_supplement_is_rejected(public_fixture):
    root, union, _ = public_fixture
    write(root, union['inputs'][1]['path'], dict(wordings=['Changed']))
    with pytest.raises(ValueError, match='input changed'):
        load_public_exposure(root)


@pytest.mark.parametrize('mutation', ['drop_wording', 'drop_intent', 'drop_origin', 'count', 'normalization'])
def test_rehashed_materialized_tampering_still_rejected(public_fixture, mutation):
    root, union, _ = public_fixture
    if mutation == 'drop_wording': union['inventory']['rows'].pop()
    if mutation == 'drop_intent': union['inventory']['intent_groups'] = []
    if mutation == 'drop_origin': union['inventory']['rows'][0]['origins'].pop()
    if mutation == 'count': union['inventory']['record_count'] += 1
    if mutation == 'normalization': union['normalization'] = 'other'
    write(root, DIRECTORY + 'public-exposure-v2.json', sealed(union))
    with pytest.raises(ValueError, match='Consolidated'):
        load_public_exposure(root)


def test_changed_original_development_cannot_hide_behind_unchanged_inventory(public_fixture):
    root, _, _ = public_fixture
    write(root, sorted(LEGACY_DEVELOPMENT)[0], dict(cases=[]))
    with pytest.raises(ValueError, match='input changed'):
        load_public_exposure(root)


@pytest.mark.parametrize('mutation', ['ready', 'tuning', 'final', 'corpus', 'exposure', 'state'])
def test_readiness_flags_or_old_corpus_do_not_admit_private_work(public_fixture, mutation):
    root, _, state = public_fixture
    if mutation == 'ready': state['ready_for_private_authoring'] = True
    if mutation == 'tuning': state['ready_for_tuning'] = True
    if mutation == 'final': state['final_development'] = state['prior_development']
    if mutation == 'corpus': state['corpus']['path'] = 'configs/evidence/corpus-coverage-v2.json'
    if mutation == 'exposure': state['exposure']['path'] = DIRECTORY + 'public-exposure-v1.json'
    if mutation == 'state': state['state'] = 'approved'
    write(root, DIRECTORY + 'evaluation-reconciliation-v1.json', sealed(state))
    with pytest.raises(ValueError): public_preflight(root)


def test_public_path_bounds_and_symlinks(tmp_path):
    p = tmp_path / 'data'; p.write_text('{}')
    link = tmp_path / 'link'; link.symlink_to(p)
    for bad in ('../outside', str(p), 'link'):
        with pytest.raises(ValueError): public_bytes(tmp_path, bad)
    p.write_bytes(b' ' * (LIMIT + 1))
    with pytest.raises(ValueError): public_bytes(tmp_path, 'data')


def test_current_public_inputs_cannot_fall_back_to_old_freeze(public_fixture):
    from src.retrieval.private_evaluation import load_public_inputs, PrivateValidationError
    with pytest.raises(PrivateValidationError, match='not frozen'):
        load_public_inputs(public_fixture[0])


def test_private_cli_stops_before_any_private_prompt_or_read(monkeypatch, capsys):
    from src.retrieval import private_evaluation as private
    monkeypatch.setattr('sys.argv', ['private_evaluation', '--prepare'])
    def pending(root):
        raise private.PrivateValidationError('Pending public review')
    def forbidden(*args, **kwargs):
        pytest.fail('A private operation was attempted')
    monkeypatch.setattr(private, 'load_public_inputs', pending)
    monkeypatch.setattr('builtins.input', forbidden)
    monkeypatch.setattr('getpass.getpass', forbidden)
    monkeypatch.setattr(private, 'private_path', forbidden)
    with pytest.raises(SystemExit, match='Private authoring is not ready'):
        private.main()
    assert capsys.readouterr().out == ''


def test_public_cli_does_not_require_tty_or_touch_private_loader(monkeypatch, capsys):
    from src.retrieval import private_evaluation as private
    monkeypatch.setattr('sys.argv', ['private_evaluation', '--public-preflight'])
    monkeypatch.setattr(private, 'public_preflight', lambda root: {'ready_for_private_authoring': False})
    def forbidden(*args, **kwargs): pytest.fail('Private loader called by public preflight')
    monkeypatch.setattr(private, 'load_public_inputs', forbidden)
    private.main()
    assert json.loads(capsys.readouterr().out)['ready_for_private_authoring'] is False
