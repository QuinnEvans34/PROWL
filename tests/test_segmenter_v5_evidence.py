from copy import deepcopy
import json
import numpy as np
import pytest
from segmenter_v5_fixtures import request
from src.data.manifest_records import canonical,digest
from src.data import segmenter_geometry_v1 as geometry
from src.training import segmenter_v5_evidence_v1 as e,segmenter_v5_executor_v1 as executor,segmenter_v5_training_session_v1 as core
@pytest.fixture(scope='module')
def exported():
 r,provider=request(size=144);identity=r['identity'];sid=provider.control['train'][0];x=provider.get(sid,role='train',operation='inference').image
 t=geometry.plan_geometry([8]*3,np.eye(4),[[0,0,0],[8]*3],geometry.recipe(),source_identity=dict(study_id=sid,ct_sha256=digest(b'invented')),roi_origin='provided_pancreas_reference')
 case=dict(study_id=sid,protected_role='train',transform=t,transform_sha256=digest(canonical(t)),image_sha256=digest(core.cache.encode(x)));p=np.empty((3,144,144,144),np.float32);p[0]=.1;p[1]=.2;p[2]=.7;weights=digest(b'invented_trained_weights')
 files,report=e.export(p,case,identity,48,weights);return files,dict(identity=identity,case=case,step=48,weights_sha256=weights)
def test_trained_export_truthful_step_and_native_inverse(exported):
 f,c=exported;r=json.loads(f['export.json']);assert r['completed_updates']==48 and r['task']==e.EXPORT_TASK and r['weights_sha256']==c['weights_sha256'];assert e.validate_export(f,c)['step']==48
@pytest.mark.parametrize('fault',['step0','head','task','weights','role','geometry','hash','mask','extra','scope','image'])
def test_trained_export_refuses_wrong_task_or_provenance(exported,fault):
 f,c=deepcopy(exported);r=json.loads(f['export.json'])
 if fault=='step0':r['completed_updates']=0
 if fault=='head':c['identity']['config']['architecture']['out_channels']=2
 if fault=='task':r['task']='pancreas_localizer'
 if fault=='weights':r['weights_sha256']='0'*64
 if fault=='role':r['protected_role']='validation'
 if fault=='geometry':r['source_shape'][0]+=1
 if fault=='hash':r['native_sha256']='0'*64
 if fault=='mask':f['mask.npy']+=b'x'
 if fault=='extra':f['unused']=b'x'
 if fault=='scope':r['native_reference_metrics']='original_truth_is_cached_targets'
 if fault=='image':r['image_sha256']='0'*64
 f['export.json']=canonical(r)
 with pytest.raises(ValueError):e.validate_export(f,c)
@pytest.fixture
def summary(tmp_path):
 from test_segmenter_native_score_transaction import evidence as old
 native,old_identity=old.__wrapped__();projection=old_identity['request'];r,_=request();cases=deepcopy(projection['cases']);scores=json.loads(native['scores.json'])
 for c,s in zip(cases,scores):
  c['reference_components']=[{k:v[k] for k in ('component_id','native_voxels','bounds_xyz_half_open','source_boundary_contact')} for v in s['components']]
  t=geometry.plan_geometry([4]*3,np.eye(4),[[0,0,0],[4]*3],geometry.recipe(),source_identity=dict(study_id=c['study_id'],ct_sha256=digest(b'invented')),roi_origin='provided_pancreas_reference');c|=dict(transform=t,transform_sha256=digest(canonical(t)),image_sha256=digest(('image'+c['study_id']).encode()))
 r['targets']=dict(domain='invented_native_targets',cases=cases,files=projection['files'],limits=projection['limits']);i=r['identity'];weights=digest(b'invented_terminal');steps=r['checkpoint_steps'];checkpoints=[]
 for step in steps:
  primary=dict(artifact_id=i['run_id']+':step:'+str(step),receipt_sha256='a'*64,derivation_sha256=digest(canonical(dict(identity=i,step=step))),step=step);checkpoints.append(dict(primary=primary,backup=dict(artifact_id='backup:'+primary['artifact_id'],receipt_sha256='b'*64),weights_sha256=weights))
 exports=[]
 for c,s,old_export in zip(cases,scores,projection['prediction_exports']):
  report=old_export|dict(study_id=c['study_id'],protected_role=c['protected_role'],task=e.EXPORT_TASK,identity_sha256=digest(canonical(i)),source_shape=[4]*3,source_affine=c['transform']['source_affine'],transform_sha256=c['transform_sha256'],image_sha256=c['image_sha256'],probability_sha256=digest(b'invented_probability'),inverse='continuous_three_channel_then_argmax',outside_roi='background',native_reference_metrics='separate_original_reference_scoring',completed_updates=6,weights_sha256=weights);primary=dict(artifact_id=i['run_id']+':native:'+c['study_id'],receipt_sha256='c'*64);exports.append(dict(primary=primary,backup=dict(artifact_id='backup:'+primary['artifact_id'],receipt_sha256='d'*64),report=report))
 projection=e.scoring_request(r,[v['report'] for v in exports]);native['request.json']=canonical(projection);production=json.loads(native['production.json']);production|=dict(request_sha256=digest(canonical(projection)),code_pins=r['source_pins'],runtime=r['runtime']);native['production.json']=canonical(production)
 path=tmp_path/'journal';j=executor.Journal(path,r);j.append(dict(state='attempt_started'))
 for step in steps:
  if step:
   previous=steps[steps.index(step)-1]
   for n in range(previous+1,step+1):j.append(dict(state='update_complete',completed_step=n))
  j.append(dict(state='tensor_evaluation_complete',step=step));j.append(dict(state='checkpoint_durable',step=step))
 j.append(dict(state='transaction_verified'));j.close();raw=path.read_bytes();_,last=executor.verify_journal(raw,r)
 def pair(suffix):return dict(primary=dict(artifact_id=i['run_id']+suffix,receipt_sha256='e'*64),backup=dict(artifact_id='backup:'+i['run_id']+suffix,receipt_sha256='f'*64))
 result=dict(task=e.SUMMARY_TASK,state='complete',request_sha256=digest(canonical(r)),identity_sha256=digest(canonical(i)),completed_steps=6,weights_sha256=weights,checkpoints=checkpoints,exports=exports,probe_reference=pair(':probes'),images_reference=pair(':images'),exposure={n:1 for n in json.loads(r['controls']['inputs.json'])['train']},journal_sha256=digest(raw),last_event_sha256=last,native_evidence_sha256={n:digest(v) for n,v in native.items()},comparison_result=None,seconds=1.)
 files={'request.json':canonical(r),'completion.json':canonical(result),'journal.jsonl':raw}|{('native-request.json' if n=='request.json' else n):v for n,v in native.items()};return files,r
def test_complete_training_summary_binds_original_counts(summary):assert e.validate_summary(*summary)['native_cases']==7
@pytest.mark.parametrize('fault',['missing','step','weights','checkpoint','keeper','export_step','export_weights','images','probe','exposure','dice','component','bounds','reference','counts','journal','native_pin','extra'])
def test_training_summary_refuses_incomplete_or_forged_results(summary,fault):
 files,r=deepcopy(summary);result=json.loads(files['completion.json']);scores=json.loads(files['scores.json']);production=json.loads(files['production.json'])
 if fault=='missing':files.pop('references.json')
 if fault=='step':result['completed_steps']=0
 if fault=='weights':result['weights_sha256']='0'*64
 if fault=='checkpoint':result['checkpoints'].pop()
 if fault=='keeper':result['checkpoints'][-1]['backup']['artifact_id']='other'
 if fault=='export_step':result['exports'][0]['report']['completed_updates']=0
 if fault=='export_weights':result['exports'][0]['report']['weights_sha256']='0'*64
 if fault=='images':result['images_reference']['primary']['artifact_id']='other'
 if fault=='probe':result['probe_reference']['backup']['artifact_id']='other'
 if fault=='exposure':result['exposure'][next(iter(result['exposure']))]=2
 if fault=='dice':scores[0]['metrics']['lesion']['dice']=1.
 if fault=='component':scores[0]['components'].pop()
 if fault=='bounds':scores[0]['components'][0]['bounds_xyz_half_open'][0][0]=0
 if fault=='reference':ref=json.loads(files['references.json']);ref[0]['read']['sha256']='0'*64;files['references.json']=canonical(ref)
 if fault=='counts':production['source_counts']['hash_bytes']+=1
 if fault=='journal':files['journal.jsonl']+=canonical(dict(sequence=999,previous_sha256='0'*64,event={'state':'transaction_verified'}))
 if fault=='native_pin':result['native_evidence_sha256']['scores.json']='0'*64
 if fault=='extra':files['unused']=b'x'
 files['completion.json']=canonical(result);files['scores.json']=canonical(scores);files['production.json']=canonical(production)
 with pytest.raises((ValueError,KeyError)):e.validate_summary(files,r)

def test_cached_roi_review_view_preserves_original_arrays_and_labels(exported):
 from src.data.segmenter_training_views_v1 import render
 from io import BytesIO
 from PIL import Image
 files,c=exported;case=deepcopy(c['case']);case['reference_components']=[dict(component_id=1,bounds_xyz_half_open=[[1,2],[1,2],[1,2]])];pan=np.ones((8,8,8),np.uint8);les=np.zeros_like(pan);les[1,1,1]=1;pred=np.zeros_like(pan);pred[2,2,2]=2;x=np.full((1,144,144,144),.4,np.float32);before=[a.copy() for a in (x,pan,les,pred)]
 png,record=render(x,pan,les,pred,case,48,c['weights_sha256']);assert Image.open(BytesIO(png)).width==1440 and record['display_only'] and record['outside_roi_CT_information'] is False and record['source']=='normalized_cached_ROI_display_not_original_CT' and record['png_sha256']==digest(png)
 assert all(np.array_equal(a,b) for a,b in zip((x,pan,les,pred),before))

@pytest.fixture
def probes(summary):
 from src.training import segmenter_training_probe_v1 as oldprobe
 files,r=summary;completion=json.loads(files['completion.json']);r=deepcopy(r);c=deepcopy(completion['exports']);x=np.full((1,24,24,24),.4,np.float32);raw=core.cache.encode(x);r['targets']['cases'][0]['image_sha256']=digest(raw);c[0]['report']['image_sha256']=digest(raw);p=np.empty((3,24,24,24),np.float32);p[0]=.2;p[1]=.3;p[2]=.5;model=core.scratch(r['identity']['config']);weights=oldprobe.encode_weights(model);pin=core.numerical.state_hash(model.state_dict());manifest=e.probe_manifest(r['identity'],r['checkpoint_steps'],completion['checkpoints'],pin,r['targets']['cases'],c)
 return {'manifest.json':canonical(manifest),'image.npy':raw,'next-weights.pt':weights}|{f'prob-{n}.npy':core.cache.encode(p) for n in r['checkpoint_steps']},r

def test_protected_probe_inventory_valid(probes):
 f,r=probes;assert e.validate_probes(f,r['identity'],r)['steps']==[0,2,6]

@pytest.mark.parametrize('fault',['source','checkpoint','step','weights','task','probability','extra','export'])
def test_protected_probes_refuse_forged_binding(probes,fault):
 f,r=deepcopy(probes);m=json.loads(f['manifest.json'])
 if fault=='source':m['cases'][0]['study_id']='other'
 if fault=='checkpoint':m['checkpoints'][0]['primary']['artifact_id']='other'
 if fault=='step':m['next_weights_step']=4
 if fault=='weights':m['next_weights_sha256']='0'*64
 if fault=='task':m['task']='localizer'
 if fault=='probability':f['prob-2.npy']=core.cache.encode(np.zeros((3,24,24,24),np.float32))
 if fault=='extra':f['unused']=b'x'
 if fault=='export':m['exports'][0]['report']['image_sha256']='0'*64
 f['manifest.json']=canonical(m)
 with pytest.raises(ValueError):e.validate_probes(f,r['identity'],r)

@pytest.mark.parametrize('fault',['approval','artifact','omission','same_domain','bytes'])
def test_short_keeper_rejects_wrong_provenance(fault):
 from test_segmenter_training_backup import fixture as old_fixture
 from src.operations.segmenter_v5_backup_v1 import validate_backup
 files,ref,validator=old_fixture.__wrapped__();cat=json.loads(files['catalog.json']);cat['approval']='D-333'
 if fault=='approval':cat['approval']='D-327'
 if fault=='artifact':
  completion=json.loads(files['primary-complete.json']);completion['metadata']['artifact_type']='localizer-checkpoint';files['primary-complete.json']=canonical(completion);ref['receipt_sha256']=digest(files['primary-complete.json']);cat['source_reference']=ref
 if fault=='omission':cat['omissions']=['state.pt']
 if fault=='same_domain':cat['destination_domain']=cat['source_domain']
 if fault=='bytes':files['state.pt']+=b'x'
 files['catalog.json']=canonical(cat)
 with pytest.raises(ValueError):validate_backup(files,{},ref,validator)
