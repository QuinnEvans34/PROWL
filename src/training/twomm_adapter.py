"""Versioned 144-cube mechanics, with processed-grid sampling and reversible padding.

No optimizer/launch interface. Callers must bind a future run to its qualified cache.
"""
from copy import deepcopy
import hashlib
import math
import torch
import torch.nn.functional as F
from src.data.source_inventory_records import require
from src.training.localizer import validate_config as old_config


def validate_config(c):
    tail=c.get('schema_version')=='twomm-adapter-3';parented=c.get('schema_version') in ('twomm-adapter-4','twomm-adapter-5','twomm-adapter-6')
    require(set(c)=={'schema_version','patch_size','seed','learning_rate','weight_decay','max_steps','loss_id'}|({'schedule'} if tail else {'parent_steps'} if parented else set()),'Adapter config fields differ')
    require(c['schema_version'] in ('twomm-adapter-1','twomm-adapter-2','twomm-adapter-3','twomm-adapter-4','twomm-adapter-5','twomm-adapter-6') and c['patch_size']==[144]*3 and all(type(n)==int for n in c['patch_size']),'Wrong adapter/patch version')
    require(c['loss_id']==({'twomm-adapter-5':'class_mean_25_75_ce_dice_v1','twomm-adapter-6':'class_mean_37_5_62_5_ce_dice_v1'}.get(c['schema_version'],'balanced_ce_dice_v1')),'Wrong objective')
    base={k:v for k,v in c.items() if k not in ('schema_version','schedule','parent_steps')};base['patch_size']=[96]*3
    if c['schema_version'] in ('twomm-adapter-5','twomm-adapter-6'):base['loss_id']='balanced_ce_dice_v1'  # Reuse scalar bounds only; legacy loss dispatch stays closed.
    if c['schema_version'] in ('twomm-adapter-2','twomm-adapter-3','twomm-adapter-4','twomm-adapter-5','twomm-adapter-6'):
        require(type(c['max_steps']) is int and 1<=c['max_steps']<=(300 if parented else 600 if tail else 1200),'Invalid extended step budget')
        base['max_steps']=min(c['max_steps'],300)
    if parented:require(type(c['parent_steps']) is int and 0<c['parent_steps']<=300,'Invalid parent sampler offset')
    if tail:
        from src.training.twomm_tail_schedule import validate
        validate(c['schedule'],c)
    old_config(base)  # Version 1 retains its <=300 ceiling; version 2 is separately bounded.


def image_tensor(image):
    x=image.as_tensor() if hasattr(image,'as_tensor') else torch.as_tensor(image)
    require(x.device.type=='cpu' and x.dtype==torch.float32 and x.ndim==4 and x.shape[0]==1 and 0<math.prod(x.shape[1:])<=16_000_000,'Invalid bounded image')
    require(torch.isfinite(x).all().item() and x.min()>=0 and x.max()<=1,'Invalid normalized image')
    return x


def pad_image(image,config):
    validate_config(config);x=image_tensor(image);shape=list(x.shape[1:]);pads=[max(0,144-n) for n in shape]
    require(math.prod([s+n for s,n in zip(shape,pads)])<=16_000_000,'Temporary padding voxel cap')
    pad=[v for n in reversed(pads) for v in (n//2,n-n//2)]
    trace=dict(schema_version='twomm-padding-1',original_shape=shape,padding=pad,padded_shape=[s+n for s,n in zip(shape,pads)])
    return F.pad(x,tuple(pad)),trace


def remove_padding(values,trace):
    require(set(trace)=={'schema_version','original_shape','padding','padded_shape'} and trace['schema_version']=='twomm-padding-1','Invalid padding trace')
    shape=trace['original_shape'];require(len(shape)==3 and all(type(n)==int and n>0 for n in shape) and math.prod(shape)<=16_000_000,'Invalid original shape')
    pads=[max(0,144-n) for n in shape];pad=[v for n in reversed(pads) for v in (n//2,n-n//2)]
    require(trace['padding']==pad and trace['padded_shape']==[s+n for s,n in zip(shape,pads)],'Padding trace changed')
    require(values.ndim==4 and list(values.shape[1:])==trace['padded_shape'],'Wrong padded prediction grid')
    slices=tuple(slice(n//2,n//2+s) for s,n in zip(shape,pads))
    return values[(slice(None),)+slices].clone()


def patch_batch(item,config,*,step):
    validate_config(config)
    require(item['operation']=='optimizer' and item['descriptor']['operation']=='optimizer' and item['descriptor']['protected_role']=='train','Validation cannot reach optimizer sampler')
    member=item['study_id'];require(member==item['descriptor']['study_id'] and isinstance(member,str) and member,'Member identity differs')
    offset=config.get('parent_steps',0)
    require(type(step)==int and offset<=step<offset+config['max_steps'],'Step budget exhausted')
    x=image_tensor(item['image']);y=torch.as_tensor(item['label']);require(y.device.type=='cpu' and y.shape==x.shape and torch.all((y==0)|(y==1)).item(),'Invalid target')
    seed=int.from_bytes(hashlib.sha256(f"{config['seed']}:{step}:{member}".encode()).digest()[:8],'little');rng=torch.Generator().manual_seed(seed)
    positive=bool(torch.rand((),generator=rng)<.5)
    # Choose centers before extra patch padding. Existing preprocessing padding remains eligible.
    coords=torch.nonzero(y[0]==int(positive),as_tuple=False)
    if not len(coords):positive=not positive;coords=torch.nonzero(y[0]==int(positive),as_tuple=False)
    center=coords[torch.randint(len(coords),(1,),generator=rng).item()].tolist()
    x,padding=pad_image(x,config);y=F.pad(y,tuple(padding['padding']));offset=[padding['padding'][i] for i in (4,2,0)]
    pc=[a+b for a,b in zip(center,offset)];origin=[max(0,min(c-72,s-144)) for c,s in zip(pc,x.shape[1:])];slices=tuple(slice(a,a+144) for a in origin)
    trace=dict(member_id=member,step=step,policy='processed_grid_pancreas_background_equal_v2',center_original_grid=center,center_class=int(positive),origin_padded_grid=origin,padding=padding)
    return x[(slice(None),)+slices][None].clone(),y[(slice(None),)+slices][None].long().clone(),deepcopy(trace)
