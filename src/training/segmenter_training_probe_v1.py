"""Protected transaction probes and invented native-reference replay, separate from real evaluation."""
from io import BytesIO
import json
import numpy as np
import torch
from src.data import segmenter_geometry_v1 as geometry,segmenter_cache_v1 as cache
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training import segmenter_training_session_v1 as session,segmenter_inference_v1 as inverse,segmenter_native_scoring_v1 as scoring


def native_case(image):
    t=geometry.plan_geometry([512,402,197],np.diag([.78,.78,1.25,1.]),[[100,120,0],[281,261,81]],geometry.recipe(),source_identity=dict(study_id='invented-native-training-probe',ct_sha256=digest(b'invented_no_CT')),roi_origin='provided_pancreas_reference')
    return dict(study_id='invented-native-training-probe',protected_role='train',transform=t,transform_sha256=digest(canonical(t)),image_sha256=digest(cache.encode(image)))


def native_score(mask):
    pan=np.zeros((512,402,197),np.uint8);les=np.zeros_like(pan);pan[100:281,120:261,:81]=1;les[180:182,200:202,:2]=1;les[240:242,210:212,20:22]=1;les[280:283,200:202,40:42]=1
    r=scoring.score(mask,pan,les,target_state='positive');require(r['metrics']['lesion']['target_voxels']==28 and len(r['components'])==3 and r['outside_pancreas_voxels']==8,'Invented original-reference oracle');return r


def encode_weights(model):
    b=BytesIO();torch.save(session.numerical.cpu_tree(model.state_dict()),b);return b.getvalue()


def validate(files,identity):
    session.validate_identity(identity);size=identity['config']['tensor_shape'][0];steps=[0,2,3,6] if size==24 else [0,2,3];expected={'manifest.json','image.npy','next-weights.pt'}|{f'prob-{n}.npy' for n in steps}
    if size==144:expected|={'native-2.npy'}
    require(set(files)==expected and identity['domain']=='invented_arrays_only','Wrong probe inventory/domain');m=json.loads(files['manifest.json']);require(set(m)=={'task','identity_sha256','steps','checkpoints','next_weights_sha256','native_case','native_score'} and m['task']==session.TASK and m['identity_sha256']==digest(canonical(identity)) and m['steps']==steps and [p['primary']['step'] for p in m['checkpoints']]==steps,'Probe task/checkpoint scope')
    for ref in m['checkpoints']:require(ref['primary']['artifact_id']==f"{identity['run_id']}:step:{ref['primary']['step']}" and ref['primary']['derivation_sha256']==digest(canonical(dict(identity=identity,step=ref['primary']['step']))),'Probe cross-run checkpoint reference')
    image=inverse.decode_array(files['image.npy'],[1,size,size,size],'float32');require(np.isfinite(image).all() and image.min()>=0 and image.max()<=1,'Probe image dtype/range')
    for n in steps:
        p=inverse.decode_array(files[f'prob-{n}.npy'],[3,size,size,size],'float32');require(np.isfinite(p).all() and np.allclose(p.sum(0),1,atol=1e-5,rtol=0),'Probe probabilities')
    require(len(files['next-weights.pt'])<=32*1024**2,'Next-weight payload cap');weights=torch.load(BytesIO(files['next-weights.pt']),map_location='cpu',weights_only=True);fresh=session.scratch(identity['config']);expected_weights=fresh.state_dict();require(set(weights)==set(expected_weights) and all(isinstance(v,torch.Tensor) and v.shape==expected_weights[n].shape and v.dtype==expected_weights[n].dtype for n,v in weights.items()) and session.numerical.finite(weights) and session.numerical.state_hash(weights)==m['next_weights_sha256'],'Next-update weight identity/head')
    if size==144:
        case=native_case(image);require(case==m['native_case'],'Native probe geometry differs');p=inverse.decode_array(files['prob-2.npy'],[3,144,144,144],'float32');mask,report=inverse.export(p,case);require(cache.encode(mask)==files['native-2.npy'] and native_score(mask)==m['native_score'],'Native inverse/count/component probe differs')
    else:require(m['native_case'] is None and m['native_score'] is None,'CPU-sized probe cannot claim production native evaluation')
    return dict(task=session.TASK,identity_sha256=digest(canonical(identity)),probe_steps=steps,next_weights_sha256=m['next_weights_sha256'],members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})
