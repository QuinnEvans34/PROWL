from pathlib import Path
import json
from retained_segmenter_metadata import metadata,fixture_path
from src.data.manifest_records import canonical,digest
from src.data import segmenter_training_inputs_v1 as data,segmenter_v5_targets_v1 as targets
from src.training import segmenter_v5_training_session_v1 as core,segmenter_v5_executor_v1 as e,segmenter_v5_comparison_v1 as comparison
REPO=Path(__file__).resolve().parents[1]
def request(real=False,size=24):
    provider=data.InventedInputs(size);context={n:canonical({'invented':n}) for n in ('source.json','environment.json','geometry.json')};context['lineage.json']=canonical(dict(checkpoint_inventory_sha256=digest(b'invented_inventory'),weight_imports_allowed=False,teacher_models=[],selected_import_sha256=None))
    if real:
        saved=metadata();provider=object.__new__(data.QualifiedInputs);provider.control=saved['training_control'];size=144
    i,controls=core.make_identity(core.config(size=size,steps=6 if size==24 else 48),provider,context,run_id='segmenter-v5-training-unit-launch',device='cpu' if size==24 else 'mps');phase='real' if real else 'rehearsal';cap=json.loads((REPO/('docs/capstone/operations/SEGMENTER-V5-'+phase.upper()+'-STORAGE-PROPOSAL-2026-10-03.json')).read_bytes())['capability']
    scope=dict(domain='invented_native_targets')
    if real:
        old=saved['native_targets'];before=json.loads(fixture_path('accepted-native-baseline.json').read_bytes());cases=[]
        for n,(c,v) in enumerate(zip(old['cases'],saved['cache_entries'])):
            comps=next(s['components'] for s in before['cases'] if s['study_id']==c['study_id']);cases.append(c|dict(transform=v['transform'],transform_sha256=v['transform_sha256'],image_sha256=provider.control['member_sha256'][data.cache.names(n)['image']],reference_components=[{k:q[k] for k in ('component_id','native_voxels','bounds_xyz_half_open','source_boundary_contact')} for q in comps]))
        scope=targets.original_scope(cases,old['files'],old['capability'],digest(b'invented_metadata_pin_for_pure_authorization_test'))
    r=dict(schema_version='1.0.0',task=e.TASK,preparation_decision='D-333',experiment_id='CAP-EXP-014' if real else 'D333-UNIT',identity=i,controls={n:v.decode() for n,v in controls.items()},checkpoint_steps=[0,2,6],evaluation_steps=[0,2,6],targets=scope,baseline=dict(kind='D325_original_native',acceptance_sha256='f4bfcaf0dd63ff066ce8456d66b978e738e8cca8322a6c74fcce23c89b090db2') if real else dict(kind='invented_tensor_diagnostics_no_real_baseline'),source_pins=json.loads(context['source.json']),runtime=json.loads(context['environment.json']),storage_capability_sha256=digest(canonical(cap)),storage_capability=cap,storage_ceilings=[cap["primary_ceiling"],cap["absolute_backup_ceiling"],cap["absolute_backup_ceiling"]],limits=e.LIMITS,initial_weights_sha256=core.INITIAL,weight_imports_allowed=False,continuation_allowed=False,recovery_policy=dict(primary_denied=True,replay_images=7,next_update='invented_only',original_target_reads=0,real_optimizer_calls=0))
    if size==144:r['experiment_id']='CAP-EXP-014' if real else 'D333-INVENTED-REHEARSAL';r['checkpoint_steps']=r['evaluation_steps']=[0,6,24,48]
    if size==144:
        controls['geometry.json']=canonical(dict(target_scope_sha256=digest(canonical(scope)),stage=targets.STAGE));i['geometry_sha256']=digest(controls['geometry.json']);r['controls']={n:v.decode() for n,v in controls.items()}
    r['comparison']=comparison.policy() if real else None
    r['readiness']=dict(kind='qualified_v5_executor_rehearsal',acceptance_sha256='a'*64,producer_receipt_sha256='b'*64,recovery_receipt_sha256='c'*64,tests_sha256='d'*64) if real else dict(kind='D332_numerical_qualification',acceptance_sha256='f7a2f6d941c72ebc346b21a89492725f371ab403e095863ee4a05165df718ea8')
    return r,provider
def approval(r):return canonical(dict(kind='exact_segmenter_v5_launch',decision='D-999-INVENTED-TEST',author='Quinton Evans',user_instruction='Invented authority test only; not a user approval',request_sha256=digest(canonical(r)),identity_sha256=digest(canonical(r['identity'])),real_updates=True,original_final_targets=True,automatic_extension=False,continuation=False))
