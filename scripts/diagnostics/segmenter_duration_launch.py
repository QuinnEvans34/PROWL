"""Fixed duration worker entry points. No active native/scientific request ships with this code."""
import argparse
import gc
import json
import os
from pathlib import Path
import time
import sys

REPO=Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:sys.path.insert(0,str(REPO))

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK","0")
os.environ.setdefault("OMP_NUM_THREADS","2")
os.environ.setdefault("OPENBLAS_NUM_THREADS","2")

import numpy as np
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_training_inputs_v1 as inputs, segmenter_duration_targets_v1 as targets
from src.training import segmenter_duration_session_v1 as core, segmenter_duration_executor_v1 as engine
from src.training import segmenter_duration_evidence_v1 as evidence,segmenter_native_scoring_v1 as scoring
from src.operations.segmenter_duration_backup_v1 import backup_checkpoint,restore_backup
from src.operations.segmenter_duration_storage_v1 import duration_stores,qualified_cache_reader
from src.operations.segmenter_duration_dispatch_v1 import read_control,verify_code,dispatch,owned_tree

def stores(r,args,*,recovery=False):
    raw=read_control(args.storage,args.storage_pin)
    return duration_stores(REPO/"configs/local/roots.yaml",canonical(r["storage_capability"]),
        trusted_capability_sha256=r["storage_capability_sha256"],approval=raw,
        trusted_approval_sha256=args.storage_pin,recovery_only=recovery)


def provider(r):
    if r["kind"]=="native_rehearsal":return inputs.InventedInputs(144)
    require(r["kind"]=="scientific","Unit worker cannot resolve actual inputs")
    from scripts.diagnostics import segmenter_cache_qualification as old
    from src.data import segmenter_geometry_loader_v1 as loader
    from src.operations.segmenter_duration_storage_v1 import qualified_cache_reader
    accept=json.loads(read_control(REPO/"outputs/prowl/SEGMENTER-CACHE-REVIEW-20261002/accepted-cache.json",r["input_cache"]["acceptance_sha256"]))
    request=json.loads(read_control(old.DEST/"request.json",r["input_cache"]["request_sha256"]))
    reader=qualified_cache_reader(REPO/"configs/local/roots.yaml",canonical(r["storage_capability"]),
        trusted_capability_sha256=r["storage_capability_sha256"],cache_area=r["input_cache"]["area"])
    reference=dict(artifact_id=accept["cache_artifact_id"],receipt_sha256=accept["cache_completion_sha256"],derivation_sha256=accept["request_sha256"])
    files,_=reader.resolve(reference["artifact_id"],receipt_sha256=reference["receipt_sha256"],expected_derivation=reference["derivation_sha256"],
        validate=lambda f:old.validate_production(f,request,r["input_cache"]["request_sha256"]))
    require(sum(len(v) for n,v in files.items() if n.endswith(".npy"))<=r["input_cache"]["payload_bytes"]+14*4096,"Cached serialization inventory")
    from src.operations.segmenter_duration_storage_v1 import replay_descriptors
    session=replay_descriptors(REPO/"configs/local/roots.yaml",canonical(r["storage_capability"]),trusted_capability_sha256=r["storage_capability_sha256"])
    return inputs.QualifiedInputs(inputs._TOKEN,session,files,request["binding"],request["binding_sha256"],reference)


def kept(r,ss,files,suffix,kind,validator):
    identity=r["identity"];artifact_id=identity["run_id"]+suffix;derivation=digest(canonical(dict(identity=identity,artifact_id=artifact_id)))
    metadata=dict(artifact_type=kind,schema_version="1.0.0",component=engine.TASK,code_sha256=identity["source_sha256"],
        parents=[identity["inputs_sha256"]],retention="required_duration_keeper",sensitivity="private_research",run_id=identity["run_id"],stage_id=kind)
    pin,_=ss[0].publish(artifact_id,derivation_sha256=derivation,files=files,metadata=metadata,validate=lambda f:validator(f,identity))
    primary=dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation)
    cap=r["storage_capability"]
    backup=backup_checkpoint(ss[0],ss[1],primary,identity,source_domain=cap["primary_volume_uuid"],destination_domain=cap["backup_volume_uuid"],validator=validator)
    return dict(primary=primary,backup=backup)


def checkpoint(r,ss,s):
    primary=core.publish_checkpoint(ss[0],s);cap=r["storage_capability"]
    backup=backup_checkpoint(ss[0],ss[1],primary,s.identity,source_domain=cap["primary_volume_uuid"],destination_domain=cap["backup_volume_uuid"])
    return dict(step=s.step,primary=primary,backup=backup,weights_sha256=core.numerical.state_hash(s.model.state_dict()))


def row(case,score):
    return dict(case_id=case["study_id"],role="train" if case["protected_role"]=="train" else "report_only",status="valid",reason=None,
        counts=dict(confusion_matrix=score["confusion_matrix"],voxel_volume_mm3=float(abs(np.linalg.det(np.asarray(case["descriptor"]["geometry"]["affine_ras"]).reshape(4,4)[:3,:3]))),
        source_boundary_contact=any(v["source_boundary_contact"] for v in case["reference_components"]),
        components=[dict(component_id=v["component_id"],reference_voxels=v["native_voxels"],true_positive=v["true_positive"]) for v in score["components"]]),reported_metrics=None)


def validate_stage(files,r,step,exports):
    require(set(files)=={"screen.json","native.json"} and sum(map(len,files.values()))<=4*1024**2,"Native stage inventory/budget")
    native={n:v.encode() for n,v in json.loads(files["native.json"]).items()}
    evidence.validate_native(native,r,[v["report"] for v in exports],step)
    screen=json.loads(files["screen.json"])
    require(set(screen)=={"schema_version","policy_sha256","baseline_sha256","step","outcomes"}
            and screen["schema_version"]=="1.0.0" and screen["step"]==step
            and screen["policy_sha256"]==r["policy_sha256"] and screen["baseline_sha256"]==r["policy"]["baseline_sha256"],"Stage policy binding")
    scores=json.loads(native["scores.json"])
    require(screen["outcomes"]==[row(c,s) for c,s in zip(targets.stage_scope(r["targets"],step)["cases"],scores)],"Screen does not represent native counts")
    return dict(task="segmenter_duration_native_screen_v1",step=step,screen_sha256=digest(files["screen.json"]),members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})


def metadata_result(dest,receipt_pin):
    """Reuse a pinned prior acceptance's numeric result without opening its model payloads."""
    receipt=json.loads(read_control(Path(dest)/'receipt.json',receipt_pin))
    require(receipt['state']=='complete' and 'result.json' in receipt['files'],"Incomplete numerical acceptance receipt")
    row=receipt['files']['result.json'];raw=read_control(Path(dest)/'result.json',row['sha256'])
    require(len(raw)==row['bytes'],"Numerical acceptance result size")
    return json.loads(raw)


def validate_readiness(r):
    from scripts.diagnostics import segmenter_lowrate_native_qualification as old
    from scripts.diagnostics import segmenter_training_qualification as qualification
    require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and qualification.runtime()==r['runtime'],"Native environment drift")
    cpu=metadata_result(old.cpu.DEST,old.CPU_PIN)
    native=metadata_result(old.DEST,'3e13f53adec249ed55a1fe5de7be126ad78e6002536f9ac7f6d9f7d74f26b391')
    require(cpu['state']=='qualified' and cpu['gate']['passed'] and native['state']=='qualified_native_mechanics_not_real_training' and native['producer']['state']=='passed' and native['recovery']['state']=='passed',"Frozen numerical qualification missing")
    from src.operations.segmenter_duration_readiness_v1 import reconcile
    reconcile(REPO,r['source_pins'],cpu,native)
    if r['kind']=='native_rehearsal':
        require(r['readiness']['acceptance_sha256']==old.CPU_PIN,"Frozen numerical readiness identity")
    elif r['readiness']['kind']=='qualified_duration_inference_v1':
        import math
        base=REPO/'outputs/prowl/SEGMENTER-DURATION-DUR06-I03-20261007'
        job=REPO/'outputs/prowl/SEGMENTER-DURATION-INFERENCE-I03-20261007'
        a=json.loads(read_control(REPO/'outputs/prowl/SEGMENTER-DURATION-INFERENCE-READINESS.json',r['readiness']['acceptance_sha256']))
        fields={'state','source_pins','runtime','completed_steps','primary_reads_blocked','training_resume_qualified',
                'next_update_exact','continuation_status','all_native_exports_exact','cold_original_reads','model_calls',
                'producer_sha256','recovery_sha256','tests_sha256','lineage_sha256','checkpoints','probe_checks',
                'native_checks','view_checks','origin_request_sha256'}
        require(type(a) is dict and set(a)==fields and a['state']=='qualified_duration_inference_v1'
                and r['kind']=='scientific' and a['source_pins']==r['source_pins'] and a['runtime']==r['runtime']
                and type(a['completed_steps']) is int and a['completed_steps']==192
                and a['primary_reads_blocked'] is True and a['training_resume_qualified'] is False
                and r['readiness']['training_resume_qualified'] is False and a['next_update_exact'] is False
                and a['continuation_status']=='failed_bit_exact_deferred' and a['all_native_exports_exact'] is True
                and type(a['cold_original_reads']) is int and a['cold_original_reads']==0
                and a['model_calls']==dict(producer=engine.call_limits('scientific')['producer'],cold=engine.call_limits('scientific')['cold'])
                and all(type(v) is int for row in a['model_calls'].values() for v in row.values())
                and all(a[k]==r['readiness'][k] for k in ('producer_sha256','recovery_sha256','tests_sha256','lineage_sha256')),
                'Missing inference-only qualification')
        require(r['extension_allowed'] is False and r['recovery_policy']==dict(primary_denied=True,
                original_target_reads=0,original_ct_reads=0,real_optimizer_calls=0,automatic_restart=False),
                'Inference qualification cannot permit restart')
        origin=json.loads(read_control(REPO/'outputs/prowl/SEGMENTER-DURATION-NATIVE-N02-20261007/frozen-manifest.json',
                '40cbd6ca620d3dcd7bbf1d6118acbe00456530c50d964c82d1fcbc774f426c36'))
        prior=json.loads(read_control(REPO/'outputs/prowl/SEGMENTER-DURATION-DUR05-20261007/protected-pins-post-repair.json',
                '05d4532ee7856fda80939fa89bd55ef33b96edcbfbb192fff55a46cebd47d965'))
        lineage=json.loads(read_control(base/'source-lineage.json',a['lineage_sha256']))
        amended=['scripts/diagnostics/segmenter_duration_launch.py','src/training/segmenter_duration_executor_v1.py']
        require(lineage==dict(state='reviewed_DUR06_function_scope',source_pins=r['source_pins'],prior_source_pins=prior,
                origin_source_pins=origin['source_pins'],amended=amended,outside_approved_regions_identical=True,
                numerical_recipe_unchanged=True,original_replay_assertion_unchanged=True)
                and len(prior)==400 and all(r['source_pins'].get(n)==h for n,h in prior.items() if n not in amended)
                and all(prior.get(n)==h for n,h in origin['source_pins'].items() if n!=amended[0]),
                'Inference producing lineage differs')
        require(a['origin_request_sha256']==origin['pins']['request_sha256']
                and a['origin_request_sha256']=='575603717131190f97ea7496e4ef0d4c0311ae5f9be0599658dad1c0671fd70b'
                and a['producer_sha256']=='a1930dd30180be300a07dd9a6aaa1e57650d4e0b1c8d93dc1c73864999151e3b',
                'Inference producer origin differs')
        tests=json.loads(read_control(base/'unit-qualification.json',a['tests_sha256']))
        require(tests['state']=='qualified_model_free_DUR06' and tests['source_pins']==r['source_pins']
                and type(tests['passed']) is int and tests['passed']>0
                and all(type(tests[k]) is int and tests[k]==0 for k in ('model_forwards','optimizer_calls','actual_arrays')),
                'Inference readiness unit qualification absent')
        recovery=json.loads(read_control(job/'result.json',a['recovery_sha256']))
        require(recovery['state']=='passed_duration_inference_v1' and recovery['attempt']=='DUR_INFERENCE_20261007_I03'
                and recovery['source_pins']==r['source_pins'] and recovery['runtime']==r['runtime']
                and recovery['producer_sha256']==a['producer_sha256'] and recovery['origin_request_sha256']==a['origin_request_sha256']
                and recovery['lineage_sha256']==a['lineage_sha256'] and recovery['tests_sha256']==a['tests_sha256']
                and recovery['model_calls']==dict(forwards=30,optimizer_calls=0) and all(type(v) is int for v in recovery['model_calls'].values())
                and recovery['primary_reads_blocked'] is True
                and all(type(recovery[k]) is int and recovery[k]==0 for k in ('original_arrays','third_party_weights'))
                and recovery['training_resume_qualified'] is False
                and recovery['scientific_launch'] is False and type(recovery['payload_member_bytes']) is int
                and 0<recovery['payload_member_bytes']<=2*1024**3
                and type(recovery['seconds']) in (float,int) and math.isfinite(recovery['seconds']) and 0<=recovery['seconds']<600
                and all(recovery[k]==a[k] for k in ('checkpoints','probe_checks','native_checks','view_checks')),
                'Inference cold qualification absent')
        steps=[0,48,96,144,192];cases=origin['targets']['cases']
        expected=[(step,c['study_id']) for step in steps[1:] for c in (cases if step==192 else cases[:6])]
        require(a['checkpoints']==steps and all(type(n) is int for n in a['checkpoints'])
                and type(a['probe_checks']) is list and len(a['probe_checks'])==5
                and all(set(v)=={'step','max_absolute_difference'} and type(v['step']) is int and v['step']==n
                    and type(v['max_absolute_difference']) in (float,int) and math.isfinite(v['max_absolute_difference'])
                    and 0<=v['max_absolute_difference']<=1e-6 for n,v in zip(steps,a['probe_checks']))
                and type(a['native_checks']) is list and len(a['native_checks'])==25
                and all(set(v)=={'step','study_id','prediction_exact','view_validated'} and type(v['step']) is int
                    and (v['step'],v['study_id'])==pair and v['prediction_exact'] is True and v['view_validated'] is True
                    for pair,v in zip(expected,a['native_checks'])) and type(a['view_checks']) is int and a['view_checks']==25,
                'Incomplete inference checkpoint/export/view qualification')
    else:
        acceptance=json.loads(read_control(REPO/'outputs/prowl/SEGMENTER-DURATION-NATIVE-READINESS.json',r['readiness']['acceptance_sha256']))
        require(acceptance['state']=='qualified_duration_native_v1' and acceptance['source_pins']==r['source_pins'] and acceptance['runtime']==r['runtime'] and acceptance['completed_steps']==192 and acceptance['primary_reads_blocked'] is True and acceptance['next_update_exact'] is True and acceptance['all_native_exports_exact'] is True and acceptance['cold_original_reads']==0 and acceptance['model_calls']==dict(producer=engine.call_limits('native_rehearsal')['producer'],cold=engine.call_limits('native_rehearsal')['cold']) and all(acceptance[k]==r['readiness'][k] for k in ('producer_sha256','recovery_sha256','tests_sha256')),"Missing exact duration native qualification")


def produce(r,args,grant):
    engine.checked_grant(r,grant);verify_code(r);validate_readiness(r);torch.set_num_threads(2)
    ss=stores(r,args)
    from src.operations.segmenter_duration_storage_v1 import areas
    require(Path(args.dest)==ss[1].root.parent/areas(r['storage_capability'])['controls'],"Worker output outside approved control area")
    p=provider(r);reader=targets.RealTargets(p,r,grant) if r["kind"]=="scientific" else targets.InventedTargets(p)
    require(canonical(reader.scope if hasattr(reader,"scope") else reader.request["targets"])==canonical(r["targets"]),"Prepared target scope differs")
    start=time.monotonic();exports=[];screen_records=[]
    def guard():
        _,rss=owned_tree(os.getpid());require(rss<=r["limits"]["rss_bytes"] and time.monotonic()-start<r["limits"]["producer_seconds"],"Producer time/RSS stop")
        from scripts.diagnostics.segmenter_training_qualification import power
        require(torch.mps.driver_allocated_memory()<=r["limits"]["driver_bytes"] and power()[0],"MPS driver/power stop")
    def screen(s,ref,tick):
        stage=targets.stage_scope(r["targets"],s.step);stage_exports=[];scores=[];references=[]
        weights=core.numerical.state_hash(s.model.state_dict())
        for case in stage["cases"]:
            tick();batch=p.get(case["study_id"],role=case["protected_role"],operation="inference")
            require(batch.target is None,"Native inference cannot see target")
            probability=s.predict(batch.image);files,report=evidence.export(probability,case,s.identity,s.step,weights,tick=tick);del probability
            context=dict(identity=s.identity,case=case,step=s.step,weights_sha256=weights)
            pair=kept(r,ss,files,":native:"+str(s.step)+":"+case["study_id"],"segmenter-duration-trained-native-case",lambda f,i,context=context:evidence.validate_export(f,context))
            pred=scoring.decode_prediction(files["mask.npy"],case["descriptor"]["geometry"]["shape_xyz"])
            pan,les,refs=reader.read(s,case["study_id"],tick=tick)
            score=scoring.score(pred,pan,les,target_state=case["descriptor"]["lesion_target_state"],tick=tick)
            from scripts.diagnostics.segmenter_native_scoring import oracle
            independent=oracle(pred,pan,les,tick);require(independent["confusion_matrix"]==score["confusion_matrix"],"Independent native count drift")
            from src.data.segmenter_training_views_v1 import render
            png,view=render(batch.image,pan,les,pred,case,s.step,weights,tick=tick)
            view|=dict(prediction_sha256=report["native_sha256"],reference_decoded_sha256={v['kind']:v['decoded_sha256'] for v in refs})
            view_context=context|dict(prediction_sha256=report["native_sha256"])
            view_pair=kept(r,ss,{"view.png":png,"view.json":canonical(view)},":view:"+str(s.step)+":"+case['study_id'],"segmenter-duration-views",lambda f,i,view_context=view_context:evidence.validate_views(f,view_context))
            pair|=dict(view_reference=view_pair);del png,view
            scores.append(dict(study_id=case["study_id"],protected_role=case["protected_role"],source_shape=list(pred.shape),source_affine=np.asarray(case["descriptor"]["geometry"]["affine_ras"]).reshape(4,4).tolist(),prediction_sha256=report["native_sha256"],**score,oracle=independent))
            references.extend(refs);stage_exports.append(pair|dict(report=report));del files,pred,pan,les;gc.collect();tick()
        require(reader.stage_counts[str(s.step)]==stage["limits"],"Incomplete native-stage source accounting")
        projection=evidence.scoring_request(r,[e["report"] for e in stage_exports],s.step)
        production=dict(request_sha256=digest(canonical(projection)),source_counts=reader.stage_counts[str(s.step)],source_arrays_read=2*len(stage["cases"]),ct_arrays_read=0,model_forwards=0,model_updates=0,code_pins=r["source_pins"],runtime=r["runtime"],mount_before=reader.mount_before,mount_after=reader.mount_after)
        native={n+".json":canonical(v) for n,v in dict(request=projection,scores=scores,references=references,aggregates=scoring.aggregates(scores),production=production).items()}
        record=dict(schema_version="1.0.0",policy_sha256=r["policy_sha256"],baseline_sha256=r["policy"]["baseline_sha256"],step=s.step,outcomes=[row(c,v) for c,v in zip(stage["cases"],scores)])
        files={"screen.json":canonical(record),"native.json":canonical({n:v.decode() for n,v in native.items()})}
        pair=kept(r,ss,files,":screen:"+str(s.step),"segmenter-duration-native-screen",lambda f,i:validate_stage(f,r,s.step,stage_exports))
        exports.extend(stage_exports);screen_records.append(record)
        return record,pair|dict(step=s.step,screen_sha256=digest(canonical(record)))
    def finish(s,result,probabilities,next_weights,tick):
        if result["state"]=="stopped":return dict(screen_records=screen_records,exports=exports,images_reference=None,probe_reference=None,next_state_reference=None)
        require(reader.counts==r["targets"]["limits"] and len(reader.used)==25,"Incomplete aggregate target scope")
        image_files={"manifest.json":canonical(dict(task="segmenter_duration_recovery_images_v1",request_sha256=digest(canonical(r)),cases=r["targets"]["cases"]))}
        for n,c in enumerate(r["targets"]["cases"]):image_files[f"image-{n:02d}.npy"]=core.cache.encode(p.get(c["study_id"],role=c["protected_role"],operation="inference").image)
        images=kept(r,ss,image_files,":images","segmenter-duration-images",lambda f,i:evidence.validate_images(f,r));del image_files
        next_state=kept(r,ss,next_weights["state"],":next-state","segmenter-duration-next-state",core.validate_payload)
        terminal=[v for v in exports if v["report"]["completed_updates"]==192]
        probes={"image.npy":core.cache.encode(p.get(r["policy"]["train_case_ids"][0],role="train",operation="inference").image),"next-weights.pt":next_weights["bytes"]}
        probes|={f"prob-{n}.npy":core.cache.encode(v) for n,v in probabilities.items()}
        probes["manifest.json"]=canonical(evidence.probe_manifest(s.identity,r["checkpoint_steps"],result["checkpoints"],next_weights["sha256"],r["targets"]["cases"],terminal))
        protected=kept(r,ss,probes,":probes","segmenter-duration-run-probes",lambda f,i:evidence.validate_probes(f,i,r));tick()
        return dict(screen_records=screen_records,exports=exports,images_reference=images,probe_reference=protected,next_state_reference=next_state)
    try:
        return engine.execute(r,p,Path(args.dest),save_checkpoint=lambda s:checkpoint(r,ss,s),screen=screen,finish=finish,
        protect_summary=lambda files,i:kept(r,ss,files,":summary","segmenter-duration-run-summary",lambda f,j:evidence.validate_summary(f,r)),
        grant=grant,guard=guard,verify_source=lambda:verify_code(r))
    except BaseException as exc:
        engine.put(Path(args.dest)/'producer-source-failure.json',canonical(dict(state='consumed_incomplete',error_type=type(exc).__name__,message=str(exc),source_counts=reader.counts,stage_counts=reader.stage_counts,attempted_target_pairs=sorted(reader.used))))
        raise


def cold(r,args,grant):
    engine.checked_grant(r,grant);verify_code(r);validate_readiness(r);torch.set_num_threads(2)
    from src.operations.segmenter_primary_read_guard_v1 import install
    install()
    ss=stores(r,args,recovery=True)
    from src.operations.segmenter_duration_storage_v1 import areas
    require(Path(args.dest)==ss[1].root.parent/areas(r['storage_capability'])['controls'],"Cold output outside approved control area")
    producer=json.loads(read_control(Path(args.dest)/"transaction.json",args.producer_pin,8*1024**2))
    identity=r["identity"];restored=[];counter=engine.CallCounter(r["model_calls"]["cold"]);start=time.monotonic()
    from src.training import segmenter_duration_recovery_audit_v1 as recovery_audit
    deltas=[];native=[];component_audit=None;phase="restore_summary"
    def tick():
        _,rss=owned_tree(os.getpid())
        require(rss<=r["limits"]["rss_bytes"] and time.monotonic()-start<r["limits"]["recovery_seconds"] and torch.mps.driver_allocated_memory()<=r["limits"]["driver_bytes"],"Cold resource stop")
        from scripts.diagnostics.segmenter_training_qualification import power
        require(power()[0],"Cold AC-power stop")
    def restore(pair,validator):
        tick();files,reference=restore_backup(ss[1],ss[2],pair["backup"],pair["primary"],identity,validator)
        restored.append(reference);tick();return files
    try:
        summary=restore(producer["summary_reference"],lambda f,i:evidence.validate_summary(f,r))
        completion=json.loads(summary["completion.json"])
        require(completion=={k:v for k,v in producer.items() if k!="summary_reference"},"Producer result differs from independent summary")
        all_exports=completion["recovery"]["exports"]
        for pair in completion["screens"]:
            phase="restore_screen"
            step=pair["step"];exports=[v for v in all_exports if v["report"]["completed_updates"]==step]
            restore(pair,lambda f,i,step=step,exports=exports:validate_stage(f,r,step,exports))
        if completion["state"]=="stopped":
            for pair in all_exports:
                phase="restore_stopped_export"
                report=pair['report'];case=next(c for c in r['targets']['cases'] if c['study_id']==report['study_id']);context=dict(identity=identity,case=case,step=report['completed_updates'],weights_sha256=report['weights_sha256'])
                restore(pair,lambda f,i,context=context:evidence.validate_export(f,context))
                restore(pair['view_reference'],lambda f,i,context=context,report=report:evidence.validate_views(f,context|dict(prediction_sha256=report['native_sha256'])))
            for pair in completion["checkpoints"]:
                phase="restore_stopped_checkpoint"
                files=restore(pair,core.validate_payload);session=core.restore_payload(files,identity)
                require(session.step==pair["step"],"Stopped checkpoint boundary drift");del session,files;gc.collect();torch.mps.empty_cache()
            result=dict(state="stopped_checkpoints_restored",full_duration_qualified=False,restores=restored,model_calls=counter.counts,original_targets=0,original_ct=0)
        else:
            phase="restore_images"
            images=restore(completion["recovery"]["images_reference"],lambda f,i:evidence.validate_images(f,r))
            phase="restore_probes"
            probes=restore(completion["recovery"]["probe_reference"],lambda f,i:evidence.validate_probes(f,i,r))
            phase="restore_expected_next_state"
            next_state=restore(completion["recovery"]["next_state_reference"],core.validate_payload)
            expected_next=core.restore_payload(next_state,identity);require(expected_next.step==49,"Next-state boundary")
            image=core.cache.decode(probes["image.npy"],"image");next_exact=False
            for pair in completion["checkpoints"]:
                step=pair["step"];phase="restore_checkpoint_"+str(step);files=restore(pair,core.validate_payload);session=counter.attach(core.restore_payload(files,identity));del files
                require(session.step==step,"Cold checkpoint boundary drift");tick()
                expected=np.load(__import__('io').BytesIO(probes[f"prob-{step}.npy"]),allow_pickle=False)
                phase="checkpoint_probability"
                difference=float(np.max(np.abs(session.predict(image)-expected)));deltas.append(difference);require(difference<=1e-6,"Cold probability drift")
                for exported in [v for v in all_exports if v["report"]["completed_updates"]==step]:
                    phase="native_export"
                    report=exported["report"];case=next(c for c in r["targets"]["cases"] if c["study_id"]==report["study_id"])
                    context=dict(identity=identity,case=case,step=step,weights_sha256=report["weights_sha256"])
                    files=restore(exported,lambda f,i,context=context:evidence.validate_export(f,context))
                    restore(exported['view_reference'],lambda f,i,context=context,report=report:evidence.validate_views(f,context|dict(prediction_sha256=report['native_sha256'])))
                    n=r["targets"]["cases"].index(case);x=core.cache.decode(images[f"image-{n:02d}.npy"],"image")
                    probability=session.predict(x);mask,_=evidence.codec.export(probability,case,tick=tick)
                    require(evidence.codec.array_bytes(mask)==files["mask.npy"],"Cold native export drift");native.append(dict(study_id=case["study_id"],step=step,prediction_exact=True))
                    del probability,mask,files,x;tick()
                if step==48 and r["kind"]=="native_rehearsal":
                    p=inputs.InventedInputs(144);require(canonical(p.control)==r["controls"]["inputs.json"].encode(),"Invented replay identity")
                    phase="replay_next_update";session.update(p);tick()
                    phase="compare_next_update"
                    def state_parts(s):
                        return dict(model=s.model.state_dict(),optimizer=s.optimizer.state_dict(),progress=core.progress(s),cpu_rng=s.cpu_rng,mps_rng=s.mps_rng)
                    component_audit=recovery_audit.compare(state_parts(session),state_parts(expected_next),tree_equal=core.tree_exact)
                    recovery_audit.publish(Path(args.dest)/"next-update-audit.json",component_audit)
                    require(component_audit["all_exact"],"Independent full next-update recovery differs")
                    require(core.numerical.state_hash(session.model.state_dict())==json.loads(probes["manifest.json"])["next_weights_sha256"],"Independent next weights differ");next_exact=True;del p
                del session;gc.collect();torch.mps.empty_cache();tick()
            require(counter.counts==r["model_calls"]["cold"],"Incomplete cold model-call inventory")
            result=dict(state="passed",full_duration_qualified=True,engineering_only=r["kind"]=="native_rehearsal",restores=restored,probability_max_difference=max(deltas),native_checks=native,next_update_exact=next_exact if r["kind"]=="native_rehearsal" else None,model_calls=counter.counts,original_targets=0,original_ct=0)
        phase="persist_success"
        verify_code(r);engine.put(Path(args.dest)/"cold-result.json",canonical(result));return result
    except BaseException as exc:
        try:
            report=recovery_audit.failure(phase=phase,error=exc,counts=counter.counts,restored=len(restored),deltas=deltas,native=native,component_audit=component_audit)
            recovery_audit.publish(Path(args.dest)/"cold-failure-audit.json",report)
        except BaseException as audit_error:
            if hasattr(exc,"add_note"):exc.add_note("Cold failure metadata could not be persisted: "+type(audit_error).__name__)
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["validate","dispatch","_producer","_cold","_unit_echo","_unit_sleep"])
    for name in ("request","request-pin","dest","approval","approval-pin","storage","storage-pin","producer-pin"):parser.add_argument("--"+name,required=name in ("request","request-pin"))
    parser.add_argument("--stage",choices=["producer","cold","unit_echo","unit_sleep"],default="producer")
    args=parser.parse_args(argv);raw=read_control(args.request,args.request_pin);r=json.loads(raw);engine.validate_request(r);require(raw==canonical(r),"Noncanonical worker request")
    if args.action=="validate":print(json.dumps(dict(state="valid_request_no_dispatch",kind=r["kind"],request_sha256=args.request_pin)));return
    require(args.dest is not None,"Destination required")
    if args.action=="dispatch":result=dispatch(args.request,args.request_pin,args.dest,approval_path=args.approval,approval_pin=args.approval_pin,storage_path=args.storage,storage_pin=args.storage_pin,stage=args.stage)
    elif args.action in ("_unit_echo","_unit_sleep"):
        require(r["kind"]=="unit" and args.approval is None and args.storage is None,"Unit worker domain")
        if args.action=="_unit_sleep":time.sleep(10)
        result=dict(state="unit_no_model_worker_complete",model_forwards=0,optimizer_calls=0)
        engine.put(Path(args.dest)/"unit-worker-result.json",canonical(result))
    else:
        require(r["kind"]!="unit" and args.approval is not None and args.storage is not None,"Actual worker requires authority")
        grant=engine.authorize(r,read_control(args.approval,args.approval_pin),trusted_approval_sha256=args.approval_pin)
        stage='producer' if args.action=='_producer' else 'cold'
        marker=json.loads((Path(args.dest)/('dispatch-'+stage+'-consumed.json')).read_bytes())
        require(marker['state']=='consumed' and marker['request_sha256']==args.request_pin and marker['stage']==stage,"Worker missing exclusive matching dispatch consumption")
        result=produce(r,args,grant) if args.action=="_producer" else cold(r,args,grant)
    print(json.dumps(dict(state=result["state"])))


if __name__=="__main__":main()
