"""Closed scratch step-0 image-only transaction; no training or weight import API."""
from copy import deepcopy
from io import BytesIO
import json
import math
import numpy as np
import torch
import nibabel as nib
from src.models.segresnet import build_model
from src.training.segmenter_session_v1 import ARCH,state_hash,signature
from src.data import segmenter_cache_v1 as cache,segmenter_geometry_v1 as geometry
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require,content_hash

TASK='pancreas_lesion_segmenter_step0_inference_v1'
CONFIG=dict(task=TASK,seed=42,architecture=deepcopy(ARCH),tensor_shape=[144]*3,precision='float32',completed_updates=0,weight_import_allowed=False,optimizer_allowed=False)


def scratch():
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(CONFIG['seed']);return build_model({'model':CONFIG['architecture']})


def array_bytes(a):return cache.encode(np.ascontiguousarray(a))


def decode_array(raw,shape,dtype):
    """Verify allocation header and exact bytes before allocating any native grid."""
    require(isinstance(raw,bytes) and all(type(n)==int and n>0 for n in shape) and math.prod(shape)<=3*geometry.MAX_SOURCE,'Array envelope')
    b=BytesIO(raw);require(np.lib.format.read_magic(b)==(1,0),'Wrong array encoding')
    actual,fortran,kind=np.lib.format.read_array_header_1_0(b,max_header_size=512)
    require(actual==tuple(shape) and kind==np.dtype(dtype) and fortran is False and len(raw)==b.tell()+math.prod(shape)*kind.itemsize,'Changed array shape/dtype/order/length')
    return np.load(BytesIO(raw),allow_pickle=False)


def probabilities(p):
    require(p.dtype==np.float32 and p.shape==(3,144,144,144) and np.isfinite(p).all() and p.min()>=0 and p.max()<=1 and np.allclose(p.sum(0),1,rtol=0,atol=1e-4),'Wrong three-class probabilities')
    return p


def make_identity(cases,context,*,run_id,domain):
    require(domain in ('invented_profile','qualified_cache'),'Wrong inference domain')
    require(set(context)=={'source','environment','ancestry'},'Context inventory differs')
    require(isinstance(cases,list) and 0<len(cases)<=7 and len({e['study_id'] for e in cases})==len(cases),'Case inventory')
    for e in cases:
        require(set(e)=={'study_id','protected_role','transform','transform_sha256','image_sha256'},'Input fields differ')
        require(e['protected_role'] in ('train','validation'),'Input role')
        geometry.validate_record(e['transform'],e['transform_sha256'])
        require(e['transform']['tensor_shape']==[144]*3 and e['transform']['source_identity']['study_id']==e['study_id'],'Input transform lineage')
    m=scratch()
    return dict(schema_version='segmenter-step0-identity-1',task=TASK,run_id=run_id,domain=domain,config=deepcopy(CONFIG),cases=deepcopy(cases),context=deepcopy(context),source_sha256=content_hash(context['source']),initial_weight_sha256=state_hash(m.state_dict()),signature=signature(m))


def checked_identity(identity):
    require(identity==make_identity(identity['cases'],identity['context'],run_id=identity['run_id'],domain=identity['domain']),'Non-scratch/wrong task identity')


class Session:
    def __init__(self,identity,*,device='cpu'):
        checked_identity(identity);require(device in ('cpu','mps'),'Device envelope')
        self.identity=deepcopy(identity);self.model=scratch().to(device).eval();self.device=device
        self.model.requires_grad_(False)

    def step(self,*_args,**_kwargs):raise ValueError('Optimizer closed for inference-only task')
    def import_weights(self,*_args,**_kwargs):raise ValueError('All weight imports closed')

    def predict(self,item):
        require(set(item)=={'image','study_id','protected_role','transform','transform_sha256'},'Image-only input required')
        matches=[e for e in self.identity['cases'] if e['study_id']==item['study_id'] and e['protected_role']==item['protected_role']]
        require(len(matches)==1,'Held/absent/wrong-role input');e=matches[0]
        require(item['transform']==e['transform'] and item['transform_sha256']==e['transform_sha256'],'Transform drift')
        x=item['image'];require(digest(array_bytes(x))==e['image_sha256'],'Changed image bytes')
        cache.decode(array_bytes(x),'image')
        require(state_hash(self.model.state_dict())==self.identity['initial_weight_sha256'],'Mutated scratch weights')
        with torch.inference_mode():
            y=self.model(torch.from_numpy(np.array(x,copy=True))[None].to(self.device))
            require(y.shape==(1,3,144,144,144) and torch.isfinite(y).all().item(),'Three-class head confusion/nonfinite logits')
            p=y.softmax(1)[0].cpu().numpy()
        if self.device=='mps':torch.mps.synchronize()
        require(state_hash(self.model.state_dict())==self.identity['initial_weight_sha256'],'Forward mutated weights')
        return probabilities(p)


def export(p,case,*,tick=lambda:None):
    probabilities(p);t=case['transform'];pin=case['transform_sha256'];geometry.validate_record(t,pin)
    restored=geometry.restore_probabilities(p,t,trusted_record_sha256=pin,tick=tick)
    codes=restored.argmax(0).astype(np.uint8);del restored
    report=dict(study_id=case['study_id'],protected_role=case['protected_role'],source_shape=t['source_shape'],source_affine=t['source_affine'],transform_sha256=pin,image_sha256=case['image_sha256'],probability_sha256=digest(array_bytes(p)),native_sha256=digest(array_bytes(codes)),class_counts=np.bincount(codes.ravel(),minlength=3).tolist(),inverse='continuous_three_channel_then_argmax',outside_roi='background',completed_updates=0,native_reference_metrics='not_scored')
    validate_export(array_bytes(codes),report,case)
    return codes,report


def validate_export(raw,report,case):
    t=case['transform'];geometry.validate_record(t,case['transform_sha256'])
    require(set(report)=={'study_id','protected_role','source_shape','source_affine','transform_sha256','image_sha256','probability_sha256','native_sha256','class_counts','inverse','outside_roi','completed_updates','native_reference_metrics'},'Export fields differ')
    require(all(report[k]==case[k] for k in ('study_id','protected_role','transform_sha256','image_sha256')) and report['source_shape']==t['source_shape'] and report['source_affine']==t['source_affine'],'Export source/role differs')
    require(report['native_sha256']==digest(raw) and report['inverse']=='continuous_three_channel_then_argmax' and report['outside_roi']=='background' and type(report['completed_updates']) is int and report['completed_updates']==0 and report['native_reference_metrics']=='not_scored','Export bytes/task differs')
    require(isinstance(report['probability_sha256'],str) and len(report['probability_sha256'])==64,'Missing probability pin')
    a=decode_array(raw,t['source_shape'],'uint8');require(np.isin(a,[0,1,2]).all() and np.bincount(a.ravel(),minlength=3).tolist()==report['class_counts'],'Export class counts differ')
    # Six outside slabs avoid a full-volume boolean allocation. No foreground/component cap.
    oriented=nib.orientations.apply_orientation(a,np.asarray(t['orientation_forward']))
    lo,hi=t['box_ras_half_open']
    for axis in range(3):
        s=[slice(None)]*3;s[axis]=slice(0,lo[axis]);require(not oriented[tuple(s)].any(),'Foreground outside ROI')
        s[axis]=slice(hi[axis],None);require(not oriented[tuple(s)].any(),'Foreground outside ROI')
    return a


def payload(session,probe_image,probe_prob,exports):
    state={n:v.detach().cpu() for n,v in session.model.state_dict().items()};s=BytesIO();torch.save(dict(task=TASK,completed_updates=0,weights=state),s)
    files={'identity.json':canonical(session.identity),'state.pt':s.getvalue(),'probe-image.npy':array_bytes(probe_image),'probe-probabilities.npy':array_bytes(probe_prob),'exports.json':canonical([r for _,r in exports])}
    files.update({f'case-{i:02d}-native.npy':array_bytes(a) for i,(a,_) in enumerate(exports)})
    validate_payload(files,session.identity);return files


def validate_payload(files,identity):
    checked_identity(identity);expected={'identity.json','state.pt','probe-image.npy','probe-probabilities.npy','exports.json'}|{f'case-{i:02d}-native.npy' for i in range(len(identity['cases']))}
    require(set(files)==expected and files['identity.json']==canonical(identity),'Checkpoint/control inventory differs')
    require(len(files['state.pt'])<=96*1024**2,'Weight serialization cap')
    value=torch.load(BytesIO(files['state.pt']),map_location='cpu',weights_only=True)
    require(set(value)=={'task','completed_updates','weights'} and value['task']==TASK and type(value['completed_updates']) is int and value['completed_updates']==0,'Wrong task/progress or optimizer state')
    fresh=scratch();require(signature(fresh)=={n:dict(shape=list(v.shape),dtype=str(v.dtype)) for n,v in value['weights'].items()} and all(torch.isfinite(v).all().item() for v in value['weights'].values()) and state_hash(value['weights'])==identity['initial_weight_sha256'],'Imported/trained/mutated state refused')
    im=cache.decode(files['probe-image.npy'],'image');require(digest(files['probe-image.npy'])==identity['cases'][0]['image_sha256'],'Probe image differs')
    probabilities(decode_array(files['probe-probabilities.npy'],[3,144,144,144],'float32'))
    rows=json.loads(files['exports.json']);require(len(rows)==len(identity['cases']) and rows[0]['probability_sha256']==digest(files['probe-probabilities.npy']),'Probe/export identity differs')
    for i,(r,e) in enumerate(zip(rows,identity['cases'])):validate_export(files[f'case-{i:02d}-native.npy'],r,e)
    return dict(task=TASK,completed_updates=0,identity_sha256=content_hash(identity),initial_weight_sha256=identity['initial_weight_sha256'],members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})


def recover_probe(files,identity,*,device='mps',tick=lambda:None):
    validate_payload(files,identity);s=Session(identity,device=device)
    item=dict(identity['cases'][0]);item.pop('image_sha256');item['image']=cache.decode(files['probe-image.npy'],'image')
    p=s.predict(item);expected=decode_array(files['probe-probabilities.npy'],[3,144,144,144],'float32');delta=float(np.max(np.abs(p-expected)))
    require(delta<=1e-6,'Restored prediction differs');a,_=export(p,identity['cases'][0],tick=tick)
    require(array_bytes(a)==files['case-00-native.npy'],'Restored continuous native inverse differs')
    return dict(prediction_max_abs_difference=delta,native_mask_exact=True,weight_sha256=state_hash(s.model.state_dict()),completed_updates=0)
