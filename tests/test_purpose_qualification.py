from copy import deepcopy
import pytest
from jsonschema import ValidationError
from qualification_fixtures import fixture, add_qualification
from src.data.manifest_records_v3 import build_manifest_v3
from src.data.purpose_qualification import build_qualification, validate_qualification
from src.data.source_inventory_records import content_hash

pytestmark=pytest.mark.unit


def validation(c,q):
    return dict(trusted_qualification_sha256=content_hash(q),manifest=c['manifest'],
        **{k:c[k] for k in ('trusted_manifest_sha256','trusted_policy_sha256','evidence_by_sha256','trusted_evidence_sha256')})


def test_positive_evidence_required_and_held_case_not_promoted():
    a,c=fixture();q=add_qualification(c);held=add_qualification(c,1)
    assert q['outcome']=='qualified' and held['outcome']=='held'
    assert validate_qualification(q,**validation(c,q))=='qualified'
    assert c['manifest']['annotations'][1]['allowed_uses']==[]


@pytest.mark.parametrize('name',['geometry','source_readiness','target','permitted_use','mapping_lineage'])
def test_each_required_check_can_hold(name):
    a,c=fixture();assert add_qualification(c,results={name:'hold'})['outcome']=='held'


@pytest.mark.parametrize('fault',['checks','receipt','review_pin','manifest_pin','q_pin','policy','outcome','dependency','version'])
def test_qualification_forgery_and_binding_faults(fault):
    a,c=fixture();q=add_qualification(c);kw=validation(c,q)
    if fault=='checks':q['checks'].pop()
    if fault=='receipt':c['evidence_by_sha256'][q['checks'][0]['evidence_sha256']]=b'changed'
    if fault=='review_pin':c['trusted_evidence_sha256'].remove(q['checks'][0]['evidence_sha256'])
    if fault=='manifest_pin':kw['trusted_manifest_sha256']='f'*64
    if fault=='q_pin':kw['trusted_qualification_sha256']='f'*64
    if fault=='policy':kw['trusted_policy_sha256']='f'*64
    if fault=='outcome':q['outcome']='held'
    if fault=='dependency':q['annotation_id']=c['manifest']['annotations'][1]['annotation_id']
    if fault=='version':q['schema_version']='9.0.0'
    with pytest.raises((ValueError,ValidationError)):validate_qualification(q,**kw)


@pytest.mark.parametrize('fault',['unknown_issue','unapproved_mapping','singular_geometry','no_allowed_use','source_hash'])
def test_positive_claim_cannot_override_record_fault(fault):
    a,c=fixture()
    if fault=='unknown_issue':
        i=deepcopy(a['issues'][0]);i.update(issue_id='issue:22222222-2222-4222-8222-222222222222',
          entity_id=a['annotations'][0]['annotation_id'],severity='warning',disposition='retain',rule_code='UNCLASSIFIED')
        a['annotations'][0]['issue_ids']=[i['issue_id']];a['issues'].append(i)
    if fault=='unapproved_mapping':a['annotations'][0]['label_encoding']['mapping']['policy_id']='unapproved'
    if fault=='singular_geometry':a['studies'][0]['geometry']['affine_ras'][0]=0
    if fault=='no_allowed_use':a['annotations'][0]['allowed_uses']=['display_reference']
    if fault=='source_hash':a['studies'][0]['image']['content_sha256']='f'*64
    m=build_manifest_v3(**a);c.update(manifest=m,trusted_manifest_sha256=content_hash(m))
    if fault=='unknown_issue':assert add_qualification(c)['outcome']=='held'
    else:
        with pytest.raises(ValueError):add_qualification(c)


def test_documented_difficulty_remains_qualified():
    a,c=fixture()
    i=deepcopy(a['issues'][0]);i.update(issue_id='issue:22222222-2222-4222-8222-222222222222',
        entity_id=a['annotations'][0]['annotation_id'],severity='information',disposition='retain',
        rule_code='DIFFICULTY_OBSERVATION',message='Low contrast, noise, unusual anatomy; previous Dice 0.0')
    a['issues'].append(i);a['annotations'][0]['issue_ids']=[i['issue_id']]
    m=build_manifest_v3(**a);c.update(manifest=m,trusted_manifest_sha256=content_hash(m))
    assert add_qualification(c)['outcome']=='qualified'


def test_empty_pancreas_is_not_selected_for_this_smoke():
    a,c=fixture();enc=a['annotations'][0]['label_encoding'];enc.update(value_counts=[dict(value=0,count=4)],stored_range=[0,0])
    m=build_manifest_v3(**a);c.update(manifest=m,trusted_manifest_sha256=content_hash(m))
    with pytest.raises(ValueError,match='foreground'):add_qualification(c)


def test_reviewed_receipt_cannot_be_reused_for_another_check():
    a,c=fixture();q=add_qualification(c);checks=deepcopy(q['checks'])
    checks[1]['evidence_sha256']=checks[0]['evidence_sha256']
    with pytest.raises(ValueError,match='receipt'):
        build_qualification(manifest=c['manifest'],study_id=q['study_id'],annotation_id=q['annotation_id'],checks=checks,
            **{k:c[k] for k in ('trusted_manifest_sha256','trusted_policy_sha256','evidence_by_sha256','trusted_evidence_sha256')})


def test_audit_voxel_count_must_match_qualified_grid():
    a,c=fixture();a['studies'][0]['geometry']['shape_xyz']=[3,3,3]
    m=build_manifest_v3(**a);c.update(manifest=m,trusted_manifest_sha256=content_hash(m))
    with pytest.raises(ValueError,match='voxel count'):add_qualification(c)
