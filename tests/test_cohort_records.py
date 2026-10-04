from copy import deepcopy
import pytest
from jsonschema import ValidationError
from qualification_fixtures import fixture,add_qualification,parent,child
from src.data.cohort_records import checked_members,build_cohort,validate_cohort
from src.data.source_inventory_records import content_hash

pytestmark=pytest.mark.unit


def ready():
    a,c=fixture();add_qualification(c);add_qualification(c,1);p=parent(c)
    return c,p


def test_protected_parent_keeps_held_case_child_only_qualified():
    c,p=ready();before=deepcopy(c);r=child(c)
    assert len(p['members'])==2 and len(r['members'])==1
    assert c==before and r==child(c)
    assert checked_members(r,trusted_record_sha256=content_hash(r),**c)==r['members']
    with pytest.raises(ValueError,match='Protection-only'):checked_members(p,trusted_record_sha256=content_hash(p),**c)


@pytest.mark.parametrize('fault',['held','validation','shortage','duplicate','no_parent','family','unreviewed_parent','unreviewed_q'])
def test_bad_cohort_is_rejected(fault):
    c,p=ready();kwargs={}
    if fault=='held':kwargs['ids']=[c['manifest']['protection'][1]['study_id']]
    if fault=='validation':kwargs['ids']=[c['manifest']['protection'][2]['study_id']]
    if fault=='shortage':kwargs['requested_count']=2
    if fault=='duplicate':kwargs['ids']=[c['manifest']['protection'][0]['study_id']]*2
    if fault=='no_parent':kwargs['parent_ids']=[]
    if fault=='family':kwargs['cohort_family_id']='other-family'
    if fault=='unreviewed_parent':c['trusted_cohort_sha256']={}
    if fault=='unreviewed_q':c['trusted_qualification_sha256']={}
    with pytest.raises(ValueError):child(c,**kwargs)


def test_protection_parent_cannot_drop_held_member():
    c,p=ready()
    with pytest.raises(ValueError,match='omitted'):
        build_cohort(cohort_id='cohort:bad:v1',cohort_family_id='synthetic',capability='protection_only',
            protected_role='train',study_ids=[c['manifest']['protection'][0]['study_id']],requested_count=1,parent_ids=[],context=c)


def test_grandparent_tamper_detected_and_complete_ancestry_required():
    c,p=ready();first=child(c);c['cohorts_by_id'][first['cohort_id']]=first
    c['trusted_cohort_sha256'][first['cohort_id']]=content_hash(first)
    second=child(c,cohort_id='cohort:smoke-child:v1',parent_ids=[first['cohort_id']])
    assert len(second['ancestors'])==2
    c['cohorts_by_id'][p['cohort_id']]['protected_role']='validation'
    with pytest.raises(ValueError):checked_members(second,trusted_record_sha256=content_hash(second),**c)


@pytest.mark.parametrize('field',['members','ancestors','profile','state','manifest','definition'])
def test_changed_cohort_not_accepted_with_old_identity(field):
    c,p=ready();r=child(c)
    if field in ('members','ancestors'):r[field]=[]
    if field=='profile':r[field]['study_count']=20
    if field=='state':r[field]='frozen'
    if field=='manifest':r[field]['sha256']='f'*64
    if field=='definition':r[field]['selection_method']='easy_cases'
    with pytest.raises((ValueError,ValidationError)):validate_cohort(r,**c)
