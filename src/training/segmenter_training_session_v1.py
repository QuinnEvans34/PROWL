"""Versioned six/one segmenter transaction; real updates require a later exact launch permit."""
from contextlib import contextmanager
from copy import deepcopy
from io import BytesIO
import hashlib,json,math,os
import numpy as np
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_training_inputs_v1 as inputs,segmenter_cache_v1 as cache
from src.training import segmenter_session_v1 as numerical,segmenter_native_scoring_v1 as scoring,segmenter_inference_v1 as inverse
TASK='pancreas_lesion_segmenter_training_transaction_v1'
POLICY='six_member_seeded_epoch_permutation_v1'
INITIAL='3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add'
CONTROLS={n+'.json':n+'_sha256' for n in ('inputs','source','environment','geometry','initialization','lineage')}
_REAL_LAUNCH_TOKEN=object()


def config(*,size=144,steps=48):
    return dict(schema_version='segmenter-training-config-1',tensor_shape=[size]*3,seed=42,architecture=deepcopy(numerical.ARCH),precision='float32',loss_id=numerical.LOSS_V3,learning_rate=.0003,weight_decay=1e-5,max_steps=steps,sampling_policy=POLICY,lr_schedule='constant',primary_checkpoint='terminal',jitter='none')


def validate_config(c):
    require(set(c)==set(config()) and isinstance(c['tensor_shape'],list) and len(c['tensor_shape'])==3 and all(type(v) is int for v in c['tensor_shape']) and c==config(size=c['tensor_shape'][0],steps=c['max_steps']) and c['tensor_shape'] in ([24]*3,[144]*3) and type(c['max_steps']) is int and 1<=c['max_steps']<=180,'Unsupported training recipe/update envelope')


def scratch(c):
    validate_config(c)
    # Numerical factory only; no historical/synthetic-trained checkpoint is loaded.
    return numerical.scratch(numerical.config(size=c['tensor_shape'][0],steps=4 if c['tensor_shape'][0]==144 else 6,lr=c['learning_rate']))


def deny_import(file_sha256,inventory):
    require(isinstance(file_sha256,str) and len(file_sha256)==64,'Missing import identity')
    known=any(v['sha256']==file_sha256 for v in inventory['files'])
    raise ValueError('Known historical/third-party/capstone weight import denied' if known else 'Unknown weight provenance denied')


def next_member(c,control,step):
    validate_config(c);names=control['train'];require(len(names)==6 and len(set(names))==6 and type(step) is int and 0<=step<c['max_steps'],'Sampler membership/budget')
    epoch,cursor=divmod(step,6);seed=int.from_bytes(hashlib.sha256(f"{c['seed']}:{epoch}:{POLICY}".encode()).digest()[:8],'little')
    order=torch.randperm(6,generator=torch.Generator().manual_seed(seed)).tolist();ordered=[names[i] for i in order]
    return ordered[cursor],dict(epoch=epoch,cursor=cursor,order=ordered,completed_updates=step,policy=POLICY)


def make_identity(c,provider,context,*,run_id,device):
    validate_config(c);require(type(provider) in (inputs.InventedInputs,inputs.QualifiedInputs),'Checked input provider required')
    require(set(context)=={'source.json','environment.json','geometry.json','lineage.json'},'Required lineage context')
    control=deepcopy(provider.control);domain=control['domain'];require(domain in ('invented_arrays_only','qualified_real_cache') and (domain!='qualified_real_cache' or c['tensor_shape']==[144]*3),'Real input/tensor domain')
    require(len(control['train'])==6 and len(control['validation'])==1 and not set(control['train'])&set(control['validation']),'Protected role separation')
    model=scratch(c);initial=numerical.state_hash(model.state_dict());require(initial==INITIAL,'Scratch initialization does not match D-324/D-325 baseline')
    controls=deepcopy(context)|{'inputs.json':canonical(control),'initialization.json':canonical(dict(task=TASK,mode='fresh_random_only',seed=42,initial_weights_sha256=initial,model_signature=numerical.signature(model),weight_imports=[]))}
    i=dict(schema_version='segmenter-training-session-1',task=TASK,domain=domain,run_id=run_id,device=device,config=deepcopy(c),**{k:digest(controls[n]) for n,k in CONTROLS.items()});validate_controls(i,controls);return i,controls


def validate_identity(i):
    require(set(i)=={'schema_version','task','domain','run_id','device','config'}|set(CONTROLS.values()) and i['schema_version']=='segmenter-training-session-1' and i['task']==TASK and i['domain'] in ('invented_arrays_only','qualified_real_cache') and i['device'] in ('cpu','mps') and isinstance(i['run_id'],str) and i['run_id'].startswith('segmenter-training-') and len(i['run_id'])<=100,'Wrong task/domain/session')
    validate_config(i['config']);require(i['domain']!='qualified_real_cache' or i['config']['tensor_shape']==[144]*3,'Real tensor shape')
    for k in CONTROLS.values():require(isinstance(i[k],str) and len(i[k])==64 and all(c in '0123456789abcdef' for c in i[k]),'Bad control identity')


def validate_controls(i,files):
    validate_identity(i);require(set(files)==set(CONTROLS) and all(digest(files[n])==i[k] for n,k in CONTROLS.items()),'Missing/changed controls')
    control=json.loads(files['inputs.json']);init=json.loads(files['initialization.json']);lineage=json.loads(files['lineage.json'])
    require(control['domain']==i['domain'] and len(control['train'])==6 and len(control['validation'])==1 and len(set(control['train']+control['validation']))==7 and control['jitter']=='none','Wrong input-role control')
    require(init==dict(task=TASK,mode='fresh_random_only',seed=42,initial_weights_sha256=INITIAL,model_signature=numerical.signature(scratch(i['config'])),weight_imports=[]),'Warm start/head/init substitution')
    require(lineage['weight_imports_allowed'] is False and lineage['teacher_models']==[] and lineage['selected_import_sha256'] is None and isinstance(lineage['checkpoint_inventory_sha256'],str) and len(lineage['checkpoint_inventory_sha256'])==64,'Missing historical import-denial evidence')
    return control


class UpdatePermit:
    """No public grant factory in readiness code. Exact launch executor must supply one later."""
    def __init__(self,token,identity_sha256,request_sha256):
        require(token is _REAL_LAUNCH_TOKEN,'Only an exact authorized launch can grant updates');self.identity_sha256=identity_sha256;self.request_sha256=request_sha256


class Session:
    def __init__(self,i,controls,*,restoring_on_cpu=False):
        self.control=validate_controls(i,controls);self.identity=deepcopy(i);self.controls=deepcopy(controls);self.config=deepcopy(i['config']);self.model=scratch(self.config)
        self.device='cpu' if restoring_on_cpu else i['device']
        if self.device=='mps':require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and torch.backends.mps.is_available(),'Native MPS/no fallback required')
        self.model.to(self.device);self.optimizer=torch.optim.AdamW(self.model.parameters(),lr=self.config['learning_rate'],weight_decay=self.config['weight_decay'])
        self.step=0;self.dirty=False;self.history=[];self.evaluations=[];self.cpu_rng=torch.Generator().manual_seed(42).get_state();self.mps_rng=None
        if self.device=='mps':
            old=torch.mps.get_rng_state();torch.mps.manual_seed(42);self.mps_rng=torch.mps.get_rng_state().cpu().clone();torch.mps.set_rng_state(old)
    def import_weights(self,*args,**kwargs):raise ValueError('All weight imports denied; fresh scratch or same-run checkpoint resume only')
    def update(self,provider,*,permit=None):
        require(not self.dirty,'Dirty update requires last-complete checkpoint reload')
        if self.identity['domain']=='qualified_real_cache':require(type(permit) is UpdatePermit and permit.identity_sha256==digest(canonical(self.identity)) and len(permit.request_sha256)==64,'No exact real launch permit')
        require(type(provider) is (inputs.InventedInputs if self.identity['domain']=='invented_arrays_only' else inputs.QualifiedInputs) and canonical(provider.control)==self.controls['inputs.json'],'Wrong provider/domain/lineage')
        name,trace=next_member(self.config,self.control,self.step);batch=provider.get(name,role='train',operation='optimizer');require(type(batch) is inputs.Batch,'Raw tuple/evaluator result cannot optimize')
        x,y=batch.checked(self.identity['inputs_sha256'],'optimizer',name);x=torch.as_tensor(x);y=torch.as_tensor(y,dtype=torch.long)
        require(x.dtype==torch.float32 and x.shape==(1,*self.config['tensor_shape']) and y.shape==tuple(self.config['tensor_shape']) and torch.isfinite(x).all() and x.min()>=0 and x.max()<=1 and ((y>=0)&(y<=2)).all(),'Invalid optimizer input')
        self.dirty=True
        with self.rng_scope():
            self.model.train();self.optimizer.zero_grad(set_to_none=True);loss=numerical.objective(self.model(x[None].to(self.device)),y[None].to(self.device),self.config['loss_id']);require(torch.isfinite(loss).item(),'Nonfinite loss');loss.backward()
            require(all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in self.model.parameters()),'Invalid gradient');self.optimizer.step();require(numerical.finite(self.model.state_dict()) and numerical.finite(self.optimizer.state_dict()),'Invalid mutated state')
            row=dict(completed_step=self.step+1,member_id=name,sampling=trace,loss=float(loss.detach().cpu()),learning_rate=self.optimizer.param_groups[0]['lr'],batch_sha256=batch.hashes())
        self.history.append(row);self.step+=1;self.dirty=False;return deepcopy(row)
    @contextmanager
    def rng_scope(self):
        old=torch.get_rng_state();other=torch.mps.get_rng_state() if self.device=='mps' else None;torch.set_rng_state(self.cpu_rng)
        if other is not None:torch.mps.set_rng_state(self.mps_rng)
        try:yield
        finally:
            self.cpu_rng=torch.get_rng_state().clone();torch.set_rng_state(old)
            if other is not None:self.mps_rng=torch.mps.get_rng_state().cpu().clone();torch.mps.set_rng_state(other)
    @torch.no_grad()
    def predict(self,image):
        require(not self.dirty,'Dirty state cannot infer');x=torch.as_tensor(image);require(x.device.type=='cpu' and x.dtype==torch.float32 and x.shape==(1,*self.config['tensor_shape']) and torch.isfinite(x).all() and x.min()>=0 and x.max()<=1,'Bad image-only inference input');self.model.eval();p=self.model(x[None].to(self.device)).softmax(1)[0].cpu().numpy();require(np.isfinite(p).all() and np.allclose(p.sum(0),1,atol=1e-5,rtol=0),'Invalid probabilities');return p
    def evaluate(self,provider):
        require(not self.dirty and canonical(provider.control)==self.controls['inputs.json'] and (not self.evaluations or self.evaluations[-1]['step']<self.step),'Duplicate/changed evaluation');rows=[]
        for role,key in [('train','train'),('validation','validation')]:
            for name in self.control[key]:
                b=provider.get(name,role=role,operation='evaluator');x,y=b.checked(self.identity['inputs_sha256'],'evaluator',name);p=self.predict(x);m=scoring.score(p.argmax(0).astype(np.uint8), (y>0).astype(np.uint8),(y==2).astype(np.uint8),target_state='positive' if (y==2).any() else 'verified_negative');rows.append(dict(study_id=name,protected_role=role,**m))
        e=dict(step=self.step,scope='tensor_diagnostics_not_original_native_truth',cases=rows,aggregate=scoring.aggregates(rows));self.evaluations.append(e);return deepcopy(e)


def progress(s):
    return dict(schema_version='segmenter-training-progress-1',step=s.step,history=deepcopy(s.history),evaluations=deepcopy(s.evaluations),primary_checkpoint='terminal',exposure={n:sum(r['member_id']==n for r in s.history) for n in s.control['train']},sampler=next_member(s.config,s.control,s.step)[1] if s.step<s.config['max_steps'] else dict(exhausted=True,completed_updates=s.step,policy=POLICY))


def validate_progress(p,i,control):
    c=i['config'];require(set(p)=={'schema_version','step','history','evaluations','primary_checkpoint','exposure','sampler'} and p['schema_version']=='segmenter-training-progress-1' and p['primary_checkpoint']=='terminal' and numerical.finite(p),'Invalid progress/selection')
    step=p['step'];require(type(step) is int and 0<=step<=c['max_steps'] and len(p['history'])==step,'Committed update count differs')
    for j,row in enumerate(p['history']):
        name,trace=next_member(c,control,j);require(set(row)=={'completed_step','member_id','sampling','loss','learning_rate','batch_sha256'} and row['completed_step']==j+1 and row['member_id']==name and row['sampling']==trace and type(row['loss']) is float and row['loss']>=0 and row['learning_rate']==c['learning_rate'],'Update/exposure/schedule history differs')
        expected=control['member_sha256'][name] if i['domain']=='invented_arrays_only' else {k:control['member_sha256'][cache.names(control['train'].index(name))[k]] for k in ('image','target')}
        require(row['batch_sha256']==expected,'Consumed array identity differs')
    require(p['exposure']=={n:sum(r['member_id']==n for r in p['history']) for n in control['train']} and p['sampler']==(next_member(c,control,step)[1] if step<c['max_steps'] else dict(exhausted=True,completed_updates=step,policy=POLICY)),'Exposure/cursor reset')
    previous=-1
    for e in p['evaluations']:
        require(set(e)=={'step','scope','cases','aggregate'} and type(e['step']) is int and previous<e['step']<=step and e['scope']=='tensor_diagnostics_not_original_native_truth','Evaluation chronology differs');previous=e['step']
        require([(r['study_id'],r['protected_role']) for r in e['cases']]==[(n,'train') for n in control['train']]+[(n,'validation') for n in control['validation']],'Evaluation role membership differs')
        for r in e['cases']:
            require(set(r)=={'study_id','protected_role','confusion_matrix','metrics','outside_pancreas_voxels','connectivity','components'} and r['outside_pancreas_voxels']==0,'Tensor evaluation fields/relationship differ')
            require(r['metrics']==scoring.from_confusion(r['confusion_matrix']) and sum(map(sum,r['confusion_matrix']))==math.prod(c['tensor_shape']) and r['connectivity']==26,'Evaluation integer formulas differ')
            expected=control['target_metadata'][r['study_id']];require(np.asarray(r['confusion_matrix']).sum(1).tolist()==expected['class_counts'],'Tensor reference counts changed');require([{k:v[k] for k in ('component_id','native_voxels','bounds_xyz_half_open','source_boundary_contact')} for v in r['components']]==expected['components'],'Tensor reference component identity changed')
            require(all(set(v)=={'component_id','native_voxels','true_positive','recall','missed','bounds_xyz_half_open','source_boundary_contact'} and all(type(v[k]) is int for k in ('component_id','native_voxels','true_positive')) and 0<=v['true_positive']<=v['native_voxels'] and all(type(k) is int for axis in v['bounds_xyz_half_open'] for k in axis) for v in r['components']),'Invalid integer component records')
            require(sum(v['native_voxels'] for v in r['components'])==r['metrics']['lesion']['target_voxels'] and sum(v['true_positive'] for v in r['components'])==r['metrics']['lesion']['true_positive'] and all(v['recall']==v['true_positive']/v['native_voxels'] and v['missed']==(v['true_positive']==0) for v in r['components']),'Evaluation component accounting differs')
        require(e['aggregate']==scoring.aggregates(e['cases']),'Evaluation aggregate differs')


def payload(s):
    require(not s.dirty and s.config==s.identity['config'],'Dirty/config-mutated checkpoint refused');control=validate_controls(s.identity,s.controls);p=progress(s);validate_progress(p,s.identity,control)
    state=numerical.cpu_tree(dict(schema_version='segmenter-training-state-1',identity_sha256=digest(canonical(s.identity)),step=s.step,model=s.model.state_dict(),optimizer=s.optimizer.state_dict(),cpu_rng=s.cpu_rng,mps_rng=s.mps_rng));buf=BytesIO();torch.save(state,buf)
    files=dict(s.controls,**{'identity.json':canonical(s.identity),'progress.json':canonical(p),'state.pt':buf.getvalue()});validate_payload(files,s.identity);return files


def decode(files,i):
    validate_identity(i);require(set(files)==set(CONTROLS)|{'identity.json','progress.json','state.pt'} and files['identity.json']==canonical(i) and len(files['state.pt'])<=96*1024**2,'Wrong checkpoint task/inventory/size');controls={n:files[n] for n in CONTROLS};control=validate_controls(i,controls);p=json.loads(files['progress.json']);validate_progress(p,i,control);state=torch.load(BytesIO(files['state.pt']),map_location='cpu',weights_only=True)
    require(set(state)=={'schema_version','identity_sha256','step','model','optimizer','cpu_rng','mps_rng'} and state['schema_version']=='segmenter-training-state-1' and state['identity_sha256']==digest(canonical(i)) and type(state['step']) is int and state['step']==p['step'] and numerical.finite(state),'Changed state identity/progress')
    s=Session(i,controls,restoring_on_cpu=True);expected=s.model.state_dict();require(set(state['model'])==set(expected) and all(isinstance(state['model'][n],torch.Tensor) and state['model'][n].shape==v.shape and state['model'][n].dtype==v.dtype for n,v in expected.items()),'Model/head inventory differs')
    if not state['step']:require(numerical.state_hash(state['model'])==INITIAL,'Step0 weights not scratch')
    opt=state['optimizer'];standard=s.optimizer.state_dict();require(set(opt)==set(standard) and opt['param_groups']==standard['param_groups'],'Optimizer/rate policy differs');ids=standard['param_groups'][0]['params'];require(set(opt['state'])==(set(ids) if state['step'] else set()),'Optimizer state missing/mixed')
    for idx,param in zip(ids,s.model.parameters()):
        if state['step']:
            e=opt['state'][idx];require(set(e)=={'step','exp_avg','exp_avg_sq'} and isinstance(e['step'],torch.Tensor) and e['step'].numel()==1 and e['step'].item()==state['step'] and all(isinstance(e[k],torch.Tensor) and e[k].shape==param.shape and e[k].dtype==param.dtype for k in ('exp_avg','exp_avg_sq')) and (e['exp_avg_sq']>=0).all(),'Mixed AdamW update state')
    require(isinstance(state['cpu_rng'],torch.Tensor) and state['cpu_rng'].dtype==torch.uint8 and state['cpu_rng'].shape==torch.get_rng_state().shape,'CPU RNG differs');torch.Generator().set_state(state['cpu_rng']);mr=state['mps_rng'];require((i['device']=='cpu' and mr is None) or (i['device']=='mps' and isinstance(mr,torch.Tensor) and mr.dtype==torch.uint8 and mr.ndim==1 and 0<mr.numel()<=4096),'MPS RNG differs')
    s.model.load_state_dict(state['model'],strict=True);s.optimizer.load_state_dict(opt);s.step=state['step'];s.history=p['history'];s.evaluations=p['evaluations'];s.cpu_rng=state['cpu_rng'];s.mps_rng=mr;return s


def validate_payload(files,i):
    s=decode(files,i);return dict(task=TASK,step=s.step,identity_sha256=digest(canonical(i)),weights_sha256=numerical.state_hash(s.model.state_dict()),progress_sha256=digest(files['progress.json']),members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})


def restore_payload(files,i):
    s=decode(files,i)
    if i['device']=='mps':
        out=Session(i,s.controls);require(s.mps_rng.shape==out.mps_rng.shape,'Native RNG shape differs');out.model.load_state_dict(s.model.state_dict());out.optimizer.load_state_dict(s.optimizer.state_dict());out.step=s.step;out.history=s.history;out.evaluations=s.evaluations;out.cpu_rng=s.cpu_rng;out.mps_rng=s.mps_rng;s=out
    return s


def publish_checkpoint(store,s):
    files=payload(s);i=s.identity;artifact_id=f"{i['run_id']}:step:{s.step}";derivation=digest(canonical(dict(identity=i,step=s.step)))
    metadata=dict(artifact_type='segmenter-training-checkpoint',schema_version='segmenter-training-session-1',component=TASK,code_sha256=i['source_sha256'],parents=[i['geometry_sha256'],i['inputs_sha256'],i['lineage_sha256']],retention='training-transaction-keeper',sensitivity='private-research',run_id=i['run_id'],stage_id='checkpoint')
    pin,status=store.publish(artifact_id,derivation_sha256=derivation,files=files,metadata=metadata,validate=lambda f:validate_payload(f,i));return dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation,step=s.step,status=status)


def tree_exact(a,b):
    if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and set(a)==set(b) and all(tree_exact(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return type(a) is type(b) and len(a)==len(b) and all(tree_exact(x,y) for x,y in zip(a,b))
    return type(a) is type(b) and a==b


def resume(store,reference,identity):
    validate_identity(identity);step=reference['step'];require(type(step) is int and 0<=step<=identity['config']['max_steps'] and reference['artifact_id']==f"{identity['run_id']}:step:{step}" and reference['derivation_sha256']==digest(canonical(dict(identity=identity,step=step))),'Wrong run/task/checkpoint reference')
    files,receipt=store.resolve(reference['artifact_id'],receipt_sha256=reference['receipt_sha256'],expected_derivation=reference['derivation_sha256'],validate=lambda f:validate_payload(f,identity));require(receipt['metadata']['artifact_type']=='segmenter-training-checkpoint' and receipt['metadata']['run_id']==identity['run_id'] and receipt['metadata']['code_sha256']==identity['source_sha256'],'Wrong checkpoint publication lineage')
    s=restore_payload(files,identity);require(s.step==step,'Restored committed step differs');return s
