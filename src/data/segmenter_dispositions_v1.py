"""Retained-evidence dual-target dispositions. No source access, cohort or model operations."""
from copy import deepcopy
import json
import math
import numpy as np
from src.data.manifest_records import canonical, digest
from src.data.manifest_records_v3 import build_manifest_v3, validate_manifest_v3
from src.data.source_inventory_records import require, unique, content_hash
from src.data.localizer_expansion_v2 import evidence_ref, issue
from src.data.segmenter_qualification_v1 import POLICY_SHA256, PURPOSES, CHECKS, context_for, context_bindings, build_qualification


def derive(*, prior, bases, evidence, facts, review_bytes, trusted_review_sha256, decisions,
           use_ref, source_ref, recorded_at):
    validate_manifest_v3(prior,base_membership_bytes=bases)
    require(digest(review_bytes)==trusted_review_sha256,'Unreviewed diagnostic ledger')
    review=unique(json.loads(review_bytes)['cases'],'study_id')
    require(set(facts)==set(review)==set(decisions) and facts,'Disposition coverage differs')
    evidence=dict(evidence)
    require(all(digest(b)==h for h,b in evidence.items()),'Changed retained evidence')
    for ref in [use_ref,source_ref]:
        require(ref['content_sha256'] in evidence and len(evidence[ref['content_sha256']])==ref['bytes'],'Missing use/provenance evidence')
    evidence[trusted_review_sha256]=review_bytes
    records={k:deepcopy(prior[k]) for k in ['subjects','studies','annotations','issues']}
    protection=unique(prior['protection'],'study_id'); snapshots=unique(prior['snapshots'],'source_snapshot_id')
    selected=[];parsed={};sidecars=[]
    for sid in sorted(facts):
        row=review[sid];raw=facts[sid];fact=json.loads(raw);parsed[sid]=fact
        require(digest(raw)==row['case_report_sha256'] and fact['study_id']==sid,'Unreviewed facts')
        role=protection[sid]['protected_role'];purpose=next(p for p,(r,_) in PURPOSES.items() if r==role)
        require(fact['protected_role']==row['protected_role']==role and row['technical_content']=='passed' and
                row['visual_review']=='technical_review_complete' and not fact['holds'],'Unreviewed role/content/holds')
        require(fact['ct_finite'] and fact['lesion_voxels']==row['lesion_voxels'] and
                not row['unshown_component_ids'],'Content ledger differs')
        files=unique(fact['files'],'kind');require(set(files)=={'ct','pancreas','lesion'},'Exact triple required')
        require(all(f['gzip_eof_crc_verified'] for f in files.values()),'Incomplete consumed arrays')
        study=next(s for s in records['studies'] if s['study_id']==sid)
        pan=next(a for a in records['annotations'] if a['annotation_id'] in study['annotation_ids'] and a['structure']=='pancreas')
        oldlesions=[a for a in records['annotations'] if a['annotation_id'] in study['annotation_ids'] and a['structure']=='lesion']
        require(len(oldlesions)<=1,'Ambiguous lesion predecessor')
        old=oldlesions[0] if oldlesions else None
        def ref(f):return dict(root_alias=pan['file']['root_alias'],uri=f['uri'],bytes=f['compressed_bytes'],content_sha256=f['sha256'],media_type='application/gzip')
        require(ref(files['ct'])==study['image'] and ref(files['pancreas'])==pan['file'],'CT/pancreas identity differs')
        if old:require(ref(files['lesion'])==old['file'],'Lesion predecessor bytes changed')
        g=study['geometry'];require(g and files['ct']['header']['units'][0]=='mm','Qualified mm CT required')
        for f in files.values():
            h=f['header'];require(h['shape']==g['shape_xyz'] and np.allclose(np.asarray(h['affine']).ravel(),g['affine_ras'],atol=1e-5,rtol=0),'Measured geometry differs')
            require(h['units'][0] in ('mm','unknown'),'Unsupported units')
        reason=decisions[sid]
        require(reason in ('positive','empty_unknown','annotation_relationship_unresolved'),'Unsupported disposition')
        require((reason=='empty_unknown')==(fact['lesion_voxels']==0),'Empty target decision differs')
        held=reason!='positive';use=PURPOSES[purpose][1]
        # Preserve pancreas records exactly; their existing role-specific permission remains required.
        require(pan['status']=='eligible' and use in pan['allowed_uses'],'Pancreas permission missing')
        f=files['lesion'];audit=fact['lesion_decode'];values=audit['semantic_value_counts'];header=f['header']
        require(sum(v['count'] for v in values)==math.prod(g['shape_xyz']) and
                sum(v['count'] for v in values if abs(v['semantic']-1)<=1e-6)==fact['lesion_voxels'],'Measured target counts differ')
        aid='pants:annotation:'+sid.split(':')[-1]+'-segmenter-lesion-'+content_hash(dict(facts=digest(raw),use=use_ref,decision=reason))[:16]
        mapping=deepcopy(pan['label_encoding']['mapping']);mapping['canonical_foreground']=2
        ann=dict(schema_version='2.0.0',annotation_id=aid,study_id=sid,source_snapshot_id=study['source_snapshot_id'],source='pants',
            structure='lesion',source_structure='pancreatic_lesion',file=ref(f),annotation_version='segmenter-visible-reference-v1',
            method='human_manual',validation_status='source_asserted',allowed_uses=[] if held else [use],status='quarantined' if held else 'eligible',issue_ids=[],
            provenance=dict(scope='publisher_protocol',release_applicability='confirmed',evidence_files=[source_ref,use_ref,evidence_ref('candidate-ledger.json',review_bytes)],allowed_use_decision_file=use_ref),
            label_encoding=dict(representation='original_source',audit_file=evidence_ref(sid.split(':')[-1]+'.json',raw),audit_source_sha256=f['sha256'],
                values_basis='stored',value_counts=[dict(value=v['stored'],count=v['count']) for v in values],voxel_count=math.prod(g['shape_xyz']),
                stored_range=[min(v['stored'] for v in values),max(v['stored'] for v in values)],effective_scaling=dict(slope=header['slope'],intercept=header['intercept']),mapping=mapping))
        added=[]
        if held:
            code='EMPTY_LESION_REFERENCE_UNRESOLVED' if reason=='empty_unknown' else 'LESION_ANNOTATION_RELATIONSHIP_UNRESOLVED'
            added.append(issue(sid,code,reason+'; no segmenter target permission',trusted_review_sha256,'annotation',aid,created_at=recorded_at))
        for note in row['observations']:
            added.append(issue(sid,'DIFFICULTY_OBSERVATION',note,trusted_review_sha256,'annotation',aid,created_at=recorded_at))
        ann['issue_ids']=sorted(i['issue_id'] for i in added)
        study['annotation_ids']=sorted(study['annotation_ids']+[aid])
        study['target_statuses']=[t for t in study['target_statuses'] if t['target'] not in ('lesion','pancreatic_lesion')]+[
            dict(target='pancreatic_lesion',status='unknown' if held else 'positive',method='unavailable' if held else 'annotation_voxel_presence',reference_id=None if held else aid)]
        records['annotations'].append(ann);records['issues'].extend(added);evidence[digest(raw)]=raw
        snapshot=snapshots[study['source_snapshot_id']]
        inv=dict(schema_version='1.0.0',component='segmenter-lesion-inventory-v1',state='present',study_id=sid,
            source_snapshot_id=snapshot['source_snapshot_id'],source_version_sha256=content_hash(snapshot['source_version']),file=ref(f))
        payload=canonical(inv);evidence[digest(payload)]=payload;sidecars.append(inv)
        selected.append(dict(study_id=sid,purpose=purpose,pancreas_annotation_id=pan['annotation_id'],prior_lesion_annotation_id=old['annotation_id'] if old else None,
            lesion_annotation_id=aid,decision=reason,lesion_inventory_sha256=digest(payload)))
    manifest=build_manifest_v3(name='segmenter-dispositions-0001',snapshots=prior['snapshots'],protection=prior['protection'],
        qualification_policy_sha256=POLICY_SHA256,base_membership_bytes=bases,**records)
    qualifications=[]
    for row in selected:
        sid=row['study_id'];fact=parsed[sid];files=unique(fact['files'],'kind');g=next(s['geometry'] for s in manifest['studies'] if s['study_id']==sid)
        context=context_for(manifest,sid,row['pancreas_annotation_id'],row['lesion_annotation_id'],trusted_manifest_sha256=content_hash(manifest),base_membership_bytes=bases)
        details={name:{} for name in CHECKS};details['geometry']=dict(ct_units='mm',source_shape=g['shape_xyz'],source_affine=g['affine_ras'])
        for kind in ['pancreas','lesion']:
            h=files[kind]['header'];details['geometry'].update({kind+'_shape':h['shape'],kind+'_affine':sum(h['affine'],[]),kind+'_units':'mm' if h['units'][0]=='mm' else 'matched_mm_ct_grid'})
        details['mapping_lineage']=dict(audit_sha256=digest(facts[sid]),binary_policy='pants-semantic-binary-atol1e-6-v1',class_precedence='lesion_over_pancreas')
        details['permitted_use']=dict(use_decision_sha256=use_ref['content_sha256'],scope='private_noncommercial_visible_source_references')
        details['source_readiness']=dict(lesion_inventory_sha256=row['lesion_inventory_sha256'])
        details['pancreas_target']=dict(classification='positive',foreground_voxels=fact['pancreas_decode']['foreground_voxels'])
        details['lesion_target']=dict(classification='positive' if fact['lesion_voxels'] else 'unknown',foreground_voxels=fact['lesion_voxels'],negative_basis_sha256=None)
        checks=[]
        for name in CHECKS:
            result='hold' if name=='lesion_target' and row['decision']!='positive' else 'pass'
            payload=canonical(dict(schema_version='1.0.0',component='segmenter-check-v1',purpose=row['purpose'],check=name,bindings=context_bindings(context),
                policy_sha256=POLICY_SHA256,result=result,details=details[name]))
            pin=digest(payload);evidence[pin]=payload;checks.append(dict(name=name,result=result,evidence_sha256=pin))
        q=build_qualification(manifest=manifest,study_id=sid,pancreas_annotation_id=row['pancreas_annotation_id'],lesion_annotation_id=row['lesion_annotation_id'],
            checks=checks,purpose=row['purpose'],trusted_manifest_sha256=content_hash(manifest),trusted_policy_sha256=POLICY_SHA256,
            evidence_by_sha256=evidence,trusted_evidence_sha256=set(evidence),base_membership_bytes=bases)
        require(q['outcome']==('qualified' if row['decision']=='positive' else 'held'),'Unexpected disposition outcome')
        qualifications.append(q)
    return dict(manifest=manifest,qualifications=qualifications,selected=selected,lesion_inventories=sidecars,evidence={h:b.decode() for h,b in evidence.items()})
