from copy import deepcopy
from io import BytesIO
import json
import numpy as np
import pytest
import torch
from src.data import segmenter_training_inputs_v1 as data
from src.training import segmenter_v5_training_session_v1 as c
from src.data.manifest_records import canonical,digest

@pytest.fixture
def provider():return data.InventedInputs(24)
@pytest.fixture
def identity(provider):
 context={n:canonical({'invented':n}) for n in ('source.json','environment.json','geometry.json')};context['lineage.json']=canonical(dict(checkpoint_inventory_sha256=digest(b'invented_inventory'),weight_imports_allowed=False,teacher_models=[],selected_import_sha256=None))
 return c.make_identity(c.config(size=24,steps=6),provider,context,run_id='segmenter-v5-training-unit',device='cpu')

@pytest.mark.parametrize('role,operation,name',[('validation','optimizer','invented-validation'),('train','optimizer','invented-validation'),('validation','evaluator','invented-train-0'),('train','optimizer','held')])
def test_optimizer_role_boundary(provider,role,operation,name):
 with pytest.raises(ValueError):provider.get(name,role=role,operation=operation)
def test_image_only_inference(provider):assert provider.get('invented-validation',role='validation',operation='inference').target is None
@pytest.mark.parametrize('fault',['array','role','operation','id','control'])
def test_mutated_batch_refused(provider,fault):
 b=provider.get('invented-train-0',role='train',operation='optimizer')
 if fault=='array':b.target[0,0,0]=2
 if fault=='role':b.role='validation'
 if fault=='operation':b.operation='evaluator'
 if fault=='id':b.study_id='invented-validation'
 if fault=='control':b.control_sha256='0'*64
 with pytest.raises(ValueError):b.checked(digest(canonical(provider.control)),'optimizer','invented-train-0')
def test_unsealed_batch_refused():
 with pytest.raises(ValueError):data.Batch(object(),study_id='x',role='train',operation='optimizer',image=np.zeros((1,24,24,24),np.float32),target=np.zeros((24,24,24),np.uint8),control_sha256='0'*64)
def test_bare_cohort_records_refused():
 with pytest.raises(ValueError):data.QualifiedInputs(object(),{}, {},{},'0'*64,{})
@pytest.mark.parametrize('seed',['a'*64,'b'*64])
def test_known_and_unknown_imports_denied(seed):
 with pytest.raises(ValueError):c.deny_import(seed,dict(files=[dict(sha256='a'*64)]))
def test_no_public_real_update_grant():
 with pytest.raises(ValueError):c.UpdatePermit(object(),'0'*64,'1'*64)
@pytest.mark.parametrize('fault',['lr','head','jitter','steps','schedule','selection'])
def test_recipe_cannot_silently_change(fault):
 cfg=c.config(size=24,steps=6)
 if fault=='lr':cfg['learning_rate']=.003
 if fault=='head':cfg['architecture']['out_channels']=2
 if fault=='jitter':cfg['jitter']='translation'
 if fault=='steps':cfg['max_steps']=181
 if fault=='schedule':cfg['lr_schedule']='cosine'
 if fault=='selection':cfg['primary_checkpoint']='best_validation'
 with pytest.raises(ValueError):c.validate_config(cfg)
def test_exact_scratch_and_no_import_calls(identity,monkeypatch):
 monkeypatch.setattr(torch,'load',lambda *a,**k:pytest.fail('Scratch creation opened a checkpoint'))
 s=c.Session(*identity);assert c.numerical.state_hash(s.model.state_dict())==c.INITIAL
 with pytest.raises(ValueError):s.import_weights({'weights':'anything'})
def test_sampler_full_epoch_and_replay(provider):
 cfg=c.config(size=24,steps=18);seq=[c.next_member(cfg,provider.control,i) for i in range(18)]
 for start in (0,6,12):assert set(x[0] for x in seq[start:start+6])==set(provider.control['train'])
 assert seq==[c.next_member(cfg,provider.control,i) for i in range(18)]
def test_external_tuple_refused_before_step(identity):
 s=c.Session(*identity);before=c.numerical.state_hash(s.model.state_dict())
 with pytest.raises(ValueError):s.update((np.zeros((1,24,24,24),np.float32),np.zeros((24,24,24),np.uint8)))
 assert s.step==0 and not s.dirty and before==c.numerical.state_hash(s.model.state_dict())
def test_cpu_interruption_recovery_exact(identity,provider):
 torch.set_num_threads(2);s=c.Session(*identity);s.evaluate(provider);s.update(provider);saved=c.payload(s);s.update(provider);expected=c.numerical.cpu_tree(s.model.state_dict());wanted=c.progress(s)
 restored=c.restore_payload(saved,identity[0]);restored.update(provider);assert c.progress(restored)==wanted and all(torch.equal(expected[n],v) for n,v in restored.model.state_dict().items())
 saved=c.payload(restored);old=restored.optimizer.step
 def fail():old();raise RuntimeError('after_mutation')
 restored.optimizer.step=fail
 with pytest.raises(RuntimeError):restored.update(provider)
 assert restored.dirty and restored.step==2
 for f in (lambda:restored.update(provider),lambda:c.payload(restored),lambda:restored.predict(provider.get('invented-train-0',role='train',operation='inference').image)):
  with pytest.raises(ValueError):f()
 assert c.restore_payload(saved,identity[0]).step==2

@pytest.fixture
def saved(identity,provider):
 s=c.Session(*identity);s.evaluate(provider);s.update(provider);return c.payload(s),identity[0]
@pytest.mark.parametrize('fault',['task','run','step','cursor','exposure','member','lr','metric','aggregate','init','lineage','extra','optimizer','head','rng'])
def test_checkpoint_forgery_refused(saved,fault):
 files,i=deepcopy(saved)
 if fault in ('task','run'):i['task' if fault=='task' else 'run_id']='wrong'
 elif fault=='extra':files['junk']=b'x'
 elif fault=='init':
  r=json.loads(files['initialization.json']);r['weight_imports']=['prior'];files['initialization.json']=canonical(r)
 elif fault=='lineage':
  r=json.loads(files['lineage.json']);r['selected_import_sha256']='a'*64;files['lineage.json']=canonical(r)
 elif fault in ('optimizer','head','rng'):
  r=torch.load(BytesIO(files['state.pt']),weights_only=True)
  if fault=='optimizer':r['optimizer']['state'][0]['step']+=1
  if fault=='head':r['model']['conv_final.2.conv.weight']=r['model']['conv_final.2.conv.weight'][:2]
  if fault=='rng':r['cpu_rng']=torch.zeros(1,dtype=torch.float32)
  b=BytesIO();torch.save(r,b);files['state.pt']=b.getvalue()
 else:
  p=json.loads(files['progress.json'])
  if fault=='step':p['step']+=1
  if fault=='cursor':p['sampler']['cursor']+=1
  if fault=='exposure':p['exposure']['invented-train-0']+=1
  if fault=='member':p['history'][0]['member_id']='invented-validation'
  if fault=='lr':p['history'][0]['learning_rate']=.003
  if fault=='metric':p['evaluations'][0]['cases'][0]['metrics']['lesion']['dice']=1.
  if fault=='aggregate':p['evaluations'][0]['aggregate']['train']['cases']=7
  files['progress.json']=canonical(p)
 with pytest.raises((ValueError,KeyError)):c.validate_payload(files,i)


def test_real_domain_requires_separate_launch_permit(identity,provider):
 i,controls=deepcopy(identity);i['domain']='qualified_real_cache';i['config']=c.config(size=144,steps=6)
 ctrl=json.loads(controls['inputs.json']);ctrl['domain']='qualified_real_cache';controls['inputs.json']=canonical(ctrl);i['inputs_sha256']=digest(controls['inputs.json'])
 s=c.Session(i,controls);before=c.numerical.state_hash(s.model.state_dict())
 with pytest.raises(ValueError):s.update(provider)
 assert s.step==0 and not s.dirty and c.numerical.state_hash(s.model.state_dict())==before


def test_absent_class_objective_and_gradients_explicit():
 logits=torch.zeros((1,3,4,4,4),requires_grad=True);target=torch.zeros((1,4,4,4),dtype=torch.long);loss=c.loss_candidate.objective(logits,target,c.config()['loss_id']);assert loss.item()==pytest.approx(np.log(3));loss.backward();assert torch.isfinite(logits.grad).all() and logits.grad[0,2].sum()>0
 logits=torch.zeros((1,3,4,4,4),requires_grad=True);target[0,1:3,1:3,1:3]=1;target[0,2,2,2]=2;loss=c.loss_candidate.objective(logits,target,c.config()['loss_id']);loss.backward();assert torch.isfinite(logits.grad).all() and logits.grad[0,2,2,2,2]<0 and logits.grad[0,1,1,1,1]<0

@pytest.fixture
def qualified(monkeypatch):
 from src.data import segmenter_cache_v1 as ca,segmenter_geometry_v1 as g,segmenter_geometry_loader_v1 as loader
 from src.data.source_inventory_records import content_hash
 records={'optimizer':[],'evaluator':[]};entries=[];files={};rows=[]
 x=np.full((1,144,144,144),.4,np.float32);y=np.zeros((144,144,144),np.uint8);y[40:100,40:100,40:100]=1;y[80:82,80:82,80:82]=2;counts=np.bincount(y.ravel(),minlength=3).tolist()
 for i in range(7):
  op='optimizer' if i<6 else 'evaluator';role='train' if i<6 else 'validation';sid='invented-qualified-'+str(i)
  d=dict(study_id=sid,operation=op,protected_role=role,purpose='pancreas_lesion_segmenter_'+('training' if role=='train' else 'validation'),roi_source='pancreas_only',class_precedence='lesion_over_pancreas',lesion_target_state='positive',image=dict(content_sha256=digest(sid.encode())),geometry=dict(shape_xyz=[8]*3,affine_ras=np.eye(4).ravel().tolist()));records[op].append(d)
  t=g.plan_geometry([8]*3,np.eye(4),[[0,0,0],[8,8,8]],g.recipe(),source_identity=dict(study_id=sid,ct_sha256=d['image']['content_sha256']),roi_origin='provided_pancreas_reference');e=dict(operation=op,descriptor=d,transform=t,transform_sha256=content_hash(t),fidelity=dict(lesion_target_state='positive',source_arrays_changed=False,metrics=dict(pancreas_parenchyma={'tensor_voxels':counts[1]},lesion={'tensor_voxels':counts[2]})),tensor_class_counts=counts);entries.append(e);nm=ca.names(i)
  for k,a in [('image',x),('target',y)]:files[nm[k]]=ca.encode(a)
  rows.append(dict(study_id=sid,protected_role=role,transform_sha256=e['transform_sha256'],tensor_class_counts=counts,files={k:dict(name=n,bytes=len(files[n]),sha256=digest(files[n])) for k,n in nm.items()}))
 b=dict(schema_version=ca.VERSION,cohort_completion_sha256='a'*64,descriptor_sha256=content_hash(records),geometry_acceptance_sha256='b'*64,records=records,entries=entries,model_updates_allowed=False);pin=content_hash(b);files['binding.json']=canonical(b);files['production.json']=canonical(dict(schema_version=ca.VERSION,binding_sha256=pin,request_sha256='c'*64,code_pins={},runtime={},source_counts=dict(hash_bytes=21,decode_bytes=21,expanded_bytes=21),cases=rows,model_updates=0,source_arrays_read=21));monkeypatch.setattr(loader,'COMPLETION','a'*64);monkeypatch.setattr(loader,'DESCRIPTORS',content_hash(records));session=loader.ResolvedInputs(records,loader._TOKEN)
 return data.QualifiedInputs(data._TOKEN,session,files,b,pin,dict(artifact_id='invented_cache',receipt_sha256='d'*64,derivation_sha256='c'*64))

def test_qualified_optimizer_and_inference_parity(qualified):
 b=qualified.get('invented-qualified-0',role='train',operation='optimizer');inf=qualified.get('invented-qualified-0',role='train',operation='inference');assert np.array_equal(b.image,inf.image) and inf.target is None and (b.target==2).sum()==8
@pytest.mark.parametrize('fault',['validation','held','wrong_role','payload','roles'])
def test_qualified_boundary_refusal_before_decode(qualified,monkeypatch,fault):
 name='invented-qualified-0';role='train'
 if fault=='validation':name='invented-qualified-6';role='validation'
 if fault=='held':name='held'
 if fault=='wrong_role':role='validation'
 if fault=='payload':qualified._files['case-00-target.npy']+=b'x'
 if fault=='roles':qualified._session.records['optimizer'][0]['protected_role']='validation'
 monkeypatch.setattr(data.cache,'decode',lambda *a:pytest.fail('Array decoded after boundary refusal'))
 with pytest.raises(ValueError):qualified.get(name,role=role,operation='optimizer')

@pytest.mark.parametrize('fault',['class_count','component_bounds','component_size'])
def test_consistent_tensor_reference_forgery_refused(saved,fault):
 files,i=deepcopy(saved);p=json.loads(files['progress.json']);r=p['evaluations'][0]['cases'][0]
 if fault=='class_count':r['confusion_matrix'][0][0]-=1;r['confusion_matrix'][1][0]+=1;r['metrics']=c.scoring.from_confusion(r['confusion_matrix'])
 if fault=='component_bounds':r['components'][0]['bounds_xyz_half_open'][0][0]+=1
 if fault=='component_size':r['components'][0]['native_voxels']+=1
 p['evaluations'][0]['aggregate']=c.scoring.aggregates(p['evaluations'][0]['cases']);files['progress.json']=canonical(p)
 with pytest.raises(ValueError):c.validate_payload(files,i)

@pytest.mark.parametrize('fault',['run','step','derivation'])
def test_production_resume_refuses_unbound_reference_before_store(identity,fault):
 from types import SimpleNamespace
 i=identity[0];ref=dict(step=0,artifact_id=f"{i['run_id']}:step:0",derivation_sha256=digest(canonical(dict(identity=i,step=0))),receipt_sha256='a'*64)
 if fault=='run':ref['artifact_id']='other-run:step:0'
 if fault=='step':ref['step']=1
 if fault=='derivation':ref['derivation_sha256']='0'*64
 with pytest.raises(ValueError):c.resume(SimpleNamespace(resolve=lambda *a,**k:pytest.fail('Unbound resume read store')),ref,i)

def test_production_completion_bound_resume_and_changed_bytes(identity,provider,tmp_path):
 from src.operations.artifact_store import ArtifactStore
 s=c.Session(*identity);s.update(provider);st=ArtifactStore(tmp_path,check_root=lambda:None,max_bytes=192*1024**2,minimum_free_bytes=0);ref=c.publish_checkpoint(st,s);restored=c.resume(st,ref,identity[0]);assert c.numerical.state_hash(restored.model.state_dict())==c.numerical.state_hash(s.model.state_dict()) and c.tree_exact(restored.optimizer.state_dict(),s.optimizer.state_dict())
 child=tmp_path/digest(ref['artifact_id'].encode());withstate=child/'state.pt';withstate.write_bytes(withstate.read_bytes()+b'x')
 with pytest.raises(ValueError):c.resume(st,ref,identity[0])

def test_production_interrupted_publication_not_resolvable(identity,tmp_path):
 from src.operations.artifact_store import ArtifactStore
 s=c.Session(*identity);files=c.payload(s);st=ArtifactStore(tmp_path,check_root=lambda:None,max_bytes=192*1024**2,minimum_free_bytes=0);calls=0
 def check(f):
  nonlocal calls
  calls+=1
  if calls==2:raise ValueError('injected persisted validation failure')
  return c.validate_payload(f,identity[0])
 meta=dict(artifact_type='segmenter-v5-training-checkpoint',schema_version='1.0.0',component=c.TASK,code_sha256=identity[0]['source_sha256'],parents=[],retention='invented',sensitivity='synthetic',run_id=identity[0]['run_id'],stage_id='checkpoint')
 aid=identity[0]['run_id']+':step:0'
 with pytest.raises(ValueError):st.publish(aid,derivation_sha256='a'*64,files=files,metadata=meta,validate=check)
 assert not (tmp_path/digest(aid.encode())).exists() and list(tmp_path.glob('.attempt-*'))
