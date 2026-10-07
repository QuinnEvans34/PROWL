"""Invented unit controls and retained numeric metadata; no actual payload or execution grant."""
from copy import deepcopy
from pathlib import Path
import json
import torch
from src.data.manifest_records import canonical,digest
from src.data import segmenter_training_inputs_v1 as inputs,segmenter_duration_targets_v1 as targets
from src.training import segmenter_duration_session_v1 as core,segmenter_duration_executor_v1 as engine,segmenter_duration_policy_v1 as policy
from src.operations.segmenter_duration_storage_v1 import GIB
REPO=Path(__file__).resolve().parents[1]


def count_row(name,role='train',*,fp=100,boundary=False):
    return dict(case_id=name,role=role,status='valid',reason=None,reported_metrics=None,counts=dict(confusion_matrix=[[800-fp,100,fp],[0,100,0],[0,0,100]],components=[dict(component_id=1,reference_voxels=100,true_positive=100)],voxel_volume_mm3=12.,source_boundary_contact=boundary))


def request(kind='unit'):
    p=inputs.InventedInputs(24);scope=dict(domain='invented_unit_targets');size=24
    if kind!='unit':
        # Pinned portable descriptors/geometry/counts only; no cache or NIfTI payloads included.
        from segmenter_v5_fixtures import request as old_request
        old,p=old_request(real=True);size=144
        oldscope=old['targets'];scope=targets.original_scope(oldscope['cases'],oldscope['files'],oldscope['capability'],oldscope['metadata_receipt_sha256'])
        if kind=='native_rehearsal':
            q=object.__new__(inputs.InventedInputs);q.control=deepcopy(p.control);q.control['domain']='invented_arrays_only'
            q.control['member_sha256']={n:dict(image=p.control['member_sha256'][core.cache.names(i)['image']],target=p.control['member_sha256'][core.cache.names(i)['target']]) for i,n in enumerate(p.control['train']+p.control['validation'])};p=q;scope['domain']='invented_native_targets'
    source={'src/training/segmenter_duration_session_v1.py':digest((REPO/'src/training/segmenter_duration_session_v1.py').read_bytes())}
    if kind!='unit':source|={n:digest((REPO/n).read_bytes()) for n in engine.REQUIRED_CODE}
    context={n:canonical({'invented_only':n}) for n in ('environment.json','geometry.json')}
    context['source.json']=canonical(source);context['lineage.json']=canonical(dict(checkpoint_inventory_sha256=digest(b'invented_inventory'),weight_imports_allowed=False,teacher_models=[],selected_import_sha256=None))
    if kind!='unit':context['geometry.json']=canonical(dict(target_scope_sha256=digest(canonical(scope)),stage=targets.STAGE))
    i,controls=core.make_identity(core.config(size=size,steps=6 if size==24 else 192),p,context,run_id='segmenter-duration-training-unit',device='cpu' if size==24 else 'mps')
    names=p.control['train'];report=p.control['validation'][0]
    baseline=dict(schema_version='1.0.0',kind=policy.BASELINE_KIND,cases=[count_row(n,boundary=n==names[1]) for n in names]+[count_row(report,'report_only')])
    rules=policy.build_policy(baseline,trusted_baseline_sha256=policy.record_digest(baseline),tiny_case_id=names[0],boundary_case_id=names[1])
    cap=dict(schema_version='1.0.0',operation='duration_transaction_v1',phase='real' if kind=='scientific' else 'rehearsal',namespace='segmenter-duration-unit',registry_sha256='a'*64,primary_volume_uuid='invented-external',backup_volume_uuid='invented-internal',backup_baseline_bytes=17341924636,absolute_backup_ceiling=26*GIB,maximum_new_backup_bytes=8*GIB,child_ceiling=2*GIB,phase_ceiling=4*GIB,minimum_free_bytes=100*GIB,control_reserve_bytes=64*1024**2)
    unit=kind=='unit'
    readiness=dict(kind='invented_unit_only') if unit else dict(kind='qualified_duration_native_v1' if kind=='scientific' else 'frozen_v5_numerics_v1',acceptance_sha256='a'*64)
    if kind=='scientific':readiness|=dict(producer_sha256='b'*64,recovery_sha256='c'*64,tests_sha256='d'*64)
    r=dict(schema_version='1.0.0',task=engine.TASK,kind=kind,experiment_id='DURATION-INVENTED-AUTHORIZATION-TEST',identity=i,controls={n:v.decode() for n,v in controls.items()},checkpoint_steps=[0,2,4,6] if unit else [0,48,96,144,192],screen_steps=[2,4,6] if unit else [48,96,144,192],policy=rules,policy_sha256=policy.record_digest(rules),targets=scope,source_pins=source,runtime=json.loads(context['environment.json']),storage_capability=None if unit else cap,storage_capability_sha256=None if unit else digest(canonical(cap)),limits=deepcopy(engine.UNIT_LIMITS if unit else engine.LIMITS),readiness=readiness,input_cache=dict(area='segmenter-input-cache',acceptance_sha256='8b21315b14e38a6f582964a274d430ce768af9fb8348c8858c9ece62221125f3',request_sha256='d84cdcdc828410ed4603dccf1bab29ecf6d0e9154f9a4f6f3f9f9cd0bc613364',payload_bytes=104509440) if kind=='scientific' else None,imports_allowed=False,extension_allowed=False,recovery_policy=dict(primary_denied=True,original_target_reads=0,original_ct_reads=0,real_optimizer_calls=0,automatic_restart=False),screen_mode='engineering_native_counts' if kind=='native_rehearsal' else 'duration_policy',model_calls=engine.call_limits(kind))
    return r,p


def approval(r):
    return canonical(dict(kind='exact_duration_job_v1',author='Quinton Evans',user_instruction='INVENTED AUTHORIZATION TEST; not human launch approval',request_sha256=digest(canonical(r)),identity_sha256=digest(canonical(r['identity'])),job_kind=r['kind'],model_calls=r['model_calls'],screen_mode=r['screen_mode'],original_target_reads=50 if r['kind']=='scientific' else 0,original_ct_reads=0,extension=False,restart=False))


def screen_record(r,step,*,fp=100):
    mapped=engine.policy_step(r,step);names=json.loads(r['controls']['inputs.json'])
    rows=[count_row(n,fp=fp,boundary=n==names['train'][1]) for n in names['train']]
    if mapped==192:rows.append(count_row(names['validation'][0],'report_only',fp=fp))
    return dict(schema_version='1.0.0',policy_sha256=r['policy_sha256'],baseline_sha256=r['policy']['baseline_sha256'],step=mapped,outcomes=rows)


class FakeModel:
    def state_dict(self):return {'invented-counter':torch.zeros(1)}


class FakeSession:
    def __init__(self,identity,controls):
        self.identity=deepcopy(identity);self.config=deepcopy(identity['config']);self.control=json.loads(controls['inputs.json']);self.step=0;self.dirty=False;self.model=FakeModel();self.history=[];self.evaluated=[]
    def update(self,provider,permit=None):
        member,trace=core.next_member(self.config,self.control,self.step);self.step+=1
        row=dict(completed_step=self.step,member_id=member,sampling=trace);self.history.append(row);return row
    def evaluate(self,provider):self.evaluated.append((self.step,self.step==self.config['max_steps']))
    def predict(self,image):return 'mock_no_model_forward'


def checkpoint(s):
    aid=s.identity['run_id']+':step:'+str(s.step)
    return dict(step=s.step,primary=dict(artifact_id=aid,receipt_sha256='a'*64,derivation_sha256='b'*64,step=s.step),backup=dict(artifact_id='backup:'+aid,receipt_sha256='c'*64,derivation_sha256='d'*64),weights_sha256=core.numerical.state_hash(s.model.state_dict()))


def screen_pair(r,s,fp=100):
    record=screen_record(r,s.step,fp=fp);aid=s.identity['run_id']+':screen:'+str(s.step)
    return record,dict(step=s.step,screen_sha256=digest(canonical(record)),primary=dict(artifact_id=aid,receipt_sha256='a'*64),backup=dict(artifact_id='backup:'+aid,receipt_sha256='b'*64))
