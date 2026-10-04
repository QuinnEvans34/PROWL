"""New child experiment with an immutable parent and absolute sampler ancestry."""
from copy import deepcopy
from io import BytesIO
import hashlib,json,math
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training import twomm_training as original
from src.training.twomm_training import REAL_BINDING,REAL_CACHE,SHUFFLE,PREDICTION,schedule
from src.training.twomm_adapter import validate_config,patch_batch
from src.training.twomm_session import initialize_model,load_model_state,Session as Readiness,weight_digest,POLICY
from src.training.twomm_cache import DiskRoleCache,checked_binding
from src.training.localizer import configured_loss
from src.training.localizer_checkpoint import finite_tree
from src.training.localizer_run import cpu_tree
from src.training.twomm_coverage_guard import validate_policy,REAL_POLICY
from src.training.twomm_prefix_parity import validate_reference

CONTROLS=dict(original.CONTROLS,**{'parent-reference.json':'parent_reference_sha256'})
REAL_PARENT='969d86b898e90ff8c5afc340c336588f5f757615409feb12bf8f975948f4d5cc'
COVERAGE=dict(REAL_POLICY,start_step=0)


def tree_digest(value):
    h=hashlib.sha256()
    def visit(x):
        if isinstance(x,torch.Tensor):
            h.update(canonical(dict(dtype=str(x.dtype),shape=list(x.shape))))
            h.update(x.detach().cpu().contiguous().numpy().tobytes())
        elif isinstance(x,dict):
            for k in sorted(x,key=str):h.update(canonical(k));visit(x[k])
        elif isinstance(x,(list,tuple)):
            h.update(canonical(len(x)))
            for z in x:visit(z)
        else:h.update(canonical(x))
    visit(value);return h.hexdigest()


def optimizer_digest(opt):
    opt=deepcopy(opt)
    for group in opt['param_groups']:group.pop('lr');group.pop('initial_lr')
    return tree_digest(opt)


def reference(files,identity,checkpoint,prefix_reference):
    parent,rng=original.decode(files,identity)
    return dict(schema_version='twomm-parent-reference-1',step=parent.step,identity=identity,checkpoint=checkpoint,
        weight_sha256=weight_digest(parent),optimizer_sha256=optimizer_digest(parent.optimizer.state_dict()),
        cpu_rng_sha256=tree_digest(rng),files={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()},prefix_reference=prefix_reference)


def validate_controls(i,c):
    require(set(i)=={'schema_version','run_id','purpose','device','config','sampling_policy','shuffle_policy',
        'prediction_policy','cache_receipt_sha256',*CONTROLS.values()} and i['schema_version']=='twomm-training-4' and
        i['purpose'] in ('synthetic-training-transaction','qualified-twomm-training') and i['device'] in ('cpu','mps'),'Wrong parented identity')
    require(isinstance(i['run_id'],str) and i['run_id'].startswith('twomm-training-') and len(i['run_id'])<=100 and
        all(z.isalnum() or z=='-' for z in i['run_id']),'Wrong child run ID')
    require(set(c)==set(CONTROLS) and all(digest(c[n])==i[k] for n,k in CONTROLS.items()),'Child control inventory/pins differ')
    for k,v in i.items():
        if k.endswith('_sha256'):require(isinstance(v,str) and len(v)==64 and all(z in '0123456789abcdef' for z in v),'Invalid child pin')
    require((i['sampling_policy'],i['shuffle_policy'],i['prediction_policy'])==(POLICY,SHUFFLE,PREDICTION),'Child policies differ')
    cfg=i['config'];validate_config(cfg);require(cfg['schema_version']=='twomm-adapter-4','Wrong child adapter')
    b=json.loads(c['inputs.json']);checked_binding(b,i['inputs_sha256'])
    p=json.loads(c['plan.json']);r=json.loads(c['parent-reference.json']);a=json.loads(c['authorization.json'])
    require(set(r)=={'schema_version','step','identity','checkpoint','weight_sha256','optimizer_sha256','cpu_rng_sha256','files','prefix_reference'} and
        r['schema_version']=='twomm-parent-reference-1' and type(r['step']) is int and r['step']==cfg['parent_steps'],'Parent reference differs')
    original.validate_identity(r['identity'])
    require(r['identity']['inputs_sha256']==i['inputs_sha256'] and r['identity']['cache_receipt_sha256']==i['cache_receipt_sha256'] and
        r['identity']['config']['seed']==cfg['seed'] and r['identity']['config']['weight_decay']==cfg['weight_decay'] and
        r['identity']['config']['loss_id']==cfg['loss_id'] and r['step']==r['identity']['config']['max_steps'],'Parent inputs/recipe/terminal differ')
    require(set(r['files'])==set(original.CONTROLS)|{'identity.json','progress.json','state.pt'},'Parent file inventory differs')
    require(set(p)=={'schema_version','config','checkpoint_steps','evaluations','total_seconds','output_bytes','reference_policy','coverage_guard','execution_mode'} and
        p['schema_version']=='twomm-training-plan-4' and p['config']==cfg and p['execution_mode'] in ('zero_update_parent_check','tail_training') and
        p['reference_policy'] in ('fresh_native_references_each_stage_v1','fresh_native_references_volume_rebound_v2'),'Wrong child plan')
    steps=p['checkpoint_steps'];n=cfg['max_steps'];zero=p['execution_mode']=='zero_update_parent_check'
    require(isinstance(steps,list) and all(type(s) is int for s in steps) and steps==sorted(set(steps)) and steps[0]==0 and
        (steps==[0] if zero else steps[-1]==n and all(0<=s<=n for s in steps)),'Wrong child cadence')
    require([e['step'] for e in p['evaluations']]==steps,'Child evaluation cadence differs')
    for e in p['evaluations']:
        require(set(e)=={'step','roles'} and e['roles']==(['optimizer','evaluator'] if not zero and e['step']==n else ['evaluator']),'Child evaluation roles differ')
    validate_policy(p['coverage_guard']);require(p['coverage_guard']['start_step']==0,'Parent baseline must be active')
    require(type(p['total_seconds']) is int and 0<p['total_seconds']<=(900 if zero else 2700) and
        type(p['output_bytes']) is int and 0<p['output_bytes']<=4*1024**3,'Child resource envelope differs')
    require(set(a)=={'allowed','operation','authority','request_sha256','identity'} and a['allowed'] is True and
        a['identity']=={k:v for k,v in i.items() if k!='authorization_sha256'},'Missing child authorization')
    real=i['purpose']=='qualified-twomm-training'
    require(a['operation']==(('qualify_CAP-EXP-010_parent' if zero else 'launch_CAP-EXP-010') if real else 'synthetic_training_verification') and
        a['authority']==('Quinton Evans' if real else 'Codex synthetic verification'),'Wrong child authorization scope')
    if real:
        require(i['device']=='mps' and i['inputs_sha256']==REAL_BINDING and i['cache_receipt_sha256']==REAL_CACHE and
            i['parent_reference_sha256']==REAL_PARENT,'Unqualified real child inputs/parent')
        validate_reference(r['prefix_reference'],b)
        require(cfg==dict(schema_version='twomm-adapter-4',patch_size=[144]*3,seed=42,learning_rate=.00001,
            weight_decay=.00001,max_steps=300,loss_id='balanced_ce_dice_v1',parent_steps=300),'Real child recipe differs')
        require(steps==([0] if zero else [0,150,300]) and p['coverage_guard']==COVERAGE and
            p['total_seconds']==(900 if zero else 2700) and p['reference_policy']=='fresh_native_references_volume_rebound_v2', 'Real child scope differs')
        require(isinstance(a['request_sha256'],str) and len(a['request_sha256'])==64 and all(z in '0123456789abcdef' for z in a['request_sha256']),'Missing child request pin')
    else:
        require(a['request_sha256'] is None and r['identity']['purpose']=='synthetic-training-transaction','Synthetic parent scope differs')
        for es in b['roles'].values():
            for e in es:
                sid=e['descriptor']['study_id'];require(sid.startswith('synthetic-') or sid.endswith('-synthetic'),'Synthetic requires invented members')
    return b,p,r


class Session:
    predict=Readiness.predict
    def __init__(self,i,c,parent_progress,*,restoring_on_cpu=False):
        self.binding,self.plan,self.parent_reference=validate_controls(i,c)
        require(digest(parent_progress)==self.parent_reference['files']['progress.json']['sha256'],'Parent history changed')
        original.validate_history(json.loads(parent_progress),self.binding,self.parent_reference['identity']['config'],self.parent_reference['step'])
        self.parent_progress=parent_progress;self.identity=deepcopy(i);self.controls=deepcopy(c)
        self._identity_pin=digest(canonical(i));self.history=[];self.poisoned=False;self.imported=False
        initialize_model(self,i,restoring_on_cpu=restoring_on_cpu)
    def verify(self,cache=None):
        require(not self.poisoned and self.imported,'Unimported/interrupted child cannot continue')
        require(digest(canonical(self.identity))==self._identity_pin and self.config==self.identity['config'],'Child identity changed')
        b,p,r=validate_controls(self.identity,self.controls)
        require(b==self.binding and p==self.plan and r==self.parent_reference and self.step==len(self.history) and
            digest(self.parent_progress)==r['files']['progress.json']['sha256'],'Child progress/ancestry changed')
        if self.step==0:
            require(weight_digest(self)==r['weight_sha256'] and optimizer_digest(self.optimizer.state_dict())==r['optimizer_sha256'],'Child import changed model/moments')
        if cache is not None:
            require(type(cache) is DiskRoleCache and digest(canonical(cache._manifest['binding']))==self.identity['inputs_sha256'] and
                digest((cache.path/'complete.json').read_bytes())==self.identity['cache_receipt_sha256'],'Child cache changed')
            for role in ('optimizer','evaluator'):require(cache.members(role)==[e['descriptor']['study_id'] for e in b['roles'][role]],'Child cache roles differ')
    def update(self,cache,*,guard=lambda:None):
        self.verify(cache);require(self.plan['execution_mode']=='tail_training','Zero-update qualification cannot train')
        require(self.step<self.config['max_steps'],'Child update budget exhausted')
        absolute=self.config['parent_steps']+self.step;index,epoch,offset=schedule(self.binding,self.config['seed'],absolute)
        guard();item=cache.get('optimizer',index);x,y,trace=patch_batch(item,self.config,step=absolute);guard()
        try:
            self.model.train();self.optimizer.zero_grad(set_to_none=True);used=self.optimizer.param_groups[0]['lr']
            require(used==self.config['learning_rate'],'Child rate changed')
            loss=configured_loss(self.model(x.to(self.device)),y.to(self.device),self.config)
            require(torch.isfinite(loss).item(),'Nonfinite child loss');loss.backward()
            require(all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in self.model.parameters()),'Invalid child gradients')
            guard();self.optimizer.step();self.scheduler.step();self.step+=1
            require(finite_tree(self.model.state_dict()) and finite_tree(self.optimizer.state_dict()),'Nonfinite child state')
            row=dict(completed_step=self.step,absolute_completed_step=self.config['parent_steps']+self.step,
                member_index=index,pass_index=epoch,pass_offset=offset,loss=loss.item(),sampling=trace,
                learning_rate_used=used,learning_rate_next=self.optimizer.param_groups[0]['lr'])
            self.history.append(row);guard();return deepcopy(row)
        except BaseException:self.poisoned=True;raise


def import_parent(files,i,c):
    _,_,r=validate_controls(i,c)
    require({n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()}==r['files'],'Parent bytes changed')
    parent,rng=original.decode(files,r['identity'])
    require(weight_digest(parent)==r['weight_sha256'] and optimizer_digest(parent.optimizer.state_dict())==r['optimizer_sha256'] and
        tree_digest(rng)==r['cpu_rng_sha256'],'Parent state pins differ')
    s=Session(i,c,files['progress.json']);s.model.load_state_dict(parent.model.state_dict(),strict=True)
    opt=deepcopy(parent.optimizer.state_dict());opt['param_groups'][0]['lr']=s.config['learning_rate'];s.optimizer.load_state_dict(opt)
    s.imported=True;torch.set_rng_state(rng);s.verify();return s


def validate_history(h,b,cfg,step):
    require(isinstance(h,list) and len(h)==step,'Child history length differs')
    for j,row in enumerate(h):
        absolute=cfg['parent_steps']+j;index,epoch,offset=schedule(b,cfg['seed'],absolute)
        fields={'completed_step','absolute_completed_step','member_index','pass_index','pass_offset','loss','sampling','learning_rate_used','learning_rate_next'}
        require(set(row)==fields and all(type(row[k]) is int for k in ('completed_step','absolute_completed_step','member_index','pass_index','pass_offset')) and
            (row['completed_step'],row['absolute_completed_step'],row['member_index'],row['pass_index'],row['pass_offset'])==(j+1,absolute+1,index,epoch,offset),'Child absolute sampler history differs')
        require(type(row['loss']) in (int,float) and math.isfinite(row['loss']) and row['loss']>=0 and
            all(type(row[k]) in (int,float) and row[k]==cfg['learning_rate'] for k in ('learning_rate_used','learning_rate_next')),'Child loss/rate invalid')
        t=row['sampling'];e=b['roles']['optimizer'][index];shape=e['transform_record']['processed_shape'];pads=[max(0,144-n) for n in shape]
        require(set(t)=={'member_id','step','policy','center_original_grid','center_class','origin_padded_grid','padding'} and
            type(t['step']) is int and t['step']==absolute and t['member_id']==e['descriptor']['study_id'] and t['policy']==POLICY,'Child crop binding differs')
        require(t['padding']==dict(schema_version='twomm-padding-1',original_shape=shape,padding=[v for n in reversed(pads) for v in (n//2,n-n//2)],
            padded_shape=[s+n for s,n in zip(shape,pads)]),'Child padding differs')
        center=t['center_original_grid'];origin=t['origin_padded_grid']
        require(len(center)==3 and all(type(z) is int and 0<=z<n for z,n in zip(center,shape)) and type(t['center_class']) is int and
            t['center_class'] in (0,1) and origin==[max(0,min(z+n//2-72,s+n-144)) for z,n,s in zip(center,pads,shape)],'Child crop trace invalid')


def payload(s):
    s.verify();state=cpu_tree(dict(schema_version='twomm-parented-state-1',identity_sha256=s._identity_pin,step=s.step,
        absolute_step=s.config['parent_steps']+s.step,model=s.model.state_dict(),optimizer=s.optimizer.state_dict(),scheduler=s.scheduler.state_dict(),cpu_rng=torch.get_rng_state()))
    stream=BytesIO();torch.save(state,stream)
    files=dict(s.controls,**{'identity.json':canonical(s.identity),'progress.json':canonical(s.history),'state.pt':stream.getvalue(),'parent-progress.json':s.parent_progress})
    validate_payload(files,s.identity);return files


def decode(files,i):
    require(set(files)==set(CONTROLS)|{'identity.json','progress.json','state.pt','parent-progress.json'} and files['identity.json']==canonical(i),'Child checkpoint inventory/identity differs')
    c={n:files[n] for n in CONTROLS};b,_,r=validate_controls(i,c)
    state=torch.load(BytesIO(files['state.pt']),map_location='cpu',weights_only=True)
    require(set(state)=={'schema_version','identity_sha256','step','absolute_step','model','optimizer','scheduler','cpu_rng'} and
        state['schema_version']=='twomm-parented-state-1' and state['identity_sha256']==digest(canonical(i)),'Child state identity differs')
    step=state['step'];require(type(step) is int and 0<=step<=i['config']['max_steps'] and type(state['absolute_step']) is int and
        state['absolute_step']==r['step']+step and finite_tree(state),'Invalid child step/state')
    rng=state['cpu_rng'];require(isinstance(rng,torch.Tensor) and rng.dtype==torch.uint8 and rng.shape==torch.get_rng_state().shape,'Invalid child RNG')
    if step==0:require(tree_digest(rng)==r['cpu_rng_sha256'],'Imported RNG changed')
    h=json.loads(files['progress.json']);validate_history(h,b,i['config'],step)
    s=Session(i,c,files['parent-progress.json'],restoring_on_cpu=True);load_model_state(s,state,i['config'],step)
    s.history=h;s.imported=True;s.verify();return s,rng


def validate_payload(files,i):
    s,_=decode(files,i);return dict(step=s.step,absolute_step=s.config['parent_steps']+s.step,identity_sha256=s._identity_pin,
        progress_sha256=digest(files['progress.json']),parent_reference_sha256=i['parent_reference_sha256'])


def restore_payload(files,i):
    s,rng=decode(files,i)
    if i['device']=='cpu':torch.set_rng_state(rng);return s
    out=Session(i,s.controls,s.parent_progress);out.model.load_state_dict(s.model.state_dict());out.optimizer.load_state_dict(s.optimizer.state_dict());out.scheduler.load_state_dict(s.scheduler.state_dict())
    out.step=s.step;out.history=s.history;out.imported=True;torch.set_rng_state(rng);out.verify();return out


def publish_checkpoint(store,files,i):
    checked=validate_payload(files,i);step=checked['step'];aid=f"{i['run_id']}:step:{step}"
    derivation=digest(canonical(dict(identity=i,step=step)))
    metadata=dict(artifact_type='localizer-checkpoint',schema_version=i['schema_version'],component='twomm-parented-training',
        code_sha256=i['source_sha256'],parents=[i['inputs_sha256'],i['plan_sha256'],i['parent_reference_sha256']],retention='research-keeper',sensitivity='private-research',run_id=i['run_id'],stage_id='checkpoint')
    pin,status=store.publish(aid,derivation_sha256=derivation,files=files,metadata=metadata,validate=lambda f:validate_payload(f,i))
    return dict(artifact_id=aid,receipt_sha256=pin,derivation_sha256=derivation,step=step,status=status)
