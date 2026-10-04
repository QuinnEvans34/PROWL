"""Invented retained-annotation history, dual roles and explicit holds; no source arrays."""
from copy import deepcopy
import json
import pytest
from qualification_fixtures import fixture as base_fixture
from src.data.manifest_records import canonical,digest
from src.data.manifest_records_v3 import build_manifest_v3
from src.data.source_inventory_records import content_hash
from src.data.segmenter_dispositions_v1 import derive
from src.data.segmenter_transition_v1 import build_transition,validate_transition


def fixture(decision='positive',inherited='ANNOTATION_USE_PENDING'):
    args,ctx=base_fixture();args['annotations'][2]['allowed_uses']=['evaluation_reference'];pan=args['annotations'][0];sid=pan['study_id']
    old=deepcopy(pan);old.update(annotation_id=pan['annotation_id']+'-lesion-original',structure='lesion',source_structure='pancreatic_lesion',
        status='quarantined',allowed_uses=[],method='unknown',validation_status='unverified')
    old['file']['uri']=sid.split(':')[-1]+'/lesion.nii.gz';old['file']['content_sha256']=digest(b'invented lesion1')
    old['label_encoding']['audit_source_sha256']=old['file']['content_sha256'];old['label_encoding']['mapping']=None
    old['provenance']=dict(scope='unknown',release_applicability='unresolved',evidence_files=[],allowed_use_decision_file=None)
    iid='issue:22222222-2222-4222-8222-222222222222';old['issue_ids']=[iid]
    args['annotations'].append(old);args['studies'][0]['annotation_ids'].append(old['annotation_id'])
    args['issues'].append(dict(schema_version='1.0.0',issue_id=iid,rule_code=inherited,entity_type='annotation',entity_id=old['annotation_id'],
        severity='blocking',disposition='quarantine',message='Invented unresolved annotation use',evidence=[dict(kind='validator_output',reference='synthetic')],created_at='2026-10-01T00:00:00Z'))
    prior=build_manifest_v3(**args);e=ctx['evidence_by_sha256'];facts={};rows=[];decisions={}
    source_ref=pan['provenance']['evidence_files'][0];rawuse=b'Invented new dual-target use';e[digest(rawuse)]=rawuse
    use_ref=dict(source_ref,uri='new-use.txt',bytes=len(rawuse),content_sha256=digest(rawuse))
    for i in [0,2]:
        s=args['studies'][i];p=args['annotations'][i];sid=s['study_id'];g=s['geometry'];les=old['file'] if i==0 else dict(p['file'],uri=sid.split(':')[-1]+'/lesion.nii.gz',content_sha256=digest(b'invented lesion3'))
        rowsf=[]
        for kind,ref in [('ct',s['image']),('pancreas',p['file']),('lesion',les)]:
            rowsf.append(dict(kind=kind,uri=ref['uri'],sha256=ref['content_sha256'],compressed_bytes=ref['bytes'],gzip_eof_crc_verified=True,
                header=dict(shape=g['shape_xyz'],affine=[g['affine_ras'][j:j+4] for j in range(0,16,4)],slope=1.,intercept=0.,units=['mm','unknown'])))
        empty=decision=='empty_unknown' and i==2;count=0 if empty else 1
        fact=dict(study_id=sid,protected_role='train' if i==0 else 'validation',holds=[],ct_finite=True,lesion_voxels=count,files=rowsf,
            lesion_decode=dict(semantic_value_counts=[dict(stored=0.,semantic=0.,count=4-count)]+([] if empty else [dict(stored=1.,semantic=1.,count=1)])),
            pancreas_decode=dict(foreground_voxels=1))
        facts[sid]=canonical(fact);rows.append(dict(study_id=sid,case_report_sha256=digest(facts[sid]),protected_role=fact['protected_role'],
            technical_content='passed',visual_review='technical_review_complete',lesion_voxels=count,unshown_component_ids=[],observations=[]))
        decisions[sid]='positive' if i==0 else decision
    review=canonical(dict(cases=rows));d=derive(prior=prior,bases=None,evidence=e,facts=facts,review_bytes=review,trusted_review_sha256=digest(review),
        decisions=decisions,use_ref=use_ref,source_ref=source_ref,recorded_at='2026-10-01T00:00:00Z')
    return prior,d


def transition_args(prior,d):
    cases=[]
    for row in d['selected']:
        ids=[]
        if row['prior_lesion_annotation_id'] and row['decision']=='positive':
            a=next(a for a in prior['annotations'] if a['annotation_id']==row['prior_lesion_annotation_id'])
            ids=[dict(issue_id=i['issue_id'],sha256=content_hash(i)) for i in sorted(prior['issues'],key=lambda i:i['issue_id']) if i['issue_id'] in a['issue_ids']]
        cases.append({k:row[k] for k in ['study_id','decision','pancreas_annotation_id','prior_lesion_annotation_id','lesion_annotation_id']}|dict(superseded_pending_use_issues=ids))
    raw=canonical(dict(component='segmenter-transition-review-v1',prior_manifest_sha256=content_hash(prior),manifest_sha256=content_hash(d['manifest']),cases=cases))
    return dict(prior_manifest=prior,derived=d,trusted_prior_manifest_sha256=content_hash(prior),trusted_manifest_sha256=content_hash(d['manifest']),
        review_bytes=raw,trusted_review_sha256=digest(raw),evidence_by_sha256={h:b.encode() for h,b in d['evidence'].items()},trusted_evidence_sha256=set(d['evidence']))


def test_dual_role_positive_transition_preserves_exact_predecessor_history():
    prior,d=fixture();a=transition_args(prior,d);r=build_transition(**a)
    assert [q['outcome'] for q in d['qualifications']]==['qualified','qualified']
    assert all(x in d['manifest']['annotations'] for x in prior['annotations']) and all(x in d['manifest']['issues'] for x in prior['issues'])
    assert sum(bool(c['superseded_pending_use_issues']) for c in r['cases'])==1
    assert r['cohort_or_training_granted'] is False
    assert validate_transition(r,trusted_transition_sha256=content_hash(r),**a)==r


@pytest.mark.parametrize('decision',['empty_unknown','annotation_relationship_unresolved'])
def test_held_references_have_no_permission_or_negative_claim(decision):
    prior,d=fixture(decision);r=build_transition(**transition_args(prior,d))
    q=next(q for q in d['qualifications'] if q['protected_role']=='validation');a=next(a for a in d['manifest']['annotations'] if a['annotation_id']==q['lesion_annotation_id'])
    assert q['outcome']=='held' and q['lesion_target_state']=='unknown' and a['allowed_uses']==[] and a['issue_ids']
    assert not any(t['status']=='negative' for s in d['manifest']['studies'] for t in s['target_statuses'])


@pytest.mark.parametrize('code',['PHYSICAL_UNITS_UNRESOLVED','WRONG_SOURCE','UNREVIEWED_ANNOTATION'])
def test_specific_inherited_hold_cannot_be_detached_into_successor(code):
    prior,d=fixture(inherited=code)
    with pytest.raises(ValueError,match='Specific inherited'):build_transition(**transition_args(prior,d))


@pytest.mark.parametrize('fault',['lost_issue','changed_issue','changed_predecessor','changed_pancreas','role','source','subject','unrelated_study','raw_bytes','extra_annotation','omit_qualification','sidecar','forged_pass','review_omission','review_issue','history_link','target_claim','old_pin','certificate'])
def test_transition_adversarial_changes_are_refused(fault):
    prior,d=fixture();a=transition_args(prior,d)
    if fault=='certificate':
        r=build_transition(**a);r['cases'][0]['superseded_pending_use_issues']=[]
        with pytest.raises(ValueError):validate_transition(r,trusted_transition_sha256=content_hash(r),**a)
        return
    m=d['manifest'];selected=d['selected'][0];sid=selected['study_id'];ann=next(x for x in m['annotations'] if x['annotation_id']==selected['lesion_annotation_id'])
    if fault=='lost_issue':m['issues'].pop(0)
    elif fault=='changed_issue':m['issues'][0]['message']='other'
    elif fault=='changed_predecessor':next(x for x in m['annotations'] if x['annotation_id']==selected['prior_lesion_annotation_id'])['annotation_version']='other'
    elif fault=='changed_pancreas':next(x for x in m['annotations'] if x['annotation_id']==selected['pancreas_annotation_id'])['allowed_uses']=['display_reference']
    elif fault=='role':m['protection'][0]['protected_role']='validation'
    elif fault=='source':m['snapshots'][0]['root_alias']='other'
    elif fault=='subject':m['subjects'][0]['identity_assurance']='other'
    elif fault=='unrelated_study':m['studies'][1]['acquisition']['site']='other'
    elif fault=='raw_bytes':ann['file']['content_sha256']='0'*64
    elif fault=='extra_annotation':m['annotations'].append(deepcopy(ann))
    elif fault=='omit_qualification':d['qualifications'].pop()
    elif fault=='sidecar':selected['lesion_inventory_sha256']='0'*64
    elif fault=='forged_pass':d['qualifications'][0]['checks'][0]['result']='exclude'
    elif fault=='history_link':next(s for s in m['studies'] if s['study_id']==sid)['annotation_ids'].remove(selected['prior_lesion_annotation_id'])
    elif fault=='target_claim':next(s for s in m['studies'] if s['study_id']==sid)['target_statuses'][-1]['status']='negative'
    elif fault=='old_pin':a['trusted_prior_manifest_sha256']='0'*64
    elif fault.startswith('review'):
        r=json.loads(a['review_bytes'])
        if fault=='review_omission':r['cases'].pop()
        else:r['cases'][0]['superseded_pending_use_issues']=[]
        a['review_bytes']=canonical(r);a['trusted_review_sha256']=digest(a['review_bytes'])
    # Refresh structural identity to ensure semantic guards are also exercised when possible.
    if fault not in ['extra_annotation','lost_issue','subject','source']:
        from src.data.manifest_records_v3 import _id
        m['manifest_id']=_id(m);a['trusted_manifest_sha256']=content_hash(m)
        if not fault.startswith('review'):
            r=json.loads(a['review_bytes']);r['manifest_sha256']=content_hash(m)
            a['review_bytes']=canonical(r);a['trusted_review_sha256']=digest(a['review_bytes'])
    with pytest.raises(Exception):build_transition(**a)
