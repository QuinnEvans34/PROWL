from copy import deepcopy
import pytest
from segmenter_fixtures import fixture,qualify,cohort,TRAIN
from src.data.segmenter_cohort_v1 import checked_members,build_cohort,validate_pair
from src.data.source_inventory_records import content_hash


def test_role_safe_three_input_descriptors_and_pair():
    _,ctx=fixture();qualify(ctx);qualify(ctx,index=2);a=cohort(ctx);b=cohort(ctx,index=2)
    r=checked_members(a,trusted_record_sha256=content_hash(a),operation='optimizer',**ctx)[0]
    assert set(['image','pancreas','lesion'])<=set(r) and r['roi_source']=='pancreas_only'
    assert validate_pair(a,b,trusted_train_sha256=content_hash(a),trusted_validation_sha256=content_hash(b),**ctx)['validation_count']==1
    with pytest.raises(ValueError,match='operation'):checked_members(a,trusted_record_sha256=content_hash(a),operation='evaluator',**ctx)
    with pytest.raises(TypeError):checked_members(a,trusted_record_sha256=content_hash(a),**ctx)


@pytest.mark.parametrize('field',['qualification','pancreas_annotation_id','lesion_target_state','protection_parent','cohort_id','evidence_domain'])
def test_cohort_tampering_even_when_rehashed_rejected(field):
    _,ctx=fixture();qualify(ctx);c=cohort(ctx);bad=deepcopy(c)
    if field in ['qualification','pancreas_annotation_id','lesion_target_state']:bad['members'][0][field]={'id':'fake','sha256':'0'*64} if field=='qualification' else 'fake'
    elif field=='protection_parent':bad[field]['sha256']='0'*64
    elif field=='cohort_id':bad[field]='segmenter-cohort:'+'0'*64
    else:bad[field]='retained_source'
    with pytest.raises(Exception):checked_members(bad,trusted_record_sha256=content_hash(bad),operation='optimizer',**ctx)


def test_hold_cannot_enter_and_no_refill_or_missing_members():
    _,ctx=fixture();qualify(ctx,index=1)
    with pytest.raises(ValueError,match='Held/excluded'):cohort(ctx,index=1)
    _,ctx=fixture();qualify(ctx);c=cohort(ctx)
    args=dict(name='new',purpose=TRAIN,parent_id=c['protection_parent']['id'],context=ctx)
    sid=ctx['manifest']['studies'][0]['study_id']
    with pytest.raises(ValueError,match='refill'):build_cohort(study_ids=[sid],requested_count=2,**args)
    with pytest.raises(ValueError,match='unique'):build_cohort(study_ids=[sid,sid],requested_count=2,**args)
    with pytest.raises(ValueError,match='outside'):build_cohort(study_ids=[ctx['manifest']['studies'][2]['study_id']],requested_count=1,**args)


def test_missing_review_pin_and_changed_evidence_rechecked_on_resolution():
    _,ctx=fixture();q=qualify(ctx);c=cohort(ctx)
    ctx['trusted_qualification_sha256'].clear()
    with pytest.raises(ValueError,match='pin'):checked_members(c,trusted_record_sha256=content_hash(c),operation='optimizer',**ctx)
    ctx['trusted_qualification_sha256'][q['qualification_id']]=content_hash(q)
    ctx['evidence_by_sha256'][q['checks'][0]['evidence_sha256']]=b'changed'
    with pytest.raises(ValueError,match='evidence'):checked_members(c,trusted_record_sha256=content_hash(c),operation='optimizer',**ctx)
