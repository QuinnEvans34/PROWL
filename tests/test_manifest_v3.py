from copy import deepcopy
import pytest
from jsonschema import ValidationError
from qualification_fixtures import fixture
from src.data.manifest_records_v3 import build_manifest_v3, validate_manifest_v3

pytestmark=pytest.mark.unit


def test_held_member_retained_without_global_permission():
    a,c=fixture();before=deepcopy(a);m=build_manifest_v3(**a)
    assert m['accounting_status']=='complete' and len(m['protection'])==4 and len(m['issues'])==1
    assert m['annotations'][1]['allowed_uses']==[] and m['annotations'][1]['status']=='quarantined'
    assert a==before and build_manifest_v3(**a)==c['manifest']
    for k in ('subjects','studies','protection','annotations'):a[k].reverse()
    assert build_manifest_v3(**a)==m


@pytest.mark.parametrize('fault',['omitted','wrong_role','subject','snapshot','issue_omitted','issue_detached','duplicate',
    'group_overlap','resolved','annotation_link','test_role','snapshot_overlap','claim_real'])
def test_manifest_integrity_faults(fault):
    a,c=fixture()
    if fault=='omitted':a['protection'].pop()
    if fault=='wrong_role':a['protection'][3]['protected_role']='train'
    if fault=='subject':a['studies'][0]['subject_id']=a['studies'][1]['subject_id']
    if fault=='snapshot':a['annotations'][0]['source_snapshot_id']='snapshot:pants:'+'f'*64
    if fault=='issue_omitted':a['issues']=[]
    if fault=='issue_detached':a['annotations'][1]['issue_ids']=[]
    if fault=='duplicate':a['studies']*=2
    if fault=='group_overlap':
        a['protection'][0]['protection_group_id']='same';a['protection'][2]['protection_group_id']='same'
    if fault=='resolved':a['issues'][0]['disposition']='resolved_by_new_artifact'
    if fault=='annotation_link':a['studies'][0]['annotation_ids']=[]
    if fault=='test_role':a['studies'][-1]['source_partition']='publisher_train'
    if fault=='snapshot_overlap':a['snapshots']*=2
    if fault=='claim_real':a['base_membership_bytes']={k:b'fake\n' for k in ('train','validation','test')}
    with pytest.raises((ValueError,ValidationError)):build_manifest_v3(**a)


def test_changed_record_cannot_retain_id():
    m=fixture()[1]['manifest'];m['studies'][0]['image']['content_sha256']='f'*64
    with pytest.raises(ValueError,match='Stale'):validate_manifest_v3(m)


def test_available_exact_hash_collision_blocks_qualification_not_preservation():
    from src.data.manifest_records_v3 import verified_context
    from src.data.source_inventory_records import content_hash
    a,c=fixture();a['studies'][2]['image']['content_sha256']=a['studies'][0]['image']['content_sha256']
    m=build_manifest_v3(**a)
    assert len(m['protection'])==4
    with pytest.raises(ValueError,match='duplicate candidate'):
        verified_context(m,m['studies'][0]['study_id'],m['annotations'][0]['annotation_id'],trusted_manifest_sha256=content_hash(m))
