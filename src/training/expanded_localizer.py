"""Expanded role cache, deterministic schedule and identity-bound checkpoint mechanics.

Production inputs originate from open_expanded_inputs; constructors also support fixtures.
No real training launch API is provided by this readiness module.
"""
from copy import deepcopy
from io import BytesIO
import json
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training.localizer import image_tensor,validate_config,foreground_dice,LocalizerSession
from src.training.localizer_run import cpu_tree,MPSRun
from src.training.localizer_checkpoint import decode_state

ROLES=('optimizer','evaluator')
MAX_CACHE=512*1024**2


def tensor_pin(t):
    return digest(t.contiguous().numpy().tobytes())


class RoleCache:
    """Complete all-or-fail load, explicit roles, owned compact arrays, defensive copies."""
    def __init__(self,datasets,*,max_bytes=MAX_CACHE,guard=lambda:None):
        require(set(datasets)==set(ROLES),'Both role datasets required')
        require(type(max_bytes)==int and 0<max_bytes<=MAX_CACHE,'Invalid cache cap')
        self._items={};self._pins={};self.bytes=0
        self.inputs={'schema_version':'1.0.0','cache_policy':'owned_float32_uint8_ram_v1','cache_limit_bytes':max_bytes,'roles':{},'recipes':{}}
        seen=set()
        # Capture all descriptors before source reads, reject leakage first.
        for role in ROLES:
            ds=datasets[role];require(len(ds)>0,'Empty role')
            desc=[ds.descriptor(i) for i in range(len(ds))]
            for d in desc:
                require(d['operation']==role and d['protected_role']=={'optimizer':'train','evaluator':'validation'}[role],'Wrong role descriptor')
                require(d['study_id'] not in seen,'Duplicate or cross-role member');seen.add(d['study_id'])
            self.inputs['roles'][role]=desc;self.inputs['recipes'][role]=ds.recipe
        require(self.inputs['recipes']['optimizer']==self.inputs['recipes']['evaluator'],'Role recipes differ')
        for role in ROLES:
            self._items[role]=[];self._pins[role]=[]
            for i,d in enumerate(self.inputs['roles'][role]):
                guard();loaded=datasets[role].load(i,operation=role)
                require(loaded['provenance']['descriptor']==d,'Loaded member differs')
                record=loaded['transform_record'];check=deepcopy(record);pin=check.pop('record_sha256')
                require(digest(canonical(check))==pin and record['schema_version']=='2.0.0' and record['recipe']==self.inputs['recipes'][role],'Transform identity differs')
                x=image_tensor(loaded['image']);y=torch.as_tensor(loaded['label'])
                require(list(x.shape[1:])==record['processed_shape'],'Cached geometry differs')
                require(y.device.type=='cpu' and y.shape==x.shape and torch.all((y==0)|(y==1)) and y.any(),'Invalid cached pancreas target')
                needed=x.numel()*5
                require(self.bytes+needed<=max_bytes,'Processed cache byte cap')
                x=x.clone().contiguous();y=y.to(torch.uint8).clone().contiguous()
                item=dict(image=x,label=y,transform_record=deepcopy(record),study_id=d['study_id'])
                self._items[role].append(item);self._pins[role].append((tensor_pin(x),tensor_pin(y),digest(canonical(record))))
                self.bytes+=needed;del loaded;guard()
        self._input_pin=digest(canonical(self.inputs))

    def members(self,role):
        require(role in ROLES,'Explicit role required')
        require(digest(canonical(self.inputs))==self._input_pin,'Cache input binding changed')
        return [d['study_id'] for d in self.inputs['roles'][role]]

    def get(self,role,index):
        ids=self.members(role);require(type(index)==int and 0<=index<len(ids),'Invalid member index')
        item=self._items[role][index]
        require((tensor_pin(item['image']),tensor_pin(item['label']),digest(canonical(item['transform_record'])))==self._pins[role][index] and item['study_id']==ids[index],'Cached input changed')
        return deepcopy(item)


def scheduled_member(inputs,step):
    require(type(step)==int and step>=0,'Invalid schedule step')
    ids=[d['study_id'] for d in inputs['roles']['optimizer']]
    require(ids and len(ids)==len(set(ids)),'Invalid optimizer membership')
    return ids[step%len(ids)]


def validate_identity(identity,inputs):
    fields={'schema_version','purpose','run_id','device','config','inputs_sha256','source_sha256','environment_sha256'}
    launched=identity.get('schema_version')=='2.0.0'
    require(set(identity)==(fields|{'plan_sha256'} if launched else fields),'Identity fields differ')
    require((launched and identity['purpose'] in ('synthetic-expanded-executor','qualified-expanded-executor') or identity['schema_version']=='1.0.0' and identity['purpose'] in ('synthetic-expanded-verification','qualified-expanded-forward-profile')) and identity['device'] in ('cpu','mps'),'Unsupported expanded identity')
    require(isinstance(identity['run_id'],str) and identity['run_id'].startswith('expanded-'),'Invalid run ID')
    validate_config(identity['config'])
    for k in ('inputs_sha256','source_sha256','environment_sha256')+ (('plan_sha256',) if launched else ()):
        require(isinstance(identity[k],str) and len(identity[k])==64 and all(c in '0123456789abcdef' for c in identity[k]),'Invalid identity digest')
    require(digest(canonical(inputs))==identity['inputs_sha256'],'Input binding differs')
    require(set(inputs['roles'])==set(ROLES),'Checkpoint role inventory differs')
    ids=[]
    for role in ROLES:
        require(inputs['roles'][role],'Empty checkpoint role')
        for d in inputs['roles'][role]:
            require(d['operation']==role and d['protected_role']=={'optimizer':'train','evaluator':'validation'}[role],'Checkpoint member role differs')
            ids.append(d['study_id'])
    require(len(ids)==len(set(ids)),'Checkpoint membership overlaps')


def verify_session(session,identity,cache):
    validate_identity(identity,cache.inputs)
    require(session.config==identity['config'] and (isinstance(session,MPSRun)==(identity['device']=='mps')),'Session configuration/device differs')


def synthetic_update(session,cache,identity):
    verify_session(session,identity,cache)
    require(identity['purpose']=='synthetic-expanded-verification','Real updates require a frozen launch executor')
    require(session.step<session.config['max_steps'],'Update cap')
    sid=scheduled_member(cache.inputs,session.step);index=session.step%len(cache.members('optimizer'))
    item=cache.get('optimizer',index)
    if isinstance(session,MPSRun):return session._step(item['image'],item['label'],sid)
    return session.update(item['image'],item['label'],sid)


def evaluate_role(session,cache,identity,role,*,guard=lambda:None):
    verify_session(session,identity,cache);rows=[]
    for i,sid in enumerate(cache.members(role)):
        guard();item=cache.get(role,i);p=session.predict(item['image']);guard()
        require(p.shape==(2,*item['image'].shape[1:]) and torch.isfinite(p).all() and torch.allclose(p.sum(0),torch.ones_like(p[0]),atol=1e-5),'Invalid full-volume probabilities')
        metrics=foreground_dice(p.argmax(0,keepdim=True),item['label'])
        rows.append(dict(study_id=sid,**metrics))
    return dict(role=role,cases=rows,mean_dice=sum(r['dice'] for r in rows)/len(rows),completed_step=session.step)


def checkpoint(session,cache,identity,history):
    verify_session(session,identity,cache)
    state=cpu_tree(dict(schema_version='1.0.0',identity_sha256=digest(canonical(identity)),step=session.step,
        model=session.model.state_dict(),optimizer=session.optimizer.state_dict(),scheduler=session.scheduler.state_dict(),cpu_rng=torch.get_rng_state()))
    stream=BytesIO();torch.save(state,stream)
    files={'identity.json':canonical(identity),'inputs.json':canonical(cache.inputs),'progress.json':canonical(history),'state.pt':stream.getvalue()}
    restore(files,identity,device='cpu')
    return files


def restore(files,identity,*,device=None):
    require(set(files)=={'identity.json','inputs.json','progress.json','state.pt'},'Checkpoint inventory differs')
    inputs=json.loads(files['inputs.json']);validate_identity(identity,inputs)
    require(files['identity.json']==canonical(identity),'Checkpoint identity differs')
    session,rng=decode_state(torch.load(BytesIO(files['state.pt']),map_location='cpu',weights_only=True),identity)
    history=json.loads(files['progress.json'])
    require(len(history)==session.step,'Progress length differs')
    for i,r in enumerate(history):
        require(r['completed_step']==i+1 and r['sampling']['step']==i and r['sampling']['member_id']==scheduled_member(inputs,i),'Wrong update schedule')
        require(type(r['loss']) in (int,float) and torch.isfinite(torch.tensor(r['loss'])),'Invalid update loss')
    require(identity['purpose']!='qualified-expanded-forward-profile' or session.step==0,'Real profile contains optimizer updates')
    target=identity['device'] if device is None else device
    require(target in ('cpu',identity['device']),'Restore device differs')
    torch.set_rng_state(rng)
    return MPSRun(identity['config'],restored=session) if target=='mps' else session
