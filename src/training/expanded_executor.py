"""Complete bounded expanded experiment transaction; caller supplies pinned approval/stores."""
from io import BytesIO
import gzip
import json
import math
import time
import numpy as np
import nibabel as nib
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data.localizer_preprocessing_v2 import restore_to_source
from src.training.expanded_localizer import verify_session,scheduled_member,checkpoint,restore
from src.training.localizer import configured_loss
from src.training.localizer_run import MPSRun
from src.training.localizer_smoke import contact_sheet,model_digest,INITIAL_WEIGHTS_SHA

CONFIG=dict(patch_size=[96]*3,seed=42,learning_rate=.0003,weight_decay=.00001,max_steps=288,loss_id='balanced_ce_dice_v1')
SUSTAINED_CONFIG=dict(CONFIG,max_steps=2400,budget_id='sustained_localizer_v1')
EXPERIMENTS={
    'CAP-EXP-005':dict(config=CONFIG,evaluation_steps=[0,144,288],checkpoint_steps=[0,96,192,288],total_seconds=1200,update_seconds=600),
    'CAP-EXP-006':dict(config=SUSTAINED_CONFIG,evaluation_steps=[0,288,800,1600,2400],checkpoint_steps=list(range(0,2401,400)),total_seconds=3600,update_seconds=3000),
}
REAL_INPUT_PIN='562f95b4d8b0a29d9cd5e31543a723c9f9299f02b0c3e1ee6cd280db15ced447'


def validate_controls(identity,inputs,plan,approval):
    from src.training.expanded_localizer import validate_identity
    validate_identity(identity,inputs)
    require(identity['schema_version']=='2.0.0' and digest(canonical(plan))==identity['plan_sha256'],'Plan identity differs')
    require(set(plan)=={'experiment_id','config','evaluation_steps','checkpoint_steps','total_seconds','update_seconds','margin_mm','export_final'},'Plan fields differ')
    require(plan['config']==identity['config'] and plan['config'].get('loss_id')=='balanced_ce_dice_v1' and plan['margin_mm']==10 and plan['export_final'] is True,'Plan recipe differs')
    n=identity['config']['max_steps']
    for key in ('evaluation_steps','checkpoint_steps'):
        v=plan[key];require(v==sorted(set(v)) and v[0]==0 and v[-1]==n and all(type(s)==int and 0<=s<=n for s in v),'Invalid cadence')
    sustained='budget_id' in identity['config']
    require(0<plan['update_seconds']<=(3000 if sustained else 600) and 0<plan['total_seconds']<=(3600 if sustained else 1200),'Time envelope differs')
    require(approval.get('allowed') is True and approval.get('bindings')=={k:identity[k] for k in ('inputs_sha256','source_sha256','environment_sha256','plan_sha256')},'Missing or mismatched launch approval')
    real=identity['purpose']=='qualified-expanded-executor'
    require(approval.get('operation')==('launch_'+plan['experiment_id'] if real else 'synthetic_executor_verification'),'Wrong approval operation')
    if real:
        require(approval.get('authority')=='Quinton Evans' and identity['device']=='mps' and plan['experiment_id'] in EXPERIMENTS,'Wrong real launch scope')
        require(all(plan[k]==v for k,v in EXPERIMENTS[plan['experiment_id']].items()),'Real schedule differs')
        require(identity['inputs_sha256']==REAL_INPUT_PIN and len(inputs['roles']['optimizer'])==16 and len(inputs['roles']['evaluator'])==11,'Wrong frozen real inputs')
    else:require(identity['purpose']=='synthetic-expanded-executor' and plan['experiment_id']=='synthetic','Invalid fixture scope')


def metrics(pred,target,affine):
    """All-component box is bounded independently of component-count diagnostics."""
    require(np.isin(pred,[0,1]).all() and np.isin(target,[0,1]).all(),'Binary metric masks required')
    p=np.asarray(pred,dtype=bool);y=np.asarray(target,dtype=bool);a=np.asarray(affine)
    require(p.shape==y.shape and p.ndim==3 and 0<p.size<=8_000_000,'Wrong metric grid')
    spacing=np.diag(a)[:3];require(a.shape==(4,4) and np.isfinite(a).all() and (spacing>0).all() and np.allclose(a[:3,:3],np.diag(spacing)),'Noncanonical metric affine')
    n=int(y.sum());v=int(p.sum());tp=int((p&y).sum());require(n>0,'Positive reference required')
    box=None;fraction=None;coverage=None
    if v:
        coords=np.nonzero(p);pad=np.ceil(10/spacing).astype(int)
        lo=np.maximum(0,np.array([c.min() for c in coords])-pad);hi=np.minimum(p.shape,np.array([c.max()+1 for c in coords])+pad)
        box=[lo.tolist(),hi.tolist()];fraction=float(np.prod(hi-lo)/p.size);coverage=float(y[tuple(slice(int(l),int(h)) for l,h in zip(lo,hi))].sum()/n)
    from scipy import ndimage
    _,components=ndimage.label(p,structure=ndimage.generate_binary_structure(3,1))
    dice=2*tp/(n+v);recall=tp/n;ratio=v/n
    return dict(dice=dice,precision=tp/v if v else None,recall=recall,volume_ratio=ratio,reference_voxels=n,predicted_voxels=v,
        true_positive=tp,false_positive=v-tp,false_negative=n-tp,box=box,margin_mm=10.,scan_fraction=fraction,box_reference_coverage=coverage,
        localization_state='region_available' if v else 'failed_empty_localization',component_count=int(components),
        component_detail_state='budget_exceeded' if components>4096 else 'count_available',
        fit_diagnostic_pass=recall>=.98 and dice>=.65 and ratio<=2.,pre_mapping_roi_diagnostic_pass=coverage is not None and coverage>=.995 and fraction<=.25,
        scope='processed-grid pancreas only; no lesion or complete-organ claim')


def validate_checkpoint(files,identity):
    required={'identity.json','inputs.json','progress.json','state.pt','plan.json','approval.json'}
    require(set(files)==required,'Executor checkpoint inventory differs')
    validate_controls(identity,json.loads(files['inputs.json']),json.loads(files['plan.json']),json.loads(files['approval.json']))
    session=restore({k:v for k,v in files.items() if k not in {'plan.json','approval.json'}},identity,device='cpu')
    return dict(step=session.step,identity_sha256=digest(canonical(identity)))


def publish(store,identity,suffix,files,validator):
    artifact_id=identity['run_id']+':'+suffix;derivation=digest(canonical(dict(identity=identity,suffix=suffix)))
    meta=dict(run_id=identity['run_id'],stage_id=suffix,artifact_type='expanded-localizer-'+suffix.split(':')[0],schema_version='1.0.0',component='expanded-executor-v1',code_sha256=identity['source_sha256'],parents=[identity['inputs_sha256']],retention='research-keeper',sensitivity='private-research')
    pin,status=store.publish(artifact_id,derivation_sha256=derivation,files=files,metadata=meta,validate=validator)
    return dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation,status=status)


def validate_export(files,expected):
    require(set(files)=={'prediction.nii.gz','overlay.png','record.json'},'Export inventory differs')
    record=json.loads(files['record.json']);require(record==expected,'Export record differs')
    transform=record['transform'];require(digest(canonical({k:v for k,v in transform.items() if k!='record_sha256'}))==transform['record_sha256'],'Export transform changed')
    with gzip.GzipFile(fileobj=BytesIO(files['prediction.nii.gz'])) as f:raw=f.read(64_000_000+4097)
    require(len(raw)<=64_000_000+4096,'Native export cap')
    image=nib.Nifti1Image.from_bytes(raw);values=np.asarray(image.dataobj)
    require(values.dtype==np.uint8 and list(values.shape)==record['transform']['source_shape'] and np.isin(values,[0,1]).all() and int(values.sum())==record['native_foreground'] and np.allclose(image.affine,record['transform']['source_affine'],rtol=0,atol=1e-5),'Native export geometry/content differs')
    from PIL import Image
    with Image.open(BytesIO(files['overlay.png'])) as picture:picture.verify()
    return dict(study_id=record['study_id'],role=record['role'],native_foreground=record['native_foreground'])


def evaluate(session,cache,identity,store,*,export=False,guard=lambda:None):
    result={};refs=[]
    for role in ('optimizer','evaluator'):
        rows=[]
        for i,sid in enumerate(cache.members(role)):
            guard();item=cache.get(role,i);prob=session.predict(item['image']);pred=prob.argmax(0,keepdim=True)
            require(prob.shape==(2,*item['image'].shape[1:]) and torch.isfinite(prob).all() and prob.min()>=0 and prob.max()<=1,'Invalid prediction')
            m=metrics(pred[0].numpy(),item['label'][0].numpy(),item['transform_record']['processed_affine'])
            from src.training.localizer_coverage import mapped_source_box
            transform=item['transform_record']
            m['source_crop_geometry']=mapped_source_box(m['box'],**{k:transform[k] for k in ('processed_shape','processed_affine','source_shape','source_affine')})
            m['scan_fraction_scope']='padded_processed_tensor; use source_crop_geometry for acquired-scan crop size'
            m['source_size_diagnostic_pass']=m['source_crop_geometry']['scan_fraction'] is not None and 0<m['source_crop_geometry']['scan_fraction']<=.25
            m['loss']=float(configured_loss(prob.clamp_min(1e-7).log()[None],item['label'].long()[None],identity['config']))
            m['loss_definition']='balanced_CE_plus_foreground_soft_Dice_on_log_clamped_stitched_probabilities_v1'
            rows.append(dict(study_id=sid,**m))
            if export:
                native=restore_to_source(pred,item['transform_record'],discrete=True)[0].numpy().astype(np.uint8)
                record=dict(study_id=sid,role=role,step=session.step,metrics=m,transform=item['transform_record'],native_foreground=int(native.sum()))
                image=nib.Nifti1Image(native,np.asarray(record['transform']['source_affine']));image.header.set_xyzt_units('mm')
                files={'prediction.nii.gz':gzip.compress(image.to_bytes(),mtime=0),'overlay.png':contact_sheet(item['image'][0].numpy(),item['label'][0].numpy(),pred[0].numpy(),sid),'record.json':canonical(record)}
                ref=publish(store,identity,'case:'+role+':'+str(i),files,lambda f,r=record:validate_export(f,r));refs.append(dict(study_id=sid,role=role,reference=ref))
            guard()
        result[role]=dict(cases=rows,mean_dice=sum(r['dice'] for r in rows)/len(rows),mean_loss=sum(r['loss'] for r in rows)/len(rows))
    return result,refs


def validate_terminal(files,identity,store):
    require(set(files)=={'result.json','trajectory.json','probe.pt'},'Terminal inventory differs')
    result=json.loads(files['result.json']);trajectory=json.loads(files['trajectory.json'])
    require(result['state']=='complete' and result['completed_steps']==identity['config']['max_steps'],'Incomplete terminal')
    cp=result['checkpoints'][-1];payload,_=store.resolve(cp['artifact_id'],receipt_sha256=cp['receipt_sha256'],expected_derivation=cp['derivation_sha256'],validate=lambda f:validate_checkpoint(f,identity))
    plan=json.loads(payload['plan.json']);inputs=json.loads(payload['inputs.json'])
    require(validate_checkpoint(payload,identity)['step']==result['completed_steps'],'Terminal checkpoint differs')
    require([t['step'] for t in trajectory]==plan['evaluation_steps'],'Incomplete evaluation cadence')
    steps=[]
    for ref in result['checkpoints']:
        data,_=store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],expected_derivation=ref['derivation_sha256'],validate=lambda f:validate_checkpoint(f,identity))
        steps.append(validate_checkpoint(data,identity)['step'])
    require(steps==plan['checkpoint_steps'],'Incomplete checkpoint cadence')
    for t in trajectory:
        for role in ('optimizer','evaluator'):
            rows=t['metrics'][role]['cases'];require([r['study_id'] for r in rows]==[d['study_id'] for d in inputs['roles'][role]],'Evaluation membership differs')
            require(all(type(r['dice']) in (int,float) and math.isfinite(r['dice']) and 0<=r['dice']<=1 for r in rows),'Invalid evaluation metrics')
            require(t['metrics'][role]['mean_dice']==sum(r['dice'] for r in rows)/len(rows),'Mean differs')
            require(all(math.isfinite(r['loss']) and r['loss']>=0 for r in rows) and t['metrics'][role]['mean_loss']==sum(r['loss'] for r in rows)/len(rows),'Loss differs')
    expected=[(role,d['study_id']) for role in ('optimizer','evaluator') for d in inputs['roles'][role]]
    require([(r['role'],r['study_id']) for r in result['exports']]==expected,'Incomplete exports')
    for row in result['exports']:
        ref=row['reference']
        def check(f):
            r=json.loads(f['record.json']);require(r['study_id']==row['study_id'] and r['role']==row['role'] and r['step']==result['completed_steps'],'Wrong export binding')
            final=next(x for x in trajectory[-1]['metrics'][row['role']]['cases'] if x['study_id']==row['study_id'])
            require(r['metrics']=={k:v for k,v in final.items() if k!='study_id'},'Export metrics differ from final evaluation')
            return validate_export(f,r)
        store.resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],expected_derivation=ref['derivation_sha256'],validate=check)
    probe=torch.load(BytesIO(files['probe.pt']),map_location='cpu',weights_only=True)
    require(probe.shape==(2,*identity['config']['patch_size']) and torch.isfinite(probe).all(),'Invalid terminal probe')
    return dict(step=result['completed_steps'],exports=len(expected),identity_sha256=digest(canonical(identity)))


def execute(session,cache,identity,plan,approval,store,*,guard=lambda:None,event=lambda r:None,clock=time.monotonic):
    verify_session(session,identity,cache);validate_controls(identity,cache.inputs,plan,approval)
    require(session.step==0,'Fresh run only; no automatic resume')
    if identity['purpose']=='qualified-expanded-executor':require(model_digest(session.model)==INITIAL_WEIGHTS_SHA,'Not the frozen scratch initialization')
    started=clock();history=[];refs=[];trajectory=[]
    def check():guard();require(clock()-started<plan['total_seconds'],'Total budget reached')
    def save():
        files=checkpoint(session,cache,identity,history);files.update({'plan.json':canonical(plan),'approval.json':canonical(approval)})
        ref=publish(store,identity,'checkpoint:'+str(session.step),files,lambda f:validate_checkpoint(f,identity));refs.append(ref);event(dict(state='checkpoint_complete',step=session.step,reference=ref))
    try:
        check();save();before,_=evaluate(session,cache,identity,store,guard=check);trajectory.append(dict(step=0,metrics=before));event(dict(state='evaluation_complete',**trajectory[-1]));update_start=clock();event(dict(state='update_phase_started'))
        while session.step<session.config['max_steps']:
            check();require(clock()-update_start<plan['update_seconds'],'Update budget reached')
            index=session.step%len(cache.members('optimizer'));sid=scheduled_member(cache.inputs,session.step);item=cache.get('optimizer',index)
            row=session._step(item['image'],item['label'],sid) if isinstance(session,MPSRun) else session.update(item['image'],item['label'],sid)
            history.append(row);event(dict(state='update_complete',**row));check();require(clock()-update_start<plan['update_seconds'],'Update budget reached')
            if session.step in plan['checkpoint_steps']:save()
            if session.step in plan['evaluation_steps'] and session.step<session.config['max_steps']:
                mid,_=evaluate(session,cache,identity,store,guard=check);trajectory.append(dict(step=session.step,metrics=mid));event(dict(state='evaluation_complete',**trajectory[-1]))
        event(dict(state='update_phase_complete',completed_step=session.step))
        final,exports=evaluate(session,cache,identity,store,export=True,guard=check);trajectory.append(dict(step=session.step,metrics=final));event(dict(state='evaluation_complete',**trajectory[-1]))
        result=dict(state='complete',completed_steps=session.step,checkpoints=refs,exports=exports,elapsed_seconds=clock()-started)
        stream=BytesIO();torch.save(session.predict(torch.full((1,*session.config['patch_size']),.25)),stream)
        files={'result.json':canonical(result),'trajectory.json':canonical(trajectory),'probe.pt':stream.getvalue()};check()
        terminal=publish(store,identity,'terminal',files,lambda f:validate_terminal(f,identity,store));event(dict(state='terminal_complete',reference=terminal));return result,terminal
    except BaseException as exc:
        event(dict(state='failed_or_interrupted',completed_steps=session.step,error_type=type(exc).__name__,message=str(exc),last_complete_checkpoint=refs[-1] if refs else None));raise
