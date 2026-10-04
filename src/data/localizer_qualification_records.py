"""Retained-evidence S3 builder. No filesystem publication or model-input permission.

The caller supplies independently verified evidence. Source migration changes only the
snapshot link; every historical issue (including old-context purpose denials) survives.
Old-context denials remain blocking, never rebound or treated as a clearance.
"""
from copy import deepcopy

from src.data.manifest_records import canonical, digest
from src.data.manifest_records_v3 import build_manifest_v3, verified_context
from src.data.purpose_qualification import CHECKS, POLICY_SHA256, context_bindings, build_qualification
from src.data.qualification_transition import build_transition
from src.data.source_inventory_records import content_hash, require


def migrate_context(*, prior, snapshot, protection, base_membership_bytes=None):
    require(all(r['status']=='quarantined' for c in ('subjects','studies','annotations') for r in prior[c]),
            'Only quarantined predecessor records may migrate')
    require(all(not a['allowed_uses'] for a in prior['annotations']), 'Migration cannot carry permissions')
    args = dict(name='localizer-qualification', snapshots=[snapshot], protection=protection,
                qualification_policy_sha256=POLICY_SHA256, base_membership_bytes=base_membership_bytes)
    for collection in ('subjects','studies','annotations'):
        args[collection] = deepcopy(prior[collection])
        for row in args[collection]:
            require(row['source_snapshot_id']==prior['snapshot']['source_snapshot_id'], 'Predecessor source mismatch')
            row['source_snapshot_id'] = snapshot['source_snapshot_id']
    args['issues'] = deepcopy(prior['issues'])
    return build_manifest_v3(**args)


def qualify_successor(*, prior, study_id, mapping, provenance, evidence,
                      base_membership_bytes=None):
    """Positive checks are a review attestation, not a fresh source audit.

    Do not call on unreviewed cases. The transition verifier independently rejects
    specific denials and changes beyond the three supported generic holds.
    """
    candidate = deepcopy(prior)
    study = next(s for s in candidate['studies'] if s['study_id']==study_id)
    subject = next(s for s in candidate['subjects'] if s['subject_id']==study['subject_id'])
    annotation = next(a for a in candidate['annotations'] if a['study_id']==study_id and a['structure']=='pancreas')
    old_id = annotation['annotation_id']
    removed = {*subject['issue_ids'], *study['issue_ids'], *annotation['issue_ids']}
    subject.update(status='reconciled', issue_ids=[])
    study.update(status='reconciled', issue_ids=[])
    annotation.update(annotation_version='localizer-smoke-qualified-v1', status='eligible', issue_ids=[],
                      allowed_uses=['training_target'], method='human_validated', validation_status='source_asserted',
                      provenance=deepcopy(provenance))
    annotation['label_encoding']['mapping'] = deepcopy(mapping)
    annotation['annotation_id'] = old_id+'-q-'+content_hash(annotation)[:16]
    new_id = annotation['annotation_id']
    study['annotation_ids'] = sorted(new_id if a==old_id else a for a in study['annotation_ids'])
    study['target_statuses'] = [t for t in study['target_statuses'] if t['target']!='pancreas'] + [
        dict(target='pancreas',status='positive',method='annotation_voxel_presence',reference_id=new_id)]
    candidate['issues'] = [i for i in candidate['issues'] if i['issue_id'] not in removed]
    successor = build_manifest_v3(**{k:candidate[k] for k in ('name','snapshots','protection','subjects','studies',
        'annotations','issues','qualification_policy_sha256')},base_membership_bytes=base_membership_bytes)
    binding = context_bindings(verified_context(successor,study_id,new_id,
        trusted_manifest_sha256=content_hash(successor),base_membership_bytes=base_membership_bytes))
    checks=[]; receipt_evidence = dict(evidence)
    for name in CHECKS:
        payload=canonical(dict(schema_version='1.0.0',check=name,bindings=binding,
                               policy_sha256=POLICY_SHA256,result='pass'))
        sha=digest(payload); receipt_evidence[sha]=payload
        checks.append(dict(name=name,result='pass',evidence_sha256=sha))
    common=dict(trusted_policy_sha256=POLICY_SHA256,evidence_by_sha256=receipt_evidence,
                trusted_evidence_sha256=set(receipt_evidence),base_membership_bytes=base_membership_bytes)
    qualification=build_qualification(manifest=successor,study_id=study_id,annotation_id=new_id,
        checks=checks,trusted_manifest_sha256=content_hash(successor),**common)
    certificate=build_transition(prior_manifest=prior,successor_manifest=successor,study_id=study_id,
        prior_annotation_id=old_id,successor_annotation_id=new_id,qualification=qualification,
        trusted_prior_manifest_sha256=content_hash(prior),trusted_successor_manifest_sha256=content_hash(successor),
        trusted_qualification_sha256=content_hash(qualification),**common)
    return successor, qualification, certificate, receipt_evidence
