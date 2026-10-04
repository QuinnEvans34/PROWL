"""Append-only segmenter transition certificate; does not broaden the localizer transition."""
import json
from src.data.manifest_records import canonical,digest
from src.data.manifest_records_v3 import validate_manifest_v3
from src.data.source_inventory_records import require,unique,content_hash,verify_pin
from src.data.segmenter_qualification_v1 import POLICY_SHA256,PURPOSES,validate_qualification,evidence


def build_transition(*, prior_manifest, derived, trusted_prior_manifest_sha256, trusted_manifest_sha256,
                     review_bytes, trusted_review_sha256, evidence_by_sha256, trusted_evidence_sha256,
                     base_membership_bytes=None):
    before=prior_manifest;after=derived['manifest']
    verify_pin(before,trusted_prior_manifest_sha256);verify_pin(after,trusted_manifest_sha256)
    validate_manifest_v3(before,base_membership_bytes=base_membership_bytes);validate_manifest_v3(after,base_membership_bytes=base_membership_bytes)
    require(digest(review_bytes)==trusted_review_sha256,'Transition review changed')
    review=json.loads(review_bytes);canonical(review)
    selected=unique(derived['selected'],'study_id');reviewed=unique(review['cases'],'study_id')
    require(set(selected)==set(reviewed) and selected,'Exact reviewed transition coverage required')
    require(set(review)=={'component','prior_manifest_sha256','manifest_sha256','cases'} and
            review['component']=='segmenter-transition-review-v1' and review['prior_manifest_sha256']==trusted_prior_manifest_sha256 and
            review['manifest_sha256']==trusted_manifest_sha256,'Transition review ancestry differs')
    for key in ['evidence_domain','migration_pins','protection','snapshots','subjects']:
        require(before[key]==after[key],'Protected/source/subject records changed')
    require(after['qualification_policy_sha256']==POLICY_SHA256,'Wrong successor policy')
    oldanns=unique(before['annotations'],'annotation_id');newanns=unique(after['annotations'],'annotation_id')
    require(all(newanns.get(aid)==a for aid,a in oldanns.items()),'Predecessor annotation changed or lost')
    oldissues=unique(before['issues'],'issue_id');newissues=unique(after['issues'],'issue_id')
    require(all(newissues.get(iid)==i for iid,i in oldissues.items()),'Inherited issue changed or lost')
    added_ids={row['lesion_annotation_id'] for row in selected.values()}
    require(len(added_ids)==len(selected) and set(newanns)-set(oldanns)==added_ids,'Unexpected annotation additions')
    oldstudies=unique(before['studies'],'study_id');newstudies=unique(after['studies'],'study_id')
    require(set(oldstudies)==set(newstudies),'Study membership changed')
    qs=unique(derived['qualifications'],'study_id');require(set(qs)==set(selected),'Qualification omission')
    allowed_codes={'DIFFICULTY_OBSERVATION','EMPTY_LESION_REFERENCE_UNRESOLVED','LESION_ANNOTATION_RELATIONSHIP_UNRESOLVED'}
    for iid,i in newissues.items():
        if iid in oldissues:continue
        require(i['entity_type']=='annotation' and i['entity_id'] in added_ids and i['rule_code'] in allowed_codes,'Unreviewed issue addition')
        require((i['severity'],i['disposition'])==(('information','retain') if i['rule_code']=='DIFFICULTY_OBSERVATION' else ('blocking','quarantine')),'Wrong issue semantics')
    transitions=[]
    for sid,oldstudy in oldstudies.items():
        newstudy=newstudies[sid]
        if sid not in selected:
            require(newstudy==oldstudy,'Unrelated study changed');continue
        row=selected[sid];ann=newanns[row['lesion_annotation_id']];pan=oldanns[row['pancreas_annotation_id']]
        decision=row['decision'];q=qs[sid];r=reviewed[sid]
        require(set(row)=={'study_id','purpose','pancreas_annotation_id','prior_lesion_annotation_id','lesion_annotation_id','decision','lesion_inventory_sha256'},'Transition row fields differ')
        require(set(r)=={'study_id','decision','pancreas_annotation_id','prior_lesion_annotation_id','lesion_annotation_id','superseded_pending_use_issues'},'Review row fields differ')
        require(all(r[k]==row[k] for k in r if k!='superseded_pending_use_issues'),'Reviewed transition differs')
        require(pan['study_id']==sid and pan['structure']=='pancreas' and row['pancreas_annotation_id'] in oldstudy['annotation_ids'],'Wrong pancreas context')
        oldlesions=[oldanns[aid] for aid in oldstudy['annotation_ids'] if oldanns[aid]['structure']=='lesion']
        require(len(oldlesions)<=1 and row['prior_lesion_annotation_id']==(oldlesions[0]['annotation_id'] if oldlesions else None),'Invented/omitted lesion predecessor')
        previous=oldlesions[0] if oldlesions else None
        pending=[]
        if previous:
            require(previous['file']==ann['file'],'Raw predecessor lesion changed')
            inherited=[oldissues[iid] for iid in previous['issue_ids']]
            require(all(i['rule_code']=='ANNOTATION_USE_PENDING' and i['severity']=='blocking' and i['disposition']=='quarantine' and
                        i['entity_type']=='annotation' and i['entity_id']==previous['annotation_id'] for i in inherited),'Specific inherited blocker cannot be superseded')
            pending=[dict(issue_id=i['issue_id'],sha256=content_hash(i)) for i in sorted(inherited,key=lambda i:i['issue_id'])] if decision=='positive' else []
        require(r['superseded_pending_use_issues']==pending,'Pending-use issue review differs')
        require(ann['study_id']==sid and ann['source_snapshot_id']==oldstudy['source_snapshot_id'] and ann['structure']=='lesion' and
                ann['source_structure']=='pancreatic_lesion','Wrong successor annotation context')
        require({k:v for k,v in oldstudy.items() if k not in ('annotation_ids','target_statuses')}==
                {k:v for k,v in newstudy.items() if k not in ('annotation_ids','target_statuses')},'Study changed outside transition scope')
        require(set(newstudy['annotation_ids'])==set(oldstudy['annotation_ids'])|{ann['annotation_id']},'Study annotation history lost')
        held=decision!='positive'
        require(decision in ('positive','empty_unknown','annotation_relationship_unresolved'),'Unsupported decision')
        expected=[t for t in oldstudy['target_statuses'] if t['target'] not in ('lesion','pancreatic_lesion')]+[
            dict(target='pancreatic_lesion',status='unknown' if held else 'positive',method='unavailable' if held else 'annotation_voxel_presence',reference_id=None if held else ann['annotation_id'])]
        require(sorted(newstudy['target_statuses'],key=lambda t:t['target'])==sorted(expected,key=lambda t:t['target']),'Unreviewed target claim')
        role=next(p['protected_role'] for p in before['protection'] if p['study_id']==sid)
        require(row['purpose'] in PURPOSES and PURPOSES[row['purpose']][0]==role,'Wrong role/purpose')
        require(ann['allowed_uses']==([] if held else [PURPOSES[row['purpose']][1]]) and ann['status']==('quarantined' if held else 'eligible'),'Unreviewed permission')
        require(q['purpose']==row['purpose'] and q['pancreas_annotation_id']==pan['annotation_id'] and q['lesion_annotation_id']==ann['annotation_id'],'Qualification target differs')
        outcome=validate_qualification(q,trusted_qualification_sha256=content_hash(q),manifest=after,trusted_manifest_sha256=trusted_manifest_sha256,
            trusted_policy_sha256=POLICY_SHA256,evidence_by_sha256=evidence_by_sha256,trusted_evidence_sha256=trusted_evidence_sha256,base_membership_bytes=base_membership_bytes)
        require(outcome==('held' if held else 'qualified'),'Transition outcome differs')
        inv=json.loads(evidence(row['lesion_inventory_sha256'],evidence_by_sha256,trusted_evidence_sha256))
        snapshot=next(s for s in after['snapshots'] if s['source_snapshot_id']==oldstudy['source_snapshot_id'])
        require(inv==dict(schema_version='1.0.0',component='segmenter-lesion-inventory-v1',state='present',study_id=sid,
            source_snapshot_id=snapshot['source_snapshot_id'],source_version_sha256=content_hash(snapshot['source_version']),file=ann['file']),'Paired inventory context changed')
        if held:
            code='EMPTY_LESION_REFERENCE_UNRESOLVED' if decision=='empty_unknown' else 'LESION_ANNOTATION_RELATIONSHIP_UNRESOLVED'
            require(any(newissues[i]['rule_code']==code for i in ann['issue_ids']),'Held annotation lost its requirement')
        transitions.append(dict(study_id=sid,protected_role=role,purpose=row['purpose'],prior_lesion_annotation_id=row['prior_lesion_annotation_id'],
            pancreas_annotation_id=pan['annotation_id'],lesion_annotation_id=ann['annotation_id'],qualification_sha256=content_hash(q),
            outcome=outcome,superseded_pending_use_issues=pending,history_preserved=True))
    result=dict(component='segmenter-transition-v1',schema_version='1.0.0',prior_manifest_sha256=trusted_prior_manifest_sha256,
        manifest_sha256=trusted_manifest_sha256,review_sha256=trusted_review_sha256,cases=sorted(transitions,key=lambda x:x['study_id']),
        original_membership_preserved=True,all_predecessor_annotations_preserved=True,all_predecessor_issues_preserved=True,
        cohort_or_training_granted=False)
    result['transition_id']='segmenter-transition:'+content_hash(result)
    return result


def validate_transition(record, *, trusted_transition_sha256, **kwargs):
    verify_pin(record,trusted_transition_sha256)
    require(record==build_transition(**kwargs),'Transition identity/dependencies changed')
    return record
