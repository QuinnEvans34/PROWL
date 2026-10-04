# Isolated D-333 v5 version; v3 producing source is preserved.
"""Trained native exports and original-reference evidence; unchanged numerical codecs."""
from copy import deepcopy
import json
import numpy as np
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training import segmenter_v5_training_session_v1 as core,segmenter_inference_v1 as codec,segmenter_native_scoring_v1 as scoring

EXPORT_TASK='segmenter_v5_trained_native_export_v1'
SUMMARY_TASK='segmenter_v5_run_summary_v1'
PROBE_TASK='segmenter_v5_run_probes_v1'

def validate_images(files,request):
    require(sum(map(len,files.values()))<=96*1024**2,'Recovery image budget');require(set(files)=={'manifest.json'}|{f'image-{n:02d}.npy' for n in range(7)},'Recovery image inventory')
    require(files['manifest.json']==canonical(dict(task='segmenter_v5_recovery_images_v1',request_sha256=digest(canonical(request)),cases=request['targets']['cases'])),'Recovery image lineage')
    for n,c in enumerate(request['targets']['cases']):
        raw=files[f'image-{n:02d}.npy'];require(digest(raw)==c['image_sha256'],'Recovery image hash');x=codec.decode_array(raw,[1,144,144,144],'float32');require(np.isfinite(x).all() and x.min()>=0 and x.max()<=1,'Recovery image values')
    return dict(task='segmenter_v5_recovery_images_v1',request_sha256=digest(canonical(request)),members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})

def export(probability,case,identity,step,weights_sha256,*,tick=lambda:None):
    core.validate_identity(identity);require(type(step) is int and step==identity['config']['max_steps'] and len(weights_sha256)==64,'Wrong committed terminal export')
    mask,report=codec.export(probability,case,tick=tick)
    report=report|dict(task=EXPORT_TASK,identity_sha256=digest(canonical(identity)),completed_updates=step,weights_sha256=weights_sha256,native_reference_metrics='separate_original_reference_scoring')
    files={'mask.npy':codec.array_bytes(mask),'export.json':canonical(report)};validate_export(files,dict(identity=identity,case=case,step=step,weights_sha256=weights_sha256));return files,report

def validate_export(files,context):
    require(len(files['export.json'])<=1024**2,'Native export report budget');require(set(files)=={'mask.npy','export.json'},'Trained export inventory');r=json.loads(files['export.json']);i=context['identity'];core.validate_identity(i)
    validate_export_record(r,context)
    projected={k:v for k,v in r.items() if k not in ('task','identity_sha256','weights_sha256')}|dict(completed_updates=0,native_reference_metrics='not_scored')
    codec.validate_export(files['mask.npy'],projected,context['case'])
    return dict(task=EXPORT_TASK,step=context['step'],weights_sha256=context['weights_sha256'],identity_sha256=r['identity_sha256'],study_id=r['study_id'],native_sha256=r['native_sha256'],members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})

def validate_export_record(r,context):
    i=context['identity'];case=context['case'];core.validate_identity(i)
    require(set(r)=={'task','identity_sha256','weights_sha256'}|{'study_id','protected_role','source_shape','source_affine','transform_sha256','image_sha256','probability_sha256','native_sha256','class_counts','inverse','outside_roi','completed_updates','native_reference_metrics'},'Trained export fields')
    require(r['task']==EXPORT_TASK and r['identity_sha256']==digest(canonical(i)) and r['weights_sha256']==context['weights_sha256'] and type(r['completed_updates']) is int and r['completed_updates']==context['step']==i['config']['max_steps'] and r['native_reference_metrics']=='separate_original_reference_scoring','Wrong trained task/weights/step')
    require(all(r[k]==case[k] for k in ('study_id','protected_role','transform_sha256','image_sha256')) and r['source_shape']==case['transform']['source_shape'] and r['source_affine']==case['transform']['source_affine'] and r['inverse']=='continuous_three_channel_then_argmax' and r['outside_roi']=='background','Trained export source/role/policy')
    require(len(r['class_counts'])==3 and all(type(n) is int and n>=0 for n in r['class_counts']) and sum(r['class_counts'])==int(np.prod(r['source_shape'])) and all(isinstance(r[k],str) and len(r[k])==64 for k in ('weights_sha256','probability_sha256','native_sha256')),'Trained export count/hash envelope')

def scoring_request(request,exports):
    scope=request['targets'];return dict(task=scoring.TASK,stage='original_native_scoring',model_updates_allowed=False,ct_reads_allowed=False,cases=scope['cases'],files=scope['files'],prediction_exports=exports,limits=scope['limits'],code_pins=request['source_pins'],runtime=request['runtime'])

def validate_native(files,request,exports):
    projection=scoring_request(request,exports);require(files['request.json']==canonical(projection),'Native stage projection changed')
    result=scoring.validate_payload(files,dict(request=projection,request_sha256=digest(canonical(projection))))
    rows=json.loads(files['scores.json'])
    for row,case,exported in zip(rows,request['targets']['cases'],exports):
        require(row['prediction_sha256']==exported['native_sha256'],'Native prediction binding')
        expected=case['reference_components']
        require([{k:c[k] for k in ('component_id','native_voxels','bounds_xyz_half_open','source_boundary_contact')} for c in row['components']]==expected,'Native reference components/bounds differ')
    return result

def probe_manifest(identity,steps,checkpoints,next_weights_hash,cases,exports):
    return dict(task=PROBE_TASK,identity_sha256=digest(canonical(identity)),steps=steps,checkpoints=checkpoints,next_weights_step=steps[1]+1,next_weights_sha256=next_weights_hash,cases=cases,exports=exports)

def validate_probes(files,identity,request):
    require(sum(map(len,files.values()))<=192*1024**2,'Protected probe payload budget');core.validate_identity(identity);m=json.loads(files['manifest.json']);size=identity['config']['tensor_shape'][0];steps=[0,6,24,48] if identity['config']['max_steps']==48 else [0,2,6]
    require(set(files)=={'manifest.json','image.npy','next-weights.pt'}|{f'prob-{n}.npy' for n in steps},'Short-run probe inventory')
    require(set(m)=={'task','identity_sha256','steps','checkpoints','next_weights_step','next_weights_sha256','cases','exports'} and m['task']==PROBE_TASK and m['identity_sha256']==digest(canonical(identity)) and m['steps']==steps and m['next_weights_step']==steps[1]+1,'Probe task/steps/identity')
    require([p['primary']['step'] for p in m['checkpoints']]==steps and len(m['cases'])==len(m['exports'])==7 and len({c['study_id'] for c in m['cases']})==7,'Probe reference membership')
    require(identity==request['identity'] and m['cases']==request['targets']['cases'],'Probe source/case scope differs')
    for p in m['checkpoints']:require(p['primary']['artifact_id']==f"{identity['run_id']}:step:{p['primary']['step']}" and p['primary']['derivation_sha256']==digest(canonical(dict(identity=identity,step=p['primary']['step']))),'Probe checkpoint cross-run')
    for c,p in zip(m['cases'],m['exports']):validate_export_record(p['report'],dict(identity=identity,case=c,step=identity['config']['max_steps'],weights_sha256=m['checkpoints'][-1]['weights_sha256']))
    x=codec.decode_array(files['image.npy'],[1,size,size,size],'float32');require(np.isfinite(x).all() and x.min()>=0 and x.max()<=1 and digest(files['image.npy'])==m['cases'][0]['image_sha256'],'Probe image differs')
    for n in steps:
        p=codec.decode_array(files[f'prob-{n}.npy'],[3,size,size,size],'float32');require(np.isfinite(p).all() and p.min()>=0 and p.max()<=1 and np.allclose(p.sum(0),1,atol=1e-5,rtol=0),'Probe probabilities')
    from io import BytesIO
    import torch
    require(len(files['next-weights.pt'])<=32*1024**2,'Next weight budget');w=torch.load(BytesIO(files['next-weights.pt']),map_location='cpu',weights_only=True);expected=core.scratch(identity['config']).state_dict()
    require(set(w)==set(expected) and all(isinstance(v,torch.Tensor) and v.shape==expected[n].shape and v.dtype==expected[n].dtype for n,v in w.items()) and core.numerical.finite(w) and core.numerical.state_hash(w)==m['next_weights_sha256'],'Next-update state differs')
    return dict(task=PROBE_TASK,identity_sha256=m['identity_sha256'],steps=steps,next_weights_sha256=m['next_weights_sha256'],members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})

def validate_summary(files,request):
    require(sum(map(len,files.values()))<=8*1024**2,'Summary payload budget');require(set(files)=={'request.json','completion.json','journal.jsonl','native-request.json','scores.json','references.json','aggregates.json','production.json'},'Summary inventory')
    from src.training.segmenter_v5_executor_v1 import validate_request,verify_journal
    validate_request(request);require(files['request.json']==canonical(request),'Summary launch request differs');pin=digest(files['request.json']);r=json.loads(files['completion.json']);i=request['identity'];steps=request['checkpoint_steps']
    require(set(r)=={'task','state','request_sha256','identity_sha256','completed_steps','weights_sha256','checkpoints','exports','probe_reference','images_reference','exposure','journal_sha256','last_event_sha256','native_evidence_sha256','comparison_result','seconds'} and r['task']==SUMMARY_TASK and r['state']=='complete' and r['request_sha256']==pin and r['identity_sha256']==digest(canonical(i)) and type(r['completed_steps']) is int and r['completed_steps']==i['config']['max_steps'],'Summary task/identity/progress')
    require([c['primary']['step'] for c in r['checkpoints']]==steps and all(c['primary']['artifact_id']==f"{i['run_id']}:step:{c['primary']['step']}" and c['primary']['derivation_sha256']==digest(canonical(dict(identity=i,step=c['primary']['step']))) and c['backup']['artifact_id']=='backup:'+c['primary']['artifact_id'] for c in r['checkpoints']),'Missing/wrong checkpoint keepers')
    require(r['weights_sha256']==r['checkpoints'][-1]['weights_sha256'] and r['exposure']=={n:i['config']['max_steps']//6 for n in json.loads(request['controls']['inputs.json'])['train']},'Terminal weights/exposure')
    require(len(r['exports'])==7 and len({e['report']['study_id'] for e in r['exports']})==7 and all(e['report']['weights_sha256']==r['weights_sha256'] and e['report']['completed_updates']==r['completed_steps'] and e['report']['task']==EXPORT_TASK and e['primary']['artifact_id']==i['run_id']+':native:'+e['report']['study_id'] and e['backup']['artifact_id']=='backup:'+e['primary']['artifact_id'] for e in r['exports']),'Native export task/membership/keepers')
    for case,exported in zip(request['targets']['cases'],r['exports']):validate_export_record(exported['report'],dict(identity=i,case=case,step=r['completed_steps'],weights_sha256=r['weights_sha256']))
    for key,suffix in [('probe_reference',':probes'),('images_reference',':images')]:require(r[key]['primary']['artifact_id']==i['run_id']+suffix and r[key]['backup']['artifact_id']=='backup:'+r[key]['primary']['artifact_id'],'Recovery probe/image keeper missing')
    events,last=verify_journal(files['journal.jsonl'],request)
    require(digest(files['journal.jsonl'])==r['journal_sha256'] and last==r['last_event_sha256'] and events[-1]['state']=='transaction_verified','Summary journal binding')
    require([e['completed_step'] for e in events if e['state']=='update_complete']==list(range(1,r['completed_steps']+1)) and [e['step'] for e in events if e['state']=='checkpoint_durable']==steps and [e['step'] for e in events if e['state']=='tensor_evaluation_complete']==steps,'Incomplete update/evaluation journal')
    from src.training import segmenter_v5_comparison_v1 as comparison
    require(r['comparison_result']==(comparison.assess(json.loads(files['scores.json'])) if i['domain']=='qualified_real_cache' else None),'Comparison result or validation selection differs')
    native={n:files['native-request.json' if n=='request.json' else n] for n in ('request.json','scores.json','references.json','aggregates.json','production.json')};validate_native(native,request,[e['report'] for e in r['exports']])
    require(r['native_evidence_sha256']=={n:digest(v) for n,v in native.items()} and type(r['seconds']) is float and np.isfinite(r['seconds']) and 0<=r['seconds']<=request['limits']['producer_seconds'],'Summary native evidence/time')
    return dict(task=SUMMARY_TASK,request_sha256=pin,completed_steps=r['completed_steps'],weights_sha256=r['weights_sha256'],native_cases=7,members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})
