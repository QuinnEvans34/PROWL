"""Separate synthetic three-class scratch transaction. No external optimizer input/weight import."""
from contextlib import contextmanager
from copy import deepcopy
from io import BytesIO
import hashlib
import math
import os
import numpy as np
import torch
import torch.nn.functional as F
from scipy import ndimage
from src.models.segresnet import build_model
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_geometry_v1 as geometry

TASK='pancreas_lesion_segmenter_synthetic_v1'
LOSS='voxel_ce_present_foreground_dice_v1'
LOSS_V2='voxel_ce_lesion16_present_foreground_dice_v2'
LOSS_V3='voxel_ce_lesion256_present_foreground_dice_v3'
POLICY='full_roi_seeded_epoch_permutation_v1'
NAMES=('sparse','multiple','boundary','outside_pancreas','verified_negative')
CONTROLS={n+'.json':n+'_sha256' for n in ('inputs','source','environment','geometry','initialization')}
ARCH=dict(in_channels=1,out_channels=3,init_filters=16,norm='group',num_groups=8,
    blocks_down=[1,2,2,4],blocks_up=[1,1,1],dropout_prob=0)


def config(*,size=24,steps=120,lr=.003,loss_id=LOSS_V3):
    return dict(schema_version='segmenter-synthetic-config-3' if steps>360 else 'segmenter-synthetic-config-2' if steps>120 else 'segmenter-synthetic-config-1',tensor_shape=[size]*3,seed=42,
        learning_rate=lr,weight_decay=1e-5,max_steps=steps,architecture=deepcopy(ARCH),
        loss_id=loss_id,sampling_policy=POLICY,lr_schedule='constant',precision='float32')


def validate_config(c):
    require(set(c)==set(config()) and c['schema_version'] in ('segmenter-synthetic-config-1','segmenter-synthetic-config-2','segmenter-synthetic-config-3') and
        c['architecture']==ARCH and c['loss_id'] in (LOSS,LOSS_V2,LOSS_V3) and c['sampling_policy']==POLICY and
        c['lr_schedule']=='constant' and c['precision']=='float32','Wrong three-class configuration')
    require(c['tensor_shape'] in ([24]*3,[144]*3) and all(type(n)==int for n in c['tensor_shape']),'Synthetic shape envelope')
    require(type(c['seed'])==int and 0<=c['seed']<2**32 and type(c['max_steps'])==int and 1<=c['max_steps']<=({'segmenter-synthetic-config-1':120,'segmenter-synthetic-config-2':360,'segmenter-synthetic-config-3':480}[c['schema_version']]),'Synthetic update envelope')
    require(c['schema_version']=='segmenter-synthetic-config-1' or c['tensor_shape']==[24]*3,'Extended scope is CPU-sized only')
    require(c['tensor_shape']!=[144]*3 or (c['schema_version']=='segmenter-synthetic-config-1' and c['max_steps']<=4),'MPS-sized synthetic four-update cap')
    require(type(c['learning_rate']) in (int,float) and math.isfinite(c['learning_rate']) and 0<c['learning_rate']<=.003 and c['weight_decay']==1e-5,'Optimizer policy envelope')


def scratch(c):
    validate_config(c)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(c['seed']);model=build_model({'model':c['architecture']})
    return model


def state_hash(state):
    h=hashlib.sha256()
    for name,v in sorted(state.items()):
        h.update(canonical(dict(name=name,shape=list(v.shape),dtype=str(v.dtype))))
        h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def signature(model):return {n:dict(shape=list(v.shape),dtype=str(v.dtype)) for n,v in model.state_dict().items()}


def fixture(name,size=24):
    require(name in NAMES and size in (24,144),'Only internal invented fixtures')
    # Independent integer class oracle. Resampling here is exact block repetition, not the ROI mapper.
    y=torch.zeros((24,24,24),dtype=torch.long);y[5:19,5:19,5:19]=1
    if name=='sparse':y[10:12,10:12,10:12]=2
    if name=='multiple':y[7:9,8:10,9:11]=2;y[15:17,14:16,13:15]=2
    if name=='boundary':y.zero_();y[0:14,5:19,5:19]=1;y[0:2,10:12,10:12]=2
    if name=='outside_pancreas':y[18:21,10:12,10:12]=2
    factor=size//24
    for axis in range(3):y=y.repeat_interleave(factor,dim=axis)
    x=torch.tensor([.1,.5,.9],dtype=torch.float32)[y][None]
    return x,y


def fixture_control(c):
    return dict(domain='invented_arrays_only',fixture_version='class_cues_v1',train=list(NAMES),
        evaluator=['synthetic_evaluator_not_optimizer'],tensor_shape=c['tensor_shape'],
        policy=POLICY,real_inputs_authorized=False)


def next_member(c,step):
    require(type(step)==int and 0<=step<c['max_steps'],'Synthetic sampler budget')
    epoch,index=divmod(step,len(NAMES))
    seed=int.from_bytes(hashlib.sha256(f"{c['seed']}:{epoch}:{POLICY}".encode()).digest()[:8],'little')
    order=torch.randperm(len(NAMES),generator=torch.Generator().manual_seed(seed)).tolist()
    return NAMES[order[index]],dict(epoch=epoch,cursor=index,order=[NAMES[i] for i in order],completed_updates=step,policy=POLICY)


def checked_batch(image,target,c):
    validate_config(c);x=torch.as_tensor(image);y=torch.as_tensor(target)
    require(x.device.type==y.device.type=='cpu' and x.dtype==torch.float32 and
        x.shape==(1,*c['tensor_shape']) and y.shape==tuple(c['tensor_shape']) and y.dtype==torch.long and
        torch.isfinite(x).all().item() and x.min()>=0 and x.max()<=1 and ((y>=0)&(y<=2)).all().item(),'Invalid three-class normalized CPU input')
    return x[None],y[None]


def objective(logits,target,loss_id=LOSS):
    require(logits.ndim==5 and logits.shape[1]==3 and target.shape==(logits.shape[0],*logits.shape[2:]) and
        target.dtype==torch.long and ((target>=0)&(target<=2)).all().item() and torch.isfinite(logits).all().item(),'Invalid three-class logits/target')
    require(loss_id in (LOSS,LOSS_V2,LOSS_V3),'Unsupported segmenter objective')
    weights=logits.new_tensor([1.,1.,16. if loss_id==LOSS_V2 else 256.]) if loss_id!=LOSS else None
    ce=F.cross_entropy(logits,target,weight=weights,reduction='mean');p=logits.softmax(1);terms=[]
    for i in range(len(target)):
        present=[]
        for k in (1,2):
            truth=(target[i]==k).to(p.dtype)
            if truth.any():present.append(1-(2*(p[i,k]*truth).sum()+1e-5)/(p[i,k].sum()+truth.sum()+1e-5))
        terms.append(torch.stack(present).mean() if present else p[i].sum()*0)
    return ce+torch.stack(terms).mean()


def metrics(prediction,target):
    require(prediction.shape==target.shape and ((prediction>=0)&(prediction<=2)).all() and ((target>=0)&(target<=2)).all(),'Three-class metric grid')
    r={}
    for name,classes in [('background',[0]),('pancreas_parenchyma',[1]),('lesion',[2]),('pancreas_lesion_union',[1,2])]:
        a=sum((prediction==k).to(torch.int8) for k in classes).bool();b=sum((target==k).to(torch.int8) for k in classes).bool()
        n=int(b.sum());v=int(a.sum());tp=int((a&b).sum());r[name]=dict(target_voxels=n,predicted_voxels=v,true_positive=tp,
            dice=2*tp/(n+v) if n else None,recall=tp/n if n else None)
    labels,count=ndimage.label((target==2).cpu().numpy(),np.ones((3,3,3)))
    a=(prediction==2).cpu().numpy();r['components']=[dict(component_id=i,native_voxels=int((labels==i).sum()),
        true_positive=int(((labels==i)&a).sum())) for i in range(1,count+1)]
    r['lesion_false_positive_fraction']=r['lesion']['predicted_voxels']/target.numel() if not r['lesion']['target_voxels'] else None
    return r


def make_identity(c,controls,*,run_id,device):
    validate_config(c);controls=deepcopy(controls);require(set(controls)=={'source.json','environment.json','geometry.json'},'Initial context inventory')
    model=scratch(c)
    controls['initialization.json']=canonical(dict(mode='fresh_random_only',seed=c['seed'],task=TASK,
        model_signature=signature(model),initial_weights_sha256=state_hash(model.state_dict()),weight_imports=[]))
    controls['inputs.json']=canonical(fixture_control(c))
    identity=dict(schema_version='segmenter-synthetic-session-1',task=TASK,data_mode='synthetic',run_id=run_id,
        device=device,config=deepcopy(c),**{k:digest(controls[n]) for n,k in CONTROLS.items()})
    validate_identity(identity);return identity,controls


def validate_identity(i):
    require(set(i)=={'schema_version','task','data_mode','run_id','device','config'}|set(CONTROLS.values()) and
        i['schema_version']=='segmenter-synthetic-session-1' and i['task']==TASK and i['data_mode']=='synthetic' and
        i['device'] in ('cpu','mps') and isinstance(i['run_id'],str) and i['run_id'].startswith('segmenter-synthetic-') and len(i['run_id'])<=100,'Wrong synthetic segmenter identity')
    validate_config(i['config'])
    for k in CONTROLS.values():require(isinstance(i[k],str) and len(i[k])==64 and all(ch in '0123456789abcdef' for ch in i[k]),'Invalid control pin')


def validate_controls(i,controls):
    validate_identity(i);require(set(controls)==set(CONTROLS),'Wrong controls')
    for n,k in CONTROLS.items():require(digest(controls[n])==i[k],'Control identity changed')
    require(controls['inputs.json']==canonical(fixture_control(i['config'])),'External input substitution')
    init=__import__('json').loads(controls['initialization.json'])
    require(set(init)=={'mode','seed','task','model_signature','initial_weights_sha256','weight_imports'} and
        init['mode']=='fresh_random_only' and init['seed']==i['config']['seed'] and init['task']==TASK and init['weight_imports']==[],'Warm start or wrong-task initialization forbidden')
    return init


def cpu_tree(x):
    if isinstance(x,torch.Tensor):return x.detach().cpu().clone()
    if isinstance(x,dict):return {k:cpu_tree(v) for k,v in x.items()}
    if isinstance(x,list):return [cpu_tree(v) for v in x]
    if isinstance(x,tuple):return tuple(cpu_tree(v) for v in x)
    return deepcopy(x)


def finite(x):
    if isinstance(x,torch.Tensor):return bool(torch.isfinite(x).all())
    if isinstance(x,dict):return all(finite(v) for v in x.values())
    if isinstance(x,(list,tuple)):return all(finite(v) for v in x)
    if isinstance(x,float):return math.isfinite(x)
    return True


class Session:
    def __init__(self,identity,controls,*,restoring_on_cpu=False):
        init=validate_controls(identity,controls);self.identity=deepcopy(identity);self.controls=deepcopy(controls);self.config=deepcopy(identity['config'])
        self.model=scratch(self.config)
        require(signature(self.model)==init['model_signature'] and state_hash(self.model.state_dict())==init['initial_weights_sha256'],'Initialization is not exact deterministic scratch')
        self.device='cpu' if restoring_on_cpu else identity['device']
        if self.device=='mps':require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0' and torch.backends.mps.is_available(),'Native MPS without fallback required')
        self.model.to(self.device);self.optimizer=torch.optim.AdamW(self.model.parameters(),lr=self.config['learning_rate'],weight_decay=self.config['weight_decay'])
        self.step=0;self.dirty=False;self.history=[];self.evaluations=[];self.best=None
        self.cpu_rng=torch.Generator().manual_seed(self.config['seed']).get_state()
        self.mps_rng=None
        if self.device=='mps':
            old=torch.mps.get_rng_state();torch.mps.manual_seed(self.config['seed'])
            self.mps_rng=torch.mps.get_rng_state().cpu().clone();torch.mps.set_rng_state(old)

    def update(self,*args,**kwargs):raise ValueError('No external or real optimizer-input interface')

    def import_weights(self,*args,**kwargs):raise ValueError('Synthetic segmenter is fresh scratch only')

    def synthetic_update(self):
        require(not self.dirty,'Interrupted update: reload the last completed checkpoint')
        name,trace=next_member(self.config,self.step);x,y=checked_batch(*fixture(name,self.config['tensor_shape'][0]),self.config)
        self.dirty=True
        with self.rng_scope():
            self.model.train();self.optimizer.zero_grad(set_to_none=True)
            loss=objective(self.model(x.to(self.device)),y.to(self.device),self.config['loss_id']);require(torch.isfinite(loss).item(),'Nonfinite loss')
            loss.backward();require(all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in self.model.parameters()),'Invalid gradients')
            self.optimizer.step();require(finite(self.model.state_dict()) and finite(self.optimizer.state_dict()),'Nonfinite updated state')
            row=dict(completed_step=self.step+1,member_id=name,sampling=trace,loss=float(loss.detach().cpu()))
        self.history.append(row);self.step+=1;self.dirty=False;return deepcopy(row)

    @contextmanager
    def rng_scope(self):
        old=torch.get_rng_state();other=torch.mps.get_rng_state() if self.device=='mps' else None
        torch.set_rng_state(self.cpu_rng)
        if other is not None:torch.mps.set_rng_state(self.mps_rng)
        try:yield
        finally:
            self.cpu_rng=torch.get_rng_state().clone();torch.set_rng_state(old)
            if other is not None:
                self.mps_rng=torch.mps.get_rng_state().cpu().clone();torch.mps.set_rng_state(other)

    @torch.no_grad()
    def predict(self,image):
        require(not self.dirty,'Dirty transaction cannot infer')
        x=torch.as_tensor(image);require(x.device.type=='cpu' and x.dtype==torch.float32 and x.shape==(1,*self.config['tensor_shape']) and
            torch.isfinite(x).all().item() and x.min()>=0 and x.max()<=1,'Invalid image-only model input')
        self.model.eval();p=self.model(x[None].to(self.device)).softmax(1)[0].cpu()
        require(p.shape==(3,*self.config['tensor_shape']) and torch.isfinite(p).all() and torch.allclose(p.sum(0),torch.ones_like(p[0]),atol=1e-5,rtol=0),'Invalid three-class prediction')
        return p

    def evaluate(self):
        require(not self.dirty and (not self.evaluations or self.evaluations[-1]['step']<self.step),'Duplicate/out-of-order evaluation')
        rows=[]
        for name in NAMES:
            x,y=fixture(name,self.config['tensor_shape'][0]);p=self.predict(x)
            value=float(objective(torch.log(p.clamp_min(1e-20))[None],y[None],self.config['loss_id']));rows.append(dict(member_id=name,loss=value,metrics=metrics(p.argmax(0),y)))
        score=sum(r['metrics']['lesion']['dice'] for r in rows if r['metrics']['lesion']['dice'] is not None)/4
        r=dict(step=self.step,scope='synthetic_train_mechanics_not_validation_selection',mean_lesion_dice=score,cases=rows)
        self.evaluations.append(r)
        if self.best is None or score>self.best['mean_lesion_dice']:self.best=dict(step=self.step,mean_lesion_dice=score)
        return deepcopy(r)


def progress(s):
    return dict(schema_version='segmenter-progress-1',step=s.step,history=deepcopy(s.history),evaluations=deepcopy(s.evaluations),best=deepcopy(s.best),
        exposure={n:sum(r['member_id']==n for r in s.history) for n in NAMES},sampler=next_member(s.config,s.step)[1] if s.step<s.config['max_steps'] else dict(exhausted=True,completed_updates=s.step,policy=POLICY))


def validate_progress(p,c):
    require(set(p)=={'schema_version','step','history','evaluations','best','exposure','sampler'} and p['schema_version']=='segmenter-progress-1','Incomplete progress')
    step=p['step'];require(type(step)==int and 0<=step<=c['max_steps'] and len(p['history'])==step and finite(p),'Invalid committed progress')
    for k,row in enumerate(p['history']):
        name,trace=next_member(c,k)
        require(set(row)=={'completed_step','member_id','sampling','loss'} and row['completed_step']==k+1 and row['member_id']==name and row['sampling']==trace and type(row['loss'])==float and row['loss']>=0,'Sampler/update history differs')
    require(set(p['exposure'])==set(NAMES) and all(type(v)==int for v in p['exposure'].values()),'Exposure types differ')
    require(p['exposure']=={n:sum(r['member_id']==n for r in p['history']) for n in NAMES} and
        p['sampler']==(next_member(c,step)[1] if step<c['max_steps'] else dict(exhausted=True,completed_updates=step,policy=POLICY)),'Exposure/cursor differs')
    previous=-1;best=None
    for e in p['evaluations']:
        require(set(e)=={'step','scope','mean_lesion_dice','cases'} and type(e['step'])==int and previous<e['step']<=step and
            e['scope']=='synthetic_train_mechanics_not_validation_selection' and [r['member_id'] for r in e['cases']]==list(NAMES),'Evaluation history differs')
        previous=e['step']
        for r in e['cases']:
            require(set(r)=={'member_id','loss','metrics'} and r['loss']>=0 and finite(r),'Invalid evaluation')
            m=r['metrics'];x,y=fixture(r['member_id'],c['tensor_shape'][0]);expected=metrics(y,y)
            require(set(m)==set(expected),'Metric inventory differs')
            for n in ('background','pancreas_parenchyma','lesion','pancreas_lesion_union'):
                a=m[n];require(set(a)==set(expected[n]) and all(type(a[k])==int and a[k]>=0 for k in ('target_voxels','predicted_voxels','true_positive')) and a['target_voxels']==expected[n]['target_voxels'] and a['true_positive']<=min(a['target_voxels'],a['predicted_voxels']) and a['predicted_voxels']<=y.numel(),'Invalid metric counts')
                require(a['dice']==(2*a['true_positive']/(a['target_voxels']+a['predicted_voxels']) if a['target_voxels'] else None) and
                    a['recall']==(a['true_positive']/a['target_voxels'] if a['target_voxels'] else None),'Metric score/count mismatch')
            require(len(m['components'])==len(expected['components']) and all(set(a)=={'component_id','native_voxels','true_positive'} and a['component_id']==b['component_id'] and a['native_voxels']==b['native_voxels'] and type(a['true_positive'])==int and 0<=a['true_positive']<=a['native_voxels'] for a,b in zip(m['components'],expected['components'])),'Component accounting differs')
            require(sum(m[n]['predicted_voxels'] for n in ('background','pancreas_parenchyma','lesion'))==y.numel() and m['pancreas_lesion_union']['predicted_voxels']==m['pancreas_parenchyma']['predicted_voxels']+m['lesion']['predicted_voxels'] and m['pancreas_lesion_union']['true_positive']>=m['pancreas_parenchyma']['true_positive']+m['lesion']['true_positive'],'Class-count conservation differs')
            require(m['lesion_false_positive_fraction']==(m['lesion']['predicted_voxels']/y.numel() if not m['lesion']['target_voxels'] else None),'Negative metric differs')
        score=sum(r['metrics']['lesion']['dice'] for r in e['cases'] if r['metrics']['lesion']['dice'] is not None)/4
        require(type(e['mean_lesion_dice'])==float and e['mean_lesion_dice']==score,'Selection score differs')
        if best is None or score>best['mean_lesion_dice']:best=dict(step=e['step'],mean_lesion_dice=score)
    require(p['best']==best,'Best history reset/mismatch')


def payload(s):
    require(not s.dirty,'Incomplete optimizer transaction cannot checkpoint');validate_controls(s.identity,s.controls)
    require(s.config==s.identity['config'],'Session configuration changed')
    p=progress(s);validate_progress(p,s.config)
    state=cpu_tree(dict(schema_version='segmenter-state-1',identity_sha256=digest(canonical(s.identity)),step=s.step,
        model=s.model.state_dict(),optimizer=s.optimizer.state_dict(),cpu_rng=s.cpu_rng,mps_rng=s.mps_rng))
    stream=BytesIO();torch.save(state,stream);raw=stream.getvalue()
    files=dict(s.controls,**{'identity.json':canonical(s.identity),'progress.json':canonical(p),'state.pt':raw})
    validate_payload(files,s.identity);return files


def decode(files,i):
    import json
    validate_identity(i);require(set(files)==set(CONTROLS)|{'identity.json','progress.json','state.pt'} and files['identity.json']==canonical(i),'Checkpoint task/control inventory differs')
    controls={n:files[n] for n in CONTROLS};validate_controls(i,controls)
    p=json.loads(files['progress.json']);validate_progress(p,i['config']);state=torch.load(BytesIO(files['state.pt']),map_location='cpu',weights_only=True)
    require(set(state)=={'schema_version','identity_sha256','step','model','optimizer','cpu_rng','mps_rng'} and state['schema_version']=='segmenter-state-1' and state['identity_sha256']==digest(canonical(i)) and type(state['step'])==int and state['step']==p['step'] and finite(state),'Invalid state identity/step')
    restored=Session(i,controls,restoring_on_cpu=True);expected=restored.model.state_dict()
    require(set(state['model'])==set(expected) and all(isinstance(state['model'][n],torch.Tensor) and state['model'][n].shape==v.shape and state['model'][n].dtype==v.dtype for n,v in expected.items()),'Model inventory differs')
    if state['step']==0:require(state_hash(state['model'])==state_hash(expected),'Step0 weights differ from deterministic scratch')
    opt=state['optimizer'];standard=restored.optimizer.state_dict();require(set(opt)==set(standard) and opt['param_groups']==standard['param_groups'],'AdamW policy differs')
    ids=standard['param_groups'][0]['params'];require(set(opt['state'])==(set(ids) if state['step'] else set()),'Optimizer state inventory differs')
    for index,param in zip(ids,restored.model.parameters()):
        if state['step']:
            e=opt['state'][index];require(set(e)=={'step','exp_avg','exp_avg_sq'} and isinstance(e['step'],torch.Tensor) and e['step'].numel()==1 and e['step'].item()==state['step'] and all(isinstance(e[k],torch.Tensor) and e[k].shape==param.shape and e[k].dtype==param.dtype for k in ('exp_avg','exp_avg_sq')) and (e['exp_avg_sq']>=0).all(),'AdamW committed history differs')
    require(isinstance(state['cpu_rng'],torch.Tensor) and state['cpu_rng'].dtype==torch.uint8 and state['cpu_rng'].shape==torch.get_rng_state().shape,'Invalid CPU RNG')
    torch.Generator().set_state(state['cpu_rng'])
    mr=state['mps_rng'];require((i['device']=='cpu' and mr is None) or (i['device']=='mps' and isinstance(mr,torch.Tensor) and mr.dtype==torch.uint8 and mr.ndim==1 and 0<mr.numel()<=4096),'Invalid MPS RNG')
    restored.model.load_state_dict(state['model'],strict=True);restored.optimizer.load_state_dict(opt);restored.step=state['step']
    restored.history=p['history'];restored.evaluations=p['evaluations'];restored.best=p['best'];restored.cpu_rng=state['cpu_rng'];restored.mps_rng=mr
    return restored


def validate_payload(files,i):
    s=decode(files,i);return dict(task=TASK,step=s.step,identity_sha256=digest(canonical(i)),weights_sha256=state_hash(s.model.state_dict()),progress_sha256=digest(files['progress.json']))


def restore_payload(files,i):
    s=decode(files,i)
    if i['device']=='mps':
        restored=Session(i,s.controls);require(s.mps_rng.shape==restored.mps_rng.shape,'MPS RNG shape differs')
        restored.model.load_state_dict(s.model.state_dict());restored.optimizer.load_state_dict(s.optimizer.state_dict());restored.step=s.step
        restored.history=s.history;restored.evaluations=s.evaluations;restored.best=s.best;restored.cpu_rng=s.cpu_rng;restored.mps_rng=s.mps_rng;s=restored
    return s


def publish_checkpoint(store,s):
    files=payload(s);i=s.identity;validation=validate_payload(files,i);artifact_id=f"{i['run_id']}:step:{s.step}"
    derivation=digest(canonical(dict(identity=i,step=s.step)))
    metadata=dict(artifact_type='segmenter-checkpoint',schema_version='segmenter-synthetic-session-1',component=TASK,
        code_sha256=i['source_sha256'],parents=[i['geometry_sha256'],i['inputs_sha256']],retention='synthetic-recovery-keeper',sensitivity='synthetic',run_id=i['run_id'],stage_id='checkpoint')
    pin,status=store.publish(artifact_id,derivation_sha256=derivation,files=files,metadata=metadata,validate=lambda f:validate_payload(f,i))
    return dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation,step=s.step,status=status)


def resume(store,reference,i):
    require(reference['artifact_id']==f"{i['run_id']}:step:{reference['step']}" and reference['derivation_sha256']==digest(canonical(dict(identity=i,step=reference['step']))),'Wrong checkpoint reference')
    files,_=store.resolve(reference['artifact_id'],receipt_sha256=reference['receipt_sha256'],expected_derivation=reference['derivation_sha256'],validate=lambda f:validate_payload(f,i))
    s=restore_payload(files,i);require(s.step==reference['step'],'Restored step differs');return s
