"""Pure protected/executable cohort records. NOT a frozen disk registry or model loader."""
from copy import deepcopy

from src.data.manifest_records import validate_schema
from src.data.manifest_records_v3 import validate_manifest_v3
from src.data.purpose_qualification_v2 import PURPOSES, validate_qualification
ROLE_PURPOSE = {role:purpose for purpose,(role,use) in PURPOSES.items()}
from src.data.source_inventory_records import content_hash, require, unique, verify_pin


def reference(record, key):
    return dict(id=record[key], sha256=content_hash(record))


def _derivation(record):
    return content_hash({k:v for k,v in record.items() if k != 'derivation_sha256'})


def _structure(record, manifest, cohorts_by_id, trusted_cohort_sha256, active=None):
    active = set() if active is None else active
    validate_schema('cohort-v3',record)
    require(record['derivation_sha256']==_derivation(record), 'Stale cohort identity')
    cid = record['cohort_id']
    require(cid not in active, 'Cyclic cohort ancestry')
    active = active | {cid}
    require(record['manifest']==reference(manifest,'manifest_id'), 'Cohort manifest pin mismatch')
    members = unique(record['members'],'study_id')
    require(list(members)==sorted(members) and bool(members), 'Canonical nonempty membership required')
    require(record['definition']['requested_count']==len(members), 'Requested membership shortage')
    require(record['profile']==dict(study_count=len(members),
            subject_count=len({m['subject_id'] for m in members.values()})), 'Profile mismatch')
    protection = {r['study_id']:r for r in manifest['protection']}
    for member in members.values():
        validate_schema('cohort-member-v2',member)
        require(member['study_id'] in protection, 'Member absent from protected family')
        original = protection[member['study_id']]
        require(all(member[k]==original[k] for k in ('subject_id','protected_role','protection_group_id')),
                'Member original role/group changed')
        require(member['protected_role']==record['protected_role'], 'Cohort role mismatch')
    parents = unique(record['parents'],'id')
    ancestors = {}
    for ref in parents.values():
        require(ref['id'] in cohorts_by_id and ref['id'] in trusted_cohort_sha256, 'Unregistered ancestor')
        parent = cohorts_by_id[ref['id']]
        require(parent['cohort_id']==ref['id'], 'Registry identity mismatch')
        verify_pin(parent, trusted_cohort_sha256[ref['id']])
        require(ref==reference(parent,'cohort_id'), 'Parent content changed')
        require(parent['cohort_family_id']==record['cohort_family_id'] and
                parent['protected_role']==record['protected_role'], 'Wrong ancestor family/role')
        _structure(parent,manifest,cohorts_by_id,trusted_cohort_sha256,active)
        ancestors[ref['id']] = ref
        for ancestor in parent['ancestors']:
            require(ancestor['id'] not in ancestors or ancestors[ancestor['id']]==ancestor,
                    'Conflicting ancestor identity')
            ancestors[ancestor['id']] = ancestor
        parent_members = {r['study_id']:r for r in parent['members']}
        require(set(members)<=set(parent_members), 'Child outside direct parent')
    require(record['ancestors']==[ancestors[k] for k in sorted(ancestors)], 'Incomplete ancestor graph')
    if record['capability']=='protection_only':
        require(not parents and record['purpose'] is None, 'Protection parent must be a root')
        require(set(members)=={k for k,v in protection.items() if v['protected_role']==record['protected_role']},
                'Protected membership omitted or changed')
        require(all(m['target'] is None and m['annotation'] is None and m['qualification'] is None
                    for m in members.values()), 'Protection membership cannot claim target permission')
    else:
        require(len(parents)==1 and record['protected_role'] in ROLE_PURPOSE and record['purpose']==ROLE_PURPOSE[record['protected_role']],
                'Executable cohort needs matching role ancestry and supported purpose')
        for member in members.values():
            require(member['target']=='pancreas' and member['annotation'] is not None
                    and member['qualification'] is not None, 'Positive target qualification required')
    return members


def validate_cohort(record, *, manifest, trusted_manifest_sha256, cohorts_by_id,
                    trusted_cohort_sha256, qualifications_by_id, trusted_qualification_sha256,
                    evidence_by_sha256, trusted_evidence_sha256, trusted_policy_sha256,
                    base_membership_bytes=None):
    verify_pin(manifest,trusted_manifest_sha256)
    validate_manifest_v3(manifest,base_membership_bytes=base_membership_bytes)
    members = _structure(record,manifest,cohorts_by_id,trusted_cohort_sha256)
    protection = {p['study_id']:p for p in manifest['protection']}
    content_roles = {}
    for study in manifest['studies']:
        role = protection[study['study_id']]['protected_role']
        pin = study['image']['content_sha256']
        require(content_roles.setdefault(pin, role)==role, 'Identical CT content crosses protected roles')
    # Recheck qualification for executable ancestors too, not only the selected child.
    records = [record] + [cohorts_by_id[r['id']] for r in record['ancestors']]
    annotations = {a['annotation_id']:a for a in manifest['annotations']}
    for cohort in records:
        if cohort['capability']!='executable': continue
        for member in cohort['members']:
            ref = member['qualification']
            require(ref['id'] in qualifications_by_id and ref['id'] in trusted_qualification_sha256,
                    'Independent qualification pin required')
            q = qualifications_by_id[ref['id']]
            require(ref==reference(q,'qualification_id') and q['study_id']==member['study_id'],
                    'Wrong qualification member/pin')
            require(q['purpose']==cohort['purpose'] and q['protected_role']==cohort['protected_role'], 'Qualification purpose/role differs')
            a = annotations.get(q['annotation_id'])
            require(a is not None and member['annotation']==reference(a,'annotation_id'),
                    'Wrong annotation reference')
            outcome = validate_qualification(q,trusted_qualification_sha256=trusted_qualification_sha256[ref['id']],
                manifest=manifest,trusted_manifest_sha256=trusted_manifest_sha256,
                trusted_policy_sha256=trusted_policy_sha256,evidence_by_sha256=evidence_by_sha256,
                trusted_evidence_sha256=trusted_evidence_sha256,base_membership_bytes=base_membership_bytes)
            require(outcome=='qualified', 'Held/excluded member cannot enter executable cohort')
    return members


def build_cohort(*, cohort_id, cohort_family_id, capability, protected_role, study_ids,
                 requested_count, parent_ids, context):
    """Build a fixed-membership proposal and validate it; never silently filter/refill.

    context is supplied by an independently trusted caller. No function derives its
    trust pins from the proposed cohort/qualification. Returned state is in-memory only.
    """
    require(len(study_ids)==len(set(study_ids)), 'Duplicate requested study')
    require(len(parent_ids)==len(set(parent_ids)), 'Duplicate requested parent')
    manifest=context['manifest']
    protection={r['study_id']:r for r in manifest['protection']}
    members=[]
    for sid in sorted(study_ids):
        require(sid in protection, 'Unknown protected member')
        p=protection[sid]
        member=dict(schema_version='2.0.0',study_id=sid,subject_id=p['subject_id'],
                    protected_role=p['protected_role'],protection_group_id=p['protection_group_id'],
                    target=None,annotation=None,qualification=None)
        if capability=='executable':
            matches=[q for q in context['qualifications_by_id'].values() if q['study_id']==sid]
            require(len(matches)==1, 'Exactly one selected qualification per member required')
            q=matches[0]
            annotation=next((a for a in manifest['annotations'] if a['annotation_id']==q['annotation_id']),None)
            require(annotation is not None, 'Missing annotation')
            member.update(target='pancreas',annotation=reference(annotation,'annotation_id'),
                          qualification=reference(q,'qualification_id'))
        members.append(member)
    parents=[];ancestors={}
    for pid in sorted(parent_ids):
        require(pid in context['cohorts_by_id'], 'Missing parent')
        p=context['cohorts_by_id'][pid];ref=reference(p,'cohort_id')
        parents.append(ref);ancestors[pid]=ref
        for a in p['ancestors']: ancestors[a['id']]=a
    result=dict(schema_version='3.0.0',cohort_id=cohort_id,cohort_family_id=cohort_family_id,
        capability=capability,protected_role=protected_role,
        purpose=ROLE_PURPOSE.get(protected_role) if capability=='executable' else None,
        manifest=reference(manifest,'manifest_id'),parents=parents,
        ancestors=[ancestors[k] for k in sorted(ancestors)],members=members,
        definition=dict(selection_method='fixed_membership',requested_count=requested_count,shortage_policy='fail'),
        profile=dict(study_count=len(members),subject_count=len({m['subject_id'] for m in members})),
        state='validated_in_memory')
    result['derivation_sha256']=_derivation(result)
    validate_cohort(result,**context)
    return deepcopy(result)


def checked_members(record, *, trusted_record_sha256, operation, **context):
    """Pure record consumer for tests; no arrays, root resolution or disk publication."""
    verify_pin(record,trusted_record_sha256)
    require(operation in ('optimizer','evaluator'), 'Explicit consumer operation required')
    require(record['protected_role']=={'optimizer':'train','evaluator':'validation'}[operation], 'Consumer operation/role mismatch')
    require(record['capability']=='executable', 'Protection-only membership is not consumable')
    members=validate_cohort(record,**context)
    return deepcopy(list(members.values()))
