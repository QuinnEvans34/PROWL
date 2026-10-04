"""Records, identities, event replay, rights and corpus assembly (synthetic fixtures only)."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.retrieval.passages import chunk_config, make_passages, make_representation
from src.retrieval.passages import verify_representation
from src.retrieval.records import (CONTRACTS, RecordError, answer_support_eligible, build_corpus,
                                   canonical_bytes, identity_digest, make_event, make_revision,
                                   make_rights, make_work, may_display, may_index, may_redistribute,
                                   replay_events, validate, verify_corpus_manifest, verify_event,
                                   verify_revision, verify_rights)

pytestmark = pytest.mark.unit
FIXTURE = Path(__file__).parent / 'fixtures' / 'synthetic_documents.json'
ALL = dict(retain_metadata=True, local_text_store=True, local_embedding=True, display_snippet=True,
           redistribute=False)


def chain(rights_overrides=None, work_overrides=None):
    docs = json.loads(FIXTURE.read_text(encoding='utf-8'))['works']
    works, revisions, events, reps, rights, passages = [], [], [], [], [], []
    for i, doc in enumerate(docs):
        wo = (work_overrides or {}).get(doc['work_id'], {})
        works.append(make_work(doc['work_id'], **wo))
        rev = make_revision(doc['work_id'], canonical_bytes(doc))
        revisions.append(rev)
        events.append(make_event('synthetic-base-001.jsonl', i, 'add_or_replace', doc['work_id'], rev['revision_id']))
        rep = make_representation(work_id=doc['work_id'], revision_id=rev['revision_id'], kind=doc['kind'],
                                  sections=doc['sections'])
        reps.append(rep)
        ro = (rights_overrides or {}).get(doc['work_id'], {})
        rights.append(make_rights(rep['representation_id'], decision=ro.get('decision', 'allowed'),
                                  permissions={**ALL, **ro.get('permissions', {})}))
        passages.extend(make_passages(rep, chunk_config(max_chars=90, overlap_sentences=1)))
    return dict(works=works, revisions=revisions, events=events, file_sequence=['synthetic-base-001.jsonl'],
                representations=reps, rights=rights, passages=passages)


def test_canonical_bytes_rules():
    assert canonical_bytes({'b': 1, 'a': 'é'}) == '{"a":"é","b":1}\n'.encode('utf-8')
    for bad in (float('nan'), float('inf'), {1: 'x'}, {'a': {1, 2}}):
        with pytest.raises(RecordError):
            canonical_bytes(bad)
    with pytest.raises(RecordError, match='float not permitted'):
        identity_digest({'score': 0.5})
    assert canonical_bytes({'score': 0.5}) == b'{"score":0.5}\n'


def test_identity_is_deterministic_and_content_sensitive():
    a = make_revision('work:synthetic:x', b'alpha')
    assert make_revision('work:synthetic:x', b'alpha') == a
    assert make_revision('work:synthetic:x', b'alphA')['revision_id'] != a['revision_id']
    assert make_revision('work:synthetic:y', b'alpha')['revision_id'] != a['revision_id']


@pytest.mark.parametrize('bad', [
    dict(schema_version='1.0.0', work_id='work:synthetic:x', origin='synthetic', status='active', notices=[], extra=1),
    dict(schema_version='1.0.0', work_id='work:pmid:0123', origin='synthetic', status='active', notices=[]),
    dict(schema_version='1.0.0', work_id='work:synthetic:x', origin='web', status='active', notices=[]),
    dict(schema_version='2.0.0', work_id='work:synthetic:x', origin='synthetic', status='active', notices=[]),
])
@pytest.mark.contract
def test_schema_rejects_unknown_fields_ids_enums_versions(bad):
    with pytest.raises(RecordError):
        validate('source-work', bad)


@pytest.mark.contract
def test_every_schema_is_valid_draft_2020_12():
    from jsonschema import Draft202012Validator
    names = sorted(p.name for p in CONTRACTS.glob('*.schema.json'))
    assert len(names) == 12
    for name in names:
        Draft202012Validator.check_schema(json.loads((CONTRACTS / name).read_text()))


def test_event_replay_last_wins_delete_and_readd():
    w = 'work:synthetic:x'
    r1, r2 = make_revision(w, b'v1'), make_revision(w, b'v2')
    events = [make_event('base', 0, 'add_or_replace', w, r1['revision_id']),
              make_event('upd-1', 0, 'add_or_replace', w, r2['revision_id']),
              make_event('upd-1', 1, 'add_or_replace', w, r2['revision_id']),  # identical content again
              make_event('upd-2', 0, 'delete', w)]
    final, deleted = replay_events(events, ['base', 'upd-1', 'upd-2'], [r1, r2])
    assert final == {} and deleted == [w]
    events.append(make_event('upd-3', 0, 'add_or_replace', w, r1['revision_id']))
    final, deleted = replay_events(list(reversed(events)), ['base', 'upd-1', 'upd-2', 'upd-3'], [r1, r2])
    assert final == {w: r1['revision_id']} and deleted == []


@pytest.mark.failure_injection
def test_event_replay_rejects_bad_order_and_links():
    w, other = 'work:synthetic:x', 'work:synthetic:y'
    r1 = make_revision(w, b'v1')
    with pytest.raises(RecordError, match='outside sequence'):
        replay_events([make_event('upd-9', 0, 'add_or_replace', w, r1['revision_id'])], ['base'], [r1])
    with pytest.raises(RecordError, match='duplicate event position'):
        replay_events([make_event('base', 0, 'add_or_replace', w, r1['revision_id'])] * 2, ['base'], [r1])
    with pytest.raises(RecordError, match='unknown revision'):
        replay_events([make_event('base', 0, 'add_or_replace', w, 'rev:' + '0' * 64)], ['base'], [r1])
    with pytest.raises(RecordError, match='different work'):
        replay_events([make_event('base', 0, 'add_or_replace', other, r1['revision_id'])], ['base'], [r1])
    with pytest.raises(RecordError):
        make_event('base', 0, 'delete', w, r1['revision_id'])  # delete may not carry a revision


def test_rights_permissions_are_independent_and_fail_closed():
    rep = 'repr:' + '1' * 64
    index_only = make_rights(rep, decision='allowed', permissions={**ALL, 'display_snippet': False})
    display_only = make_rights(rep, decision='allowed', permissions={**ALL, 'local_embedding': False})
    assert may_index(index_only) and not may_display(index_only)
    assert may_display(display_only) and not may_index(display_only)
    assert not may_redistribute(index_only)
    for decision in ('metadata_only', 'quarantined', 'excluded'):
        assert not may_index(make_rights(rep, decision=decision, permissions=ALL))
    with pytest.raises(RecordError, match='explicit'):
        make_rights(rep, decision='allowed', permissions={'local_text_store': True})
    record = make_rights(rep, decision='allowed', permissions=ALL)
    broken = deepcopy(record)
    del broken['permissions']['local_embedding']
    with pytest.raises(RecordError):
        may_index(broken)
    broken = deepcopy(record)
    broken['permissions']['local_embedding'] = 'yes'
    with pytest.raises(RecordError):
        may_index(broken)


def test_retraction_and_quarantine_cannot_support_answers():
    assert answer_support_eligible(make_work('work:synthetic:a'))
    assert not answer_support_eligible(make_work('work:synthetic:a', status='quarantined'))
    assert not answer_support_eligible(make_work('work:synthetic:a', notices=[
        dict(notice_type='retraction', reference='synthetic-notice-1')]))
    assert answer_support_eligible(make_work('work:synthetic:a', notices=[
        dict(notice_type='correction', reference='synthetic-notice-2')]))


@pytest.mark.component
def test_corpus_reconciles_and_excludes_with_reasons():
    c = chain(rights_overrides={'work:synthetic:quintar-review': dict(permissions={'local_embedding': False})},
              work_overrides={'work:synthetic:retracted-item': dict(notices=[
                  dict(notice_type='retraction', reference='synthetic-notice-1')])})
    manifest = build_corpus(**c)
    counts = manifest['counts']
    assert counts['members'] + counts['excluded'] == counts['input_passages'] == len(c['passages'])
    reasons = {e['reason'] for e in manifest['excluded']}
    assert reasons == {'rights_not_indexable', 'work_retracted'}
    assert {m['work_id'] for m in manifest['members']} == {'work:synthetic:zorbel-margins'}
    verify_corpus_manifest(manifest)


@pytest.mark.component
def test_corpus_identity_deterministic_and_permutation_invariant():
    c = chain()
    before = deepcopy(c)
    m1 = build_corpus(**c)
    assert c == before  # inputs not mutated
    c2 = {k: (list(reversed(v)) if isinstance(v, list) and k != 'file_sequence' else v) for k, v in c.items()}
    assert build_corpus(**c2) == m1


@pytest.mark.component
def test_changed_text_rights_or_chunking_changes_identity():
    base = build_corpus(**chain())['corpus_id']
    c = chain()
    c['passages'] = [p for rep in c['representations']
                     for p in make_passages(rep, chunk_config(max_chars=1200, overlap_sentences=0))]
    assert build_corpus(**c)['corpus_id'] != base
    c = chain(rights_overrides={'work:synthetic:retracted-item': dict(permissions={'local_embedding': False})})
    assert build_corpus(**c)['corpus_id'] != base
    docs = json.loads(FIXTURE.read_text())['works']
    docs[0]['sections'][0]['paragraphs'][0] += ' Extra.'
    rev = make_revision(docs[0]['work_id'], canonical_bytes(docs[0]))
    rep = make_representation(work_id=docs[0]['work_id'], revision_id=rev['revision_id'], kind='abstract',
                              sections=docs[0]['sections'])
    assert rep['representation_id'] != chain()['representations'][0]['representation_id']


@pytest.mark.failure_injection
def test_corpus_rejects_dangling_and_conflicting_records():
    c = chain()
    bad = deepcopy(c)
    bad['rights'] = bad['rights'][1:]
    with pytest.raises(RecordError, match='no rights decision'):
        build_corpus(**bad)
    bad = deepcopy(c)
    bad['representations'] = bad['representations'][1:]
    with pytest.raises(RecordError, match='unknown representation'):
        build_corpus(**bad)
    bad = deepcopy(c)
    bad['passages'].append(bad['passages'][0])
    with pytest.raises(RecordError, match='duplicate passage'):
        build_corpus(**bad)
    bad = deepcopy(c)
    bad['works'].append(make_work(bad['works'][0]['work_id'], status='quarantined'))
    with pytest.raises(RecordError, match='conflicting'):
        build_corpus(**bad)
    bad = deepcopy(c)
    bad['rights'].append(make_rights(bad['representations'][0]['representation_id'], decision='excluded',
                                     permissions=ALL))
    with pytest.raises(RecordError, match='more than one rights'):
        build_corpus(**bad)


@pytest.mark.component
def test_superseded_or_deleted_revision_is_not_indexed():
    c = chain()
    w = c['works'][0]['work_id']
    newer = make_revision(w, b'newer synthetic content')
    c['revisions'].append(newer)
    c['events'].append(make_event('synthetic-upd-001.jsonl', 0, 'add_or_replace', w, newer['revision_id']))
    c['file_sequence'] = c['file_sequence'] + ['synthetic-upd-001.jsonl']
    manifest = build_corpus(**c)
    assert all(m['work_id'] != w for m in manifest['members'])
    assert 'not_final_revision' in {e['reason'] for e in manifest['excluded']}
    c['events'].append(make_event('synthetic-upd-002.jsonl', 0, 'delete', w))
    c['file_sequence'] = c['file_sequence'] + ['synthetic-upd-002.jsonl']
    assert 'work_deleted' in {e['reason'] for e in build_corpus(**c)['excluded']}


def test_real_origin_refused_by_default_and_tampered_manifest_detected():
    c = chain()
    c['works'] = [make_work(w['work_id'], origin='pubmed_baseline') if i == 0 else w
                  for i, w in enumerate(c['works'])]
    manifest = build_corpus(**c)
    assert 'origin_not_allowed' in {e['reason'] for e in manifest['excluded']}
    tampered = deepcopy(manifest)
    tampered['members'] = tampered['members'][:-1]
    tampered['counts']['members'] -= 1
    with pytest.raises(RecordError, match='does not match'):
        verify_corpus_manifest(tampered)


# --- Codex P3 review R1: identities recomputed at load boundaries; duplicate logical records -----

def _set(record, dotted, value):
    *path, last = dotted.split('.')
    for key in path:
        record = record[key]
    record[last] = value


@pytest.mark.failure_injection
@pytest.mark.parametrize('field,value', [
    ('permissions.retain_metadata', False), ('permissions.local_text_store', False),
    ('permissions.local_embedding', False), ('permissions.display_snippet', False),
    ('permissions.redistribute', True), ('decision', 'restricted_local'), ('reason', 'edited after issue'),
    ('policy_version', 'synthetic-rights-v2'),
])
def test_r1_rights_changed_under_stale_id_rejected_everywhere(field, value):
    c = chain()
    _set(c['rights'][0], field, value)
    with pytest.raises(RecordError, match='rights ID does not match'):
        build_corpus(**c)
    for check in (verify_rights, may_index, may_display, may_redistribute):
        with pytest.raises(RecordError, match='rights ID does not match'):
            check(c['rights'][0])


@pytest.mark.failure_injection
def test_r1_codex_probe_display_flip_no_longer_yields_same_corpus():
    c = chain()
    c['rights'][0]['permissions']['display_snippet'] = False  # stale rights_id kept
    with pytest.raises(RecordError, match='rights ID'):
        build_corpus(**c)
    c = chain()  # the same change, properly re-issued, is a new decision and a new corpus identity
    reissued = make_rights(c['rights'][0]['representation_id'], decision='allowed',
                           permissions={**ALL, 'display_snippet': False})
    assert reissued['rights_id'] != c['rights'][0]['rights_id']
    base = build_corpus(**c)['corpus_id']
    c['rights'][0] = reissued
    assert build_corpus(**c)['corpus_id'] != base


@pytest.mark.failure_injection
def test_r1_rights_moved_to_another_representation_rejected():
    c = chain()
    c['rights'][0]['representation_id'] = c['representations'][1]['representation_id']
    with pytest.raises(RecordError, match='rights ID'):
        build_corpus(**c)


@pytest.mark.failure_injection
@pytest.mark.parametrize('field', ['content_sha256', 'work_id'])
def test_r1_revision_changed_under_stale_id_rejected(field):
    c = chain()
    c['revisions'][0][field] = 'f' * 64 if field == 'content_sha256' else c['works'][1]['work_id']
    with pytest.raises(RecordError, match='revision ID does not match'):
        build_corpus(**c)
    with pytest.raises(RecordError, match='revision ID does not match'):
        replay_events(c['events'], c['file_sequence'], c['revisions'])


def test_r1_revision_content_check_when_bytes_available():
    rev = make_revision('work:synthetic:x', b'alpha')
    assert verify_revision(rev, b'alpha') == rev
    with pytest.raises(RecordError, match='content hash'):
        verify_revision(rev, b'alphA')


@pytest.mark.failure_injection
def test_r1_event_identity_is_its_position():
    event = make_event('base', 0, 'add_or_replace', 'work:synthetic:x', 'rev:' + '1' * 64)
    verify_event(event)
    moved = dict(event, ordinal=5)
    with pytest.raises(RecordError, match='event ID does not match'):
        verify_event(moved)
    c = chain()
    c['events'][0] = dict(c['events'][0], ordinal=7)
    with pytest.raises(RecordError, match='event ID does not match'):
        build_corpus(**c)


@pytest.mark.failure_injection
@pytest.mark.parametrize('kind', ['works', 'revisions', 'representations', 'rights'])
def test_r1_identical_duplicate_logical_records_rejected(kind):
    c = chain()
    c[kind].append(deepcopy(c[kind][0]))
    with pytest.raises(RecordError, match='duplicate|more than one'):
        build_corpus(**c)


def test_r1_duplicate_revision_rejected_in_replay_but_repeated_events_allowed():
    c = chain()
    with pytest.raises(RecordError, match='duplicate source-revision'):
        replay_events(c['events'], c['file_sequence'], c['revisions'] + [deepcopy(c['revisions'][0])])
    base = build_corpus(**chain())
    w, rev = c['works'][0]['work_id'], c['revisions'][0]['revision_id']
    c['events'].append(make_event('synthetic-upd-001.jsonl', 0, 'add_or_replace', w, rev))  # same content again
    c['file_sequence'] = c['file_sequence'] + ['synthetic-upd-001.jsonl']
    assert build_corpus(**c) == base


@pytest.mark.failure_injection
def test_r1_manifest_counts_and_exclusions_must_reconcile():
    c = chain(work_overrides={'work:synthetic:retracted-item': dict(notices=[
        dict(notice_type='retraction', reference='synthetic-notice-1')])})
    manifest = build_corpus(**c)
    for mutate in (lambda m: m['counts'].update(input_passages=m['counts']['input_passages'] + 1),
                   lambda m: m['counts'].update(excluded=m['counts']['excluded'] + 1),
                   lambda m: m['excluded'].append(dict(passage_id=m['members'][0]['passage_id'],
                                                       reason='work_deleted')),
                   lambda m: m['excluded'].append(dict(m['excluded'][0]))):  # repeated exclusion
        bad = deepcopy(manifest)
        mutate(bad)
        with pytest.raises(RecordError):
            verify_corpus_manifest(bad)


def test_r1_representation_probe_from_codex_review():
    rep = chain()['representations'][0]
    rep['paragraphs'][0]['offset_map'] = [[0, 1, 9000, 9001]]
    with pytest.raises(RecordError):
        verify_representation(rep)
