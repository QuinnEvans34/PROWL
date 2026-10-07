# Duration native evidence; sealed v5 source remains fixed.
"""Trained native exports and original-reference evidence; unchanged numerical codecs."""
from copy import deepcopy
import json,math
import numpy as np
from src.data import segmenter_content_v1 as content
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training import segmenter_duration_session_v1 as core,segmenter_inference_v1 as codec,segmenter_native_scoring_v1 as scoring

EXPORT_TASK='segmenter_duration_trained_native_export_v1'
SUMMARY_TASK='segmenter_duration_run_summary_v1'
PROBE_TASK='segmenter_duration_run_probes_v1'

def validate_images(files,request):
    require(sum(map(len,files.values()))<=84*1024**2,'Recovery image budget');require(set(files)=={'manifest.json'}|{f'image-{n:02d}.npy' for n in range(7)},'Recovery image inventory')
    require(files['manifest.json']==canonical(dict(task='segmenter_duration_recovery_images_v1',request_sha256=digest(canonical(request)),cases=request['targets']['cases'])),'Recovery image lineage')
    for n,c in enumerate(request['targets']['cases']):
        raw=files[f'image-{n:02d}.npy'];require(digest(raw)==c['image_sha256'],'Recovery image hash');x=codec.decode_array(raw,[1,144,144,144],'float32');require(np.isfinite(x).all() and x.min()>=0 and x.max()<=1,'Recovery image values')
    return dict(task='segmenter_duration_recovery_images_v1',request_sha256=digest(canonical(request)),members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})

def export(probability,case,identity,step,weights_sha256,*,tick=lambda:None):
    core.validate_identity(identity);require(type(step) is int and step in (48,96,144,192) and step<=identity['config']['max_steps'] and len(weights_sha256)==64,'Wrong committed terminal export')
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
    require(r['task']==EXPORT_TASK and r['identity_sha256']==digest(canonical(i)) and r['weights_sha256']==context['weights_sha256'] and type(r['completed_updates']) is int and r['completed_updates']==context['step'] and context['step'] in (48,96,144,192) and context['step']<=i['config']['max_steps'] and r['native_reference_metrics']=='separate_original_reference_scoring','Wrong trained task/weights/step')
    require(all(r[k]==case[k] for k in ('study_id','protected_role','transform_sha256','image_sha256')) and r['source_shape']==case['transform']['source_shape'] and r['source_affine']==case['transform']['source_affine'] and r['inverse']=='continuous_three_channel_then_argmax' and r['outside_roi']=='background','Trained export source/role/policy')
    require(len(r['class_counts'])==3 and all(type(n) is int and n>=0 for n in r['class_counts']) and sum(r['class_counts'])==int(np.prod(r['source_shape'])) and all(isinstance(r[k],str) and len(r[k])==64 for k in ('weights_sha256','probability_sha256','native_sha256')),'Trained export count/hash envelope')

def scoring_request(request,exports,step):
    from src.data.segmenter_duration_targets_v1 import stage_scope
    scope=stage_scope(request['targets'],step);return dict(task=scoring.TASK,stage='original_native_scoring',model_updates_allowed=False,ct_reads_allowed=False,cases=scope['cases'],files=scope['files'],prediction_exports=exports,limits=scope['limits'],code_pins=request['source_pins'],runtime=request['runtime'])

def validate_native(files,request,exports,step):
    from src.data.segmenter_duration_targets_v1 import stage_scope
    cases=stage_scope(request['targets'],step)['cases']
    projection=scoring_request(request,exports,step);require(files['request.json']==canonical(projection),'Native stage projection changed')
    result=validate_stage_counts(files,dict(request=projection,request_sha256=digest(canonical(projection))),expected_cases=cases)
    rows=json.loads(files['scores.json'])
    for row,case,exported in zip(rows,cases,exports):
        require(row['prediction_sha256']==exported['native_sha256'],'Native prediction binding')
        expected=case['reference_components']
        require([{k:c[k] for k in ('component_id','native_voxels','bounds_xyz_half_open','source_boundary_contact')} for c in row['components']]==expected,'Native reference components/bounds differ')
    return result

def probe_manifest(identity,steps,checkpoints,next_weights_hash,cases,exports):
    return dict(task=PROBE_TASK,identity_sha256=digest(canonical(identity)),steps=steps,checkpoints=checkpoints,next_weights_step=steps[1]+1,next_weights_sha256=next_weights_hash,cases=cases,exports=exports)

def validate_probes(files,identity,request):
    require(sum(map(len,files.values()))<=211*1024**2,'Protected probe payload budget');core.validate_identity(identity);m=json.loads(files['manifest.json']);size=identity['config']['tensor_shape'][0];steps=request['checkpoint_steps']
    require(set(files)=={'manifest.json','image.npy','next-weights.pt'}|{f'prob-{n}.npy' for n in steps},'Short-run probe inventory')
    require(set(m)=={'task','identity_sha256','steps','checkpoints','next_weights_step','next_weights_sha256','cases','exports'} and m['task']==PROBE_TASK and m['identity_sha256']==digest(canonical(identity)) and m['steps']==steps and m['next_weights_step']==steps[1]+1,'Probe task/steps/identity')
    require([p['step'] for p in m['checkpoints']]==steps and len(m['cases'])==len(m['exports'])==7 and len({c['study_id'] for c in m['cases']})==7,'Probe reference membership')
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

def validate_views(files,context):
    from PIL import Image
    from io import BytesIO
    require(set(files)=={"view.png","view.json"} and sum(map(len,files.values()))<=8*1024**2,"Contour view inventory/budget")
    v=json.loads(files["view.json"]);case=context["case"]
    require(v["study_id"]==case["study_id"] and v["protected_role"]==case["protected_role"] and v["completed_updates"]==context["step"] and v["weights_sha256"]==context["weights_sha256"] and v["image_sha256"]==case["image_sha256"] and v["transform_sha256"]==case["transform_sha256"] and v["png_sha256"]==digest(files["view.png"]) and v["prediction_sha256"]==context["prediction_sha256"] and v["display_only"] is True and v["outside_roi_CT_information"] is False,"Contour view lineage")
    with Image.open(BytesIO(files["view.png"])) as image:
        require(image.format=="PNG" and image.width==1440 and 90<image.height<=2430,"Contour dimensions/format");image.verify()
    return dict(task="segmenter_duration_views_v1",study_id=v["study_id"],step=v["completed_updates"],members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})


def validate_summary(files,request):
    from src.training.segmenter_duration_executor_v1 import validate_request,verify_journal,assess_stage,policy_step
    validate_request(request)
    require(set(files)=={'request.json','completion.json','journal.jsonl','screens.json'} and sum(map(len,files.values()))<=8*1024**2,'Duration summary inventory/budget')
    require(files['request.json']==canonical(request),'Duration summary request drift')
    result=json.loads(files['completion.json']);screens=json.loads(files['screens.json'])
    fields={'state','completed_steps','checkpoints','screens','exposure','last_durable_checkpoint','terminal_decision','task','request_sha256','identity_sha256','journal_sha256','last_event_sha256','seconds','recovery'}
    require(type(result) is dict and set(result)==fields and type(result['seconds']) is float and np.isfinite(result['seconds']) and 0<=result['seconds']<request['limits']['producer_seconds'],'Summary exact fields/time')
    events,last=verify_journal(files['journal.jsonl'],request)
    expected={key:result[key] for key in ('state','completed_steps','checkpoints','screens','exposure','last_durable_checkpoint','terminal_decision')}
    require(result['task']==SUMMARY_TASK and result['request_sha256']==digest(canonical(request)) and result['identity_sha256']==digest(canonical(request['identity'])) and result['journal_sha256']==digest(files['journal.jsonl']) and result['last_event_sha256']==last,'Summary journal/task identity')
    require(result['state'] in ('complete','stopped') and type(result['completed_steps']) is int and 0<=result['completed_steps']<=request['identity']['config']['max_steps'],'Duration completion state/step')
    committed=[e for e in events if e['state']=='update_complete']
    require([e['completed_step'] for e in committed]==list(range(1,result['completed_steps']+1)) and [e['step'] for e in events if e['state']=='update_started']==list(range(result['completed_steps'])),'Missing/duplicate committed update')
    names=json.loads(request['controls']['inputs.json'])['train']
    control=json.loads(request['controls']['inputs.json'])
    for n,e in enumerate(committed):
        member,trace=core.next_member(request['identity']['config'],control,n)
        require(e['member_id']==member and e['sampling']==trace,'Committed sampler differs')
    require([e['reference'] for e in events if e['state']=='checkpoint_durable']==result['checkpoints'],'Checkpoint journal differs')
    require([e['reference'] for e in events if e['state']=='native_screen_durable']==result['screens'],'Screen journal differs')
    actual_cadence=[v for v in request['checkpoint_steps'] if v<=result['completed_steps']]
    require([v['step'] for v in result['checkpoints']]==actual_cadence and [v['step'] for v in result['screens']]==actual_cadence[1:],'Missing stage checkpoint/screen')
    require(result['checkpoints'] and result['last_durable_checkpoint']==result['checkpoints'][-1],'Last keeper differs')
    for ref in result['checkpoints']:
        require(set(ref)=={'step','primary','backup','weights_sha256'} and ref['primary']['artifact_id']==request['identity']['run_id']+':step:'+str(ref['step']) and ref['backup']['artifact_id']=='backup:'+ref['primary']['artifact_id'] and all(type(ref[k]['receipt_sha256']) is str and len(ref[k]['receipt_sha256'])==64 for k in ('primary','backup')),'Checkpoint receipt/run differs')
    require(len(screens)==len(result['screens']) and all(s['step']==policy_step(request,ref['step']) and digest(canonical(s))==ref['screen_sha256'] for s,ref in zip(screens,result['screens'])),'Screen evidence missing/changed')
    for record,ref in zip(screens,result['screens']):
        require(assess_stage(request,record)==ref['assessment'] and ref['primary']['artifact_id']==request['identity']['run_id']+':screen:'+str(ref['step']) and ref['backup']['artifact_id']=='backup:'+ref['primary']['artifact_id'],'Policy result/receipt differs')
    require(result['exposure']=={n:sum(e.get('member_id')==n for e in committed) for n in names},'Exposure mismatch')
    if result['state']=='complete':require(result['completed_steps']==request['identity']['config']['max_steps'] and result['terminal_decision'] in ('terminal_pass','terminal_insufficient') and all(v==result['completed_steps']//6 for v in result['exposure'].values()),'Incomplete terminal transaction')
    else:require(result['terminal_decision']=='stopped' and result['screens'][-1]['assessment']['decision']=='stopped','Stopped output masked')
    require(result['terminal_decision']==result['screens'][-1]['assessment']['decision'],'Terminal assessment differs')
    require(events[-1]['state']=='transaction_verified' and events[-1]['result']==expected,'Summary not tied to verified transaction')
    recovery=result['recovery'];require(type(recovery) is dict and set(recovery)=={'screen_records','exports','images_reference','probe_reference','next_state_reference','model_calls'} and recovery['screen_records']==screens,'Recovery inventory/screens differ')
    require(set(recovery['model_calls'])=={'forwards','optimizer_calls'} and all(type(v) is int and 0<=v<=request['model_calls']['producer'][k] for k,v in recovery['model_calls'].items()),'Producer call accounting')
    if request['kind']!='unit':
        require(recovery['model_calls']['optimizer_calls']==result['completed_steps'],'Committed call count differs')
        expected_exports=[(step,c['study_id']) for step in actual_cadence[1:] for c in (request['targets']['cases'] if step==192 else request['targets']['cases'][:6])]
        require([(v['report']['completed_updates'],v['report']['study_id']) for v in recovery['exports']]==expected_exports,'Native export inventory')
        for v in recovery['exports']:
            report=v['report'];case=next(c for c in request['targets']['cases'] if c['study_id']==report['study_id']);checkpoint=next(c for c in result['checkpoints'] if c['step']==report['completed_updates'])
            validate_export_record(report,dict(identity=request['identity'],case=case,step=checkpoint['step'],weights_sha256=checkpoint['weights_sha256']))
        if result['state']=='complete':require(all(recovery[k] is not None for k in ('images_reference','probe_reference','next_state_reference')) and recovery['model_calls']==request['model_calls']['producer'],'Missing full recovery/call inventory')
    return dict(task=SUMMARY_TASK,request_sha256=result['request_sha256'],completed_steps=result['completed_steps'],outcome=result['terminal_decision'],members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})


# Versioned cardinality adapter. Frozen numerical/header/component guards are reproduced unchanged.
def validate_stage_counts(files,identity,*,expected_cases):
    req=identity['request'];pin=identity['request_sha256']
    require(len(expected_cases) in (6,7) and req['cases']==expected_cases and [c['protected_role'] for c in expected_cases]==['train']*6+(['validation'] if len(expected_cases)==7 else []),'Exact duration stage membership/roles')
    require(set(files)=={'request.json','scores.json','references.json','aggregates.json','production.json'} and files['request.json']==canonical(req) and digest(files['request.json'])==pin,'Scoring inventory/request differs')
    require(req['task']==scoring.TASK and req['stage']=='original_native_scoring' and req['model_updates_allowed'] is False and req['ct_reads_allowed'] is False,'Wrong scoring stage')
    scores=json.loads(files['scores.json']);refs=json.loads(files['references.json']);production=json.loads(files['production.json'])
    require(len(scores)==len(req['cases'])==len(req['prediction_exports'])==len(expected_cases) and len({c['study_id'] for c in expected_cases})==len(expected_cases) and len(refs)==len(req['files'])==2*len(expected_cases),'Scoring case/reference inventory')
    for row,expected in zip(refs,req['files']):
        require(set(row)=={'study_id','protected_role','kind','uri','header','read','decoding','decoded_sha256'} and all(row[k]==expected[k] for k in ('study_id','protected_role','kind','uri')),'Reference scope drift')
        require(row['read']==dict(compressed_bytes=expected['compressed_bytes'],expanded_bytes=expected['expanded_bytes'],sha256=expected['sha256'],gzip_eof_crc_verified=True),'Original source accounting/hash drift')
        h=row['header'];g=expected['geometry'];require(h['shape']==g['shape_xyz'] and np.allclose(np.asarray(h['affine']).ravel(),g['affine_ras'],rtol=0,atol=1e-5),'Reference grid changed')
        scaling=expected['header'] if expected['kind']=='lesion' else expected['retained_content'];sc=dict(slope=scaling['effective_slope'],intercept=scaling['effective_intercept']) if expected['kind']=='lesion' else scaling['effective_scaling'];units=scaling['units']
        require(h['slope']==sc['slope'] and h['intercept']==sc['intercept'] and h['units']==units and h['offset']==352 and np.dtype(h['dtype'])==np.dtype(expected['dtype']) and np.allclose(h['spacing'],g['spacing_mm_xyz'],rtol=0,atol=1e-5),'Reference scaling/units/type/spacing drift')
        if expected['kind']=='lesion':require(h['header_sha256']==expected['header']['decompressed_header_sha256'],'Original lesion header drift')
        require(isinstance(row['decoded_sha256'],str) and len(row['decoded_sha256'])==64,'Missing decoded reference identity')
        dec=row['decoding'];require(dec['policy']==content.APPROVED_POLICY and dec['max_endpoint_residual']<=1e-6 and sum(p['count'] for p in dec['semantic_value_counts'])==math.prod(h['shape']) and all(p['count']>=0 and min(abs(p['semantic']),abs(p['semantic']-1))<=1e-6 for p in dec['semantic_value_counts']),'Reference binary decoding differs')
    for row,e,export in zip(scores,req['cases'],req['prediction_exports']):
        require(set(row)=={'study_id','protected_role','source_shape','source_affine','prediction_sha256','confusion_matrix','metrics','outside_pancreas_voxels','connectivity','components','oracle'},'Score fields differ')
        require(all(row[k]==e[k] for k in ('study_id','protected_role')) and row['source_shape']==e['descriptor']['geometry']['shape_xyz'] and row['source_affine']==np.asarray(e['descriptor']['geometry']['affine_ras']).reshape(4,4).tolist() and row['prediction_sha256']==export['native_sha256'],'Score image/role/grid provenance differs')
        m=scoring.from_confusion(row['confusion_matrix']);require(row['metrics']==m and sum(sum(v) for v in row['confusion_matrix'])==math.prod(row['source_shape']),'Score formula/voxel accounting differs')
        matrix=np.asarray(row['confusion_matrix'],np.int64);require(matrix.sum(0).tolist()==export['class_counts'],'Prediction counts drift')
        for name in scoring.CLASSES:require(m[name]['target_voxels']==e['fidelity']['metrics'][name]['native_voxels'],'Original target counts differ from retained accepted source evidence')
        pair=[v for v in refs if v['study_id']==row['study_id']];require(len(pair)==2 and next(v for v in pair if v['kind']=='lesion')['decoding']['foreground_voxels']==m['lesion']['target_voxels'] and next(v for v in pair if v['kind']=='pancreas')['decoding']['foreground_voxels']==m['pancreas_parenchyma']['target_voxels']+m['lesion']['target_voxels']-row['outside_pancreas_voxels'],'Decoded foreground/reference counts drift')
        require(row['outside_pancreas_voxels']==e['fidelity']['outside_pancreas_voxels'] and row['connectivity']==26 and len(row['components'])==e['fidelity']['source_component_count'],'Native component/reference relationship differs')
        for i,(c,old) in enumerate(zip(row['components'],e['fidelity']['components']),1):
            require(set(c)=={'component_id','native_voxels','true_positive','recall','missed','bounds_xyz_half_open','source_boundary_contact'} and c['component_id']==i and c['native_voxels']==old['native_voxels'] and type(c['true_positive']) is int and 0<=c['true_positive']<=c['native_voxels'] and c['recall']==c['true_positive']/c['native_voxels'] and c['missed']==(c['true_positive']==0),'Component identity/count/formula differs')
        for c in row['components']:
            b=c['bounds_xyz_half_open'];require(len(b)==3 and all(len(v)==2 and all(type(x)==int for x in v) and 0<=v[0]<v[1]<=row['source_shape'][i] for i,v in enumerate(b)) and c['source_boundary_contact']==any(v[0]==0 or v[1]==row['source_shape'][i] for i,v in enumerate(b)),'Component physical bounds drift')
        require(sum(c['native_voxels'] for c in row['components'])==m['lesion']['target_voxels'] and sum(c['true_positive'] for c in row['components'])==m['lesion']['true_positive'],'Components omitted or hits forged')
        require(row['oracle']['state']=='passed' and row['oracle']['confusion_matrix']==row['confusion_matrix'],'Independent confusion oracle differs')
    require(json.loads(files['aggregates.json'])==scoring.aggregates(scores),'Role aggregate drift')
    require(production['request_sha256']==pin and production['source_counts']=={k:req['limits'][k] for k in ('hash_bytes','decode_bytes','expanded_bytes')} and production['source_arrays_read']==2*len(expected_cases) and production['ct_arrays_read']==production['model_forwards']==production['model_updates']==0 and production['code_pins']==req['code_pins'] and production['runtime']==req['runtime'] and production['mount_before']==production['mount_after'],'Production/source/permission drift')
    return dict(task=scoring.TASK,request_sha256=pin,cases=len(expected_cases),references=2*len(expected_cases),model_updates=0,source_counts=production['source_counts'],aggregate_sha256=digest(files['aggregates.json']),members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})
