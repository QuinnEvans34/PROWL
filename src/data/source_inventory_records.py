"""Pure source accounting v2. No filesystem inspection or source readiness grant."""
from copy import deepcopy

from src.data.manifest_records import canonical, digest, file_reference, validate_schema
from src.data.protected_identity import pants_identity


def require(condition, message):
    if not condition:
        raise ValueError(message)


def content_hash(record):
    return digest(canonical(record))


def unique(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        require(value not in result, f'Duplicate {key}')
        result[value] = row
    return result


def verify_pin(record, expected):
    require(isinstance(expected, str) and content_hash(record) == expected,
            'Independent content pin mismatch')


def _summary(record):
    scope = record['scope']
    ids = scope['study_ids']
    identity_set = set(ids)
    require(ids == sorted(identity_set) and bool(ids), 'Sorted unique source identities required')
    for study_id in ids:
        require(study_id == pants_identity(study_id.removeprefix('pants:study:')).study_id,
                'Invalid source identity')
    expected = unique(scope['expected_files'], 'uri')
    observed = unique(record['observed_files'], 'uri')
    require(list(expected) == sorted(expected) and list(observed) == sorted(observed),
            'Canonical inventory order required')
    for rows in (scope['expected_files'], record['observed_files']):
        pairs = set()
        for row in rows:
            file_reference(row)
            require(row['study_id'] in identity_set, 'File outside declared identity scope')
            pair = (row['study_id'], row['kind'])
            require(pair not in pairs, 'Duplicate study/file-kind association')
            pairs.add(pair)
    for uri in expected.keys() & observed.keys():
        require(all(expected[uri][k] == observed[uri][k] for k in ('study_id', 'kind')),
                'Observed file association changed')
    for row in observed.values():
        if row['state'] != 'present':
            require(row['bytes'] is None and row['sha256'] is None,
                    'Unavailable payload cannot claim bytes/hash')
        else:
            require(type(row['bytes']) is int and row['bytes'] >= 0, 'Present file needs byte count')
    present = [r for r in observed.values() if r['state'] == 'present']
    hashed = [r for r in present if r['sha256'] is not None]
    status = ('quarantined' if observed.keys() - expected.keys() else
              'partial' if expected.keys() - observed.keys() else 'complete')
    coverage = dict(expected_files=len(expected), present_files=len(present), hashed_files=len(hashed),
                    present_bytes=sum(r['bytes'] for r in present),
                    hashed_bytes=sum(r['bytes'] for r in hashed),
                    unverified_uris=sorted(uri for uri in expected
                        if uri not in observed or observed[uri]['sha256'] is None))
    return status, coverage


def _identity(record):
    return 'snapshot:pants:' + content_hash({k: v for k, v in record.items()
                                            if k != 'source_snapshot_id'})


def build_source_snapshot_v2(*, source_version, license, root_alias, study_ids,
                             expected_files, observed_files, control_sha256):
    """Return an unattested record; complete accounting can retain missing files."""
    record = deepcopy(dict(schema_version='2.0.0', source_key='pants',
        source_version=source_version, license=license, root_alias=root_alias,
        scope=dict(study_ids=sorted(study_ids), expected_files=sorted(expected_files, key=lambda r:r['uri']),
                   control_sha256=control_sha256),
        observed_files=sorted(observed_files, key=lambda r:r['uri'])))
    status, coverage = _summary(record)
    record.update(accounting_status=status, integrity_coverage=coverage)
    record['source_snapshot_id'] = _identity(record)
    validate_source_snapshot_v2(record)
    return record


def validate_source_snapshot_v2(record):
    validate_schema('source-snapshot-v2', record)
    status, coverage = _summary(record)
    require((record['accounting_status'], record['integrity_coverage']) == (status, coverage),
            'Inventory status/assurance claim disagrees with rows')
    require(record['source_snapshot_id'] == _identity(record), 'Stale snapshot identity')
