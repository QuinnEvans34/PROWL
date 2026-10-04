from copy import deepcopy
import json
import pytest
from segmenter_fixtures import fixture,qualify,refresh
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import content_hash
from src.data.segmenter_cohort_bundle_v1 import freeze,resolve,context_for
from src.data.segmenter_cohort_v1 import checked_members


def invented():
    args,ctx=fixture();qualify(ctx);qualify(ctx,index=1);qualify(ctx,index=2)
    d=dict(manifest=ctx['manifest'],qualifications=list(ctx['qualifications_by_id'].values()),
        evidence={k:v.decode() for k,v in ctx['evidence_by_sha256'].items()})
    expected={r:[ctx['manifest']['studies'][i]['study_id']] for r,i in [('train',0),('validation',2)]}
    return args,ctx,d,expected


def test_exact_original_parents_and_role_descriptors():
    _,ctx,d,e=invented();b=freeze(d,ctx.get('base_membership_bytes'),e,family='invented-only')
    report,rows=resolve(d,ctx.get('base_membership_bytes'),b,e)
    assert report['train_count']==report['validation_count']==1
    assert len(b['parents'][0]['members'])==2 # held candidate remains permanently protected
    assert rows['optimizer'][0]['roi_source']=='pancreas_only'
    assert rows['evaluator'][0]['lesion_target_state']=='positive'
    assert set(['image','pancreas','lesion'])<=set(rows['optimizer'][0])
    with pytest.raises(ValueError,match='operation'):
        checked_members(b['cohorts'][1],trusted_record_sha256=content_hash(b['cohorts'][1]),operation='optimizer',
            **context_for(d,ctx.get('base_membership_bytes'),b['parents']))


@pytest.mark.parametrize('fault',['held','wrong_role','missing_qualification','changed_evidence','missing_member','extra_member',
    'parent_omission','child_omission','parent_role','annotation_identity','target_state','protection_pin'])
def test_forged_cohorts_or_qualifications_fail(fault):
    _,ctx,d,e=invented();bases=ctx.get('base_membership_bytes');b=freeze(d,bases,e,family='invented-only')
    if fault=='held':e['train']=[ctx['manifest']['studies'][1]['study_id']]
    if fault=='wrong_role':e['train']=e['validation']
    if fault=='missing_qualification':d['qualifications']=d['qualifications'][1:]
    if fault=='changed_evidence':d['evidence'][next(iter(d['evidence']))]='changed'
    if fault=='missing_member':b['cohorts'][0]['members']=[]
    if fault=='extra_member':b['cohorts'][0]['members'].append(deepcopy(b['cohorts'][1]['members'][0]))
    if fault=='parent_omission':b['parents'][0]['members']=b['parents'][0]['members'][:1]
    if fault=='child_omission':b['cohorts'].pop()
    if fault=='parent_role':b['parents'][0]['protected_role']='validation'
    if fault=='annotation_identity':b['cohorts'][0]['members'][0]['lesion_annotation_id']='fake'
    if fault=='target_state':b['cohorts'][0]['members'][0]['lesion_target_state']='verified_negative'
    if fault=='protection_pin':b['cohorts'][0]['protection_parent']['sha256']='0'*64
    with pytest.raises(Exception):resolve(d,bases,b,e)
    if fault in ('held','wrong_role','missing_qualification','changed_evidence'):
        with pytest.raises(Exception):freeze(d,bases,e,family='invented-only')


def test_exact_ct_leakage_fails_before_cohort_freeze():
    args,ctx,_,e=invented()
    args['studies'][2]['image']['content_sha256']=args['studies'][0]['image']['content_sha256']
    refresh(args,ctx)
    d=dict(manifest=ctx['manifest'],qualifications=list(ctx['qualifications_by_id'].values()),
        evidence={k:v.decode() for k,v in ctx['evidence_by_sha256'].items()})
    # The protection-root validator checks all CT roles before consuming qualifications.
    with pytest.raises(ValueError,match='Identical CT'):
        freeze(d,ctx.get('base_membership_bytes'),e,family='invented-only')


@pytest.mark.parametrize('fault',['receipt','plan','inputs','member_omission','extra_member','code','transition'])
def test_disk_adapter_requires_independent_purpose_pins(monkeypatch,fault):
    import scripts.diagnostics.freeze_segmenter_cohort as disk
    plan=dict(code_pins={},transition_sha256='0'*64)
    files={'inputs.json':b'inputs','derived.json':b'derived','plan.json':canonical(plan),'publication.json':b'publication'}
    files['receipt.json']=canonical(dict(files={n:dict(bytes=len(b),sha256=digest(b)) for n,b in files.items()}))
    monkeypatch.setattr(disk,'PURPOSE_RECEIPT',digest(files['receipt.json']))
    monkeypatch.setattr(disk,'PURPOSE_PLAN',digest(files['plan.json']))
    monkeypatch.setattr(disk,'PURPOSE_CODES',content_hash({}))
    def verified(payload,input_pin,manifest_pin,codes):
        assert input_pin==disk.PURPOSE_INPUT and manifest_pin==disk.PURPOSE_MANIFEST
        assert codes=={}
        if payload['inputs.json']!=b'inputs':raise ValueError('changed inputs')
        return dict(transition={})
    monkeypatch.setattr(disk.purpose,'validate_files',verified)
    if fault in ('receipt','plan','inputs'):files[fault+'.json']+=b'changed'
    if fault=='member_omission':files.pop('publication.json')
    if fault=='extra_member':files['extra']=b'new'
    if fault=='code':monkeypatch.setattr(disk,'PURPOSE_CODES','f'*64)
    # Untampered synthetic payload still has an independently rejected transition.
    with pytest.raises(ValueError):disk.replay_purpose(files)
