"""Qualified-input MPS bridge and checkpoint codec; launch remains an explicit gate."""
from copy import deepcopy
from io import BytesIO
import json
import math
import os
import torch
from monai.inferers import sliding_window_inference
from src.data.cohort_registry import COHORT_ID,MEMBERS
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training.localizer import LocalizerSession,patch_batch,configured_loss,image_tensor,validate_config
from src.training.localizer_checkpoint import decode_state


def validate_identity(identity):
    base={'schema_version','run_id','purpose','training_data','device','config','inputs_sha256','source_sha256','environment_sha256'}
    if identity.get('schema_version')=='2.0.0':
        require(set(identity)==base,'Incomplete run identity')
        require(identity['purpose']=='prelaunch-verification' and identity['training_data']=='synthetic' and
                identity['device']=='mps' and identity['run_id'].startswith('localizer-bridge-'),'Unapproved execution scope')
    else:
        require(set(identity)==base|{'plan_sha256','authorization_sha256'} and identity['schema_version'] in ('3.0.0','4.0.0'),'Incomplete smoke identity')
        require(identity['purpose']=='bounded-localizer-smoke' and identity['training_data'] in ('synthetic','qualified_cohort') and
                identity['device'] in ('cpu','mps') and identity['run_id'].startswith('localizer-smoke-'),'Wrong smoke scope')
        if identity['training_data']=='qualified_cohort':require(identity['device']=='mps','Real smoke requires MPS')
    for field in (k for k in identity if k.endswith('_sha256')):
        require(isinstance(identity[field],str) and len(identity[field])==64 and all(c in '0123456789abcdef' for c in identity[field]),'Invalid run pin')
    validate_config(identity['config'])
    if identity['schema_version']=='4.0.0':require(identity['config'].get('loss_id')=='balanced_ce_dice_v1','Version4 requires explicit balanced objective')
    else:require('loss_id' not in identity['config'],'Legacy identity cannot change objective')


def input_record(dataset):
    require([d['study_id'] for d in dataset.descriptors]==MEMBERS and all(d['cohort_id']==COHORT_ID for d in dataset.descriptors),'Wrong frozen cohort')
    return dict(cohort_id=COHORT_ID,members=deepcopy(dataset.descriptors),recipe=deepcopy(dataset.recipe))


def bind_item(dataset,index,identity):
    validate_identity(identity)
    require(digest(canonical(input_record(dataset)))==identity['inputs_sha256'],'Dataset changed from frozen run inputs')
    result=dataset[index]
    expected=dataset.descriptors[index]
    require(all(result['provenance'][k]==v for k,v in expected.items()),'Loaded provenance differs')
    require(result['transform_record']['recipe']==dataset.recipe,'Loaded transform recipe differs')
    return result


class MPSRun(LocalizerSession):
    def __init__(self,config,*,restored=None):
        require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and torch.backends.mps.is_available(),'Native MPS with fallback disabled required')
        base=restored if restored is not None else LocalizerSession(config)
        require(base.config==config,'Restored config mismatch')
        self.config=deepcopy(config);self.step=base.step;self.model=base.model.to('mps')
        self.optimizer=torch.optim.AdamW(self.model.parameters(),lr=config['learning_rate'],weight_decay=config['weight_decay'])
        self.scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(self.optimizer,T_max=config['max_steps'])
        self.optimizer.load_state_dict(base.optimizer.state_dict());self.scheduler.load_state_dict(base.scheduler.state_dict())

    def update(self,image,target,member_id):
        raise ValueError('Real optimizer updates require a separately approved launch; use synthetic_update for verification')

    def synthetic_update(self,image,target):
        return self._step(image,target,'synthetic-recovery-fixture')

    def _step(self,image,target,member_id):
        x,y,trace=patch_batch(image,target,self.config,step=self.step,member_id=member_id)
        self.model.train();self.optimizer.zero_grad(set_to_none=True)
        loss=configured_loss(self.model(x.to('mps')),y.to('mps'),self.config)
        require(torch.isfinite(loss).item(),'Nonfinite loss');loss.backward()
        require(all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in self.model.parameters()),'Invalid gradients')
        self.optimizer.step();self.scheduler.step();self.step+=1
        require(all(torch.isfinite(p).all().item() for p in self.model.parameters()),'Nonfinite parameters')
        return dict(completed_step=self.step,loss=loss.item(),sampling=trace,**(dict(target_fraction=float(y.float().mean())) if 'loss_id' in self.config else {}))

    @torch.no_grad()
    def forward_patch(self,image,target,member_id):
        self.model.eval();x,y,trace=patch_batch(image,target,self.config,step=0,member_id=member_id)
        result=self.model(x.to('mps')).cpu()
        require(result.shape==(1,2,*self.config['patch_size']) and torch.isfinite(result).all().item(),'Invalid MPS forward')
        return result.softmax(1),trace

    @torch.no_grad()
    def predict(self,image):
        image=image_tensor(image);self.model.eval()
        result=sliding_window_inference(image[None],self.config['patch_size'],1,self.model,overlap=.25,
            mode='constant',padding_mode='constant',sw_device='mps',device='cpu')
        require(result.shape==(1,2,*image.shape[1:]) and torch.isfinite(result).all().item(),'Invalid prediction grid')
        return result[0].softmax(0)


def cpu_tree(value):
    if isinstance(value,torch.Tensor):return value.detach().cpu().clone()
    if isinstance(value,dict):return {k:cpu_tree(v) for k,v in value.items()}
    if isinstance(value,list):return [cpu_tree(v) for v in value]
    if isinstance(value,tuple):return tuple(cpu_tree(v) for v in value)
    return value


def payload(session,identity,controls):
    validate_identity(identity);require(session.config==identity['config'],'Session differs from identity')
    state=cpu_tree(dict(schema_version='1.0.0',identity_sha256=digest(canonical(identity)),step=session.step,
        model=session.model.state_dict(),optimizer=session.optimizer.state_dict(),scheduler=session.scheduler.state_dict(),cpu_rng=torch.get_rng_state()))
    stream=BytesIO();torch.save(state,stream)
    files=dict(controls,**{'identity.json':canonical(identity),'state.pt':stream.getvalue()})
    validate_payload(files,identity)
    return files


def validate_payload(files,identity):
    validate_identity(identity)
    extra={'plan.json','authorization.json','progress.json'} if identity['schema_version'] in ('3.0.0','4.0.0') else set()
    require(set(files)=={'identity.json','state.pt','inputs.json','source.json','environment.json'}|extra,'Wrong checkpoint member set')
    if extra:
        from src.training.localizer_smoke import validate_controls
        validate_controls(files,identity)
    require(files['identity.json']==canonical(identity),'Changed run identity')
    for name,key in (('inputs.json','inputs_sha256'),('source.json','source_sha256'),('environment.json','environment_sha256')):
        require(digest(files[name])==identity[key],'Changed pinned checkpoint control')
    inputs=json.loads(files['inputs.json'])
    require(inputs['cohort_id']==COHORT_ID and [d['study_id'] for d in inputs['members']]==MEMBERS,'Wrong checkpoint input membership')
    state=torch.load(BytesIO(files['state.pt']),map_location='cpu',weights_only=True)
    session,_=decode_state(state,identity)
    if extra:
        rows=json.loads(files['progress.json'])['updates']
        require(len(rows)==session.step and [r['completed_step'] for r in rows]==list(range(1,session.step+1)),'Checkpoint progress differs')
        require(all(r['sampling']['member_id']==MEMBERS[i%2] and r['sampling']['step']==i and
            isinstance(r['loss'],(int,float)) and math.isfinite(r['loss']) for i,r in enumerate(rows)),'Checkpoint sampling/progress differs')
    return dict(step=session.step,identity_sha256=digest(canonical(identity)))


def restore_payload(files,identity):
    validate_payload(files,identity)
    state=torch.load(BytesIO(files['state.pt']),map_location='cpu',weights_only=True)
    session,rng=decode_state(state,identity);torch.set_rng_state(rng)
    return MPSRun(identity['config'],restored=session)


def publish_checkpoint(store,files,identity):
    check=validate_payload(files,identity);artifact_id=f"{identity['run_id']}:step:{check['step']}"
    derivation=digest(canonical(dict(identity=identity,step=check['step'])))
    metadata=dict(artifact_type='localizer-checkpoint',schema_version=identity['schema_version'],component='localizer-mps-run-v1',
        code_sha256=identity['source_sha256'],parents=[identity['inputs_sha256']],retention='recovery-verification-keeper',
        sensitivity='private-research',run_id=identity['run_id'],stage_id='checkpoint')
    pin,status=store.publish(artifact_id,derivation_sha256=derivation,files=files,metadata=metadata,
        validate=lambda f:validate_payload(f,identity))
    return dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation,step=check['step'],status=status)
