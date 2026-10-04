"""Pure dual-target qualification; reviewed evidence is supplied, never manufactured here.

No arrays, publication or live permission changes. A reviewed pin proves bytes, not reviewer truth.
"""
from copy import deepcopy
import json
import math
import numpy as np
from src.data.annotation_contract_v2 import validate_approved_binary_lineage
from src.data.manifest_records import canonical, digest, validate_schema
from src.data.manifest_records_v3 import verified_context, manifest_validation_session
from src.data.source_inventory_records import content_hash, require, unique, verify_pin

PURPOSES = {
    'pancreas_lesion_segmenter_training': ('train', 'training_target'),
    'pancreas_lesion_segmenter_validation': ('validation', 'evaluation_reference'),
}
CHECKS = ('geometry', 'mapping_lineage', 'permitted_use', 'source_readiness', 'pancreas_target', 'lesion_target')
POLICY = dict(component='segmenter-qualification-v1', schema_version='1.0.0', purposes=PURPOSES,
    checks=list(CHECKS), targets=['pancreas', 'lesion'], class_precedence='lesion_over_pancreas',
    negative_rule='explicit_reviewed_reference_standard_not_empty_mask',
    issue_rule='deny_except_information_DIFFICULTY_OBSERVATION', target_scope='visible_source_references',
    geometry_affine_atol=1e-5, original_membership='permanent', lesion_inventory='paired_sidecar_v1')
POLICY_SHA256 = content_hash(POLICY)


def context_for(manifest, study_id, pancreas_annotation_id, lesion_annotation_id, *, trusted_manifest_sha256,
                base_membership_bytes=None):
    with manifest_validation_session():
        contexts = {kind: verified_context(manifest, study_id, aid,
            trusted_manifest_sha256=trusted_manifest_sha256, base_membership_bytes=base_membership_bytes)
            for kind, aid in [('pancreas', pancreas_annotation_id), ('lesion', lesion_annotation_id)]}
    require(pancreas_annotation_id != lesion_annotation_id, 'Distinct annotations required')
    require(all(c['annotation']['structure'] == kind for kind, c in contexts.items()), 'Wrong target structure')
    require(contexts['pancreas']['study'] == contexts['lesion']['study'] and
            contexts['pancreas']['snapshot'] == contexts['lesion']['snapshot'], 'Cross-target context mismatch')
    p = contexts['pancreas']
    issues = {i['issue_id']: i for c in contexts.values() for i in c['issues']}
    protection = next(r for r in manifest['protection'] if r['study_id'] == study_id)
    return dict(snapshot=p['snapshot'], subject=p['subject'], study=p['study'], protection=protection,
        annotations={k:c['annotation'] for k,c in contexts.items()}, issues=[issues[k] for k in sorted(issues)])


def context_bindings(context):
    return {k:content_hash(v) for k,v in context.items()}


def evidence(sha, evidence_by_sha256, trusted_evidence_sha256):
    require(sha in trusted_evidence_sha256, 'Evidence is not independently reviewed')
    raw = evidence_by_sha256.get(sha)
    require(isinstance(raw, bytes) and digest(raw) == sha, 'Missing or changed evidence bytes')
    return raw


def _ref(ref, blobs, pins):
    require(ref is not None and len(evidence(ref['content_sha256'], blobs, pins)) == ref['bytes'],
            'Missing/changed evidence reference')


def _foreground(annotation):
    enc = annotation['label_encoding']
    return sum(r['count'] for r in enc['value_counts'] if abs((r['value'] if enc['values_basis'] ==
        'nifti_scaled_semantic' else r['value']*enc['effective_scaling']['slope']+
        enc['effective_scaling']['intercept']) - 1) <= 1e-6)


def _assess(context, checks, purpose, blobs, pins):
    indexed = unique(checks, 'name')
    require(set(indexed) == set(CHECKS), 'Exact qualification checks required')
    receipts = {}
    for name, check in indexed.items():
        require(set(check) == {'name', 'result', 'evidence_sha256'} and check['result'] in ('pass','hold','exclude'),
                'Invalid check shape/result')
        r = json.loads(evidence(check['evidence_sha256'], blobs, pins))
        canonical(r)  # Refuse non-finite values even in unused descriptive details.
        require(set(r) == {'schema_version','component','purpose','check','bindings','policy_sha256','result','details'} and
            all(r[k] == v for k,v in dict(schema_version='1.0.0',component='segmenter-check-v1',purpose=purpose,
                check=name,bindings=context_bindings(context),policy_sha256=POLICY_SHA256,result=check['result']).items()),
            'Check receipt has wrong dependency/purpose/policy/result')
        require(isinstance(r['details'], dict), 'Explicit receipt details required')
        receipts[name] = r
    annotations = context['annotations']; entities = [context['subject'],context['study'],*annotations.values()]
    blocking = [i for i in context['issues'] if not (i['rule_code'] == 'DIFFICULTY_OBSERVATION' and
                i['severity'] == 'information' and i['disposition'] == 'retain')]
    if any(c['result'] == 'exclude' for c in checks) or any(i['disposition'] == 'exclude' for i in blocking) or any(e['status'] == 'excluded' for e in entities):
        return 'excluded', 'unknown'
    if blocking or any(c['result'] != 'pass' for c in checks) or context['subject']['status'] != 'reconciled' or context['study']['status'] not in ('reconciled','eligible') or any(a['status'] != 'eligible' for a in annotations.values()):
        return 'held', 'unknown'
    study = context['study']; snapshot = context['snapshot']; use = PURPOSES[purpose][1]
    require(study['source_partition'] == 'publisher_train', 'Publisher test cannot supply development targets')
    require(all(use in a['allowed_uses'] for a in annotations.values()), 'Affirmative dual-target permission required')
    geometry = study['geometry']; require(geometry is not None, 'Qualified geometry required')
    a = np.asarray(geometry['affine_ras'], float).reshape(4,4)
    spacing = np.linalg.norm(a[:3,:3], axis=0)
    require(np.isfinite(a).all() and np.array_equal(a[3], [0,0,0,1]) and abs(np.linalg.det(a[:3,:3])) > 0 and
            np.allclose(spacing, geometry['spacing_mm_xyz'], atol=1e-5, rtol=0), 'Invalid physical geometry')
    g = receipts['geometry']['details']
    require(set(g) == {'ct_units','source_shape','source_affine','pancreas_shape','pancreas_affine','pancreas_units','lesion_shape','lesion_affine','lesion_units'} and
            g['ct_units'] == 'mm' and g['source_shape'] == geometry['shape_xyz'] and g['source_affine'] == geometry['affine_ras'], 'CT units/grid evidence required')
    for key in ('source_affine','pancreas_affine','lesion_affine'):
        require(isinstance(g[key], list) and len(g[key]) == 16 and all(type(v) in (int,float) and math.isfinite(v) for v in g[key]), 'Flat finite numeric affine required')
    for key in ('source_shape','pancreas_shape','lesion_shape'):
        require(isinstance(g[key], list) and len(g[key]) == 3 and all(type(v) is int and v > 0 for v in g[key]), 'Integer physical shape required')
    for kind in ('pancreas','lesion'):
        require(g[kind+'_shape'] == geometry['shape_xyz'] and g[kind+'_units'] in ('mm','matched_mm_ct_grid') and
                np.allclose(g[kind+'_affine'], geometry['affine_ras'], atol=1e-5, rtol=0), 'Target units/grid differ')
    for kind, ref in [('ct',study['image']), ('pancreas',annotations['pancreas']['file'])]:
        rows = [r for r in snapshot['observed_files'] if r['study_id'] == study['study_id'] and r['kind'] == kind]
        require(len(rows) == 1, 'Exact source inventory required')
        r = rows[0]
        require(r['state'] == 'present' and (r['sha256'],r['bytes'],r['uri'],snapshot['root_alias']) ==
                (ref['content_sha256'],ref['bytes'],ref['uri'],ref['root_alias']), 'Input identity/inventory differs')
    readiness = receipts['source_readiness']['details']
    require(set(readiness) == {'lesion_inventory_sha256'}, 'Separate paired lesion inventory required')
    inventory = json.loads(evidence(readiness['lesion_inventory_sha256'],blobs,pins))
    validate_schema('segmenter-lesion-inventory-v1',inventory)
    require(inventory['component'] == 'segmenter-lesion-inventory-v1' and inventory['state'] == 'present' and
            inventory['study_id'] == study['study_id'] and inventory['source_snapshot_id'] == snapshot['source_snapshot_id'] and
            inventory['source_version_sha256'] == content_hash(snapshot['source_version']) and
            inventory['file'] == annotations['lesion']['file'] and inventory['file']['root_alias'] == snapshot['root_alias'],
            'Lesion inventory source/study/file binding differs')
    for kind, annotation in annotations.items():
        enc = annotation['label_encoding']; mapping = enc['mapping']
        require(mapping is not None and mapping['canonical_foreground'] == {'pancreas':1,'lesion':2}[kind],
                'Explicit three-class mapping required')
        validate_approved_binary_lineage(annotation, approval_bytes=evidence(mapping['approval_file']['content_sha256'],blobs,pins),
            implementation_bytes=evidence(mapping['policy_sha256'],blobs,pins),
            trusted_approval_sha256=mapping['approval_file']['content_sha256'],trusted_implementation_sha256=mapping['policy_sha256'])
        for ref in [enc['audit_file'], *annotation['provenance']['evidence_files'], annotation['provenance']['allowed_use_decision_file']]: _ref(ref,blobs,pins)
        require(enc['voxel_count'] == math.prod(geometry['shape_xyz']), 'Mask audit voxel count/grid differs')
    require(_foreground(annotations['pancreas']) > 0, 'Pancreas-present ROI target required')
    require(receipts['pancreas_target']['details'] == dict(classification='positive',foreground_voxels=_foreground(annotations['pancreas'])), 'Pancreas target receipt differs')
    lesion = annotations['lesion']; n = _foreground(lesion); detail = receipts['lesion_target']['details']
    require(set(detail) == {'classification','foreground_voxels','negative_basis_sha256'} and type(detail['foreground_voxels']) is int and detail['foreground_voxels'] == n,
            'Lesion target count/evidence differs')
    state = detail['classification']
    target = [t for t in study['target_statuses'] if t['target'] in ('lesion',lesion['source_structure'])]
    require(len(target) == 1 and target[0]['reference_id'] == lesion['annotation_id'], 'Explicit lesion target identity required')
    if n:
        require(state == 'positive' and detail['negative_basis_sha256'] is None and target[0]['status'] == 'positive', 'Nonempty visible lesion status differs')
    else:
        require(state == 'verified_negative' and target[0]['status'] == 'negative' and target[0]['method'] == 'reference_standard', 'Empty lesion cannot infer a negative')
        basis = json.loads(evidence(detail['negative_basis_sha256'],blobs,pins))
        require(set(basis) == {'component','purpose','bindings','status','basis'} and basis['component'] == 'segmenter-negative-reference-v1' and
                basis['purpose'] == purpose and basis['bindings'] == context_bindings(context) and
                basis['status'] == 'verified_no_visible_lesion' and isinstance(basis['basis'], str) and bool(basis['basis'].strip()),
                'Explicit case-bound reviewed negative standard required')
    return 'qualified', state


def build_qualification(*, manifest, study_id, pancreas_annotation_id, lesion_annotation_id, checks, purpose,
                        trusted_manifest_sha256, trusted_policy_sha256, evidence_by_sha256, trusted_evidence_sha256,
                        base_membership_bytes=None):
    require(purpose in PURPOSES and trusted_policy_sha256 == POLICY_SHA256 == manifest['qualification_policy_sha256'],
            'Unsupported segmenter purpose/policy')
    context = context_for(manifest,study_id,pancreas_annotation_id,lesion_annotation_id,
        trusted_manifest_sha256=trusted_manifest_sha256,base_membership_bytes=base_membership_bytes)
    require(context['protection']['protected_role'] == PURPOSES[purpose][0], 'Purpose/protected role mismatch')
    outcome, target = _assess(context,checks,purpose,evidence_by_sha256,trusted_evidence_sha256)
    record = dict(schema_version='1.0.0',component='segmenter-qualification-v1',evidence_domain=manifest['evidence_domain'],
        study_id=study_id,pancreas_annotation_id=pancreas_annotation_id,lesion_annotation_id=lesion_annotation_id,
        purpose=purpose,protected_role=PURPOSES[purpose][0],policy_sha256=POLICY_SHA256,bindings=context_bindings(context),
        checks=deepcopy(sorted(checks,key=lambda c:c['name'])),outcome=outcome,lesion_target_state=target)
    record['qualification_id'] = 'segmenter-qualification:' + content_hash(record)
    validate_schema('segmenter-qualification-v1',record)
    return record


def validate_qualification(record, *, trusted_qualification_sha256, **kwargs):
    verify_pin(record,trusted_qualification_sha256); validate_schema('segmenter-qualification-v1',record)
    expected = build_qualification(study_id=record['study_id'],pancreas_annotation_id=record['pancreas_annotation_id'],
        lesion_annotation_id=record['lesion_annotation_id'],checks=record['checks'],purpose=record['purpose'],**kwargs)
    require(record == expected, 'Stale/changed segmenter qualification identity or dependencies')
    return record['outcome']
