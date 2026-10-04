"""Pure frozen-membership segmenter proposals/resolution; no disk registry or array loader."""
from copy import deepcopy
from src.data.manifest_records import validate_schema
from src.data.cohort_records_v3 import validate_cohort as validate_protection
from src.data.manifest_records_v3 import manifest_validation_session
from src.data.segmenter_qualification_v1 import PURPOSES, validate_qualification, POLICY_SHA256
from src.data.source_inventory_records import content_hash, require, verify_pin, unique


def reference(record, key):
    return dict(id=record[key],sha256=content_hash(record))


def qualification_context(context):
    return {k:context[k] for k in ('manifest','trusted_manifest_sha256','trusted_policy_sha256',
        'evidence_by_sha256','trusted_evidence_sha256')} | dict(base_membership_bytes=context.get('base_membership_bytes'))


def _members(study_ids, purpose, parent_id, context):
    require(purpose in PURPOSES and context['trusted_policy_sha256'] == POLICY_SHA256, 'Unsupported purpose/policy')
    role = PURPOSES[purpose][0]
    require(bool(study_ids) and len(study_ids) == len(set(study_ids)), 'Nonempty unique requested membership required')
    require(parent_id in context['cohorts_by_id'] and parent_id in context['trusted_cohort_sha256'], 'Independent protection parent required')
    parent = context['cohorts_by_id'][parent_id]
    verify_pin(parent, context['trusted_cohort_sha256'][parent_id])
    require(parent['capability'] == 'protection_only' and parent['purpose'] is None and parent['protected_role'] == role,
            'Only original matching-role protection root is allowed')
    old_context = {k:context[k] for k in ('manifest','trusted_manifest_sha256','cohorts_by_id','trusted_cohort_sha256',
        'evidence_by_sha256','trusted_evidence_sha256','trusted_policy_sha256')}
    validate_protection(parent,qualifications_by_id={},trusted_qualification_sha256={},
        base_membership_bytes=context.get('base_membership_bytes'),**old_context)
    original = {r['study_id']:r for r in parent['members']}
    qs = context['qualifications_by_id']; pins = context['trusted_qualification_sha256']; members=[]
    for sid in sorted(study_ids):
        require(sid in original, 'Member outside original protected parent')
        matches=[q for q in qs.values() if q['study_id'] == sid and q['purpose'] == purpose]
        require(len(matches) == 1, 'Exactly one selected purpose qualification required')
        q=matches[0]; qid=q['qualification_id']
        require(qid in pins and qs.get(qid) == q, 'Independent qualification registry pin required')
        outcome=validate_qualification(q,trusted_qualification_sha256=pins[qid],**qualification_context(context))
        require(outcome == 'qualified' and q['protected_role'] == role, 'Held/excluded or wrong-role member cannot be consumed')
        p=original[sid]
        members.append(dict(study_id=sid,subject_id=p['subject_id'],protection_group_id=p['protection_group_id'],
            protected_role=role,qualification=reference(q,'qualification_id'),
            pancreas_annotation_id=q['pancreas_annotation_id'],lesion_annotation_id=q['lesion_annotation_id'],
            lesion_target_state=q['lesion_target_state']))
    return members,parent


def build_cohort(*, name, study_ids, requested_count, purpose, parent_id, context):
    require(isinstance(name,str) and name and type(requested_count) is int and requested_count == len(study_ids),
            'Exact requested membership required; no refill/shortage')
    with manifest_validation_session():
        members,parent=_members(study_ids,purpose,parent_id,context)
    record=dict(schema_version='1.0.0',component='segmenter-cohort-v1',name=name,
        evidence_domain=context['manifest']['evidence_domain'],state='validated_in_memory',purpose=purpose,
        protected_role=PURPOSES[purpose][0],manifest=reference(context['manifest'],'manifest_id'),
        protection_parent=reference(parent,'cohort_id'),members=members,
        definition=dict(selection_method='fixed_membership',requested_count=requested_count,shortage_policy='fail'))
    record['cohort_id']='segmenter-cohort:'+content_hash(record)
    validate_schema('segmenter-cohort-v1',record)
    return record


def checked_members(record, *, trusted_record_sha256, operation, **context):
    verify_pin(record,trusted_record_sha256); validate_schema('segmenter-cohort-v1',record)
    require(operation in ('optimizer','evaluator') and record['protected_role'] == {'optimizer':'train','evaluator':'validation'}[operation],
            'Explicit consumer operation/role mismatch')
    expected=build_cohort(name=record['name'],study_ids=[r['study_id'] for r in record['members']],
        requested_count=record['definition']['requested_count'],purpose=record['purpose'],
        parent_id=record['protection_parent']['id'],context=context)
    require(record == expected, 'Stale cohort identity, annotation, status or ancestry')
    manifest=context['manifest']; annotations={a['annotation_id']:a for a in manifest['annotations']}
    studies={s['study_id']:s for s in manifest['studies']}; result=[]
    for m in record['members']:
        s=studies[m['study_id']]
        result.append(dict(study_id=m['study_id'],subject_id=m['subject_id'],protected_role=m['protected_role'],
            purpose=record['purpose'],evidence_domain=record['evidence_domain'],operation=operation,
            image=deepcopy(s['image']),pancreas=deepcopy(annotations[m['pancreas_annotation_id']]['file']),
            lesion=deepcopy(annotations[m['lesion_annotation_id']]['file']),geometry=deepcopy(s['geometry']),
            qualification=deepcopy(m['qualification']),lesion_target_state=m['lesion_target_state'],
            roi_source='pancreas_only',class_precedence='lesion_over_pancreas',scope='visible_source_references'))
    return result


def validate_pair(train, validation, *, trusted_train_sha256, trusted_validation_sha256, **context):
    a=checked_members(train,trusted_record_sha256=trusted_train_sha256,operation='optimizer',**context)
    b=checked_members(validation,trusted_record_sha256=trusted_validation_sha256,operation='evaluator',**context)
    for key in ('study_id','subject_id'):
        require(not {r[key] for r in a} & {r[key] for r in b}, 'Protected train/validation overlap')
    require(not {r['image']['content_sha256'] for r in a} & {r['image']['content_sha256'] for r in b}, 'Exact image leakage across roles')
    return dict(train_count=len(a),validation_count=len(b),state='validated_in_memory')
