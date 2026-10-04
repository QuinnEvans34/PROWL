"""Deterministic evidence-bound expansion; no filesystem or raw image access.

Callers must independently pin the reviewed inputs. Rebuilding verifies derivation, not the
truth of publisher statements or a reviewer's anatomical judgement.
"""
from copy import deepcopy
import json
import math
from uuid import UUID

from src.data.manifest_records import canonical, digest
from src.data.manifest_records_v3 import build_manifest_v3, validate_manifest_v3, verified_context
from src.data.source_inventory_records import build_source_snapshot_v2, content_hash, require, unique
from src.data.purpose_qualification_v2 import POLICY_SHA256, PURPOSES, CHECKS, context_bindings, build_qualification
from src.data.cohort_records_v3 import build_cohort, checked_members

FAMILY='pants-localizer-expansion-v1'
BUNDLE_ID='cohort-bundle:pants-localizer-expansion-0001:v1'
ROLE_PURPOSE={role:purpose for purpose,(role,_) in PURPOSES.items()}


def evidence_ref(name, payload, media='application/json'):
    return dict(root_alias='qualification_evidence',uri=name,bytes=len(payload),content_sha256=digest(payload),media_type=media)


def issue(sid, code, message, review_sha, entity_type='study', entity_id=None, *, created_at):
    entity_id=entity_id or sid
    key=content_hash(dict(entity_id=entity_id,code=code,message=message,review=review_sha))
    return dict(schema_version='1.0.0',issue_id='issue:'+str(UUID(hex=key[:32],version=4)),
        rule_code=code,entity_type=entity_type,entity_id=entity_id,
        severity='information' if code=='DIFFICULTY_OBSERVATION' else 'blocking',
        disposition='retain' if code=='DIFFICULTY_OBSERVATION' else 'quarantine',message=message,
        evidence=[dict(kind='manual_review',reference='sha256:'+review_sha)],created_at=created_at)


def derive(*, prior, bases, evidence, facts, review_bytes, selection, use_ref, source_ref, mapping, recorded_at):
    validate_manifest_v3(prior,base_membership_bytes=bases)
    evidence=dict(evidence);review=json.loads(review_bytes);review_sha=digest(review_bytes)
    evidence[review_sha]=review_bytes
    candidates=[c for role in ('train','validation') for c in selection['candidates'][role]]
    selected=unique(candidates,'study_id');reviews=unique(review['cases'],'study_id')
    require(set(selected)==set(facts)==set(reviews), 'Candidate/facts/review coverage differs')
    protection={p['study_id']:p for p in prior['protection']}
    snapshot=deepcopy(prior['snapshots'][0]);require(len(prior['snapshots'])==1,'One pinned source required')
    inventory={r['uri']:r for r in snapshot['observed_files']}
    parsed={}
    for sid,candidate in selected.items():
        fact=json.loads(facts[sid]);r=reviews[sid];parsed[sid]=fact
        require(digest(facts[sid])==r['facts_sha256'], 'Reviewed facts changed')
        require(fact['study_id']==sid and fact['protected_role']==candidate['protected_role']==r['protected_role']==protection[sid]['protected_role'], 'Candidate protected role changed')
        require(r['assessment']=='no_obvious_gross_displacement_in_sampled_views' and r['reviewed_planes']==fact['review_planes'], 'Unsupported alignment assessment')
        require(r['retained_automated_holds']==fact['holds'], 'Review omitted a hold')
        require(fact['ct_finite'] and fact['geometry_matches'] and fact['decode']['foreground_voxels']>0, 'Unsupported content/target evidence')
        require(fact['holds'] in ([],['physical_units_unresolved']), 'Unreviewed content hold')
        files=unique(fact['files'],'kind');require(set(files)=={'ct','pancreas'},'Exact CT/pancreas pair required')
        require({f['source']['uri'] for f in files.values()}=={f['uri'] for f in candidate['inventory_inputs']},'Candidate source changed')
        require(files['ct']['shape']==files['pancreas']['shape'] and files['ct']['affine']==files['pancreas']['affine'], 'Geometry evidence inconsistent')
        require((files['ct']['units'][0]=='mm')==(not fact['holds']), 'Unit hold inconsistent')
        for f in files.values():
            row=inventory.get(f['source']['uri']);require(row is not None,'File absent from source inventory')
            require(row['study_id']==sid and row['kind']==f['kind'] and row['bytes']==f['compressed_bytes'] and f['gzip_eof_crc_verified'], 'Inventory/content mismatch')
            require(row['sha256'] in (None,f['content_sha256']), 'Previously verified bytes changed')
            row['sha256']=f['content_sha256']
        evidence[digest(facts[sid])]=facts[sid]
    snapshot=build_source_snapshot_v2(source_version=snapshot['source_version'],license=snapshot['license'],
        root_alias=snapshot['root_alias'],study_ids=snapshot['scope']['study_ids'],expected_files=snapshot['scope']['expected_files'],
        observed_files=list(inventory.values()),control_sha256=content_hash(dict(prior=content_hash(prior),review=review_sha,selection=content_hash(selection),use=use_ref)))
    records={k:deepcopy(prior[k]) for k in ('subjects','studies','annotations','issues')}
    for collection in ('subjects','studies','annotations'):
        for row in records[collection]:row['source_snapshot_id']=snapshot['source_snapshot_id']
    for sid,fact in parsed.items():
        p=protection[sid];source_id=p['source_study_id'];role=p['protected_role'];held=bool(fact['holds'])
        old_study=next((s for s in records['studies'] if s['study_id']==sid),None)
        old_subject=next((s for s in records['subjects'] if s['subject_id']==p['subject_id']),None)
        old_annotation=next((a for a in records['annotations'] if a['study_id']==sid and a['structure']=='pancreas'),None)
        # No generic removal of inherited denials. This expansion only versions already-clear prior cases.
        for old in (old_study,old_subject,old_annotation):
            require(old is None or not old['issue_ids'],'Existing issues require a separate transition review')
        files={f['kind']:f for f in fact['files']};ct,mask=files['ct'],files['pancreas']
        rawref=lambda f:dict(root_alias=snapshot['root_alias'],uri=f['source']['uri'],bytes=f['compressed_bytes'],content_sha256=f['content_sha256'],media_type='application/gzip')
        aid=f'pants:annotation:{source_id}-pancreas-expansion-'+content_hash(dict(facts=digest(facts[sid]),use=use_ref,role=role))[:16]
        values=fact['semantic_values'];scaling=mask['effective_scaling'];slope=scaling['slope'];intercept=scaling['intercept']
        stored=sorted((v['value']-intercept)/slope for v in values)
        annotation=dict(schema_version='2.0.0',annotation_id=aid,study_id=sid,source_snapshot_id=snapshot['source_snapshot_id'],source='pants',
            structure='pancreas',source_structure='pancreas',file=rawref(mask),annotation_version='localizer-expansion-v1',
            method='human_validated',validation_status='source_asserted',allowed_uses=[] if held else [PURPOSES[ROLE_PURPOSE[role]][1]],
            status='quarantined' if held else 'eligible',issue_ids=[],
            provenance=dict(scope='publisher_protocol',release_applicability='confirmed',evidence_files=[source_ref,use_ref,evidence_ref('candidate-review.json',review_bytes)],allowed_use_decision_file=use_ref),
            label_encoding=dict(representation='original_source',audit_file=evidence_ref(source_id+'.json',facts[sid]),audit_source_sha256=mask['content_sha256'],
                values_basis='nifti_scaled_semantic',value_counts=values,voxel_count=math.prod(mask['shape']),stored_range=[stored[0],stored[-1]],effective_scaling=scaling,mapping=deepcopy(mapping)))
        newissues=[]
        if held:
            newissues.append(issue(sid,'PHYSICAL_UNITS_UNRESOLVED','Both CT and pancreas spatial units are unknown; no allowed use.',review_sha,'annotation',aid,created_at=recorded_at))
            newissues.append(issue(sid,'PHYSICAL_UNITS_UNRESOLVED','CT spatial units are unknown; physical geometry is not qualified.',review_sha,created_at=recorded_at))
        for note in reviews[sid]['observations']:
            if held:continue  # The unit observation is already a blocking annotation issue.
            newissues.append(issue(sid,'DIFFICULTY_OBSERVATION',note,review_sha,created_at=recorded_at))
        annotation['issue_ids']=[i['issue_id'] for i in newissues if i['entity_type']=='annotation']
        subject=old_subject or dict(schema_version='1.0.0',subject_id=p['subject_id'],source='pants',source_subject_id=source_id,
            source_snapshot_id=snapshot['source_snapshot_id'],identity_method='study_as_subject_fallback',identity_assurance='unverified_unique',status='reconciled',issue_ids=[])
        study=old_study or dict(schema_version='1.0.0',study_id=sid,subject_id=p['subject_id'],source='pants',source_study_id=source_id,
            source_partition='publisher_train',source_snapshot_id=snapshot['source_snapshot_id'],modality='CT',
            acquisition={k:None for k in ('contrast_phase','manufacturer','scanner','site','study_date','study_year')},annotation_ids=[],target_statuses=[],issue_ids=[])
        study.update(image=rawref(ct),status='quarantined' if held else 'reconciled',geometry=None if held else dict(shape_xyz=ct['shape'],
            spacing_mm_xyz=[math.sqrt(sum(ct['affine'][i][j]**2 for i in range(3))) for j in range(3)],affine_ras=sum(ct['affine'],[])))
        study['issue_ids'] += [i['issue_id'] for i in newissues if i['entity_type']=='study']
        study['annotation_ids']=sorted([a for a in study['annotation_ids'] if old_annotation is None or a!=old_annotation['annotation_id']]+[aid])
        study['target_statuses']=[t for t in study['target_statuses'] if t['target']!='pancreas']+[dict(target='pancreas',status='positive',method='annotation_voxel_presence',reference_id=aid)]
        if old_subject is None:records['subjects'].append(subject)
        if old_study is None:records['studies'].append(study)
        if old_annotation:records['annotations'].remove(old_annotation)
        records['annotations'].append(annotation);records['issues'].extend(newissues)
    manifest=build_manifest_v3(name='localizer-expansion-0001',snapshots=[snapshot],protection=prior['protection'],
        qualification_policy_sha256=POLICY_SHA256,base_membership_bytes=bases,**records)
    require(all(i in manifest['issues'] for i in prior['issues']), 'Prior issue lost')
    qualifications=[]
    for sid in sorted(selected):
        annotation=next(a for a in manifest['annotations'] if a['study_id']==sid and a['structure']=='pancreas')
        context=verified_context(manifest,sid,annotation['annotation_id'],trusted_manifest_sha256=content_hash(manifest),base_membership_bytes=bases)
        purpose=ROLE_PURPOSE[protection[sid]['protected_role']];checks=[]
        for name in CHECKS:
            result='hold' if parsed[sid]['holds'] and name=='geometry' else 'pass'
            payload=canonical(dict(schema_version='2.0.0',purpose=purpose,check=name,bindings=context_bindings(context),policy_sha256=POLICY_SHA256,result=result))
            pin=digest(payload);evidence[pin]=payload;checks.append(dict(name=name,result=result,evidence_sha256=pin))
        qualifications.append(build_qualification(manifest=manifest,study_id=sid,annotation_id=annotation['annotation_id'],checks=checks,purpose=purpose,
            trusted_manifest_sha256=content_hash(manifest),trusted_policy_sha256=POLICY_SHA256,evidence_by_sha256=evidence,trusted_evidence_sha256=set(evidence),base_membership_bytes=bases))
    return manifest,qualifications,evidence


def context(manifest,qualifications,evidence,bases):
    return dict(manifest=manifest,trusted_manifest_sha256=content_hash(manifest),trusted_policy_sha256=POLICY_SHA256,
        qualifications_by_id={q['qualification_id']:q for q in qualifications},trusted_qualification_sha256={q['qualification_id']:content_hash(q) for q in qualifications},
        evidence_by_sha256=evidence,trusted_evidence_sha256=set(evidence),base_membership_bytes=bases,cohorts_by_id={},trusted_cohort_sha256={})


def freeze_records(manifest,qualifications,evidence,bases,*,expected_members):
    ctx=context(manifest,qualifications,evidence,bases);parents=[];children=[]
    for role in ('train','validation','test'):
        ids=[p['study_id'] for p in manifest['protection'] if p['protected_role']==role]
        parent=build_cohort(cohort_id=f'cohort:pants-expansion-base-{role}:v1',cohort_family_id=FAMILY,capability='protection_only',protected_role=role,
            study_ids=ids,requested_count=len(ids),parent_ids=[],context=ctx)
        parents.append(parent);ctx['cohorts_by_id'][parent['cohort_id']]=parent;ctx['trusted_cohort_sha256'][parent['cohort_id']]=content_hash(parent)
    for role in ('train','validation'):
        ids=sorted(q['study_id'] for q in qualifications if q['protected_role']==role and q['outcome']=='qualified')
        require(ids==sorted(expected_members[role]), 'Executable membership differs from reviewed subset')
        child=build_cohort(cohort_id=f'cohort:pants-localizer-expansion-{role}-0001:v1',cohort_family_id=FAMILY,capability='executable',protected_role=role,
            study_ids=ids,requested_count=len(ids),parent_ids=[f'cohort:pants-expansion-base-{role}:v1'],context=ctx)
        children.append(child)
    return parents,children


def consume(manifest,qualifications,evidence,bases,parents,children,*,operation,current_manifest_sha256):
    require(content_hash(manifest)==current_manifest_sha256,'Current manifest differs; requalification required')
    require(operation in ('optimizer','evaluator'),'Explicit operation required')
    ctx=context(manifest,qualifications,evidence,bases)
    ctx['cohorts_by_id']={p['cohort_id']:p for p in parents};ctx['trusted_cohort_sha256']={p['cohort_id']:content_hash(p) for p in parents}
    role={'optimizer':'train','evaluator':'validation'}[operation]
    matches=[c for c in children if c['protected_role']==role];require(len(matches)==1,'Exactly one matching cohort required')
    child=matches[0]
    return checked_members(child,trusted_record_sha256=content_hash(child),operation=operation,**ctx)
