from copy import deepcopy
import pytest
from jsonschema import ValidationError
from qualification_fixtures import fixture
from src.data.source_inventory_records import build_source_snapshot_v2, validate_source_snapshot_v2

pytestmark=pytest.mark.unit


def args():
    s=fixture()[0]['snapshots'][0]
    return dict(source_version=s['source_version'],license=s['license'],root_alias=s['root_alias'],
        study_ids=s['scope']['study_ids'],expected_files=s['scope']['expected_files'],
        observed_files=s['observed_files'],control_sha256=s['scope']['control_sha256'])


def test_accounting_is_not_payload_readiness():
    a=args();a['observed_files'][0].update(state='unextracted',bytes=None,sha256=None)
    s=build_source_snapshot_v2(**a)
    assert s['accounting_status']=='complete'
    assert s['integrity_coverage']['hashed_files']==7
    assert s['integrity_coverage']['unverified_uris']==[a['observed_files'][0]['uri']]


def test_partial_inventory_and_deterministic_no_mutation():
    a=args();a['observed_files'].pop();before=deepcopy(a)
    first=build_source_snapshot_v2(**a)
    assert first['accounting_status']=='partial' and a==before
    a['expected_files'].reverse();a['observed_files'].reverse()
    assert build_source_snapshot_v2(**a)==first


@pytest.mark.parametrize('fault',['duplicate','wrong_association','unsafe','missing_hash_claim','count','identity','version','scope'])
def test_inventory_faults(fault):
    s=fixture()[0]['snapshots'][0]
    if fault=='duplicate':s['observed_files'].append(deepcopy(s['observed_files'][0]))
    if fault=='wrong_association':s['observed_files'][0]['kind']='pancreas'
    if fault=='unsafe':s['observed_files'][0]['uri']='../escape'
    if fault=='missing_hash_claim':s['observed_files'][0].update(state='missing')
    if fault=='count':s['integrity_coverage']['hashed_files']+=1
    if fault=='identity':s['source_snapshot_id']='snapshot:pants:'+'f'*64
    if fault=='version':s['schema_version']='1.0.0'
    if fault=='scope':s['scope']['study_ids'].pop()
    with pytest.raises((ValueError,ValidationError)):validate_source_snapshot_v2(s)


@pytest.mark.parametrize('change',['duplicate','reversed'])
def test_scope_lookup_still_requires_unique_canonical_identity_list(change):
    s=fixture()[0]['snapshots'][0]
    if change=='duplicate':s['scope']['study_ids'].append(s['scope']['study_ids'][-1])
    else:s['scope']['study_ids'].reverse()
    with pytest.raises((ValueError,ValidationError)):validate_source_snapshot_v2(s)
