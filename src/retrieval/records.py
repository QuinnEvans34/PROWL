"""Plan 07 record identity, validation, event replay, rights and corpus assembly.

Synthetic foundation only (P3 packet). No parser, network, database or real-corpus promotion.
Identity rules (see docs/capstone/retrieval/FOUNDATION-DESIGN-2026-09-28.md):

* Canonical JSON = UTF-8, sorted keys, no insignificant whitespace, ``allow_nan=False``, plus a
  trailing newline (the same convention as ``src.data.manifest_records.canonical``).
* Identity payloads contain only strings, integers, booleans, null, lists and objects. Floats are
  rejected in identity payloads (``identity_digest``). Finite floats are accepted only in fields
  declared as scores (supplied rankings) and NaN/Infinity are rejected everywhere.
* IDs are ``<prefix>:<sha256>`` of the canonical identity payload. Timestamps and filesystem paths
  are never part of an identity payload.
* Nothing references an ID that is derived from itself: passages do not name their corpus; the
  corpus ID is derived from the ordered member inventory.
* Identities are recomputed wherever records are loaded (event replay, corpus assembly, permission
  checks, evaluation), not only when they are constructed. A record whose content changed while it
  kept its old ID is refused (``verify_revision``, ``verify_rights``, ``verify_event``).
* Duplicate logical records are refused, even when byte-identical. Repeating the same revision
  through distinct source events is a different case and is allowed.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_VERSION = '1.0.0'
CONTRACTS = Path(__file__).resolve().parents[2] / 'docs' / 'capstone' / 'contracts' / 'retrieval'
PERMISSIONS = ('retain_metadata', 'local_text_store', 'local_embedding', 'display_snippet', 'redistribute')
INDEXABLE_DECISIONS = frozenset({'allowed', 'restricted_local'})
_SCHEMAS = {}


class RecordError(ValueError):
    """A record, relationship or identity check failed. Never repaired silently."""


# --- canonical form and hashing ----------------------------------------------------------------

def _check_json_value(value, *, allow_float, where='$'):
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RecordError(f'non-finite number at {where}')
        if not allow_float:
            raise RecordError(f'float not permitted in identity payload at {where}')
        return
    if isinstance(value, list):
        for i, item in enumerate(value):
            _check_json_value(item, allow_float=allow_float, where=f'{where}[{i}]')
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RecordError(f'non-string key at {where}')
            _check_json_value(item, allow_float=allow_float, where=f'{where}.{key}')
        return
    raise RecordError(f'unsupported JSON type {type(value).__name__} at {where}')


def canonical_bytes(value, *, allow_float=True):
    _check_json_value(value, allow_float=allow_float)
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                       allow_nan=False) + '\n').encode('utf-8')


def sha256_hex(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def identity_digest(payload):
    """SHA-256 of an identity payload. Floats are rejected so identities stay representation-exact."""
    return sha256_hex(canonical_bytes(payload, allow_float=False))


# --- schema validation -------------------------------------------------------------------------

def _validator(kind):
    if kind not in _SCHEMAS:
        path = CONTRACTS / f'{kind}.schema.json'
        schema = json.loads(path.read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        _SCHEMAS[kind] = Draft202012Validator(schema, format_checker=FormatChecker())
    return _SCHEMAS[kind]


def validate(kind, record):
    """Schema-validate one record and confirm it is canonical JSON. Raises RecordError."""
    errors = sorted(_validator(kind).iter_errors(record), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        raise RecordError(f'{kind}: {first.message} at {"/".join(map(str, first.path)) or "$"}')
    canonical_bytes(record)
    return record


# --- works, revisions, events ------------------------------------------------------------------

def make_work(work_id, *, origin='synthetic', status='active', notices=()):
    return validate('source-work', dict(schema_version=SCHEMA_VERSION, work_id=work_id, origin=origin,
                                        status=status, notices=[dict(n) for n in notices]))


def _revision_id(work_id, content_sha256):
    return 'rev:' + identity_digest(dict(work_id=work_id, content_sha256=content_sha256))


def make_revision(work_id, content_bytes):
    """A revision is one exact content version of one work (for PubMed: the canonical record XML)."""
    if not isinstance(content_bytes, (bytes, bytearray)) or not content_bytes:
        raise RecordError('revision content must be non-empty bytes')
    content_sha256 = sha256_hex(bytes(content_bytes))
    return validate('source-revision', dict(schema_version=SCHEMA_VERSION,
                                            revision_id=_revision_id(work_id, content_sha256),
                                            work_id=work_id, content_sha256=content_sha256))


def verify_revision(revision, content_bytes=None):
    """Schema plus recomputed identity. With ``content_bytes``, also the content hash itself."""
    validate('source-revision', revision)
    if _revision_id(revision['work_id'], revision['content_sha256']) != revision['revision_id']:
        raise RecordError('revision ID does not match its content')
    if content_bytes is not None and sha256_hex(bytes(content_bytes)) != revision['content_sha256']:
        raise RecordError('revision content hash does not match the supplied content')
    return revision


def make_event(source_file, ordinal, event_type, work_id, revision_id=None):
    return validate('source-event', dict(schema_version=SCHEMA_VERSION,
                                         event_id=f'evt:{source_file}:{ordinal}', source_file=source_file,
                                         ordinal=ordinal, event_type=event_type, work_id=work_id,
                                         revision_id=revision_id))


def verify_event(event):
    """Schema plus the positional identity ``evt:<source_file>:<ordinal>``."""
    validate('source-event', event)
    if type(event['ordinal']) is not int:
        raise RecordError('event ordinal must be an integer')
    if event['event_id'] != f"evt:{event['source_file']}:{event['ordinal']}":
        raise RecordError('event ID does not match its position')
    return event


def replay_events(events, file_sequence, revisions):
    """Final revision per work from ordered events. Last event wins; a delete removes the work.

    ``file_sequence`` is the authoritative ordered list of source files. Events from unknown files,
    duplicate (file, ordinal) pairs, and add events naming unknown revisions or a revision of a
    different work are errors. Repeated identical content through distinct events is allowed.
    Returns (final: {work_id: revision_id}, deleted: sorted work_ids).
    """
    order = {name: i for i, name in enumerate(file_sequence)}
    if len(order) != len(file_sequence):
        raise RecordError('duplicate file in sequence')
    rev_work = {}
    for rev in revisions:
        verify_revision(rev)
        if rev['revision_id'] in rev_work:
            raise RecordError(f"duplicate source-revision record {rev['revision_id']}")
        rev_work[rev['revision_id']] = rev['work_id']
    seen, keyed = set(), []
    for event in events:
        verify_event(event)
        if event['source_file'] not in order:
            raise RecordError(f"event from file outside sequence: {event['source_file']}")
        key = (event['source_file'], event['ordinal'])
        if key in seen:
            raise RecordError(f'duplicate event position {key}')
        seen.add(key)
        if event['event_type'] == 'add_or_replace':
            owner = rev_work.get(event['revision_id'])
            if owner is None:
                raise RecordError('event names an unknown revision')
            if owner != event['work_id']:
                raise RecordError('event revision belongs to a different work')
        keyed.append((order[event['source_file']], event['ordinal'], event))
    final, deleted = {}, set()
    for _, _, event in sorted(keyed, key=lambda t: (t[0], t[1])):
        if event['event_type'] == 'delete':
            final.pop(event['work_id'], None)
            deleted.add(event['work_id'])
        else:
            final[event['work_id']] = event['revision_id']
            deleted.discard(event['work_id'])
    return final, sorted(deleted)


# --- rights ------------------------------------------------------------------------------------

_RIGHTS_PAYLOAD = ('representation_id', 'policy_version', 'decision', 'permissions', 'reason')


def _rights_id(payload):
    return 'rights:' + identity_digest({k: payload[k] for k in _RIGHTS_PAYLOAD})


def make_rights(representation_id, *, decision, permissions, policy_version='synthetic-rights-v1',
                reason='synthetic fixture decision'):
    payload = dict(representation_id=representation_id, policy_version=policy_version,
                   decision=decision, permissions=dict(permissions), reason=reason)
    missing = [k for k in PERMISSIONS if k not in payload['permissions']]
    if missing:
        raise RecordError(f'permissions must be explicit; missing {missing}')
    return validate('rights-decision', dict(schema_version=SCHEMA_VERSION, rights_id=_rights_id(payload),
                                            **payload))


def verify_rights(rights):
    """Schema (all five permissions explicit booleans) plus the recomputed rights identity.

    A decision whose permissions, decision, reason, policy or representation changed while it kept
    its old ``rights_id`` is refused rather than trusted.
    """
    validate('rights-decision', rights)
    if _rights_id(rights) != rights['rights_id']:
        raise RecordError('rights ID does not match its decision content')
    return rights


def may_index(rights):
    """Local text storage AND local embedding/indexing, under an indexable decision. Fails closed."""
    verify_rights(rights)
    p = rights['permissions']
    return (rights['decision'] in INDEXABLE_DECISIONS and p['local_text_store'] is True
            and p['local_embedding'] is True)


def may_display(rights):
    """Snippet display is independent of indexing: both must be separately permitted."""
    verify_rights(rights)
    return rights['decision'] in INDEXABLE_DECISIONS and rights['permissions']['display_snippet'] is True


def may_redistribute(rights):
    verify_rights(rights)
    return rights['decision'] == 'allowed' and rights['permissions']['redistribute'] is True


def answer_support_eligible(work):
    """Retracted, quarantined or excluded works can never support an answer."""
    validate('source-work', work)
    if work['status'] != 'active':
        return False
    return not any(n['notice_type'] == 'retraction' for n in work['notices'])


# --- corpus assembly ---------------------------------------------------------------------------

def _index_unique(records, key, kind, verify=None):
    """Index records by ID. Any repeated ID is refused: a conflicting record is an error, and so is a
    byte-identical duplicate (a duplicate logical record is never collapsed silently)."""
    out = {}
    for record in records:
        (verify or (lambda r: validate(kind, r)))(record)
        existing = out.get(record[key])
        if existing is not None:
            if canonical_bytes(existing) != canonical_bytes(record):
                raise RecordError(f'conflicting {kind} for {record[key]}')
            raise RecordError(f'duplicate {kind} record {record[key]}')
        out[record[key]] = record
    return out


def build_corpus(*, works, revisions, events, file_sequence, representations, rights, passages,
                 allowed_origins=('synthetic',)):
    """Verify every link and content hash, then return a corpus manifest.

    Every input passage lands in exactly one of ``members`` or ``excluded`` (with a reason).
    Unresolved links, hash mismatches and conflicting duplicates raise RecordError; nothing is
    repaired. The corpus ID is derived from the ordered member inventory, so it cannot be circular.
    """
    from src.retrieval.passages import verify_passage, verify_representation  # local: avoid cycle

    allowed_origins = sorted(set(allowed_origins))
    work_by_id = _index_unique(works, 'work_id', 'source-work')
    rev_by_id = _index_unique(revisions, 'revision_id', 'source-revision', verify_revision)
    final, deleted = replay_events(events, file_sequence, rev_by_id.values())
    repr_by_id = _index_unique(representations, 'representation_id', 'representation', verify_representation)
    for rep in repr_by_id.values():
        if rep['revision_id'] not in rev_by_id:
            raise RecordError('representation names an unknown revision')
        if rev_by_id[rep['revision_id']]['work_id'] != rep['work_id']:
            raise RecordError('representation work does not match its revision')
        if rep['work_id'] not in work_by_id:
            raise RecordError('representation names an unknown work')
    rights_by_repr = {}
    for decision in rights:
        verify_rights(decision)
        if decision['representation_id'] not in repr_by_id:
            raise RecordError('rights decision names an unknown representation')
        if decision['representation_id'] in rights_by_repr:
            raise RecordError('more than one rights decision for a representation')
        rights_by_repr[decision['representation_id']] = decision

    members, excluded, seen = [], [], set()
    for passage in passages:
        validate('passage', passage)
        if passage['passage_id'] in seen:
            raise RecordError('duplicate passage in corpus input')
        seen.add(passage['passage_id'])
        rep = repr_by_id.get(passage['representation_id'])
        if rep is None:
            raise RecordError('passage names an unknown representation')
        verify_passage(passage, rep)
        decision = rights_by_repr.get(rep['representation_id'])
        if decision is None:
            raise RecordError('representation has no rights decision (fail closed)')
        work = work_by_id[rep['work_id']]
        reason = None
        if work['origin'] not in allowed_origins:
            reason = 'origin_not_allowed'
        elif rep['work_id'] in deleted:
            reason = 'work_deleted'
        elif final.get(rep['work_id']) != rep['revision_id']:
            reason = 'not_final_revision'
        elif work['status'] == 'quarantined':
            reason = 'work_quarantined'
        elif work['status'] == 'excluded':
            reason = 'work_excluded'
        elif not answer_support_eligible(work):
            reason = 'work_retracted'
        elif not may_index(decision):
            reason = 'rights_not_indexable'
        if reason:
            excluded.append(dict(passage_id=passage['passage_id'], reason=reason))
        else:
            members.append(dict(passage_id=passage['passage_id'], text_sha256=passage['text_sha256'],
                                representation_id=rep['representation_id'], work_id=rep['work_id'],
                                rights_id=decision['rights_id']))
    members.sort(key=lambda m: m['passage_id'])
    excluded.sort(key=lambda m: m['passage_id'])
    corpus_id = 'corpus:' + identity_digest(dict(allowed_origins=allowed_origins, members=members))
    manifest = dict(schema_version=SCHEMA_VERSION, corpus_id=corpus_id, allowed_origins=allowed_origins,
                    members=members, excluded=excluded,
                    counts=dict(input_passages=len(seen), members=len(members), excluded=len(excluded)))
    if manifest['counts']['members'] + manifest['counts']['excluded'] != manifest['counts']['input_passages']:
        raise RecordError('corpus reconciliation failed')  # defensive; cannot happen by construction
    return validate('corpus-manifest', manifest)


def verify_corpus_manifest(manifest):
    """Recompute the corpus ID from its members; a mismatch means the manifest was altered.

    Also checks member/exclusion ordering, disjointness and that the counts reconcile.
    """
    validate('corpus-manifest', manifest)
    expected = 'corpus:' + identity_digest(dict(allowed_origins=manifest['allowed_origins'],
                                                members=manifest['members']))
    if expected != manifest['corpus_id']:
        raise RecordError('corpus ID does not match its member inventory')
    if manifest['allowed_origins'] != sorted(manifest['allowed_origins']):
        raise RecordError('allowed_origins must be sorted')
    ids = [m['passage_id'] for m in manifest['members']]
    if ids != sorted(set(ids)):
        raise RecordError('corpus members must be unique and sorted')
    out = [e['passage_id'] for e in manifest['excluded']]
    if out != sorted(set(out)) or set(out) & set(ids):
        raise RecordError('exclusions must be unique, sorted and disjoint from members')
    counts = manifest['counts']
    if (counts['members'], counts['excluded'], counts['input_passages']) != (len(ids), len(out), len(ids) + len(out)):
        raise RecordError('corpus counts do not reconcile with members and exclusions')
    return manifest


def copy_record(record):
    """Deep copy helper for callers that must not mutate inputs."""
    return deepcopy(record)
