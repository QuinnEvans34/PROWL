"""Purpose qualification from independently reviewed evidence, not a source auditor.

All evidence/check receipts are caller-supplied bytes with independently supplied review
pins. This module proves bindings and rule consistency; it cannot prove a reviewer truthful.
No raw reads, issue resolution, publication or training permission outside this pure slice.
"""
from copy import deepcopy
import json
import math

from src.data.annotation_contract_v2 import validate_approved_binary_lineage
from src.data.manifest_records import canonical, digest, validate_schema
from src.data.manifest_records_v3 import verified_context
from src.data.source_inventory_records import content_hash, require, unique, verify_pin

CHECKS = ('geometry', 'mapping_lineage', 'permitted_use', 'source_readiness', 'target')
POLICY = dict(schema_version='1.0.0', purpose='pancreas_present_localizer',
              component='purpose-qualification-v1', checks=list(CHECKS),
              unresolved_issue_policy='deny_except_information_DIFFICULTY_OBSERVATION',
              target='pancreas', nonempty='first_pancreas_present_smoke_only')
POLICY_SHA256 = content_hash(POLICY)


def context_bindings(context):
    return {k:content_hash(context[k]) for k in ('snapshot','subject','study','annotation','issues')}


def _identity(record):
    return 'qualification:' + content_hash({k:v for k,v in record.items() if k != 'qualification_id'})


def _evidence(sha, evidence_by_sha256, trusted_evidence_sha256):
    require(sha in trusted_evidence_sha256, 'Evidence is not independently reviewed')
    data = evidence_by_sha256.get(sha)
    require(isinstance(data, bytes) and digest(data) == sha, 'Missing or changed evidence bytes')
    return data


def _assess(context, checks, evidence_by_sha256, trusted_evidence_sha256):
    indexed = unique(checks, 'name')
    require(set(indexed) == set(CHECKS), 'Exact qualification check inventory required')
    bindings = context_bindings(context)
    for name, check in indexed.items():
        receipt = json.loads(_evidence(check['evidence_sha256'], evidence_by_sha256, trusted_evidence_sha256))
        require(receipt == dict(schema_version='1.0.0',check=name,bindings=bindings,
                                policy_sha256=POLICY_SHA256,result=check['result']),
                'Check receipt has wrong dependency, purpose policy or result')
    annotation, study, subject = (context[k] for k in ('annotation','study','subject'))
    # All applicable unknown issues block. Documented difficulty is the sole information-only rule.
    blocking = [i for i in context['issues'] if not (i['rule_code']=='DIFFICULTY_OBSERVATION'
                and i['severity']=='information' and i['disposition']=='retain')]
    excluded = (any(c['result']=='exclude' for c in checks) or
                any(i['disposition']=='exclude' for i in blocking) or
                any(r['status']=='excluded' for r in (subject, study, annotation)))
    held = (bool(blocking) or any(c['result']!='pass' for c in checks)
            or subject['status'] != 'reconciled' or study['status'] not in ('reconciled','eligible')
            or annotation['status'] != 'eligible')
    if excluded: return 'excluded'
    if held: return 'held'
    require(annotation['structure']=='pancreas' and 'training_target' in annotation['allowed_uses'],
            'Affirmative pancreas target use required')
    require(study['source_partition']=='publisher_train', 'Publisher test cannot qualify for training')
    geometry = study['geometry']
    require(geometry is not None and len(geometry['shape_xyz'])==3 and len(geometry['spacing_mm_xyz'])==3,
            'Qualified geometry required')
    affine = geometry['affine_ras']
    require(all(math.isfinite(v) for v in affine) and affine[12:] == [0,0,0,1], 'Invalid affine')
    a,b,c,_,d,e,f,_,g,h,i,*_ = affine
    require(abs(a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g))>0, 'Singular affine')
    snapshot = context['snapshot']
    for kind, ref in [('ct',study['image']),('pancreas',annotation['file'])]:
        candidates = [r for r in snapshot['observed_files'] if r['study_id']==study['study_id'] and r['kind']==kind]
        require(len(candidates)==1, 'Consumed file absent from inventory')
        row = candidates[0]
        require(row['state']=='present' and row['sha256']==ref['content_sha256'] and
                row['bytes']==ref['bytes'] and row['uri']==ref['uri'] and ref['root_alias']==snapshot['root_alias'],
                'Consumed file identity differs from source inventory')
    mapping = annotation['label_encoding']['mapping']
    require(mapping is not None and mapping['canonical_foreground']==1, 'Binary pancreas mapping required')
    approval = mapping['approval_file']
    implementation = _evidence(mapping['policy_sha256'], evidence_by_sha256, trusted_evidence_sha256)
    approval_bytes = _evidence(approval['content_sha256'], evidence_by_sha256, trusted_evidence_sha256)
    validate_approved_binary_lineage(annotation, approval_bytes=approval_bytes, implementation_bytes=implementation,
        trusted_approval_sha256=approval['content_sha256'], trusted_implementation_sha256=mapping['policy_sha256'])
    for ref in [annotation['label_encoding']['audit_file'], *annotation['provenance']['evidence_files'],
                annotation['provenance']['allowed_use_decision_file']]:
        require(ref is not None, 'Required annotation evidence absent')
        require(len(_evidence(ref['content_sha256'], evidence_by_sha256, trusted_evidence_sha256))==ref['bytes'],
                'Evidence length differs from reference')
    enc = annotation['label_encoding']
    require(enc['voxel_count'] == math.prod(geometry['shape_xyz']), 'Mask audit/grid voxel count differs')
    values = [r['value'] for r in enc['value_counts']]
    if enc['values_basis']=='stored':
        values = [v*enc['effective_scaling']['slope']+enc['effective_scaling']['intercept'] for v in values]
    require(any(abs(v-1)<=1e-6 for v in values), 'Initial pancreas-present smoke requires foreground')
    return 'qualified'


def build_qualification(*, manifest, study_id, annotation_id, checks, trusted_manifest_sha256,
                        trusted_policy_sha256, evidence_by_sha256, trusted_evidence_sha256,
                        base_membership_bytes=None):
    require(trusted_policy_sha256 == POLICY_SHA256 == manifest['qualification_policy_sha256'],
            'Unsupported or unreviewed qualification policy')
    context = verified_context(manifest,study_id,annotation_id,
        trusted_manifest_sha256=trusted_manifest_sha256,base_membership_bytes=base_membership_bytes)
    record = dict(schema_version='1.0.0',study_id=study_id,annotation_id=annotation_id,
                  purpose=POLICY['purpose'],policy_sha256=POLICY_SHA256,bindings=context_bindings(context),
                  checks=deepcopy(sorted(checks,key=lambda c:c['name'])))
    # Schema check before processing potentially malformed check data.
    record.update(outcome='held',qualification_id='qualification:'+'0'*64)
    validate_schema('purpose-qualification',record)
    record['outcome'] = _assess(context,record['checks'],evidence_by_sha256,trusted_evidence_sha256)
    record['qualification_id'] = _identity(record)
    return record


def validate_qualification(record, *, trusted_qualification_sha256, **kwargs):
    verify_pin(record, trusted_qualification_sha256)
    validate_schema('purpose-qualification',record)
    require(record['qualification_id']==_identity(record), 'Stale qualification identity')
    expected = build_qualification(study_id=record['study_id'],annotation_id=record['annotation_id'],
                                  checks=record['checks'],**kwargs)
    require(record==expected, 'Qualification outcome/dependencies changed')
    return record['outcome']
