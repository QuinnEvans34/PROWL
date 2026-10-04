"""Invented evidence only. No source arrays, external roots or production permissions."""
from copy import deepcopy
from test_manifest_records import inputs
from test_annotation_contract_v2 import approved
from src.data.binary_label_policy import APPROVED_POLICY
from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import build_source_snapshot_v2, content_hash
from src.data.manifest_records_v3 import build_manifest_v3, verified_context
from src.data.purpose_qualification import POLICY_SHA256, CHECKS, context_bindings, build_qualification
from src.data.cohort_records import build_cohort


def fixture():
    old=inputs();subjects=[];studies=[];annotations=[];issues=[];protection=[];expected=[];observed=[]
    evidence={}
    def evidence_ref(text):
        data=text.encode();sha=digest(data);evidence[sha]=data
        return dict(root_alias='fixture_evidence',uri='synthetic/'+sha+'.txt',media_type='text/plain',
                    bytes=len(data),content_sha256=sha)
    approval=evidence_ref('Synthetic binary approval');implementation=evidence_ref('Synthetic decoder')
    audit=evidence_ref('Synthetic full mask audit');provenance=evidence_ref('Synthetic permitted target use')
    for n,role in [(1,'train'),(2,'train'),(3,'validation'),(9001,'test')]:
        raw=f'PanTS_{n:08}';sid='pants:study:'+raw;subid='pants:subject:'+raw;aid='pants:annotation:'+raw+'-pancreas-v2'
        protection.append(dict(study_id=sid,subject_id=subid,source_study_id=raw,protected_role=role,protection_group_id=None))
        study=deepcopy(old['studies'][0]);subject=deepcopy(old['subjects'][0]);annotation=approved()
        study.update(study_id=sid,subject_id=subid,source_study_id=raw,source_partition='publisher_test' if n>9000 else 'publisher_train',
                     annotation_ids=[aid],status='reconciled',issue_ids=[])
        study['target_statuses']=[dict(target='pancreas',status='positive',method='annotation_voxel_presence',reference_id=aid)]
        study['geometry']=dict(shape_xyz=[2,2,1],spacing_mm_xyz=[1,1,1],affine_ras=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])
        subject.update(subject_id=subid,source_subject_id=raw,status='reconciled',issue_ids=[])
        annotation.update(study_id=sid,annotation_id=aid,structure='pancreas',source_structure='pancreas')
        annotation['label_encoding'].update(audit_file=audit,stored_range=[0,1],values_basis='stored',
            value_counts=[dict(value=0,count=3),dict(value=1,count=1)],effective_scaling=dict(slope=1,intercept=0))
        annotation['label_encoding']['mapping'].update(policy_id=APPROVED_POLICY,policy_sha256=implementation['content_sha256'],
            canonical_foreground=1,approval_file=approval)
        annotation['provenance'].update(evidence_files=[provenance],allowed_use_decision_file=provenance)
        for kind,ref in [('ct',study['image']),('pancreas',annotation['file'])]:
            ref.update(root_alias='synthetic_raw',uri=f'{raw}/{kind}.nii.gz',bytes=32,
                       content_sha256=digest(f'synthetic:{raw}:{kind}'.encode()))
            entry=dict(study_id=sid,kind=kind,uri=ref['uri']);expected.append(entry)
            observed.append(dict(**entry,state='present',bytes=32,sha256=ref['content_sha256']))
        annotation['label_encoding']['audit_source_sha256']=annotation['file']['content_sha256']
        if n==2:
            iid='issue:11111111-1111-4111-8111-111111111111'
            annotation.update(status='quarantined',allowed_uses=[],issue_ids=[iid])
            issues.append(dict(schema_version='1.0.0',issue_id=iid,rule_code='PHYSICAL_UNITS_UNRESOLVED',
                entity_type='annotation',entity_id=aid,severity='blocking',disposition='quarantine',
                message='Synthetic unknown units',evidence=[dict(kind='validator_output',reference='synthetic')],
                created_at='2026-09-28T00:00:00Z'))
        subjects.append(subject);studies.append(study);annotations.append(annotation)
    snapshot=build_source_snapshot_v2(source_version=old['snapshots'][0]['source_version'],
        license=old['snapshots'][0]['license'],root_alias='synthetic_raw',study_ids=[p['study_id'] for p in protection],
        expected_files=expected,observed_files=observed,control_sha256=digest(b'synthetic-control'))
    for row in subjects+studies+annotations:row['source_snapshot_id']=snapshot['source_snapshot_id']
    args=dict(name='synthetic',snapshots=[snapshot],protection=protection,subjects=subjects,studies=studies,
              annotations=annotations,issues=issues,qualification_policy_sha256=POLICY_SHA256)
    manifest=build_manifest_v3(**args)
    context=dict(manifest=manifest,trusted_manifest_sha256=content_hash(manifest),cohorts_by_id={},
        trusted_cohort_sha256={},qualifications_by_id={},trusted_qualification_sha256={},
        evidence_by_sha256=evidence,trusted_evidence_sha256=set(evidence),trusted_policy_sha256=POLICY_SHA256)
    return args,context


def add_qualification(context,index=0,results=None):
    m=context['manifest'];study=m['studies'][index];aid=study['annotation_ids'][0]
    binding=context_bindings(verified_context(m,study['study_id'],aid,trusted_manifest_sha256=context['trusted_manifest_sha256']))
    checks=[]
    for name in CHECKS:
        result=(results or {}).get(name,'pass')
        data=canonical(dict(schema_version='1.0.0',check=name,bindings=binding,policy_sha256=POLICY_SHA256,result=result))
        sha=digest(data);context['evidence_by_sha256'][sha]=data;context['trusted_evidence_sha256'].add(sha)
        checks.append(dict(name=name,evidence_sha256=sha,result=result))
    q=build_qualification(manifest=m,study_id=study['study_id'],annotation_id=aid,checks=checks,
        **{k:context[k] for k in ('trusted_manifest_sha256','trusted_policy_sha256','evidence_by_sha256','trusted_evidence_sha256')})
    context['qualifications_by_id'][q['qualification_id']]=q
    context['trusted_qualification_sha256'][q['qualification_id']]=content_hash(q)
    return q


def parent(context,role='train'):
    p=build_cohort(cohort_id=f'cohort:base-{role}:v1',cohort_family_id='synthetic',capability='protection_only',
        protected_role=role,study_ids=[r['study_id'] for r in context['manifest']['protection'] if r['protected_role']==role],
        requested_count=2 if role=='train' else 1,parent_ids=[],context=context)
    context['cohorts_by_id'][p['cohort_id']]=p;context['trusted_cohort_sha256'][p['cohort_id']]=content_hash(p)
    return p


def child(context,ids=None,**changes):
    args=dict(cohort_id='cohort:smoke:v1',cohort_family_id='synthetic',capability='executable',protected_role='train',
        study_ids=ids or [context['manifest']['protection'][0]['study_id']],requested_count=1,
        parent_ids=['cohort:base-train:v1'],context=context)
    args.update(changes)
    return build_cohort(**args)
