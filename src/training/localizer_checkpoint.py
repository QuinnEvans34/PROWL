"""Identity-bound synthetic localizer checkpoints on the shared artifact store.

Caller supplies an authorized store and independent identity/receipt pins. No production
root activation, untrusted pickle execution, auto-discovery or optimizer fallback.
"""
from io import BytesIO
import math
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training.localizer import LocalizerSession,validate_config


def validate_identity(identity):
    require(set(identity)=={'schema_version','run_id','run_class','data_mode','config','code_sha256',
        'environment_sha256','cohort_sha256','preprocessing_sha256','device','precision','workers','cache'}, 'Incomplete run identity')
    require(identity['schema_version']=='1.0.0' and identity['run_class']=='diagnostic' and
        identity['data_mode']=='synthetic' and identity['device']=='cpu' and identity['precision']=='float32'
        and identity['workers']==0 and identity['cache']=='none', 'Unsupported execution identity')
    require(isinstance(identity['run_id'],str) and identity['run_id'].startswith('localizer-synthetic-') and
            len(identity['run_id'])<=100,'Invalid run ID')
    for k in ('code_sha256','environment_sha256','cohort_sha256','preprocessing_sha256'):
        require(isinstance(identity[k],str) and len(identity[k])==64 and all(c in '0123456789abcdef' for c in identity[k]), 'Invalid identity digest')
    validate_config(identity['config'])


def finite_tree(value):
    if isinstance(value,torch.Tensor):return bool(torch.isfinite(value).all())
    if isinstance(value,dict):return all(finite_tree(v) for v in value.values())
    if isinstance(value,(tuple,list)):return all(finite_tree(v) for v in value)
    if isinstance(value,float):return bool(torch.isfinite(torch.tensor(value)))
    return True


def decode(files,identity):
    validate_identity(identity)
    require(set(files)=={'identity.json','state.pt'},'Unexpected checkpoint members')
    require(files['identity.json']==canonical(identity),'Checkpoint run/input/config identity mismatch')
    state=torch.load(BytesIO(files['state.pt']),map_location='cpu',weights_only=True)
    return decode_state(state,identity)


def decode_state(state,identity):
    """Validate shared tensor state after the caller has verified its own typed identity."""
    require(set(state)=={'schema_version','identity_sha256','step','model','optimizer','scheduler','cpu_rng'},'Incomplete checkpoint state')
    require(state['schema_version']=='1.0.0' and state['identity_sha256']==digest(canonical(identity)), 'State identity mismatch')
    step=state['step'];require(type(step)==int and 0<=step<=identity['config']['max_steps'],'Invalid completed step')
    require(finite_tree(state),'Nonfinite checkpoint state')
    require(state['scheduler']['last_epoch']==step and state['scheduler']['T_max']==identity['config']['max_steps'] and
            state['scheduler']['eta_min']==0 and state['scheduler']['_step_count']==step+1 and
            state['scheduler']['base_lrs']==[identity['config']['learning_rate']],'Scheduler position/config mismatch')
    rng=state['cpu_rng'];require(isinstance(rng,torch.Tensor) and rng.dtype==torch.uint8 and rng.shape==torch.get_rng_state().shape,'Invalid CPU RNG state')
    # Validate into a new session. A failed reload cannot partially mutate the caller's model.
    restored=LocalizerSession(identity['config'])
    restored.model.load_state_dict(state['model'],strict=True)
    restored.optimizer.load_state_dict(state['optimizer'])
    restored.scheduler.load_state_dict(state['scheduler'])
    groups=restored.optimizer.param_groups
    require(len(groups)==1 and len(groups[0]['params'])==len(list(restored.model.parameters())), 'Optimizer parameter inventory mismatch')
    group=groups[0];expected_lr=identity['config']['learning_rate']*(1+math.cos(math.pi*step/identity['config']['max_steps']))/2
    require(abs(group['lr']-expected_lr)<1e-12 and group['weight_decay']==identity['config']['weight_decay'] and
            group['betas']==(.9,.999) and group['eps']==1e-8 and not group['amsgrad'] and
            restored.scheduler.get_last_lr()==[group['lr']], 'Optimizer policy mismatch')
    for p in restored.model.parameters():
        entry=restored.optimizer.state.get(p,{})
        if step==0:require(not entry,'Unexpected optimizer history at step zero')
        else:
            require(set(entry)=={'step','exp_avg','exp_avg_sq'} and entry['step'].item()==step and
                    entry['exp_avg'].shape==p.shape and entry['exp_avg_sq'].shape==p.shape,'Missing or inconsistent optimizer history')
    restored.step=step
    return restored,rng


def checkpoint_id(identity,step):
    return f"{identity['run_id']}:checkpoint:{step}"


def save(store,session,identity):
    validate_identity(identity);require(identity['config']==session.config,'Session configuration differs')
    state=dict(schema_version='1.0.0',identity_sha256=digest(canonical(identity)),step=session.step,
        model=session.model.state_dict(),optimizer=session.optimizer.state_dict(),scheduler=session.scheduler.state_dict(),
        cpu_rng=torch.get_rng_state())
    stream=BytesIO();torch.save(state,stream)
    files={'identity.json':canonical(identity),'state.pt':stream.getvalue()}
    artifact_id=checkpoint_id(identity,session.step)
    metadata=dict(artifact_type='localizer-checkpoint',schema_version='1.0.0',component='localizer-cpu-v1',
        code_sha256=identity['code_sha256'],parents=[identity['cohort_sha256'],identity['preprocessing_sha256']],
        retention='diagnostic',sensitivity='synthetic',run_id=identity['run_id'],stage_id='checkpoint')
    def validate(payload):
        restored,_=decode(payload,identity)
        return dict(step=restored.step,identity_sha256=digest(canonical(identity)))
    pin,status=store.publish(artifact_id,derivation_sha256=digest(canonical(dict(identity=identity,step=session.step))),
                            files=files,metadata=metadata,validate=validate)
    return dict(artifact_id=artifact_id,receipt_sha256=pin,state=status,completed_step=session.step)


def resume(store,reference,identity):
    validate_identity(identity)
    require(reference['artifact_id']==checkpoint_id(identity,reference['completed_step']),'Wrong requested checkpoint identity')
    def validate(payload):
        restored,_=decode(payload,identity)
        require(restored.step==reference['completed_step'],'Requested step mismatch')
        return dict(step=restored.step,identity_sha256=digest(canonical(identity)))
    files,_=store.resolve(reference['artifact_id'],receipt_sha256=reference['receipt_sha256'],validate=validate,
        expected_derivation=digest(canonical(dict(identity=identity,step=reference['completed_step']))))
    restored,rng=decode(files,identity);torch.set_rng_state(rng)
    return restored
