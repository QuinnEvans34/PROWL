# Isolated D-333 v5 version; v3 producing source is preserved.
"""Closed one-attempt 48-update executor; real grants require separately pinned approval."""
from copy import deepcopy
import json,os,time
from pathlib import Path
import numpy as np
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_training_inputs_v1 as inputs,segmenter_v5_targets_v1 as targets
from src.training import segmenter_v5_training_session_v1 as core,segmenter_v5_evidence_v1 as evidence,segmenter_training_probe_v1 as oldprobe,segmenter_native_scoring_v1 as scoring
from src.operations.segmenter_v5_backup_v1 import backup_checkpoint
from src.training import segmenter_v5_comparison_v1 as comparison

TASK='segmenter_v5_launch_request_v1'
LIMITS=dict(total_seconds=1800,producer_seconds=1200,recovery_seconds=300,rss_bytes=12*1024**3,driver_bytes=12*1024**3,free_bytes=100*1024**3,output_bytes=64*1024**2)
_GRANT=object()

def validate_request(r):
    require(set(r)=={'schema_version','task','preparation_decision','experiment_id','identity','controls','checkpoint_steps','evaluation_steps','targets','baseline','source_pins','runtime','storage_capability_sha256','storage_capability','storage_ceilings','limits','initial_weights_sha256','weight_imports_allowed','continuation_allowed','recovery_policy','readiness','comparison'},'Launch request inventory')
    require(r['schema_version']=='1.0.0' and r['task']==TASK and r['preparation_decision']=='D-333' and r['experiment_id'] in ('CAP-EXP-014','D333-INVENTED-REHEARSAL','D333-UNIT') and r['initial_weights_sha256']==core.INITIAL and r['weight_imports_allowed'] is False and r['continuation_allowed'] is False,'Wrong launch task/lineage')
    i=r['identity'];controls={n:v.encode() for n,v in r['controls'].items()};control=core.validate_controls(i,controls);steps=i['config']['max_steps'];size=i['config']['tensor_shape'][0]
    unit=r['experiment_id']=='D333-UNIT';require((unit and steps==6 and size==24 and i['domain']=='invented_arrays_only' and i['device']=='cpu') or (not unit and steps==48 and size==144 and i['device']=='mps'),'Short-run update/device envelope')
    cadence=[0,2,6] if unit else [0,6,24,48];require(r['checkpoint_steps']==r['evaluation_steps']==cadence and all(type(n) is int for n in r['checkpoint_steps']) and r['limits']==LIMITS,'Cadence/resource change')
    require(json.loads(controls['source.json'])==r['source_pins'] and json.loads(controls['environment.json'])==r['runtime'] and r['source_pins'] and isinstance(r['storage_ceilings'],list) and len(r['storage_ceilings'])==3 and all(type(v) is int and v>0 for v in r['storage_ceilings']),'Source/runtime/storage identity')
    from src.operations.segmenter_v5_storage_v1 import validate_capability
    cap=r['storage_capability'];validate_capability(canonical(cap));require(r['storage_ceilings']==[cap['primary_ceiling'],cap['absolute_backup_ceiling'],cap['absolute_backup_ceiling']],'Request absolute capacity changed');real=i['domain']=='qualified_real_cache';require(digest(canonical(cap))==r['storage_capability_sha256'] and cap['approval']=='D-333' and cap['phase']==('real' if real else 'rehearsal') and cap['launch_approval_required'] is real and cap['real_optimizer_updates_allowed'] is real,'Wrong conditional storage capability')
    require(r['comparison']==(comparison.policy() if real else None),'Comparison policy changed or supplied to invented scope')
    if real:
        require(r['experiment_id']=='CAP-EXP-014' and r['targets']['domain']=='original_native_targets' and r['baseline']['kind']=='D325_original_native' and r['baseline']['acceptance_sha256']=='f4bfcaf0dd63ff066ce8456d66b978e738e8cca8322a6c74fcce23c89b090db2','Real baseline/stage differs')
        require(set(r['readiness'])=={'kind','acceptance_sha256','producer_receipt_sha256','recovery_receipt_sha256','tests_sha256'} and r['readiness']['kind']=='qualified_v5_executor_rehearsal' and all(isinstance(r['readiness'][k],str) and len(r['readiness'][k])==64 for k in r['readiness'] if k!='kind'),'Unqualified real executor readiness')
    else:require(r['experiment_id']!='CAP-EXP-014' and r['targets']['domain']=='invented_native_targets' and r['baseline']==dict(kind='invented_tensor_diagnostics_no_real_baseline'),'Invented task used real evidence')
    if not unit:
        targets.validate_scope(r['targets'],control);g=json.loads(controls['geometry.json']);require(g['target_scope_sha256']==digest(canonical(r['targets'])) and g['stage']==targets.STAGE,'Final source scope not bound to session geometry identity')
    require(r['recovery_policy']==dict(primary_denied=True,replay_images=7,next_update='invented_only',original_target_reads=0,real_optimizer_calls=0),'Recovery scope silently expanded')
    return control

class Grant:
    def __init__(self,token,request_pin,identity_pin,approval_pin):
        require(token is _GRANT,'Only the exact dispatcher can issue a launch grant');self.request_pin=request_pin;self.identity_pin=identity_pin;self.approval_pin=approval_pin

def authorize(r,approval_raw=None,*,trusted_approval_sha256=None):
    validate_request(r)
    if r['identity']['domain']=='invented_arrays_only':
        require(approval_raw is None and trusted_approval_sha256 is None,'Invented rehearsal cannot use real approval');return None
    require(isinstance(approval_raw,bytes) and isinstance(trusted_approval_sha256,str) and digest(approval_raw)==trusted_approval_sha256,'Missing/unpinned exact real launch approval')
    a=json.loads(approval_raw);require(set(a)=={'kind','decision','author','user_instruction','request_sha256','identity_sha256','real_updates','original_final_targets','automatic_extension','continuation'} and a['kind']=='exact_segmenter_v5_launch' and isinstance(a['decision'],str) and a['decision'].startswith('D-') and a['decision']!='D-333' and a['author']=='Quinton Evans' and isinstance(a['user_instruction'],str) and bool(a['user_instruction'].strip()) and a['request_sha256']==digest(canonical(r)) and a['identity_sha256']==digest(canonical(r['identity'])) and a['real_updates'] is True and a['original_final_targets'] is True and a['automatic_extension'] is False and a['continuation'] is False,'Approval differs from exact real request or scope')
    return Grant(_GRANT,a['request_sha256'],a['identity_sha256'],trusted_approval_sha256)

def checked_grant(r,grant):
    require(type(grant) is Grant and grant.request_pin==digest(canonical(r)) and grant.identity_pin==digest(canonical(r['identity'])) and isinstance(grant.approval_pin,str) and len(grant.approval_pin)==64,'No exact real launch grant')

def update_permit(r,grant):
    if r['identity']['domain']=='invented_arrays_only':require(grant is None,'Wrong invented permit');return None
    checked_grant(r,grant);return core.UpdatePermit(core._REAL_LAUNCH_TOKEN,grant.identity_pin,grant.request_pin)

def put(path,raw):
    with Path(path).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())

class Journal:
    def __init__(self,path,request):self.stream=Path(path).open('xb');self.previous=digest(canonical(request));self.sequence=0
    def append(self,row):
        event=dict(sequence=self.sequence,previous_sha256=self.previous,event=row);raw=canonical(event);self.stream.write(raw);self.stream.flush();os.fsync(self.stream.fileno());self.previous=digest(raw);self.sequence+=1
    def close(self):self.stream.close()

def verify_journal(raw,request):
    previous=digest(canonical(request));rows=[]
    for n,line in enumerate(raw.splitlines()):
        r=json.loads(line);require(set(r)=={'sequence','previous_sha256','event'} and type(r['sequence']) is int and r['sequence']==n and r['previous_sha256']==previous,'Journal chain differs');previous=digest(canonical(r));rows.append(r['event'])
    require(rows and rows[0]['state']=='attempt_started','No journal start');return rows,previous

def keep(stores,identity,files,artifact_id,artifact_type,validator,*,derivation=None,parents=None):
    primary,backup,_=stores;derivation=derivation or digest(canonical(dict(identity=identity,artifact_id=artifact_id)));meta=dict(artifact_type=artifact_type,schema_version='1.0.0',component=TASK,code_sha256=identity['source_sha256'],parents=parents or [identity['inputs_sha256']],retention='required_short_run_keeper',sensitivity='private_research',run_id=identity['run_id'],stage_id=artifact_type)
    pin,_=primary.publish(artifact_id,derivation_sha256=derivation,files=files,metadata=meta,validate=lambda f:validator(f,identity));ref=dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation)
    cap=stores.capability if hasattr(stores,'capability') else None
    require(cap is not None,'Domain-bound storage set required');back=backup_checkpoint(primary,backup,ref,identity,source_domain=cap['primary_volume_uuid'],destination_domain=cap['backup_volume_uuid'],validator=validator);return dict(primary=ref,backup=back)

def checkpoint(stores,s):
    ref=core.publish_checkpoint(stores[0],s);cap=stores.capability;back=backup_checkpoint(stores[0],stores[1],ref,s.identity,source_domain=cap['primary_volume_uuid'],destination_domain=cap['backup_volume_uuid']);return dict(primary=ref,backup=back,weights_sha256=core.numerical.state_hash(s.model.state_dict()))

def finalize(request,session,provider,stores,reader,refs,probabilities,next_weights,event,guard,*,write_view=None):
    weights=core.numerical.state_hash(session.model.state_dict());identity=session.identity;cases=request['targets']['cases'];exports=[];scores=[];references=[]
    image_files={'manifest.json':canonical(dict(task='segmenter_v5_recovery_images_v1',request_sha256=digest(canonical(request)),cases=cases))}
    for n,case in enumerate(cases):
        b=provider.get(case['study_id'],role=case['protected_role'],operation='inference');image_files[f'image-{n:02d}.npy']=core.cache.encode(b.image);guard()
    images_ref=keep(stores,identity,image_files,identity['run_id']+':images','segmenter-v5-images',lambda f,i:evidence.validate_images(f,request));del image_files;guard()
    # Image-only inference/export happens before the scoring stage; its source reads/updates are zero.
    for case in cases:
        guard();x=provider.get(case['study_id'],role=case['protected_role'],operation='inference');require(x.target is None and x.hashes()['image']==case['image_sha256'],'Final image-only identity');p=session.predict(x.image);guard();files,report=evidence.export(p,case,identity,session.step,weights,tick=guard);del p
        context=dict(identity=identity,case=case,step=session.step,weights_sha256=weights);pair=keep(stores,identity,files,identity['run_id']+':native:'+case['study_id'],'segmenter-v5-trained-native-case',lambda f,i,context=context:evidence.validate_export(f,context),parents=[refs[-1]['primary']['receipt_sha256']]);exports.append(pair|dict(report=report));event(dict(state='native_export_durable',study_id=case['study_id'],reference=pair));del files;guard()
    for case,pair in zip(cases,exports):
        guard();context=dict(identity=identity,case=case,step=session.step,weights_sha256=weights);files,_=stores[0].resolve(pair['primary']['artifact_id'],receipt_sha256=pair['primary']['receipt_sha256'],expected_derivation=pair['primary']['derivation_sha256'],validate=lambda f,context=context:evidence.validate_export(f,context));pred=scoring.decode_prediction(files['mask.npy'],case['descriptor']['geometry']['shape_xyz']);event(dict(state='native_targets_started',study_id=case['study_id'],counts_before=reader.counts.copy(),upper_counts=request['targets']['limits']));pan,les,rr=reader.read(session,case['study_id'],tick=guard);score=scoring.score(pred,pan,les,target_state=case['descriptor']['lesion_target_state'],tick=guard)
        from scripts.diagnostics.segmenter_native_scoring import oracle
        checked=oracle(pred,pan,les,guard);require(checked['confusion_matrix']==score['confusion_matrix'],'Final independent count oracle')
        require(write_view is not None,'Required rebuildable contour views callback')
        from src.data.segmenter_training_views_v1 import render
        image=provider.get(case['study_id'],role=case['protected_role'],operation='inference').image;png,view=render(image,pan,les,pred,case,session.step,weights,tick=guard);view|=dict(prediction_sha256=pair['report']['native_sha256'],reference_decoded_sha256={v['kind']:v['decoded_sha256'] for v in rr});write_view(case['study_id'],png,view);del image,png
        scores.append(dict(study_id=case['study_id'],protected_role=case['protected_role'],source_shape=list(pred.shape),source_affine=np.asarray(case['descriptor']['geometry']['affine_ras']).reshape(4,4).tolist(),prediction_sha256=pair['report']['native_sha256'],**score,oracle=checked));references.extend(rr);del files,pred,pan,les;event(dict(state='native_case_scored',study_id=case['study_id']));guard()
    require(reader.counts==request['targets']['limits'] and reader.used=={c['study_id'] for c in cases} and core.numerical.state_hash(session.model.state_dict())==weights,'Final source accounting/weights')
    projection=evidence.scoring_request(request,[e['report'] for e in exports]);production=dict(request_sha256=digest(canonical(projection)),source_counts=reader.counts,source_arrays_read=14,ct_arrays_read=0,model_forwards=0,model_updates=0,code_pins=request['source_pins'],runtime=request['runtime'],mount_before=reader.mount_before,mount_after=reader.mount_after)
    native={n:canonical(v) for n,v in dict(request=projection,scores=scores,references=references,aggregates=scoring.aggregates(scores),production=production).items()};native={n+'.json':v for n,v in native.items()};evidence.validate_native(native,request,[e['report'] for e in exports])
    first=provider.get(cases[0]['study_id'],role='train',operation='inference').image;probe_files={'image.npy':core.cache.encode(first),'next-weights.pt':next_weights['bytes']}|{f'prob-{n}.npy':core.cache.encode(p) for n,p in probabilities.items()};probe_files['manifest.json']=canonical(evidence.probe_manifest(identity,request['checkpoint_steps'],refs,next_weights['sha256'],cases,exports));probe_ref=keep(stores,identity,probe_files,identity['run_id']+':probes','segmenter-v5-run-probes',lambda f,i:evidence.validate_probes(f,i,request),parents=[r['primary']['receipt_sha256'] for r in refs]);del probe_files;guard()
    return dict(exports=exports,probe_reference=probe_ref,images_reference=images_ref,native=native,weights_sha256=weights)

def r_real(request):return request['identity']['domain']=='qualified_real_cache'

def execute(request,provider,dest,*,save_checkpoint,finish,protect_summary,grant=None,guard=lambda:None,fault=lambda stage,s:None,verify_source=None):
    control=validate_request(request);require(type(provider) is (inputs.QualifiedInputs if request['identity']['domain']=='qualified_real_cache' else inputs.InventedInputs) and canonical(provider.control)==request['controls']['inputs.json'].encode(),'Wrong checked launch provider');permit=update_permit(request,grant)
    require(request['experiment_id']=='D333-UNIT' or callable(verify_source),'Production source verifier required')
    dest=Path(dest);require(dest.is_absolute() and dest.resolve(strict=True)==dest and dest.is_dir() and not (dest/'journal.jsonl').exists(),'Launch destination/attempt already consumed');s=core.Session(request['identity'],{n:v.encode() for n,v in request['controls'].items()});journal=Journal(dest/'journal.jsonl',request);start=time.monotonic();refs=[];probabilities={};next_weights=None;finished=None
    def check():
        guard();require(time.monotonic()-start<request['limits']['producer_seconds'] and s.identity==request['identity'] and s.config==request['identity']['config'] and s.controls=={n:v.encode() for n,v in request['controls'].items()} and canonical(provider.control)==request['controls']['inputs.json'].encode(),'Transaction identity/time drift')
    try:
        journal.append(dict(state='attempt_started',request_sha256=digest(canonical(request)),step=0));check()
        if verify_source:verify_source()
        for boundary in request['checkpoint_steps']:
            while s.step<boundary:
                check();fault('before_update',s);journal.append(dict(state='update_started',step=s.step));row=s.update(provider,permit=permit);journal.append(dict(state='update_complete',**row));fault('after_update',s)
                if s.step==request['checkpoint_steps'][1]+1:next_weights=dict(bytes=oldprobe.encode_weights(s.model),sha256=core.numerical.state_hash(s.model.state_dict()))
                check()
            if verify_source:verify_source()
            fault('before_evaluation',s);s.evaluate(provider);journal.append(dict(state='tensor_evaluation_complete',step=s.step));check();fault('before_checkpoint',s);ref=save_checkpoint(s);fault('after_checkpoint',s)
            require(set(ref)=={'primary','backup','weights_sha256'} and ref['primary']['step']==boundary and ref['primary']['artifact_id']==s.identity['run_id']+':step:'+str(boundary) and ref['backup']['artifact_id']=='backup:'+ref['primary']['artifact_id'] and all(len(ref[k]['receipt_sha256'])==64 for k in ('primary','backup')) and ref['weights_sha256']==core.numerical.state_hash(s.model.state_dict()),'Incomplete/wrong checkpoint/keeper')
            refs.append(ref);journal.append(dict(state='checkpoint_durable',step=s.step,reference=ref));first=provider.get(control['train'][0],role='train',operation='inference');probabilities[s.step]=s.predict(first.image);check()
        require(s.step==s.config['max_steps'] and core.progress(s)['exposure']=={n:s.step//6 for n in control['train']} and next_weights is not None,'Incomplete full-epoch exposure')
        if verify_source:verify_source()
        fault('before_final',s);finished=finish(s,refs,probabilities,next_weights,journal.append,check);check();journal.append(dict(state='transaction_verified',step=s.step));journal.close();raw=(dest/'journal.jsonl').read_bytes();_,last=verify_journal(raw,request)
        result=dict(task=evidence.SUMMARY_TASK,state='complete',request_sha256=digest(canonical(request)),identity_sha256=digest(canonical(s.identity)),completed_steps=s.step,weights_sha256=finished['weights_sha256'],checkpoints=refs,exports=finished['exports'],probe_reference=finished['probe_reference'],images_reference=finished['images_reference'],exposure=core.progress(s)['exposure'],journal_sha256=digest(raw),last_event_sha256=last,native_evidence_sha256={n:digest(v) for n,v in finished['native'].items()},comparison_result=comparison.assess(json.loads(finished['native']['scores.json'])) if r_real(request) else None,seconds=float(time.monotonic()-start))
        native=finished['native'];files={'request.json':canonical(request),'completion.json':canonical(result),'journal.jsonl':raw}|{('native-request.json' if n=='request.json' else n):v for n,v in native.items()};evidence.validate_summary(files,request)
        if verify_source:verify_source()
        protected=protect_summary(files,s.identity);check();put(dest/'transaction.json',canonical(result|dict(summary_reference=protected)));return result|dict(summary_reference=protected)
    except BaseException as exc:
        s.dirty=True
        if not journal.stream.closed:journal.append(dict(state='failed_or_interrupted',completed_steps=s.step,last_durable_checkpoint=refs[-1] if refs else None,error_type=type(exc).__name__,message=str(exc)))
        put(dest/'transaction-failure.json',canonical(dict(state='consumed_incomplete',completed_steps=s.step,last_durable_checkpoint=refs[-1] if refs else None,dirty=True,error_type=type(exc).__name__,message=str(exc))));raise
    finally:journal.close()
