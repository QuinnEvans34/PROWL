"""Portable PanTS admission snapshot for the fixed development evaluator.

Reuses the existing accepted cohort review and original protected memberships.
Only metadata is read while building/resolving; payload hashes are enforced by
prediction/scoring at use. This does not authorize training or test evaluation.
"""
import csv
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re

from src.data.protected_identity import accepted_pants_members, pants_identity, validate_role_assignments
from src.data.source_inventory_records import require

VERSION = 'prowl-portable-pants-cohort-v1'
ROLES = ('train', 'validation', 'test')
KINDS = ('ct', 'pancreas', 'lesion')


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(path, expected):
    raw = Path(path).read_bytes()
    require(digest(raw) == expected, 'Admission dependency checksum differs')
    return raw


def validate(package, *, expected_sha256, current_review_sha256):
    require(digest(canonical(package)) == expected_sha256, 'Portable cohort checksum differs')
    require(set(package) == {'version', 'cohort_id', 'review_sha256', 'provenance', 'bases', 'members', 'limitations'},
            'Exact portable cohort fields required')
    require(package['version'] == VERSION and package['cohort_id'] == 'pants-admitted-development-v1',
            'Unsupported portable cohort')
    require(package['review_sha256'] == current_review_sha256, 'Current admission review differs; rebuild required')
    require(set(package['bases']) == set(ROLES), 'All protected base roles required')
    bases = {role: accepted_pants_members(package['bases'][role].encode(), role) for role in ROLES}
    validate_role_assignments((identity, role) for role in ROLES for identity in bases[role])
    by_role = {role: {i.study_id for i in values} for role, values in bases.items()}
    seen = set(); assignments = []; counts = {r: 0 for r in ('train', 'validation')}
    for member in package['members']:
        require(set(member) == {'case_id', 'role', 'identity', 'reference_state', 'files'}, 'Exact member fields required')
        identity = pants_identity(member['case_id']); role = member['role']
        require(role in counts and identity.study_id in by_role[role], 'Member outside original protected role')
        require(member['identity'] == asdict(identity), 'Identity/grouping assurance differs')
        require(member['case_id'] not in seen, 'Duplicate cohort member')
        seen.add(member['case_id']); assignments.append((identity, role)); counts[role] += 1
        require(member['reference_state'] in ('positive', 'reference_empty'), 'Unqualified target state')
        require(set(member['files']) == set(KINDS), 'CT and both annotation identities required')
        for ref in member['files'].values():
            require(set(ref) == {'root_alias', 'uri', 'sha256'} and ref['root_alias'] == 'pants_source', 'Unknown file reference')
            uri = ref['uri']
            require(isinstance(uri, str) and uri and '\\' not in uri and ':' not in uri and
                    not PurePosixPath(uri).is_absolute() and all(p not in ('', '.', '..') for p in uri.split('/')),
                    'Safe relative source path required')
            require(re.fullmatch('[0-9a-f]{64}', ref['sha256']) is not None, 'Source SHA256 required')
    validate_role_assignments(assignments)
    require(all(counts.values()), 'Both admitted roles required')
    require(package['members'] == sorted(package['members'], key=lambda m: (m['role'], m['case_id'])),
            'Canonical member order required')
    return counts


def build(*, review_path, review_sha256, manifest, train_ids, development_ids,
          original_train_ids, original_development_ids, test_ids, source_root, cache_root):
    """Derive a portable snapshot from the exact existing admission, never resample."""
    review = json.loads(pinned(review_path, review_sha256))
    require(review['decision'] == 'accepted' and review['scope'] == 'development_experiment_using_published_reference_annotations'
            and review['empty_reference_policy'] == 'annotation_background_not_verified_healthy', 'Unsupported admission')
    paths = dict(manifest=manifest, train_ids=train_ids, development_ids=development_ids,
                 original_train_ids=original_train_ids, original_development_ids=original_development_ids, test_ids=test_ids)
    require(set(review['input_sha256']) == set(paths), 'Exact admission dependencies required')
    raw = {k: pinned(v, review['input_sha256'][k]) for k, v in paths.items()}
    bases = dict(zip(ROLES, (raw[k].decode() for k in ('original_train_ids', 'original_development_ids', 'test_ids'))))
    rows = list(csv.DictReader(raw['manifest'].decode().splitlines()))
    by_id = {r['case_id']: r for r in rows}
    require(len(by_id) == len(rows), 'Duplicate manifest member')
    selected = {'train': raw['train_ids'].decode().splitlines(), 'validation': raw['development_ids'].decode().splitlines()}
    names = selected['train'] + selected['validation']
    require(set(review['target_states']) == set(names) == set(review['prepared_cache']['members']), 'Admission inventory differs')
    control = json.loads(pinned(Path(cache_root) / 'control.json', review['prepared_cache']['control_sha256']))
    require(control['manifest_sha256'] == review['input_sha256']['manifest'], 'Cache manifest differs')
    root = PurePosixPath(source_root)
    require(root.is_absolute(), 'Explicit original source root required')
    members = []
    for role, ids in selected.items():
        for case_id in ids:
            row = by_id[case_id]
            # The full-run manifest calls the original validation role development.
            manifest_role = {'train': 'train', 'development': 'validation', 'validation': 'validation'}.get(row['protected_role'])
            require(manifest_role == role, 'Manifest protected role differs')
            meta = json.loads(pinned(Path(cache_root) / (case_id + '.json'),
                                    review['prepared_cache']['members'][case_id]['metadata_sha256']))
            require(meta['case_id'] == case_id and meta['control_sha256'] == review['prepared_cache']['control_sha256']
                    and meta['fidelity']['mechanical_survival_pass'], 'Prepared metadata differs')
            require(meta['fidelity']['lesion_target_state'] == review['target_states'][case_id], 'Target state differs')
            files = {k: dict(root_alias='pants_source', uri=PurePosixPath(row[k + '_path']).relative_to(root).as_posix(),
                             sha256=meta['source_sha256'][k]) for k in KINDS}
            members.append(dict(case_id=case_id, role=role, identity=asdict(pants_identity(case_id)),
                                reference_state=review['target_states'][case_id], files=files))
    package = dict(version=VERSION, cohort_id='pants-admitted-development-v1', review_sha256=review_sha256,
                   provenance=dict(input_sha256=review['input_sha256'], cache_control_sha256=review['prepared_cache']['control_sha256']),
                   bases=bases, members=sorted(members, key=lambda m: (m['role'], m['case_id'])),
                   limitations=['Development-only admission; biological patient uniqueness is unverified.',
                                'Empty reference annotations do not establish clinical health.',
                                'Payload identity inherited from pinned source audit; rechecked at consumption.',
                                'No training authorization, model-source separation or held-out test release.'])
    validate(package, expected_sha256=digest(canonical(package)), current_review_sha256=review_sha256)
    return package


def resolve_cases(package, roots, *, expected_sha256, current_review_sha256):
    validate(package, expected_sha256=expected_sha256, current_review_sha256=current_review_sha256)
    require(set(roots) == {'pants_source'} and Path(roots['pants_source']).is_absolute(), 'Explicit local root mapping required')
    root = Path(roots['pants_source']).resolve()
    def local(ref):
        path = (root / ref['uri']).resolve()
        require(path.is_relative_to(root), 'Source path escapes root')
        return dict(path=str(path), sha256=ref['sha256'])
    return [dict(case_id=m['case_id'], ct=local(m['files']['ct']),
                 references={**{k: local(m['files'][k]) for k in ('pancreas', 'lesion')}, 'allow_unknown_units': False},
                 reference_state=m['reference_state'], flags=['biological_patient_identity_unverified'])
            for m in package['members'] if m['role'] == 'validation']


def validate_binding(plan):
    binding = plan['cohort_binding']
    require(set(binding) == {'package', 'sha256', 'current_review_sha256', 'roots'}, 'Exact cohort binding required')
    expected = resolve_cases(binding['package'], binding['roots'], expected_sha256=binding['sha256'],
                             current_review_sha256=binding['current_review_sha256'])
    require(plan['cohort_id'] == binding['package']['cohort_id'], 'Cohort identity differs')
    require(len(plan['cases']) == len(expected), 'Exact complete development membership required')
    for actual, admitted in zip(plan['cases'], expected):
        require(all(actual[k] == admitted[k] for k in ('case_id', 'ct', 'references', 'reference_state')),
                'Evaluation member/content/role differs from admitted cohort')
        require(set(admitted['flags']) <= set(actual['flags']), 'Identity limitation omitted')
