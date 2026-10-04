from copy import deepcopy
import pytest
from qualification_fixtures import fixture
from src.data.manifest_records import canonical,digest
from src.data.manifest_records_v3 import build_manifest_v3,verified_context
from src.data.source_inventory_records import content_hash,build_source_snapshot_v2
from src.data.purpose_qualification_v2 import POLICY_SHA256,CHECKS,context_bindings,build_qualification,validate_qualification
from src.data.cohort_records_v3 import build_cohort,checked_members,validate_cohort


def context():
    args,ctx=fixture();args['qualification_policy_sha256']=POLICY_SHA256
    args['annotations'][2]['allowed_uses']=['evaluation_reference']
    m=build_manifest_v3(**args);ctx.update(manifest=m,trusted_manifest_sha256=content_hash(m),trusted_policy_sha256=POLICY_SHA256)
    return args,ctx


def qualify(ctx,index,purpose=None):
    m=ctx['manifest'];study=m['studies'][index];aid=study['annotation_ids'][0]
    purpose=purpose or ('pancreas_localizer_validation' if index==2 else 'pancreas_localizer_training')
    binding=context_bindings(verified_context(m,study['study_id'],aid,trusted_manifest_sha256=ctx['trusted_manifest_sha256']))
    checks=[]
    for name in CHECKS:
        raw=canonical(dict(schema_version='2.0.0',purpose=purpose,check=name,bindings=binding,policy_sha256=POLICY_SHA256,result='pass'));pin=digest(raw)
        ctx['evidence_by_sha256'][pin]=raw;ctx['trusted_evidence_sha256'].add(pin);checks.append(dict(name=name,result='pass',evidence_sha256=pin))
    kwargs={k:ctx[k] for k in ('trusted_manifest_sha256','trusted_policy_sha256','evidence_by_sha256','trusted_evidence_sha256')}
    q=build_qualification(manifest=m,study_id=study['study_id'],annotation_id=aid,checks=checks,purpose=purpose,**kwargs)
    ctx['qualifications_by_id'][q['qualification_id']]=q;ctx['trusted_qualification_sha256'][q['qualification_id']]=content_hash(q)
    return q


def cohorts(ctx,role,index):
    ids=[r['study_id'] for r in ctx['manifest']['protection'] if r['protected_role']==role]
    p=build_cohort(cohort_id='cohort:base-'+role+':v1',cohort_family_id='synthetic',capability='protection_only',protected_role=role,study_ids=ids,requested_count=len(ids),parent_ids=[],context=ctx)
    ctx['cohorts_by_id'][p['cohort_id']]=p;ctx['trusted_cohort_sha256'][p['cohort_id']]=content_hash(p)
    sid=ctx['manifest']['studies'][index]['study_id']
    return build_cohort(cohort_id='cohort:child-'+role+':v1',cohort_family_id='synthetic',capability='executable',protected_role=role,study_ids=[sid],requested_count=1,parent_ids=[p['cohort_id']],context=ctx)


def test_distinct_use_and_operation_required():
    _,ctx=context();qualify(ctx,0);qualify(ctx,2)
    train=cohorts(ctx,'train',0);val=cohorts(ctx,'validation',2)
    for c,op in [(train,'optimizer'),(val,'evaluator')]:
        assert len(checked_members(c,trusted_record_sha256=content_hash(c),operation=op,**ctx))==1
        with pytest.raises(ValueError,match='operation/role'):checked_members(c,trusted_record_sha256=content_hash(c),operation='evaluator' if op=='optimizer' else 'optimizer',**ctx)
    assert ctx['manifest']['annotations'][2]['allowed_uses']==['evaluation_reference']


@pytest.mark.parametrize('index,purpose',[(2,'pancreas_localizer_training'),(0,'pancreas_localizer_validation'),(3,'pancreas_localizer_validation')])
def test_wrong_role_or_publisher_test_refused(index,purpose):
    _,ctx=context()
    with pytest.raises(ValueError,match='role'):qualify(ctx,index,purpose)


def test_missing_evaluation_permission_and_hold_not_promoted():
    args,ctx=context();args['annotations'][2]['allowed_uses']=['training_target'];m=build_manifest_v3(**args);ctx.update(manifest=m,trusted_manifest_sha256=content_hash(m))
    with pytest.raises(ValueError,match='purpose-specific'):qualify(ctx,2)
    q=qualify(ctx,1);assert q['outcome']=='held'
    with pytest.raises(ValueError,match='Held/excluded'):cohorts(ctx,'train',1)


@pytest.mark.parametrize('change',['evidence','identity','manifest'])
def test_stale_dependencies_refused(change):
    _,ctx=context();q=qualify(ctx,2);c=cohorts(ctx,'validation',2)
    if change=='evidence':ctx['evidence_by_sha256'][q['checks'][0]['evidence_sha256']]=b'changed'
    elif change=='identity':q['purpose']='pancreas_localizer_training'
    else:ctx['manifest']['studies'][2]['status']='quarantined'
    with pytest.raises(ValueError):checked_members(c,trusted_record_sha256=content_hash(c),operation='evaluator',**ctx)


def test_missing_member_and_wrong_ancestry_refused():
    _,ctx=context();qualify(ctx,2);c=cohorts(ctx,'validation',2)
    bad=deepcopy(c);bad['definition']['requested_count']=2
    from src.data.cohort_records_v3 import _derivation
    bad['derivation_sha256']=_derivation(bad)
    with pytest.raises(ValueError,match='shortage'):validate_cohort(bad,**ctx)
    bad=deepcopy(c);bad['protected_role']='train';bad['derivation_sha256']=_derivation(bad)
    with pytest.raises(ValueError):validate_cohort(bad,**ctx)


def test_cross_role_ct_duplicate_rejected_even_with_rebound_manifest():
    args,ctx=context();args['studies'][2]['image']['content_sha256']=args['studies'][0]['image']['content_sha256']
    # Duplicate detection precedes qualification; a source snapshot mismatch cannot hide it.
    m=build_manifest_v3(**args);ctx.update(manifest=m,trusted_manifest_sha256=content_hash(m))
    with pytest.raises(ValueError,match='Identical CT content'):cohorts(ctx,'validation',2)


def test_no_implicit_operation_or_old_contract_acceptance():
    _,ctx=context();qualify(ctx,2);c=cohorts(ctx,'validation',2)
    with pytest.raises(TypeError):checked_members(c,trusted_record_sha256=content_hash(c),**ctx)
    with pytest.raises(ValueError,match='Explicit consumer'):checked_members(c,trusted_record_sha256=content_hash(c),operation='display',**ctx)
    from src.data.cohort_records import validate_cohort as old_validate
    from jsonschema import ValidationError
    with pytest.raises(ValidationError):old_validate(c,**ctx)
