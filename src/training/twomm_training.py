"""Bounded 144³ training session and strict, versioned progress checkpoints.

This is a separate interface from readiness sessions. Launchers must pin an approved
identity, claim an attempt once, and enforce external resource limits.
"""
from copy import deepcopy
from io import BytesIO
import json
import math
import torch
from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require
from src.training.twomm_adapter import validate_config, patch_batch
from src.training.twomm_cache import DiskRoleCache, checked_binding
from src.training.twomm_session import (initialize_model, load_model_state, Session as Readiness,
    weight_digest, POLICY)
from src.training.localizer import configured_loss
from src.training.localizer_checkpoint import finite_tree
from src.training.localizer_run import cpu_tree

CONTROLS = {'inputs.json':'inputs_sha256', 'source.json':'source_sha256',
    'environment.json':'environment_sha256', 'plan.json':'plan_sha256',
    'authorization.json':'authorization_sha256'}
REAL_BINDING = 'ceb18e13622a73596bfa68305859ff71db8ddf9d01054300ef516ed751da759d'
REAL_CACHE = 'b61897ed3176fecd9d8ca143285d9700699c1557537ba15b966a487134342bf7'
SHUFFLE = 'sha256_sorted_member_per_pass_v1'
PREDICTION = 'sliding144_overlap025_constant_softmax_argmax_native_v1'


def schedule(binding, seed, step):
    """Stable across Python versions; each full pass visits every training member once."""
    ids = [e['descriptor']['study_id'] for e in binding['roles']['optimizer']]
    require(type(step) is int and step >= 0 and ids and len(set(ids)) == len(ids), 'Invalid schedule')
    epoch, offset = divmod(step, len(ids))
    ordered = sorted(range(len(ids)), key=lambda i:(digest(canonical([SHUFFLE, seed, epoch, ids[i]])), ids[i]))
    return ordered[offset], epoch, offset


def validate_identity(i):
    require(set(i) == {'schema_version','run_id','purpose','device','config','sampling_policy',
        'shuffle_policy','prediction_policy','cache_receipt_sha256', *CONTROLS.values()}, 'Training identity fields differ')
    require(i['schema_version'] in ('twomm-training-1','twomm-training-2','twomm-training-3') and i['purpose'] in
        ('synthetic-training-transaction','qualified-twomm-training') and i['device'] in ('cpu','mps'), 'Wrong training scope')
    require(isinstance(i['run_id'],str) and i['run_id'].startswith('twomm-training-') and
        len(i['run_id'])<=100 and all(c.isalnum() or c=='-' for c in i['run_id']), 'Invalid run ID')
    require(i['sampling_policy']==POLICY and i['shuffle_policy']==SHUFFLE and
        i['prediction_policy']==PREDICTION, 'Training policy differs')
    for k,v in i.items():
        if k.endswith('_sha256'):
            require(isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v), 'Invalid identity pin')
    validate_config(i['config'])
    require(i['config']['schema_version']=='twomm-adapter-'+i['schema_version'][-1], 'Training/adapter version mismatch')
    if i['purpose']=='qualified-twomm-training':
        require(i['inputs_sha256']==REAL_BINDING and i['cache_receipt_sha256']==REAL_CACHE and
            i['device']=='mps', 'Unqualified real training inputs/device')


def validate_controls(i, controls):
    validate_identity(i)
    require(set(controls)==set(CONTROLS), 'Training controls inventory differs')
    for name,key in CONTROLS.items():
        require(digest(controls[name])==i[key], 'Training control pin differs')
    b=json.loads(controls['inputs.json']);checked_binding(b,i['inputs_sha256'])
    p=json.loads(controls['plan.json']);a=json.loads(controls['authorization.json'])
    tail=i['schema_version']=='twomm-training-3';extended=i['schema_version']!='twomm-training-1'
    require(set(p)=={'schema_version','config','checkpoint_steps','evaluations','total_seconds',
        'output_bytes','reference_policy'}|({'coverage_guard'} if extended else set())|({'prefix_reference'} if tail else set()), 'Plan fields differ')
    require(p['schema_version']=='twomm-training-plan-'+i['schema_version'][-1] and p['config']==i['config'] and
        p['reference_policy'] in (('fresh_native_references_each_stage_v1','fresh_native_references_volume_rebound_v2')
            if extended else ('fresh_native_references_each_stage_v1',)), 'Plan recipe differs')
    n=i['config']['max_steps'];steps=p['checkpoint_steps']
    require(isinstance(steps,list) and steps==sorted(set(steps)) and steps[0]==0 and steps[-1]==n and
        all(type(s) is int and 0<=s<=n for s in steps), 'Invalid checkpoint cadence')
    evals=p['evaluations'];require(isinstance(evals,list) and len(evals)>=2, 'Missing evaluation cadence')
    require([e['step'] for e in evals]==steps, 'Evaluation/checkpoint cadence differs')
    for e in evals:
        require(set(e)=={'step','roles'} and type(e['step']) is int and
            e['roles']==(['optimizer','evaluator'] if e['step'] in (0,n) else ['evaluator']), 'Wrong evaluation roles')
    require(type(p['total_seconds']) is int and 0<p['total_seconds']<=(3600 if tail else 5400 if extended else 2700) and
        type(p['output_bytes']) is int and 0<p['output_bytes']<=4*1024**3, 'Plan resource envelope differs')
    require(set(a)=={'allowed','operation','authority','identity','request_sha256'} and a['allowed'] is True and
        a['identity']=={k:v for k,v in i.items() if k!='authorization_sha256'}, 'Missing/mismatched authorization')
    real=i['purpose']=='qualified-twomm-training'
    require(a['operation']==(('launch_CAP-EXP-009' if tail else 'launch_CAP-EXP-008' if extended else 'launch_CAP-EXP-007') if real else 'synthetic_training_verification') and
        a['authority']==('Quinton Evans' if real else 'Codex synthetic verification'), 'Wrong authorization authority/scope')
    if real:
        require(isinstance(a['request_sha256'],str) and len(a['request_sha256'])==64 and
            all(c in '0123456789abcdef' for c in a['request_sha256']), 'Missing exact launch request binding')
        require(n==(600 if tail else 1200 if extended else 300) and steps==([0,300,450,600] if tail else [0,300,600,900,1200] if extended else [0,113,226,300]) and i['config']['seed']==42 and
            i['config']['learning_rate']==.0003 and i['config']['weight_decay']==.00001 and
            {r:len(v) for r,v in b['roles'].items()}=={'optimizer':113,'evaluator':40}, 'Real run differs from proposed scope')
    else:
        require(a['request_sha256'] is None, 'Synthetic cannot claim real request approval')
        for entries in b['roles'].values():
            for entry in entries:
                d=entry['descriptor'];sid=d['study_id']
                require(set(d)=={'study_id','operation','protected_role','observations'} and
                    (sid.startswith('synthetic-') or sid.endswith('-synthetic')), 'Synthetic identity requires invented descriptors')
    if extended:
        from src.training.twomm_coverage_guard import validate_policy, REAL_POLICY
        validate_policy(p['coverage_guard'])
        if real:
            require(p['coverage_guard']==REAL_POLICY and p['total_seconds']==(3600 if tail else 5400) and p['output_bytes']==4*1024**3,
                'Extended coverage/resource policy differs')
    if tail:
        from src.training.twomm_tail_schedule import REAL_SCHEDULE
        require(i['config']['schedule']['prefix_steps'] in steps and p['coverage_guard']['start_step']>=i['config']['schedule']['prefix_steps'], 'Missing prefix checkpoint/early coverage stop')
        if real:
            from src.training.twomm_prefix_parity import validate_reference
            require(i['config']['schedule']==REAL_SCHEDULE,'Real tail schedule differs')
            validate_reference(p['prefix_reference'],b)
        else:
            require(p['prefix_reference']==dict(scope='invented_prefix',step=i['config']['schedule']['prefix_steps']),
                'Synthetic prefix cannot claim real reference')
    return b,p


class Session:
    predict = Readiness.predict

    def __init__(self, identity, controls, *, restoring_on_cpu=False):
        self.binding,self.plan=validate_controls(identity,controls)
        self.identity=deepcopy(identity);self.controls=deepcopy(controls)
        self._identity_pin=digest(canonical(identity));self.history=[];self.poisoned=False
        initialize_model(self, identity, restoring_on_cpu=restoring_on_cpu)

    def verify(self, cache=None):
        require(not self.poisoned, 'Interrupted/uncertain session cannot continue')
        require(digest(canonical(self.identity))==self._identity_pin and self.config==self.identity['config'], 'Session identity changed')
        b,p=validate_controls(self.identity,self.controls)
        require(b==self.binding and p==self.plan and self.step==len(self.history), 'Session progress/controls changed')
        if cache is not None:
            require(type(cache) is DiskRoleCache, 'Verified persisted cache required')
            for role in ('optimizer','evaluator'):
                require(cache.members(role)==[e['descriptor']['study_id'] for e in b['roles'][role]], 'Cache role membership differs')
            require(digest(canonical(cache._manifest['binding']))==self.identity['inputs_sha256'] and
                digest((cache.path/'complete.json').read_bytes())==self.identity['cache_receipt_sha256'], 'Cache binding/completion differs')

    def update(self, cache, *, guard=lambda:None):
        self.verify(cache);require(self.step<self.config['max_steps'], 'Update budget exhausted')
        index,epoch,offset=schedule(self.binding,self.config['seed'],self.step)
        guard();item=cache.get('optimizer',index)
        x,y,trace=patch_batch(item,self.config,step=self.step);guard()
        try:
            self.model.train();self.optimizer.zero_grad(set_to_none=True)
            used=self.optimizer.param_groups[0]['lr']
            loss=configured_loss(self.model(x.to(self.device)),y.to(self.device),self.config)
            require(torch.isfinite(loss).item(), 'Nonfinite loss');loss.backward()
            require(all(p.grad is not None and torch.isfinite(p.grad).all().item()
                for p in self.model.parameters()), 'Invalid gradients')
            guard();self.optimizer.step();self.scheduler.step();self.step+=1
            require(finite_tree(self.model.state_dict()) and finite_tree(self.optimizer.state_dict()), 'Nonfinite updated state')
            row=dict(completed_step=self.step,member_index=index,pass_index=epoch,pass_offset=offset,
                loss=loss.item(),sampling=trace)
            if self.identity['schema_version']=='twomm-training-3':
                row.update(learning_rate_used=used,learning_rate_next=self.optimizer.param_groups[0]['lr'])
            else:row['learning_rate']=self.optimizer.param_groups[0]['lr']
            self.history.append(row);guard();return deepcopy(row)
        except BaseException:
            self.poisoned=True
            raise


def validate_history(history,binding,config,step):
    require(isinstance(history,list) and len(history)==step, 'Checkpoint history length differs')
    tail=config['schema_version']=='twomm-adapter-3'
    for j,row in enumerate(history):
        index,epoch,offset=schedule(binding,config['seed'],j)
        require(set(row)=={'completed_step','member_index','pass_index','pass_offset','loss','sampling'}|
            ({'learning_rate_used','learning_rate_next'} if tail else {'learning_rate'}) and
            all(type(row[k]) is int for k in ('completed_step','member_index','pass_index','pass_offset')) and
            (row['completed_step'],row['member_index'],row['pass_index'],row['pass_offset'])==(j+1,index,epoch,offset), 'History schedule differs')
        require(type(row['loss']) in (float,int) and math.isfinite(row['loss']) and row['loss']>=0,'Invalid history loss')
        if tail:
            from src.training.twomm_tail_schedule import next_rate
            for name,k in (('learning_rate_used',j),('learning_rate_next',j+1)):
                require(type(row[name]) in (float,int) and math.isfinite(row[name]) and
                    abs(row[name]-next_rate(config,k))<1e-12,'Invalid tail history rate')
        else:
            require(type(row['learning_rate']) in (float,int) and math.isfinite(row['learning_rate']) and
                abs(row['learning_rate']-config['learning_rate']*(1+math.cos(math.pi*(j+1)/config['max_steps']))/2)<1e-12, 'Invalid history rate')
        t=row['sampling'];entry=binding['roles']['optimizer'][index]
        require(set(t)=={'member_id','step','policy','center_original_grid','center_class','origin_padded_grid','padding'} and
            type(t['step']) is int and t['member_id']==entry['descriptor']['study_id'] and t['step']==j and t['policy']==POLICY and
            t['padding']['original_shape']==entry['transform_record']['processed_shape'], 'History crop binding differs')
        shape=t['padding']['original_shape'];pads=[max(0,144-n) for n in shape]
        require(t['padding']==dict(schema_version='twomm-padding-1', original_shape=shape,
            padding=[v for n in reversed(pads) for v in (n//2,n-n//2)],padded_shape=[s+n for s,n in zip(shape,pads)]), 'History padding differs')
        center=t['center_original_grid'];origin=t['origin_padded_grid']
        require(len(center)==3 and all(type(c) is int and 0<=c<s for c,s in zip(center,shape)) and
            type(t['center_class']) is int and t['center_class'] in (0,1) and
            origin==[max(0,min(c+n//2-72,s+n-144)) for c,n,s in zip(center,pads,shape)], 'Invalid crop trace')


def payload(session):
    session.verify()
    state=cpu_tree(dict(schema_version='twomm-training-state-1',identity_sha256=session._identity_pin,
        step=session.step,model=session.model.state_dict(),optimizer=session.optimizer.state_dict(),
        scheduler=session.scheduler.state_dict(),cpu_rng=torch.get_rng_state()))
    stream=BytesIO();torch.save(state,stream)
    files=dict(session.controls,**{'identity.json':canonical(session.identity),
        'progress.json':canonical(session.history),'state.pt':stream.getvalue()})
    validate_payload(files,session.identity);return files


def decode(files,identity):
    require(set(files)==set(CONTROLS)|{'identity.json','progress.json','state.pt'}, 'Checkpoint inventory differs')
    require(files['identity.json']==canonical(identity), 'Checkpoint identity differs')
    controls={n:files[n] for n in CONTROLS};b,_=validate_controls(identity,controls)
    state=torch.load(BytesIO(files['state.pt']),map_location='cpu',weights_only=True)
    require(set(state)=={'schema_version','identity_sha256','step','model','optimizer','scheduler','cpu_rng'} and
        state['schema_version']=='twomm-training-state-1' and state['identity_sha256']==digest(canonical(identity)), 'Wrong checkpoint state')
    step=state['step'];require(type(step) is int and 0<=step<=identity['config']['max_steps'], 'Invalid checkpoint step')
    require(finite_tree(state), 'Nonfinite checkpoint')
    rng=state['cpu_rng'];require(isinstance(rng,torch.Tensor) and rng.dtype==torch.uint8 and
        rng.shape==torch.get_rng_state().shape, 'Invalid RNG')
    history=json.loads(files['progress.json']);validate_history(history,b,identity['config'],step)
    restored=Session(identity,controls,restoring_on_cpu=True)
    load_model_state(restored,state,identity['config'],step);restored.history=history
    return restored,rng


def validate_payload(files,identity):
    s,_=decode(files,identity)
    return dict(step=s.step,identity_sha256=s._identity_pin,progress_sha256=digest(files['progress.json']))


def restore_payload(files,identity):
    base,rng=decode(files,identity)
    if identity['device']=='cpu':torch.set_rng_state(rng);return base
    s=Session(identity,base.controls);s.model.load_state_dict(base.model.state_dict())
    s.optimizer.load_state_dict(base.optimizer.state_dict());s.scheduler.load_state_dict(base.scheduler.state_dict())
    s.step=base.step;s.history=base.history;torch.set_rng_state(rng);return s


def publish_checkpoint(store,files,identity):
    check=validate_payload(files,identity);step=check['step']
    artifact_id=f"{identity['run_id']}:step:{step}";derivation=digest(canonical(dict(identity=identity,step=step)))
    metadata=dict(artifact_type='localizer-checkpoint',schema_version=identity['schema_version'],component='twomm-training',
        code_sha256=identity['source_sha256'],parents=[identity['inputs_sha256'],identity['plan_sha256']],
        retention='research-keeper',sensitivity='private-research',run_id=identity['run_id'],stage_id='checkpoint')
    pin,status=store.publish(artifact_id,derivation_sha256=derivation,files=files,metadata=metadata,
        validate=lambda f:validate_payload(f,identity))
    return dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation,step=step,status=status)
