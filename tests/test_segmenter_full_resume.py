"""Continuation checks on invented arrays; native check is explicitly opted in."""
from copy import deepcopy
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import torch

from test_segmenter_full import Invented, config, session
from src.training.segmenter_full_executor_v1 import execute
from src.training.segmenter_full_resume_v1 import read_checkpoint, restore_checkpoint
from src.training.segmenter_full_session_v1 import Session


def test_session_configuration_remains_identity_bound():
    p=Invented();s=session(p)
    s.config['learning_rate']=.5
    with pytest.raises(ValueError,match='changed'):s.state()


@pytest.fixture
def interrupted(tmp_path):
    torch.set_num_threads(2)
    p = Invented(); s = session(p, 4)
    class TransportStop(Exception): pass
    def stop(path):
        if path.name == 'last.pt' and s.step == 2: raise TransportStop()
    with pytest.raises(TransportStop):
        execute(s, p, tmp_path/'parent', validate_every=2, checkpoint_every=2, checkpoint_hook=stop)
    path = tmp_path/'parent/last.pt'
    cfg = dict(full_segmenter=dict(session={k:v for k,v in s.config.items() if k!='max_steps'}),
        device='cpu', _experiment=dict(run=dict(max_updates=4), initialization={'kind':'scratch'}))
    resume = dict(checkpoint=str(path), checkpoint_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return cfg, p, s, resume


def test_continuation_retains_parent_and_best(interrupted, tmp_path):
    cfg,p,live,resume = interrupted
    parent = Path(resume['checkpoint']).parent/'history.jsonl'; original = parent.read_bytes()
    restored,best,provenance = restore_checkpoint(cfg,p.control,**resume)
    assert restored.step == 2 and restored.next_member() == live.next_member()
    assert live.update(p) == restored.update(p)
    for k,v in live.model.state_dict().items(): assert torch.equal(v,restored.model.state_dict()[k])
    result = execute(restored,p,tmp_path/'continued',validate_every=2,checkpoint_every=2,
        initial_best=1.,continuation=provenance)
    assert result == dict(completed_updates=4,best_development_dice=1.)
    assert not (tmp_path/'continued/best.pt').exists()
    assert parent.read_bytes() == original
    rows=[json.loads(x) for x in (tmp_path/'continued/history.jsonl').read_text().splitlines()]
    assert rows[1]['event']=='resumed' and rows[1]['step']==3
    assert [r['step'] for r in rows if r['event']=='update']==[4]


@pytest.mark.parametrize('change', ['hash','cohort','horizon','journal','best'])
def test_incompatible_resume_refused(interrupted, change):
    cfg,p,live,resume = interrupted
    if change=='hash':resume['checkpoint_sha256']='0'*64
    elif change=='cohort':p.control['train']=list(reversed(p.control['train']))
    elif change=='horizon':cfg['_experiment']['run']['max_updates']=5
    elif change=='journal':(Path(resume['checkpoint']).parent/'history.jsonl').write_text('truncated')
    else:
        path=Path(resume['checkpoint']);state=torch.load(path,weights_only=True)
        state['best_score']=.999;torch.save(state,path)
        resume['checkpoint_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):read_checkpoint(cfg,p.control,**resume)


@pytest.mark.skipif(os.environ.get('PROWL_NATIVE_RESUME_TEST')!='1',reason='Explicit native qualification only')
def test_fresh_process_mps_optimizer_continuation(tmp_path):
    import numpy as np
    from src.data.segmenter_training_inputs_v1 import Batch, _TOKEN
    from src.data.manifest_records import canonical,digest
    class Native(Invented):
        def __init__(self):
            super().__init__()
            self.x=np.zeros((1,144,144,144),np.float32);self.y=np.zeros((144,144,144),np.uint8)
            self.y[35:105,35:105,35:105]=1;self.y[65:78,65:78,65:78]=2;self.x[0]=self.y/2
    p=Native();c=config();c['tensor_shape']=[144]*3
    s=Session(c,p.control,device='mps',initialization={'kind':'scratch'})
    s.update(p);saved=s.state();torch.save(saved,tmp_path/'before.pt')
    left=s.update(p);expected=s.state();torch.save(expected,tmp_path/'expected.pt')
    del s;gc.collect();torch.mps.empty_cache()
    # Independently construct the provider/model/optimizer in a fresh native process.
    code='''
import sys,json,numpy as np,torch
from pathlib import Path
from src.training.segmenter_full_session_v1 import Session
from src.data.segmenter_training_inputs_v1 import Batch,_TOKEN
from src.data.manifest_records import canonical,digest
p=Path(sys.argv[1]);state=torch.load(p/'before.pt',map_location='cpu',weights_only=True)
class Provider:
 control=state['identity']['control']
 def get(self,name,*,role,operation):
  y=np.zeros((144,144,144),np.uint8);y[35:105,35:105,35:105]=1;y[65:78,65:78,65:78]=2
  x=(y.astype(np.float32)/2)[None]
  return Batch(_TOKEN,study_id=name,role=role,operation=operation,image=x,target=y,control_sha256=digest(canonical(self.control)))
s=Session.restore(state,state['identity']);torch.save(s.state(),p/'restored.pt')
row=s.update(Provider());torch.save(s.state(),p/'after.pt');(p/'row.json').write_text(json.dumps(row))
'''
    subprocess.run([sys.executable,'-c',code,str(tmp_path)],check=True,timeout=90)
    recovered=torch.load(tmp_path/'restored.pt',weights_only=True)
    after=torch.load(tmp_path/'after.pt',weights_only=True)
    max_error=[0.]
    def compare(a,b,exact):
        if isinstance(a,torch.Tensor):
            if exact:assert torch.equal(a,b)
            else:
                # PyTorch's float32 comparison tolerances; restoration above remains exact.
                # Native next-update arithmetic is not certified bitwise deterministic.
                torch.testing.assert_close(a,b,rtol=1.3e-6,atol=1e-5)
                if a.numel():max_error[0]=max(max_error[0],float((a-b).abs().max()))
        elif isinstance(a,dict):
            assert set(a)==set(b)
            for k in a:compare(a[k],b[k],exact)
        elif isinstance(a,(list,tuple)):
            assert len(a)==len(b)
            for x,y in zip(a,b):compare(x,y,exact)
        else:assert a==b
    compare(saved,recovered,True);compare(expected,after,False)
    right=json.loads((tmp_path/'row.json').read_text())
    assert left['member_id']==right['member_id'] and left['batch_sha256']==right['batch_sha256']
    assert left['loss']==pytest.approx(right['loss'],rel=1.3e-6,abs=1e-5)
    print(json.dumps(dict(native_restore_state_exact=True,next_update_max_abs_error=max_error[0],
        rtol=1.3e-6,atol=1e-5,invented_updates=3,source_payloads=0)))
