"""Separate offline Plan07 schema section; no retrieval runtime, roots or real text."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
import pytest

pytestmark = pytest.mark.contract
ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / 'docs/capstone/contracts/retrieval'
FIXTURES = Path(__file__).parent / 'fixtures/shared_retrieval_contracts_v1'
NAMES = (
    'source-work', 'source-revision', 'source-event', 'rights-decision', 'representation', 'passage',
    'corpus-manifest', 'query', 'supplied-ranking', 'span-label', 'metric-result', 'context-result',
)
IDENTITY_FIELDS = dict(zip(NAMES, (
    'work_id', 'revision_id', 'event_id', 'rights_id', 'representation_id', 'passage_id',
    'corpus_id', 'query_id', 'ranking_id', 'question_id', 'corpus_id', 'ranking_id',
)))


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def validator(name):
    schema = load(CONTRACTS / f'{name}.schema.json')
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def control(name):
    value = load(FIXTURES / f'{name}.synthetic.json')
    validator(name).validate(value)
    return value


def parent_at(value, path):
    parent = value
    for key in path[:-1]:
        parent = parent[key]
    return parent


def test_exact_accepted_schema_fixture_scope_and_pins():
    pins = load(FIXTURES / 'pins.json')
    assert pins['schema_version'] == '1.0.0'
    assert set(pins['contracts']) == set(NAMES)
    assert {p.name for p in CONTRACTS.glob('*.schema.json')} == {f'{n}.schema.json' for n in NAMES}
    assert {p.name for p in FIXTURES.glob('*.synthetic.json')} == {f'{n}.synthetic.json' for n in NAMES}
    for name, hashes in pins['contracts'].items():
        assert hashlib.sha256((CONTRACTS / f'{name}.schema.json').read_bytes()).hexdigest() == hashes['schema_sha256']
        assert hashlib.sha256((FIXTURES / f'{name}.synthetic.json').read_bytes()).hexdigest() == hashes['fixture_sha256']


@pytest.mark.parametrize('name', NAMES)
def test_accepted_schema_and_invented_positive(name):
    schema = load(CONTRACTS / f'{name}.schema.json')
    assert schema['$schema'] == 'https://json-schema.org/draft/2020-12/schema'
    assert schema['$id'] == f'https://prowl.local/schemas/retrieval/{name}/1.0.0'
    assert schema['properties']['schema_version']['const'] == '1.0.0'
    control(name)


@pytest.mark.parametrize('name', NAMES)
@pytest.mark.parametrize('mutation', ('omit_identity', 'invalid_identity', 'wrong_version', 'unknown_field'))
def test_common_contract_boundary_rejections(name, mutation):
    value = deepcopy(control(name))
    if mutation == 'omit_identity':
        del value[IDENTITY_FIELDS[name]]
    elif mutation == 'invalid_identity':
        value[IDENTITY_FIELDS[name]] = 'not-an-identity'
    elif mutation == 'wrong_version':
        value['schema_version'] = '2.0.0'
    else:
        value['unexpected'] = True
    assert list(validator(name).iter_errors(value)), (name, mutation)


@pytest.mark.parametrize(('name', 'path', 'invalid'), [
    ('source-work', ('origin',), 'web'),
    ('source-work', ('status',), 'promoted'),
    ('source-work', ('notices', 0, 'notice_type'), 'diagnosis'),
    ('source-event', ('source_file',), '../invented.jsonl'),
    ('source-event', ('source_file',), '/invented.jsonl'),
    ('source-event', ('ordinal',), -1),
    ('source-event', ('revision_id',), None),  # Add/replace needs a revision.
    ('source-event', ('event_type',), 'delete'),  # Delete forbids a revision.
    ('rights-decision', ('permissions', 'display_snippet'), 'yes'),
    ('rights-decision', ('decision',), 'unknown'),
    ('representation', ('paragraphs', 0, 'offset_map', 0), [0, 16, 0]),
    ('representation', ('paragraphs', 0, 'original_length'), 0),
    ('representation', ('sections', 0, 'start'), -1),
    ('passage', ('start',), -1),
    ('passage', ('end',), 0),
    ('passage', ('chunking', 'max_chars'), 0),
    ('passage', ('chunking', 'overlap_sentences'), -1),
    ('corpus-manifest', ('allowed_origins',), ['synthetic', 'synthetic']),
    ('corpus-manifest', ('excluded', 0, 'reason'), 'difficult_case'),
    ('corpus-manifest', ('counts', 'members'), -1),
    ('query', ('finding', 'modality'), 'MRI'),
    ('query', ('question_original',), ''),
    ('query', ('refusal_codes',), ['RF1_diagnosis']),  # Accepted cannot carry refusal codes.
    ('query', ('state',), 'refused'),  # Refusal needs a code.
    ('supplied-ranking', ('target_depth',), 10),
    ('supplied-ranking', ('eligible_count',), -1),
    ('supplied-ranking', ('tie_policy',), 'unspecified'),
    ('span-label', ('spans', 0, 'end'), 0),
    ('span-label', ('spans', 0, 'grade'), 'diagnosis'),
    ('span-label', ('required_concepts',), ['c:invented', 'c:invented']),
    ('metric-result', ('official', 'source', 'mrr'), 1.01),
    ('metric-result', ('official', 'passage', 'n_undefined'), -1),
    ('metric-result', ('provisional', 'status'), 'accepted_additional_D-085'),
    ('context-result', ('status',), 'accepted_additional_D-085'),
    ('context-result', ('counter', 'kind'), 'generator_tokenizer'),
    ('context-result', ('budget',), 0),
    ('context-result', ('delivered_tokens',), -1),
    ('context-result', ('delivered_span_recall',), -0.01),
    ('context-result', ('concept_coverage',), 1.01),
    ('context-result', ('skipped', 0, 'tokens'), 0),
])
def test_named_nested_shape_or_policy_boundary(name, path, invalid):
    value = deepcopy(control(name))
    parent_at(value, path)[path[-1]] = invalid
    assert list(validator(name).iter_errors(value)), (name, path, invalid)


@pytest.mark.parametrize('permission', ('retain_metadata', 'local_text_store', 'local_embedding',
                                      'display_snippet', 'redistribute'))
def test_rights_require_each_explicit_permission(permission):
    value = control('rights-decision')
    del value['permissions'][permission]
    assert list(validator('rights-decision').iter_errors(value))


@pytest.mark.parametrize(('name', 'path'), [
    ('source-work', ('notices', 0)), ('rights-decision', ('permissions',)),
    ('representation', ('paragraphs', 0)), ('passage', ('chunking',)),
    ('corpus-manifest', ('members', 0)), ('query', ('finding',)),
    ('supplied-ranking', ('items', 0)), ('span-label', ('spans', 0)),
    ('metric-result', ('official', 'source')), ('context-result', ('counter',)),
])
def test_nested_unknown_fields_are_rejected(name, path):
    value = control(name)
    parent = value
    for key in path:
        parent = parent[key]
    parent['unexpected'] = True
    assert list(validator(name).iter_errors(value))


def test_ranking_target_has_a_bounded_item_shape():
    value = control('supplied-ranking')
    value['items'] *= 51
    assert list(validator('supplied-ranking').iter_errors(value))


def test_metric_requires_each_official_k_and_preserves_undefined_values():
    value = control('metric-result')
    del value['official']['source']['recall_at']['10']
    assert list(validator('metric-result').iter_errors(value))
    value = control('metric-result')
    for level in ('source', 'passage'):
        value['official'][level]['recall_at'] = {str(k): None for k in (1, 3, 5, 10)}
        value['official'][level]['mrr'] = None
    value['official'].update(n_answerable=0, undefined_reason='no_answerable_questions')
    validator('metric-result').validate(value)
