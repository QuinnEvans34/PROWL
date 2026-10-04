"""Pure manifest v3: protected accounting is separate from execution permission.

Records are inline for this bounded in-memory slice; publication is deliberately absent.
Production readers must verify the independently retained manifest pin and source evidence.
"""
import json
from copy import deepcopy
from contextlib import contextmanager
from contextvars import ContextVar

from src.data.manifest_records import canonical, digest, validate_schema, file_reference, CONTRACTS
from src.data.annotation_contract_v2 import validate_annotation_v2
from src.data.protected_identity import pants_identity, accepted_pants_members
from src.data.source_inventory_records import (
    content_hash, require, unique, validate_source_snapshot_v2, verify_pin)


def _id(record):
    return f"manifest:{record['name']}:" + content_hash({k:v for k,v in record.items() if k != 'manifest_id'})


def _check_migration(record, base_membership_bytes):
    roles = ('train', 'validation', 'test')
    if record['evidence_domain'] == 'synthetic_fixture':
        require(base_membership_bytes is None and all(v is None for v in record['migration_pins'].values()),
                'Synthetic identity accounting cannot claim real migration pins')
        return
    require(base_membership_bytes is not None and set(base_membership_bytes) == set(roles),
            'All original membership bytes required')
    expected = {}
    for role in roles:
        payload = base_membership_bytes[role]
        require(record['migration_pins'][role] == digest(payload), 'Migration hash changed')
        expected.update({i.study_id: role for i in accepted_pants_members(payload, role)})
    require({r['study_id']: r['protected_role'] for r in record['protection']} == expected,
            'Original membership changed or omitted')


def _validate_manifest_v3(record, *, base_membership_bytes=None):
    validate_schema('manifest-v3', record)
    require(record['manifest_id'] == _id(record), 'Stale manifest identity')
    _check_migration(record, base_membership_bytes)
    snapshots = unique(record['snapshots'], 'source_snapshot_id')
    require(bool(snapshots), 'Source required')
    for snapshot in snapshots.values():
        validate_source_snapshot_v2(snapshot)
    protection = unique(record['protection'], 'study_id')
    source_ids = [sid for s in snapshots.values() for sid in s['scope']['study_ids']]
    require(len(source_ids) == len(set(source_ids)), 'Overlapping source snapshot scopes')
    require(set(protection) == set(source_ids), 'Incomplete protected identity accounting')
    groups = {}
    for row in protection.values():
        identity = pants_identity(row['source_study_id'])
        require((row['study_id'], row['subject_id']) == (identity.study_id, identity.subject_id),
                'Protection identity mismatch')
        require(identity.source_partition != 'publisher_test' or row['protected_role'] == 'test',
                'Publisher test role changed')
        for group in (row['subject_id'], row['protection_group_id']):
            if group is not None:
                require(bool(group), 'Empty protection group')
                require(groups.setdefault(group, row['protected_role']) == row['protected_role'],
                        'Protection group crosses roles')
    collections = {}
    for coll, kind, key in [('subjects','subject-record','subject_id'),
                           ('studies','study-record','study_id'),
                           ('annotations','annotation-record-v2','annotation_id'),
                           ('issues','data-issue','issue_id')]:
        collections[coll] = unique(record[coll], key)
        for row in record[coll]:
            if coll == 'annotations': validate_annotation_v2(row)
            else: validate_schema(kind, row)
    subjects, studies, annotations, issues = (collections[c] for c in ('subjects','studies','annotations','issues'))
    entities = {}
    for coll, singular, key in [('subjects','subject','subject_id'),('studies','study','study_id'),
                               ('annotations','annotation','annotation_id')]:
        for row in record[coll]:
            snapshot = snapshots.get(row['source_snapshot_id'])
            require(snapshot is not None and row['source'] == snapshot['source_key'], 'Wrong source linkage')
            entities[(singular,row[key])] = row
            actual = {i['issue_id'] for i in issues.values()
                      if (i['entity_type'],i['entity_id']) == (singular,row[key])}
            require(set(row['issue_ids']) == actual, 'Issue inventory omission or wrong attachment')
    for row in subjects.values():
        require(any(p['subject_id'] == row['subject_id'] and p['source_study_id'] == row['source_subject_id']
                    for p in protection.values()), 'Subject absent from protected identity map')
        require(row['identity_method'] == 'study_as_subject_fallback' and
                row['identity_assurance'] == 'unverified_unique', 'Unsupported PanTS identity assurance')
    for row in studies.values():
        identity = pants_identity(row['source_study_id'])
        require(row['study_id'] in protection and row['subject_id'] == protection[row['study_id']]['subject_id']
                and row['study_id'] == identity.study_id and row['source_partition'] == identity.source_partition,
                'Study/protected identity mismatch')
        require(row['study_id'] in snapshots[row['source_snapshot_id']]['scope']['study_ids'], 'Study outside source scope')
        subject = subjects.get(row['subject_id'])
        require(subject is not None and subject['source_snapshot_id'] == row['source_snapshot_id'], 'Subject linkage mismatch')
        file_reference(row['image'])
        require(len({t['target'] for t in row['target_statuses']}) == len(row['target_statuses']), 'Duplicate target')
        require(set(row['annotation_ids']) == {a['annotation_id'] for a in annotations.values()
                                               if a['study_id'] == row['study_id']}, 'Annotation links disagree')
    for row in annotations.values():
        study = studies.get(row['study_id'])
        require(study is not None and row['source_snapshot_id'] == study['source_snapshot_id'], 'Annotation linkage mismatch')
    for row in issues.values():
        require((row['entity_type'],row['entity_id']) in entities or
                (row['entity_type'] == 'source_snapshot' and row['entity_id'] in snapshots), 'Dangling issue')
        require(not row.get('supersedes_issue_id') and not row.get('resolution_artifact_id')
                and row['disposition'] != 'resolved_by_new_artifact', 'Resolution requires separate reviewed implementation')
    status = ('quarantined' if any(s['accounting_status']=='quarantined' for s in snapshots.values())
              else 'partial' if any(s['accounting_status']=='partial' for s in snapshots.values()) else 'complete')
    require(record['accounting_status'] == status, 'Accounting status mismatch')
    return collections


# Opt-in only: one successful immutable manifest key per bounded publication session.
# Never share this across processes or accept caller-provided cached validation claims.
_VALIDATION_SESSION = ContextVar('prowl_manifest_validation_session', default=None)


@contextmanager
def manifest_validation_session():
    token = _VALIDATION_SESSION.set({})
    try:
        yield
    finally:
        _VALIDATION_SESSION.reset(token)


def validate_manifest_v3(record, *, base_membership_bytes=None):
    cache = _VALIDATION_SESSION.get()
    if cache is None:
        return _validate_manifest_v3(record, base_membership_bytes=base_membership_bytes)
    # Keys include actual payload bytes, migration bytes, and every contract schema's bytes.
    # A caller mutating a record or schema cannot retain a previous validation result.
    payload = canonical(record)
    require(json.loads(payload) == record, 'Validation reuse requires JSON-shaped records')
    key = (payload,
           None if base_membership_bytes is None else tuple(sorted(base_membership_bytes.items())),
           tuple((p.name, p.read_bytes()) for p in sorted(CONTRACTS.glob('*.schema.json'))))
    if cache.get('key') == key:
        return {coll: {row[field]: row for row in record[coll]}
                for coll, field in (('subjects','subject_id'), ('studies','study_id'),
                                    ('annotations','annotation_id'), ('issues','issue_id'))}
    result = _validate_manifest_v3(record, base_membership_bytes=base_membership_bytes)
    cache.clear()
    cache['key'] = key
    return result


def build_manifest_v3(*, name, snapshots, protection, subjects, studies, annotations, issues,
                      qualification_policy_sha256, base_membership_bytes=None):
    collections = dict(snapshots=(snapshots,'source_snapshot_id'),protection=(protection,'study_id'),
                       subjects=(subjects,'subject_id'),studies=(studies,'study_id'),
                       annotations=(annotations,'annotation_id'),issues=(issues,'issue_id'))
    record = dict(schema_version='3.0.0',name=name,
                  evidence_domain='synthetic_fixture' if base_membership_bytes is None else 'retained_source',
                  migration_pins={r:None if base_membership_bytes is None else digest(base_membership_bytes[r])
                                  for r in ('train','validation','test')},
                  qualification_policy_sha256=qualification_policy_sha256)
    record.update({c:deepcopy(sorted(rows,key=lambda r:r[key])) for c,(rows,key) in collections.items()})
    record['accounting_status'] = ('quarantined' if any(s['accounting_status']=='quarantined' for s in snapshots)
        else 'partial' if any(s['accounting_status']=='partial' for s in snapshots) else 'complete')
    record['manifest_id'] = _id(record)
    validate_manifest_v3(record, base_membership_bytes=base_membership_bytes)
    return record


def verified_context(manifest, study_id, annotation_id, *, trusted_manifest_sha256, base_membership_bytes=None):
    verify_pin(manifest, trusted_manifest_sha256)
    rows = validate_manifest_v3(manifest, base_membership_bytes=base_membership_bytes)
    require(manifest['accounting_status'] == 'complete', 'Incomplete source accounting')
    require(study_id in rows['studies'] and annotation_id in rows['annotations'], 'Missing target records')
    study, annotation = rows['studies'][study_id], rows['annotations'][annotation_id]
    require(annotation['study_id'] == study_id, 'Wrong target study')
    # Available exact-byte collisions are known candidates, not silently ignored.
    require(not any(other['study_id'] != study_id and
                    other['image']['content_sha256'] == study['image']['content_sha256']
                    for other in rows['studies'].values()), 'Unresolved exact image duplicate candidate')
    subject = rows['subjects'][study['subject_id']]
    snapshot = next(s for s in manifest['snapshots'] if s['source_snapshot_id'] == study['source_snapshot_id'])
    entities = {('subject', subject['subject_id']), ('study', study_id), ('annotation', annotation_id),
                ('source_snapshot', snapshot['source_snapshot_id'])}
    issues = sorted([i for i in rows['issues'].values() if (i['entity_type'],i['entity_id']) in entities],key=lambda i:i['issue_id'])
    return dict(snapshot=snapshot,subject=subject,study=study,annotation=annotation,issues=issues)
