from copy import deepcopy
import pytest

from qualification_fixtures import fixture, add_qualification
from src.data.manifest_records_v3 import build_manifest_v3
from src.data.source_inventory_records import content_hash
from src.data.qualification_transition import build_transition, validate_transition


def setup():
    args,ctx=fixture()
    # Successor claims publisher protocol only, never expert certification.
    a=args['annotations'][0];a['validation_status']='source_asserted';a['method']='human_validated'
    a['provenance']['scope']='publisher_protocol'
    old=deepcopy(args)
    for kind,idkey,code in [('subjects','subject_id','IDENTITY_UNVERIFIED'),
                          ('studies','study_id','STUDY_QUALIFICATION_PENDING'),
                          ('annotations','annotation_id','ANNOTATION_USE_PENDING')]:
        row=old[kind][0];row['status']='quarantined'
        iid=f'issue:00000000-0000-4000-8000-{len(old["issues"]):012d}'
        row['issue_ids']=[iid]
        old['issues'].append(dict(schema_version='1.0.0',issue_id=iid,rule_code=code,
            entity_type=kind[:-1] if kind!='studies' else 'study',entity_id=row[idkey],severity='blocking',
            disposition='quarantine',message='Invented prior hold',created_at='2026-09-28T00:00:00Z',
            evidence=[dict(kind='validator_output',reference='synthetic')]))
    old['annotations'][0]['allowed_uses']=[]
    old['annotations'][0]['label_encoding']['mapping']=None
    prior=build_manifest_v3(**old)
    a['annotation_id']+='-successor';a['annotation_version']='successor'
    args['studies'][0]['annotation_ids']=[a['annotation_id']]
    args['studies'][0]['target_statuses'][0]['reference_id']=a['annotation_id']
    ctx['manifest']=build_manifest_v3(**args);ctx['trusted_manifest_sha256']=content_hash(ctx['manifest'])
    q=add_qualification(ctx)
    kw=dict(prior_manifest=prior,successor_manifest=ctx['manifest'],study_id=args['studies'][0]['study_id'],
        prior_annotation_id=old['annotations'][0]['annotation_id'],successor_annotation_id=a['annotation_id'],
        qualification=q,trusted_prior_manifest_sha256=content_hash(prior),
        trusted_successor_manifest_sha256=content_hash(ctx['manifest']),trusted_qualification_sha256=content_hash(q),
        **{k:ctx[k] for k in ('trusted_policy_sha256','evidence_by_sha256','trusted_evidence_sha256')})
    return old,args,ctx,kw


def test_positive_transition_preserves_history_and_replays():
    old,args,ctx,kw=setup();before=deepcopy(kw)
    result=build_transition(**kw)
    assert kw==before
    assert len(result['superseded_holds'])==3
    assert result['identity_assurance']=='unverified_unique'
    assert not result['production_consumer_enabled']
    assert validate_transition(result,trusted_transition_sha256=content_hash(result),**kw)==result


@pytest.mark.parametrize('code',['PHYSICAL_UNITS_UNRESOLVED','PANCREAS_PRESENT_TARGET_EXCLUDED','NEW_UNKNOWN_HOLD'])
def test_specific_or_unknown_hold_cannot_be_removed(code):
    old,args,ctx,kw=setup()
    old['issues'][-1]['rule_code']=code
    kw['prior_manifest']=build_manifest_v3(**old)
    kw['trusted_prior_manifest_sha256']=content_hash(kw['prior_manifest'])
    with pytest.raises(ValueError,match='three generic holds'):build_transition(**kw)


@pytest.mark.parametrize('change',['mask','ct','geometry','membership','assurance','permission','same_id','audit'])
def test_recomputed_successor_cannot_expand_scope(change):
    old,args,ctx,kw=setup()
    a=args['annotations'][0];s=args['studies'][0]
    if change=='mask':a['file']['bytes']+=1
    if change=='ct':s['image']['bytes']+=1
    if change=='geometry':s['geometry']['spacing_mm_xyz'][0]=2
    if change=='membership':args['protection'][0]['protected_role']='validation'
    if change=='assurance':a['validation_status']='project_verified';a['provenance']['scope']='per_file_review'
    if change=='permission':a['allowed_uses'].append('reference_evaluation')
    if change=='same_id':
        a['annotation_id']=kw['prior_annotation_id'];s['annotation_ids']=[a['annotation_id']]
        kw['successor_annotation_id']=a['annotation_id']
    if change=='audit':a['label_encoding']['audit_file']['bytes']+=1
    # Even if a caller recomputes the new manifest pin, the transition must refuse.
    with pytest.raises(Exception):
        kw['successor_manifest']=build_manifest_v3(**args)
        kw['trusted_successor_manifest_sha256']=content_hash(kw['successor_manifest'])
        build_transition(**kw)


def test_forged_positive_qualification_refused():
    old,args,ctx,kw=setup();kw['qualification']['checks'][0]['evidence_sha256']='0'*64
    kw['trusted_qualification_sha256']=content_hash(kw['qualification'])
    with pytest.raises(ValueError):build_transition(**kw)


def test_certificate_edit_refused_even_with_new_pin():
    old,args,ctx,kw=setup();r=build_transition(**kw);r['superseded_holds']=[]
    with pytest.raises(ValueError):validate_transition(r,trusted_transition_sha256=content_hash(r),**kw)


@pytest.mark.parametrize('change',['other_study','other_issue','target_claim'])
def test_unrelated_changes_cannot_hide_in_certificate(change):
    old,args,ctx,kw=setup()
    if change=='other_study':args['studies'][1]['acquisition']['site']='changed'
    if change=='other_issue':args['issues'][0]['message']='changed'
    if change=='target_claim':args['studies'][0]['target_statuses'][0]['status']='negative'
    kw['successor_manifest']=build_manifest_v3(**args)
    kw['trusted_successor_manifest_sha256']=content_hash(kw['successor_manifest'])
    with pytest.raises(ValueError):build_transition(**kw)
