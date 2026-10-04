"""Invented source/permissions only; never load arrays or manufacture real attestations."""
from copy import deepcopy
from qualification_fixtures import fixture as old_fixture
from src.data.manifest_records import canonical,digest
from src.data.manifest_records_v3 import build_manifest_v3
from src.data.source_inventory_records import build_source_snapshot_v2,content_hash
from src.data.segmenter_qualification_v1 import POLICY_SHA256,CHECKS,context_for,context_bindings,build_qualification
from src.data.cohort_records_v3 import build_cohort as build_parent
from src.data.segmenter_cohort_v1 import build_cohort

TRAIN='pancreas_lesion_segmenter_training'
VAL='pancreas_lesion_segmenter_validation'


def fixture(negative=False):
    args,ctx=old_fixture(); snap=args['snapshots'][0]
    for s,a in zip(args['studies'],list(args['annotations'])):
        lesion=deepcopy(a);lesion['annotation_id']=a['annotation_id'].replace('pancreas','lesion')
        lesion.update(structure='lesion',source_structure='pancreatic_lesion')
        # Keep the inherited unit hold attached to the original pancreas annotation only.
        lesion.update(status='eligible',issue_ids=[],allowed_uses=['training_target','evaluation_reference'])
        lesion['label_encoding']['mapping']['canonical_foreground']=2
        lesion['file']['uri']=lesion['file']['uri'].replace('pancreas','pancreatic_lesion')
        lesion['file']['content_sha256']=digest(('synthetic-lesion:'+s['study_id']).encode())
        lesion['label_encoding']['audit_source_sha256']=lesion['file']['content_sha256']
        if negative and s==args['studies'][0]:
            lesion['label_encoding'].update(value_counts=[dict(value=0,count=4)],stored_range=[0,0])
        if a['status']=='eligible':a['allowed_uses']=['training_target','evaluation_reference']
        args['annotations'].append(lesion);s['annotation_ids']=sorted([a['annotation_id'],lesion['annotation_id']])
        s['target_statuses'].append(dict(target='pancreatic_lesion',status='negative' if negative and s==args['studies'][0] else 'positive',
            method='reference_standard' if negative and s==args['studies'][0] else 'annotation_voxel_presence',reference_id=lesion['annotation_id']))
        expected=dict(study_id=s['study_id'],kind='lesion',uri=lesion['file']['uri'])
    snapshot=build_source_snapshot_v2(source_version=snap['source_version'],license=snap['license'],root_alias=snap['root_alias'],
        study_ids=snap['scope']['study_ids'],expected_files=snap['scope']['expected_files'],observed_files=snap['observed_files'],control_sha256=snap['scope']['control_sha256'])
    args['snapshots']=[snapshot]
    for key in ['subjects','studies','annotations']:
        for r in args[key]:r['source_snapshot_id']=snapshot['source_snapshot_id']
    args['qualification_policy_sha256']=POLICY_SHA256;refresh(args,ctx)
    return args,ctx


def refresh(args,ctx):
    m=build_manifest_v3(**args);ctx.update(manifest=m,trusted_manifest_sha256=content_hash(m),trusted_policy_sha256=POLICY_SHA256)


def qualify(ctx,index=0,results=None,negative_basis=True,receipt_change=None):
    m=ctx['manifest'];s=m['studies'][index];anns={a['structure']:a for a in m['annotations'] if a['annotation_id'] in s['annotation_ids']}
    purpose=TRAIN if index<2 else VAL
    context=context_for(m,s['study_id'],anns['pancreas']['annotation_id'],anns['lesion']['annotation_id'],trusted_manifest_sha256=ctx['trusted_manifest_sha256'])
    binding=context_bindings(context);checks=[]
    def add(raw):
        b=canonical(raw);pin=digest(b);ctx['evidence_by_sha256'][pin]=b;ctx['trusted_evidence_sha256'].add(pin);return pin
    count=sum(r['count'] for r in anns['lesion']['label_encoding']['value_counts'] if r['value']==1)
    basis=add(dict(component='segmenter-negative-reference-v1',purpose=purpose,bindings=binding,
        status='verified_no_visible_lesion',basis='Invented reviewed complete negative reference')) if not count and negative_basis else None
    g=s['geometry'];details={name:{} for name in CHECKS}
    details['geometry']=dict(ct_units='mm',source_shape=g['shape_xyz'],source_affine=g['affine_ras'])
    for kind in ['pancreas','lesion']:details['geometry'].update({kind+'_shape':g['shape_xyz'],kind+'_affine':g['affine_ras'],kind+'_units':'matched_mm_ct_grid'})
    inventory=dict(schema_version='1.0.0',component='segmenter-lesion-inventory-v1',state='present',
        study_id=s['study_id'],source_snapshot_id=context['snapshot']['source_snapshot_id'],
        source_version_sha256=content_hash(context['snapshot']['source_version']),file=anns['lesion']['file'])
    details['source_readiness']=dict(lesion_inventory_sha256=add(inventory))
    details['pancreas_target']=dict(classification='positive',foreground_voxels=1)
    details['lesion_target']=dict(classification='positive' if count else 'verified_negative',foreground_voxels=count,negative_basis_sha256=basis)
    for name in CHECKS:
        result=(results or {}).get(name,'pass')
        r=dict(schema_version='1.0.0',component='segmenter-check-v1',purpose=purpose,check=name,bindings=binding,policy_sha256=POLICY_SHA256,result=result,details=deepcopy(details[name]))
        if receipt_change:receipt_change(name,r)
        checks.append(dict(name=name,result=result,evidence_sha256=add(r)))
    q=build_qualification(manifest=m,study_id=s['study_id'],pancreas_annotation_id=anns['pancreas']['annotation_id'],
        lesion_annotation_id=anns['lesion']['annotation_id'],checks=checks,purpose=purpose,
        **{k:ctx[k] for k in ['trusted_manifest_sha256','trusted_policy_sha256','evidence_by_sha256','trusted_evidence_sha256']})
    ctx['qualifications_by_id'][q['qualification_id']]=q;ctx['trusted_qualification_sha256'][q['qualification_id']]=content_hash(q)
    return q


def cohort(ctx,index=0):
    role='train' if index<2 else 'validation';purpose=TRAIN if role=='train' else VAL
    ids=[r['study_id'] for r in ctx['manifest']['protection'] if r['protected_role']==role]
    parent=build_parent(cohort_id=f'cohort:segmenter-protection-{role}:v1',cohort_family_id='segmenter-synthetic',capability='protection_only',
        protected_role=role,study_ids=ids,requested_count=len(ids),parent_ids=[],context=ctx)
    ctx['cohorts_by_id'][parent['cohort_id']]=parent;ctx['trusted_cohort_sha256'][parent['cohort_id']]=content_hash(parent)
    return build_cohort(name='synthetic-'+role,study_ids=[ctx['manifest']['studies'][index]['study_id']],requested_count=1,purpose=purpose,parent_id=parent['cohort_id'],context=ctx)
