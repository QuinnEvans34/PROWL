"""Bounded two-case executor, explicit authorization, full-volume metrics and exports."""
from copy import deepcopy
from io import BytesIO
import gzip
import json
import math
import time
import numpy as np
import nibabel as nib
from PIL import Image,ImageDraw
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data.cohort_registry import MEMBERS
from src.data.localizer_preprocessing import restore_to_source
from src.training.localizer import foreground_dice,loss_value,configured_loss,patch_batch
from src.training.localizer_run import (bind_item,payload,publish_checkpoint,validate_payload,MPSRun)

REAL_CONFIG=dict(patch_size=[96]*3,seed=42,learning_rate=.003,weight_decay=.00001,max_steps=100)
BALANCED_REAL_CONFIG=dict(REAL_CONFIG,loss_id='balanced_ce_dice_v1')
BALANCED_EXPERIMENTS={'CAP-EXP-002':BALANCED_REAL_CONFIG,'CAP-EXP-003':dict(BALANCED_REAL_CONFIG,learning_rate=.0003),'CAP-EXP-004':dict(BALANCED_REAL_CONFIG,learning_rate=.0003,max_steps=300)}
INITIAL_WEIGHTS_SHA='365306b1aec77681bd651a1e87ca7902b10efffef38607f1618303220d20954e'

def model_digest(model):
    import hashlib
    h=hashlib.sha256()
    for name,value in model.state_dict().items():h.update(name.encode());h.update(value.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def validate_controls(files,identity):
    for name,key in [('plan.json','plan_sha256'),('authorization.json','authorization_sha256')]:
        require(digest(files[name])==identity[key],'Changed smoke control')
    plan=json.loads(files['plan.json']);auth=json.loads(files['authorization.json'])
    require(plan['schema_version']=='1.0.0' and plan['config']==identity['config'] and plan['member_ids']==MEMBERS and
        plan['checkpoint_every']>0 and type(plan['checkpoint_every'])==int and
        0<plan['update_seconds']<=600 and 0<plan['total_seconds']<=1200,'Invalid bounded plan')
    expected={k:identity[k] for k in ('inputs_sha256','source_sha256','environment_sha256','plan_sha256')}
    require(auth['bindings']==expected and auth['allowed'] is True and auth['data_mode']==identity['training_data'], 'Unapproved smoke authorization')
    if identity['training_data']=='qualified_cohort':
        balanced=identity['schema_version']=='4.0.0';experiment=plan['experiment_id'] if balanced else 'CAP-EXP-001'
        require(not balanced or experiment in BALANCED_EXPERIMENTS,'Unregistered balanced experiment')
        require(plan['experiment_id']==experiment and plan['config']==(BALANCED_EXPERIMENTS[experiment] if balanced else REAL_CONFIG) and
            plan['checkpoint_every']==(75 if experiment=='CAP-EXP-004' else 25) and auth['authority']=='Quinton Evans' and
            auth['operation']=='launch_'+experiment,'Real launch scope differs')
    if identity['schema_version']=='4.0.0':
        require(plan.get('evaluation_policy')=='balanced_and_legacy_v1','Missing objective-aware evaluation')
    if identity['training_data']=='synthetic':require(auth['operation']=='synthetic_executor_check','Wrong fixture authorization')


def probability_metrics(probabilities,target,affine):
    p=torch.as_tensor(probabilities).cpu().float();y=torch.as_tensor(target).cpu().long()
    require(p.ndim==4 and p.shape[0]==2 and y.shape==(1,*p.shape[1:]) and torch.isfinite(p).all().item() and
        p.min().item()>=0 and p.max().item()<=1 and torch.allclose(p.sum(0),torch.ones_like(p[0]),atol=1e-5,rtol=0),'Invalid full-volume probabilities')
    require(torch.all((y==0)|(y==1)).item(),'Invalid reference classes')
    pred=p.argmax(0,keepdim=True);metrics=foreground_dice(pred,y)
    voxel_volume=abs(float(np.linalg.det(np.asarray(affine)[:3,:3])))
    require(math.isfinite(voxel_volume) and voxel_volume>0,'Invalid physical volume')
    metrics.update(loss=float(loss_value(p.clamp_min(1e-7).log()[None],y[None])),
        target_volume_mm3=metrics['target_foreground']*voxel_volume,predicted_volume_mm3=metrics['predicted_foreground']*voxel_volume)
    return metrics


def contact_sheet(image,target,prediction,title):
    image=np.asarray(image);target=np.asarray(target);prediction=np.asarray(prediction)
    canvas=Image.new('RGB',(768,294),'white');draw=ImageDraw.Draw(canvas);draw.text((8,4),title,fill='black')
    draw.text((8,20),'Processed RAS grid; target green, prediction red, overlap yellow',fill='black')
    for axis in range(3):
        locations=np.where(target>0)[axis]
        index=int(np.median(locations)) if len(locations) else image.shape[axis]//2
        plane=np.take(image,index,axis=axis).T;truth=np.take(target,index,axis=axis).T.astype(bool);pred=np.take(prediction,index,axis=axis).T.astype(bool)
        rgb=np.repeat((np.clip(plane,0,1)*255).astype(np.uint8)[...,None],3,axis=2)
        rgb[truth]=((rgb[truth].astype(float)+[0,255,0])/2).astype(np.uint8)
        rgb[pred]=((rgb[pred].astype(float)+[255,0,0])/2).astype(np.uint8)
        rgb[truth&pred]=[255,255,0]
        panel=Image.fromarray(rgb);panel.thumbnail((256,240));canvas.paste(panel,(axis*256,50))
        draw.text((axis*256+5,35),f'axis {axis}, slice {index}',fill='black')
    stream=BytesIO();canvas.save(stream,format='PNG');return stream.getvalue()


def evaluate(session,dataset,identity,*,guard=lambda:None):
    rows=[];exports={}
    for index,sid in enumerate(MEMBERS):
        guard();item=bind_item(dataset,index,identity)
        # The predictor's signature receives image only, never target or reference ROI.
        probabilities=session.predict(item['image']);record=item['transform_record']
        metrics=probability_metrics(probabilities,item['label'],record['processed_affine'])
        if identity['schema_version']=='4.0.0':
            from src.training.localizer_diagnostics import probability_summary,logit_diagnostics
            metrics['legacy_loss']=metrics['loss']
            metrics['loss']=float(configured_loss(probabilities.clamp_min(1e-7).log()[None],item['label'][None],session.config))
            metrics['probability_diagnostics']=probability_summary(probabilities[1],item['label'][0])
            d=metrics['probability_diagnostics'];count=sum(d[k] is not None for k in ('mean_ce_foreground','mean_ce_background'))
            metrics['balanced_ce_contributions']={k:(d[k]/count if d[k] is not None else 0.) for k in ('mean_ce_foreground','mean_ce_background')}
            probe_step=min(index+2,session.config['max_steps']-1)
            x,y,trace=patch_batch(item['image'],item['label'],session.config,step=probe_step,member_id=sid)
            with torch.no_grad():logits=session.model(x.to(identity['device'])).cpu()
            metrics['fixed_patch_probe']=dict(sampling=trace,terms=logit_diagnostics(logits,y,include_balanced=True),
                probability=probability_summary(logits.softmax(1)[:,1],y[:,0]))

        native=restore_to_source(probabilities,record,discrete=False).as_tensor().argmax(0).numpy().astype(np.uint8)
        image=nib.Nifti1Image(native,np.asarray(record['source_affine']));image.header.set_xyzt_units('mm')
        code=sid.split(':')[-1];exports[code+'.nii.gz']=gzip.compress(image.to_bytes(),mtime=0)
        exports[code+'.png']=contact_sheet(item['image'][0],item['label'][0],probabilities.argmax(0),code)
        rows.append(dict(study_id=sid,**metrics,native_shape=list(native.shape),native_foreground=int(native.sum()),
            transform_sha256=record['record_sha256'],source_affine=record['source_affine']))
        guard()
    return dict(cases=rows,mean_loss=sum(r['loss'] for r in rows)/2,
        mean_dice=None if any(r['dice'] is None for r in rows) else sum(r['dice'] for r in rows)/2,
        loss_definition=('balanced_CE_plus_foreground_soft_Dice_on_log_clamped_stitched_probabilities_v1' if identity['schema_version']=='4.0.0' else 'CE_plus_foreground_soft_Dice_on_log_clamped_stitched_probabilities_v1')),exports


def learning_observed(before,after):
    return (before['mean_dice'] is not None and after['mean_dice'] is not None and
        after['mean_loss']<=.9*before['mean_loss'] and after['mean_dice']-before['mean_dice']>=.1)


def checkpoint_files(files):
    return {k:v for k,v in files.items() if k in {'identity.json','state.pt','inputs.json','source.json','environment.json','plan.json','authorization.json','progress.json'}}


def validate_terminal(files,identity):
    checked=validate_payload(checkpoint_files(files),identity)
    expected=set(checkpoint_files(files))|{'before.json','after.json','result.json','probe.pt'}|{
        phase+'-'+sid.split(':')[-1]+suffix for phase in ('before','after') for sid in MEMBERS for suffix in ('.nii.gz','.png')}
    if identity['schema_version']=='4.0.0':expected.add('trajectory.json')
    require(set(files)==expected,'Terminal inventory differs')
    before=json.loads(files['before.json']);after=json.loads(files['after.json']);result=json.loads(files['result.json'])
    require(result['completed_steps']==identity['config']['max_steps']==checked['step'] and
        result['learning_observed']==learning_observed(before,after) and result['state']=='complete','Terminal outcome differs')
    if identity['schema_version']=='4.0.0':
        trajectory=json.loads(files['trajectory.json']);plan=json.loads(files['plan.json'])
        steps=[0]+[s for s in range(1,identity['config']['max_steps']+1) if s%plan['checkpoint_every']==0 or s==identity['config']['max_steps']]
        require([r['step'] for r in trajectory]==steps and trajectory[0]['metrics']==before and trajectory[-1]['metrics']==after,'Objective trajectory differs')
        for metrics in (r['metrics'] for r in trajectory):
            require(metrics['loss_definition'].startswith('balanced_CE_') and all(math.isfinite(c['legacy_loss']) for c in metrics['cases']),'Wrong evaluation objective')
    probe=torch.load(BytesIO(files['probe.pt']),weights_only=True)
    require(probe.shape==(2,*identity['config']['patch_size']) and torch.isfinite(probe).all().item(),'Invalid reload probe')
    for phase,metrics in [('before',before),('after',after)]:
        require([r['study_id'] for r in metrics['cases']]==MEMBERS,'Evaluation member order differs')
        require(all(math.isfinite(r['loss']) and r['loss']>=0 for r in metrics['cases']),'Invalid evaluation loss')
        require(abs(metrics['mean_loss']-sum(r['loss'] for r in metrics['cases'])/2)<1e-10,'Mean loss differs')
        expected_dice=None if any(r['dice'] is None for r in metrics['cases']) else sum(r['dice'] for r in metrics['cases'])/2
        require(metrics['mean_dice']==expected_dice,'Mean Dice differs')
        for row in metrics['cases']:
            code=row['study_id'].split(':')[-1]
            with gzip.GzipFile(fileobj=BytesIO(files[phase+'-'+code+'.nii.gz'])) as stream:data=stream.read(32*1024**2+1)
            require(len(data)<=32*1024**2,'Export size cap')
            volume=nib.Nifti1Image.from_bytes(data);values=np.asarray(volume.dataobj)
            require(list(values.shape)==row['native_shape'] and np.isin(values,[0,1]).all() and int(values.sum())==row['native_foreground'] and
                np.allclose(volume.affine,row['source_affine'],rtol=0,atol=1e-5),'Invalid native export')
            with Image.open(BytesIO(files[phase+'-'+code+'.png'])) as pic:pic.verify()
    return dict(**checked,terminal_state='complete',learning_observed=result['learning_observed'])


def execute(session,dataset,identity,controls,store,*,guard=lambda:None,event=lambda row:None,clock=time.monotonic):
    """No automatic retries or resume. Fresh scratch run; every completed checkpoint is preserved."""
    validate_controls(controls,identity);require(session.step==0 and session.config==identity['config'],'Fresh smoke must start at step zero with exact config')
    require((identity['device']=='mps')==isinstance(session,MPSRun),'Session device differs from identity')
    balanced=identity['schema_version']=='4.0.0'
    initial_weights_sha=model_digest(session.model) if balanced else None
    if balanced and identity['training_data']=='qualified_cohort':require(initial_weights_sha==INITIAL_WEIGHTS_SHA,'Scratch initialization differs from CAP-EXP-001')
    plan=json.loads(controls['plan.json']);started=clock();history=[];refs=[];trajectory=[]
    def check():
        guard();require(clock()-started<plan['total_seconds'],'Total time budget reached')
    def checkpoint():
        data=dict(controls,**{'progress.json':canonical(dict(updates=history))})
        files=payload(session,identity,data);ref=publish_checkpoint(store,files,identity);refs.append(ref)
        event(dict(state='checkpoint_complete',reference=ref));return files
    try:
        check();checkpoint();before,before_exports=evaluate(session,dataset,identity,guard=check)
        event(dict(state='before_evaluation',metrics=before));trajectory.append(dict(step=0,metrics=before));updates_started=clock()
        while session.step<identity['config']['max_steps']:
            check();require(clock()-updates_started<plan['update_seconds'],'Update time budget reached')
            iteration_started=clock()
            index=session.step%len(MEMBERS);item=bind_item(dataset,index,identity)
            check();require(clock()-updates_started<plan['update_seconds'],'Update time budget reached')
            if isinstance(session,MPSRun):row=session._step(item['image'],item['label'],MEMBERS[index])
            else:
                require(identity['training_data']=='synthetic','CPU session cannot consume real training inputs')
                row=session.update(item['image'],item['label'],MEMBERS[index])
            row['load_and_update_seconds']=clock()-iteration_started
            history.append(row);event(dict(state='update_complete',**row));check()
            require(clock()-updates_started<plan['update_seconds'],'Update time budget reached')
            if session.step%plan['checkpoint_every']==0 or session.step==identity['config']['max_steps']:
                checkpoint()
                if balanced and session.step<identity['config']['max_steps']:
                    middle,_=evaluate(session,dataset,identity,guard=check);trajectory.append(dict(step=session.step,metrics=middle));event(dict(state='intermediate_evaluation',completed_step=session.step,metrics=middle))
        event(dict(state='update_phase_complete',completed_step=session.step))
        after,after_exports=evaluate(session,dataset,identity,guard=check);check()
        trajectory.append(dict(step=session.step,metrics=after))
        result=dict(state='complete',completed_steps=session.step,learning_observed=learning_observed(before,after),
            checkpoint_references=refs,elapsed_seconds=clock()-started,data_mode=identity['training_data'])
        if balanced:result['scratch_initialization_sha256']=initial_weights_sha
        files=payload(session,identity,dict(controls,**{'progress.json':canonical(dict(updates=history))}))
        if balanced:files['trajectory.json']=canonical(trajectory)
        files.update({'before.json':canonical(before),'after.json':canonical(after),'result.json':canonical(result)})
        probe=session.predict(torch.full((1,*identity['config']['patch_size']),.25));stream=BytesIO();torch.save(probe,stream)
        files['probe.pt']=stream.getvalue();check()
        for phase,exports in [('before',before_exports),('after',after_exports)]:files.update({phase+'-'+k:v for k,v in exports.items()})
        artifact_id=identity['run_id']+':terminal';derivation=digest(canonical(identity))
        metadata=dict(artifact_type='localizer-smoke-terminal',schema_version='1.0.0',component='localizer-smoke-v1',
            code_sha256=identity['source_sha256'],parents=[identity['inputs_sha256']],retention='keeper',sensitivity='private-research',run_id=identity['run_id'],stage_id='terminal')
        pin,_=store.publish(artifact_id,derivation_sha256=derivation,files=files,metadata=metadata,validate=lambda f:validate_terminal(f,identity))
        event(dict(state='terminal_published',receipt_sha256=pin))
        return result,dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation,step=session.step,status='published')
    except BaseException as error:
        event(dict(state='failed_or_interrupted',completed_steps=session.step,error_type=type(error).__name__,message=str(error),last_complete_checkpoint=refs[-1] if refs else None))
        raise
