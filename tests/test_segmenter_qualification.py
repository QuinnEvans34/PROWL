from copy import deepcopy
import pytest
from segmenter_fixtures import fixture,qualify,refresh,TRAIN,VAL
from src.data.segmenter_qualification_v1 import validate_qualification,context_for,build_qualification
from src.data.source_inventory_records import content_hash


def common(ctx):return {k:ctx[k] for k in ['manifest','trusted_manifest_sha256','trusted_policy_sha256','evidence_by_sha256','trusted_evidence_sha256']}


def test_positive_dual_target_qualifies_and_replays():
    _,ctx=fixture();q=qualify(ctx)
    assert q['outcome']=='qualified' and q['lesion_target_state']=='positive' and q['evidence_domain']=='synthetic_fixture'
    assert validate_qualification(q,trusted_qualification_sha256=content_hash(q),**common(ctx))=='qualified'


def test_verified_negative_requires_independent_case_bound_standard():
    _,ctx=fixture(negative=True);q=qualify(ctx);assert q['lesion_target_state']=='verified_negative'
    _,ctx=fixture(negative=True)
    with pytest.raises(ValueError):qualify(ctx,negative_basis=False)


def test_empty_unknown_does_not_become_negative():
    args,ctx=fixture(negative=True);s=args['studies'][0];s['target_statuses'][-1]=dict(target='pancreatic_lesion',status='unknown',method='unavailable',reference_id=None);refresh(args,ctx)
    q=qualify(ctx,results={'lesion_target':'hold'});assert q['outcome']=='held' and q['lesion_target_state']=='unknown'
    with pytest.raises(ValueError,match='identity'):qualify(ctx)


@pytest.mark.parametrize('field',['purpose','policy_sha256','bindings','component','result'])
def test_old_or_wrong_check_receipts_refused(field):
    _,ctx=fixture()
    def change(name,r):
        if name=='lesion_target':r[field]={} if field=='bindings' else 'changed'
    with pytest.raises(ValueError,match='receipt'):qualify(ctx,receipt_change=change)


@pytest.mark.parametrize('fault',['evidence','unreviewed','identity','extra','domain','manifest'])
def test_changed_dependencies_and_claims_rejected(fault):
    _,ctx=fixture();q=qualify(ctx)
    if fault=='evidence':ctx['evidence_by_sha256'][q['checks'][0]['evidence_sha256']]=b'changed'
    if fault=='unreviewed':ctx['trusted_evidence_sha256'].remove(q['checks'][0]['evidence_sha256'])
    if fault=='identity':q['qualification_id']='segmenter-qualification:'+'0'*64
    if fault=='extra':q['allows_training']=True
    if fault=='domain':q['evidence_domain']='retained_source'
    if fault=='manifest':ctx['manifest']['annotations'][0]['file']['content_sha256']='0'*64
    with pytest.raises(Exception):validate_qualification(q,trusted_qualification_sha256=content_hash(q),**common(ctx))


@pytest.mark.parametrize('fault',['ct_units','lesion_units','lesion_affine','source_shape','foreground_voxels','negative_basis'])
def test_wrong_physical_or_target_attestation_refused(fault):
    _,ctx=fixture(negative=fault=='negative_basis')
    def change(name,r):
        if name=='geometry' and fault in ['ct_units','lesion_units']:r['details'][fault]='unknown'
        if name=='geometry' and fault=='lesion_affine':r['details'][fault]=[2]*16
        if name=='geometry' and fault=='source_shape':r['details'][fault]=[1,2,1]
        if name=='lesion_target' and fault=='foreground_voxels':r['details']['foreground_voxels']=100
        if name=='lesion_target' and fault=='negative_basis':r['details']['negative_basis_sha256']='0'*64
    with pytest.raises(ValueError):qualify(ctx,receipt_change=change)


def test_inherited_hold_exclusion_and_difficulty_remain_visible():
    args,ctx=fixture();q=qualify(ctx,index=1);assert q['outcome']=='held'
    q=qualify(ctx,results={'source_readiness':'exclude'});assert q['outcome']=='excluded'
    aid=args['annotations'][0]['annotation_id'];iid='issue:33333333-3333-4333-8333-333333333333'
    args['annotations'][0]['issue_ids']=[iid];args['issues'].append(dict(schema_version='1.0.0',issue_id=iid,rule_code='DIFFICULTY_OBSERVATION',entity_type='annotation',entity_id=aid,severity='information',disposition='retain',message='Invented noise, multiple lesions and outside-pancreas observation retained',evidence=[dict(kind='validator_output',reference='synthetic')],created_at='2026-10-01T00:00:00Z'));refresh(args,ctx)
    assert qualify(ctx)['outcome']=='qualified'


@pytest.mark.parametrize('fault',['no_lesion_permission','wrong_mapping','stale_inventory','missing_lesion','wrong_role','old_policy'])
def test_missing_permission_and_source_binding_refused(fault):
    args,ctx=fixture()
    if fault=='no_lesion_permission':args['annotations'][4]['allowed_uses']=['evaluation_reference']
    if fault=='wrong_mapping':args['annotations'][4]['label_encoding']['mapping']['canonical_foreground']=1
    missing_id=args['annotations'][4]['annotation_id']
    if fault=='missing_lesion':
        args['studies'][0]['annotation_ids'].remove(missing_id);args['annotations'].pop(4)
    if fault=='wrong_role':args['protection'][0]['protected_role']='validation'
    if fault=='old_policy':args['qualification_policy_sha256']='0'*64
    refresh(args,ctx)
    with pytest.raises(ValueError):
        if fault=='missing_lesion':
            build_qualification(study_id=ctx['manifest']['studies'][0]['study_id'],pancreas_annotation_id=args['annotations'][0]['annotation_id'],
                lesion_annotation_id=missing_id,checks=[],purpose=TRAIN,**common(ctx))
        elif fault=='stale_inventory':
            import json
            from src.data.manifest_records import canonical,digest
            def changed_inventory(name,r):
                if name=='source_readiness':
                    old=r['details']['lesion_inventory_sha256'];inv=json.loads(ctx['evidence_by_sha256'][old]);inv['file']['bytes']+=1
                    raw=canonical(inv);pin=digest(raw);ctx['evidence_by_sha256'][pin]=raw;ctx['trusted_evidence_sha256'].add(pin)
                    r['details']['lesion_inventory_sha256']=pin
            qualify(ctx,receipt_change=changed_inventory)
        else:qualify(ctx)


@pytest.mark.parametrize('fault',['broadcast_affine','bool_shape','nonfinite_details','wrong_negative_context'])
def test_geometry_and_negative_reference_cannot_exploit_shape_or_context(fault):
    _,ctx=fixture(negative=fault=='wrong_negative_context')
    def changed(name,r):
        if name=='geometry' and fault=='broadcast_affine':r['details']['lesion_affine']=[r['details']['lesion_affine']]
        if name=='geometry' and fault=='bool_shape':r['details']['lesion_shape']=[2,2,True]
        if name=='mapping_lineage' and fault=='nonfinite_details':r['details']['unused']=float('nan')
        if name=='lesion_target' and fault=='wrong_negative_context':
            import json
            from src.data.manifest_records import canonical,digest
            pin=r['details']['negative_basis_sha256'];d=json.loads(ctx['evidence_by_sha256'][pin]);d['bindings']['study']='0'*64
            b=canonical(d);new=digest(b);ctx['evidence_by_sha256'][new]=b;ctx['trusted_evidence_sha256'].add(new);r['details']['negative_basis_sha256']=new
    with pytest.raises(ValueError):qualify(ctx,receipt_change=changed)
