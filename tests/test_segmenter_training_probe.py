from copy import deepcopy
from io import BytesIO
import json
import numpy as np
import pytest
import torch
from src.training import segmenter_training_probe_v1 as p,segmenter_training_session_v1 as c
from src.data import segmenter_training_inputs_v1 as d,segmenter_cache_v1 as cache
from src.data.manifest_records import canonical,digest

@pytest.fixture
def evidence():
 provider=d.InventedInputs(24);ctx={n:canonical({'invented':n}) for n in ('source.json','environment.json','geometry.json')};ctx['lineage.json']=canonical(dict(checkpoint_inventory_sha256='a'*64,weight_imports_allowed=False,teacher_models=[],selected_import_sha256=None));i,ctrl=c.make_identity(c.config(size=24,steps=6),provider,ctx,run_id='segmenter-training-probe-test',device='cpu');steps=[0,2,3,6];refs=[dict(primary=dict(step=n,artifact_id=f"{i['run_id']}:step:{n}",derivation_sha256=digest(canonical(dict(identity=i,step=n))),receipt_sha256='b'*64),backup={}) for n in steps];model=c.scratch(i['config']);weights=p.encode_weights(model);image=provider.get('invented-train-1',role='train',operation='inference').image;prob=np.full((3,24,24,24),1/3,np.float32);m=dict(task=c.TASK,identity_sha256=digest(canonical(i)),steps=steps,checkpoints=refs,next_weights_sha256=c.numerical.state_hash(model.state_dict()),native_case=None,native_score=None);files={'manifest.json':canonical(m),'image.npy':cache.encode(image),'next-weights.pt':weights}|{f'prob-{n}.npy':cache.encode(prob) for n in steps};return files,i

def test_closed_probe_inventory_valid(evidence):assert p.validate(*evidence)['probe_steps']==[0,2,3,6]
@pytest.mark.parametrize('fault',['missing','extra','task','run','progress','next_hash','probability','shape','head','native_claim','image_range'])
def test_protected_probe_forgery_refused(evidence,fault):
 files,i=deepcopy(evidence);m=json.loads(files['manifest.json'])
 if fault=='missing':files.pop('prob-2.npy')
 if fault=='extra':files['unknown']=b'x'
 if fault=='task':m['task']='localizer'
 if fault=='run':m['checkpoints'][0]['primary']['artifact_id']='other:step:0'
 if fault=='progress':m['steps']=[0,2,4,6]
 if fault=='next_hash':m['next_weights_sha256']='0'*64
 if fault=='probability':files['prob-2.npy']=cache.encode(np.full((3,24,24,24),np.nan,np.float32))
 if fault=='shape':files['prob-2.npy']=cache.encode(np.full((3,16,16,16),1/3,np.float32))
 if fault=='head':
  state=torch.load(BytesIO(files['next-weights.pt']),weights_only=True);state['conv_final.2.conv.weight']=state['conv_final.2.conv.weight'][:2];b=BytesIO();torch.save(state,b);files['next-weights.pt']=b.getvalue()
 if fault=='native_claim':m['native_score']={'invented':True}
 if fault=='image_range':files['image.npy']=cache.encode(np.full((1,24,24,24),2,np.float32))
 files['manifest.json']=canonical(m)
 with pytest.raises(ValueError):p.validate(files,i)

@pytest.mark.parametrize('fault',['approval','quota','area','real_updates'])
def test_qualification_storage_scope_closed(fault):
 from src.operations.segmenter_training_storage_v1 import run_stores
 from scripts.diagnostics import segmenter_training_qualification as cli
 cap=json.loads(cli.CAP.read_bytes())
 if fault=='approval':cap['approval']='D-325'
 if fault=='quota':cap['max_new_bytes_per_domain']+=1
 if fault=='area':cap['primary_area']='segmenter-runs'
 if fault=='real_updates':cap['real_optimizer_updates_allowed']=True
 raw=canonical(cap)
 with pytest.raises(ValueError):run_stores(cli.REPO/'configs/local/roots.yaml',raw,trusted_capability_sha256=digest(raw))
