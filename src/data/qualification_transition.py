"""Narrow pre-publication check for PanTS localizer qualification successors.

A certificate binds independently reviewed old/new manifest pins and revalidates the
positive qualification. It is NOT a publisher, issue mutator, or consumer bypass.
Historical manifests remain authoritative history. Production publication must explicitly
require this check; existing v3 validators/denial helpers retain their original behavior.
"""
from src.data.manifest_records_v3 import verified_context
from src.data.purpose_qualification import validate_qualification
from src.data.source_inventory_records import content_hash, require, verify_pin

SUPPORTED = {'IDENTITY_UNVERIFIED': 'subject', 'STUDY_QUALIFICATION_PENDING': 'study',
             'ANNOTATION_USE_PENDING': 'annotation'}
PURPOSE = 'pancreas_present_localizer'


def _same_except(old, new, fields, description):
    require({k:v for k,v in old.items() if k not in fields} ==
            {k:v for k,v in new.items() if k not in fields}, description + ' changed outside transition scope')


def build_transition(*, prior_manifest, successor_manifest, study_id, prior_annotation_id,
                     successor_annotation_id, qualification, trusted_prior_manifest_sha256,
                     trusted_successor_manifest_sha256, trusted_qualification_sha256,
                     trusted_policy_sha256, evidence_by_sha256, trusted_evidence_sha256,
                     base_membership_bytes=None):
    """Review pins must come from independent retained evidence, never the candidate itself.

    Only the three original generic holds are supported, once each. Specific denials,
    duplicate findings and unknown/new issues cannot be removed through this path.
    The same case, raw files and protected membership must survive the transition.
    Source scope/control accounting must be unchanged; changed source evidence requires
    a separately reviewed source migration before invoking this narrow function.
    """
    before = verified_context(prior_manifest, study_id, prior_annotation_id,
        trusted_manifest_sha256=trusted_prior_manifest_sha256, base_membership_bytes=base_membership_bytes)
    after = verified_context(successor_manifest, study_id, successor_annotation_id,
        trusted_manifest_sha256=trusted_successor_manifest_sha256, base_membership_bytes=base_membership_bytes)
    require(prior_manifest['evidence_domain'] == successor_manifest['evidence_domain'], 'Evidence domain changed')
    require(prior_manifest['protection'] == successor_manifest['protection'] and
            prior_manifest['migration_pins'] == successor_manifest['migration_pins'], 'Protected membership changed')
    require(before['snapshot'] == after['snapshot'], 'Source snapshot changed outside transition scope')
    role = next(p['protected_role'] for p in prior_manifest['protection'] if p['study_id']==study_id)
    require(role == 'train', 'Train-role transition required')
    require(prior_annotation_id != successor_annotation_id, 'New annotation identity required')
    old_issues = before['issues']
    require(len(old_issues)==3 and {i['rule_code'] for i in old_issues}==set(SUPPORTED),
            'Exact three generic holds required; specific/unknown holds cannot be cleared')
    for issue in old_issues:
        require(issue['entity_type']==SUPPORTED[issue['rule_code']] and
                issue['severity']=='blocking' and issue['disposition']=='quarantine', 'Unsupported hold semantics')
    require(not after['issues'], 'Successor still has applicable holds')
    # This certificate may change exactly one subject/study/target and its three holds.
    for collection, key, old_id, new_id in (
            ('subjects','subject_id',before['subject']['subject_id'],after['subject']['subject_id']),
            ('studies','study_id',study_id,study_id),
            ('annotations','annotation_id',prior_annotation_id,successor_annotation_id)):
        require([r for r in prior_manifest[collection] if r[key]!=old_id] ==
                [r for r in successor_manifest[collection] if r[key]!=new_id],
                'Unrelated records changed or omitted')
    require(prior_manifest['snapshots']==successor_manifest['snapshots'], 'Other source snapshots changed')
    removed = {i['issue_id'] for i in old_issues}
    require([i for i in prior_manifest['issues'] if i['issue_id'] not in removed] == successor_manifest['issues'],
            'Unrelated issues changed or omitted')
    expected_targets = [t for t in before['study']['target_statuses'] if t['target']!='pancreas'] + [
        dict(target='pancreas',status='positive',method='annotation_voxel_presence',reference_id=successor_annotation_id)]
    require(sorted(after['study']['target_statuses'],key=lambda t:t['target']) ==
            sorted(expected_targets,key=lambda t:t['target']), 'Target claims changed beyond pancreas presence')
    for kind in ('subject','study','annotation'):
        require(before[kind]['status']=='quarantined', 'Expected quarantined predecessor')
    require(before['annotation']['allowed_uses']==[], 'Predecessor permission differs')
    require(after['annotation']['structure']=='pancreas' and after['annotation']['allowed_uses']==['training_target'],
            'Only pancreas training-target permission is supported')
    require(after['annotation']['validation_status']=='source_asserted' and
            after['annotation']['method']=='human_validated', 'Publisher-protocol assurance required')
    require(after['annotation']['provenance']['scope']=='publisher_protocol', 'Per-file certification is not supported')
    _same_except(before['subject'],after['subject'],{'status','issue_ids'},'Subject')
    _same_except(before['study'],after['study'],{'status','issue_ids','annotation_ids','target_statuses'},'Study')
    # Geometry is intentionally NOT editable here. Unknown-unit CT requires another path.
    require(set(after['study']['annotation_ids']) ==
            (set(before['study']['annotation_ids'])-{prior_annotation_id})|{successor_annotation_id},
            'Other annotation identity changed')
    require(before['annotation']['file']==after['annotation']['file'], 'Raw mask identity changed')
    _same_except(before['annotation'],after['annotation'],
        {'annotation_id','annotation_version','status','issue_ids','allowed_uses','method','validation_status',
         'provenance','label_encoding'},'Annotation')
    _same_except(before['annotation']['label_encoding'],after['annotation']['label_encoding'],{'mapping'},'Encoding evidence')
    require(qualification['study_id']==study_id and qualification['annotation_id']==successor_annotation_id,
            'Qualification belongs to another target')
    outcome = validate_qualification(qualification,
        trusted_qualification_sha256=trusted_qualification_sha256, manifest=successor_manifest,
        trusted_manifest_sha256=trusted_successor_manifest_sha256, trusted_policy_sha256=trusted_policy_sha256,
        evidence_by_sha256=evidence_by_sha256, trusted_evidence_sha256=trusted_evidence_sha256,
        base_membership_bytes=base_membership_bytes)
    require(outcome=='qualified', 'Fully positive qualification required')
    record = dict(schema_version='1.0.0', policy='pants-localizer-generic-holds-v1', purpose=PURPOSE,
        prior_manifest_sha256=trusted_prior_manifest_sha256, successor_manifest_sha256=trusted_successor_manifest_sha256,
        qualification_sha256=trusted_qualification_sha256, study_id=study_id,
        prior_annotation_id=prior_annotation_id, successor_annotation_id=successor_annotation_id,
        superseded_holds=[dict(issue_id=i['issue_id'],sha256=content_hash(i),rule_code=i['rule_code'])
                          for i in sorted(old_issues,key=lambda x:x['issue_id'])],
        identity_assurance='unverified_unique', raw_files_preserved=True, original_membership_preserved=True,
        scope='prepublication_only', production_consumer_enabled=False)
    record['transition_id']='qualification-transition:'+content_hash(record)
    return record


def validate_transition(record, *, trusted_transition_sha256, **kwargs):
    verify_pin(record,trusted_transition_sha256)
    require(record==build_transition(**kwargs), 'Transition certificate or dependencies changed')
    return record
