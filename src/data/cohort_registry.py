"""S4 frozen cohort bundle: exact S3 dependency replay plus protected ancestry.

Resolution returns verified descriptors, never raw arrays or a source-root activation.
A separately supplied current manifest pin is mandatory; old frozen membership does not
waive newly held/revoked inputs. Publication uses the shared artifact store.
"""
import json
from copy import deepcopy

from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import content_hash, require
from src.data.localizer_qualification_records import migrate_context
from src.data.qualification_transition import validate_transition
from src.data.purpose_qualification import POLICY_SHA256, validate_qualification
from src.data.cohort_records import build_cohort, checked_members, validate_cohort

ROLES=('train','validation','test')
FAMILY='pants-localizer-protected-v1'
COHORT_ID='cohort:pants-localizer-smoke-0001:v1'
MEMBERS=['pants:study:PanTS_00000003','pants:study:PanTS_00000026']


def qualification_context(files,*,trusted_s3_receipt_sha256,current_manifest_sha256):
    require(digest(files['s3-verification.json'])==trusted_s3_receipt_sha256, 'S3 receipt pin mismatch')
    receipt=json.loads(files['s3-verification.json'])
    require(receipt['status']=='s3_qualification_complete_not_cohort_publication', 'Incomplete S3 evidence')
    for n,pin in receipt['files'].items():
        require(digest(files['s3-'+n])==pin, 'Changed S3 dependency')
    read=lambda n:json.loads(files['s3-'+n+'.json'])
    manifests=read('manifests');qualifications=read('qualifications');transitions=read('transitions')
    require(len(manifests)==4 and len(qualifications)==len(transitions)==3, 'Incomplete qualification history')
    manifest=manifests[-1]
    require(content_hash(manifest)==current_manifest_sha256, 'Current authorization/manifest differs; requalification required')
    bases={r:v.encode() for r,v in read('membership').items()}
    evidence={sha:v.encode() for sha,v in read('evidence').items()}
    expected=migrate_context(prior=read('history'),snapshot=manifests[0]['snapshots'][0],
        protection=manifests[0]['protection'],base_membership_bytes=bases)
    require(expected==manifests[0], 'Source migration changed or omitted holds')
    common=dict(trusted_policy_sha256=POLICY_SHA256,evidence_by_sha256=evidence,
                trusted_evidence_sha256=set(evidence),base_membership_bytes=bases)
    for i,(q,t) in enumerate(zip(qualifications,transitions)):
        validate_transition(t,trusted_transition_sha256=content_hash(t),prior_manifest=manifests[i],
            successor_manifest=manifests[i+1],study_id=t['study_id'],prior_annotation_id=t['prior_annotation_id'],
            successor_annotation_id=t['successor_annotation_id'],qualification=q,
            trusted_prior_manifest_sha256=content_hash(manifests[i]),
            trusted_successor_manifest_sha256=content_hash(manifests[i+1]),trusted_qualification_sha256=content_hash(q),**common)
        require(validate_qualification(q,trusted_qualification_sha256=content_hash(q),manifest=manifest,
            trusted_manifest_sha256=current_manifest_sha256,**common)=='qualified', 'Nonpositive qualification')
    return dict(manifest=manifest,trusted_manifest_sha256=current_manifest_sha256,
        qualifications_by_id={q['qualification_id']:q for q in qualifications},
        trusted_qualification_sha256={q['qualification_id']:content_hash(q) for q in qualifications},
        cohorts_by_id={},trusted_cohort_sha256={},**common)


def add_cohorts(ctx):
    for role in ROLES:
        ids=[p['study_id'] for p in ctx['manifest']['protection'] if p['protected_role']==role]
        parent=build_cohort(cohort_id=f'cohort:pants-base-{role}:v1',cohort_family_id=FAMILY,
            capability='protection_only',protected_role=role,study_ids=ids,requested_count=len(ids),parent_ids=[],context=ctx)
        ctx['cohorts_by_id'][parent['cohort_id']]=parent
        ctx['trusted_cohort_sha256'][parent['cohort_id']]=content_hash(parent)
    child=build_cohort(cohort_id=COHORT_ID,cohort_family_id=FAMILY,capability='executable',protected_role='train',
        study_ids=MEMBERS,requested_count=2,parent_ids=['cohort:pants-base-train:v1'],context=ctx)
    return child


def validate_bundle(files,*,trusted_s3_receipt_sha256,current_manifest_sha256):
    ctx=qualification_context(files,trusted_s3_receipt_sha256=trusted_s3_receipt_sha256,
                              current_manifest_sha256=current_manifest_sha256)
    parents=json.loads(files['parents.json']);child=json.loads(files['cohort.json'])
    require(len(parents)==3 and {p['protected_role'] for p in parents}==set(ROLES), 'Complete protection parents required')
    ctx['cohorts_by_id']={p['cohort_id']:p for p in parents}
    require(len(ctx['cohorts_by_id'])==3, 'Duplicate parent identity')
    ctx['trusted_cohort_sha256']={p['cohort_id']:content_hash(p) for p in parents}
    for parent in parents:
        require(parent['capability']=='protection_only', 'Invalid protection parent')
        validate_cohort(parent,**ctx)
    require(child['cohort_id']==COHORT_ID and child['cohort_family_id']==FAMILY, 'Unexpected frozen identity')
    members=checked_members(child,trusted_record_sha256=content_hash(child),**ctx)
    require([m['study_id'] for m in members]==MEMBERS, 'Fixed membership changed; no refill permitted')
    selection=json.loads(files['selection.json'])
    expected=dict(method='ascending_qualified_id_from_retained_five_case_pool',requested_count=2,
        selected=MEMBERS,candidate_pool=[f'pants:study:PanTS_{n:08}' for n in [3,26,31,78,266]],
        qualified_unselected=['pants:study:PanTS_00000031'],shortage_policy='fail',
        limitation='source-positive and flagged convenience sample; no generalization claim')
    require(selection==expected, 'Selection report changed')
    require(set(files)=={'s3-verification.json',*[f's3-{n}' for n in json.loads(files['s3-verification.json'])['files']],
                        'parents.json','cohort.json','selection.json'}, 'Unexpected bundle members')
    return dict(cohort_id=COHORT_ID,study_ids=MEMBERS,protected_counts={p['protected_role']:len(p['members']) for p in parents},
                manifest_sha256=current_manifest_sha256,history_transitions=3,remaining_active_holds=len(ctx['manifest']['issues']))


def build_bundle(s3files,*,trusted_s3_receipt_sha256,current_manifest_sha256):
    files={'s3-'+n:v for n,v in s3files.items()}
    ctx=qualification_context(files,trusted_s3_receipt_sha256=trusted_s3_receipt_sha256,current_manifest_sha256=current_manifest_sha256)
    child=add_cohorts(ctx)
    files.update({'cohort.json':canonical(child),'parents.json':canonical(list(ctx['cohorts_by_id'].values())),
        'selection.json':canonical(dict(method='ascending_qualified_id_from_retained_five_case_pool',requested_count=2,
            selected=MEMBERS,candidate_pool=[f'pants:study:PanTS_{n:08}' for n in [3,26,31,78,266]],
            qualified_unselected=['pants:study:PanTS_00000031'],shortage_policy='fail',
            limitation='source-positive and flagged convenience sample; no generalization claim'))})
    return files


def resolve_inputs(store,*,receipt_sha256,trusted_s3_receipt_sha256,current_manifest_sha256):
    def validate(files):return validate_bundle(files,trusted_s3_receipt_sha256=trusted_s3_receipt_sha256,
                                               current_manifest_sha256=current_manifest_sha256)
    files,receipt=store.resolve(COHORT_ID,receipt_sha256=receipt_sha256,validate=validate)
    manifest=json.loads(files['s3-manifests.json'])[-1];child=json.loads(files['cohort.json'])
    descriptors=[]
    for member in child['members']:
        study=next(s for s in manifest['studies'] if s['study_id']==member['study_id'])
        annotation=next(a for a in manifest['annotations'] if a['annotation_id']==member['annotation']['id'])
        descriptors.append(deepcopy(dict(study_id=study['study_id'],image=study['image'],target=annotation['file'],
            geometry=study['geometry'],mapping=annotation['label_encoding']['mapping'],
            cohort_id=COHORT_ID,completion_sha256=receipt_sha256,manifest_sha256=current_manifest_sha256)))
    return descriptors
