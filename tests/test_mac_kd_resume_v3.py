import json
import numpy as np
import torch
import pytest
from scripts.diagnostics.qualify_mac_kd_resume_v3 import exercise
from scripts.diagnostics.pause_mac_kd_resume_v3 import request
from src.data.segmenter_teacher_cache_v1 import sha
from scripts import resume_mac_kd_treatment_v3 as m

class Session:
    identity={'invented':True}
    def __init__(self,state):self.counter=state['counter']
    def state(self):return {'counter':self.counter}

def test_real_restore_protocol_and_numpy_metadata(tmp_path):
    for name in ('producer','cold'):(tmp_path/name).mkdir()
    initial=tmp_path/'initial.pt';torch.save({'session':{'counter':472}},initial)
    context={'checkpoint':str(initial),'identity':Session.identity}
    def update(s):
        s.counter+=1
        return dict(step=s.counter,batch_sha256={'image':'synthetic'},member_id='A',learning_rate=np.float32(.1),kd_weight=np.float32(.0473),teacher_accessed=True)
    def compare(a,b):assert a==b
    for stage in ('producer','cold'):
        exercise(tmp_path,stage,{'backup':str(tmp_path/'backup')},context,lambda state,identity:Session(state),update,compare,lambda:None,lambda size:None)
    rows=json.loads((tmp_path/'producer/updates.json').read_text())
    assert [r['step'] for r in rows]==[473,474]
    assert json.loads((tmp_path/'cold/updates.json').read_text())==[rows[1]]

def test_new_pause_identity_and_binding(tmp_path):
    f=tmp_path/'ready.json';f.write_text(json.dumps({'version':'mac-kd-treatment-resume-3'}))
    pin=sha(f)
    assert request(tmp_path,pin)['cleanup_verified'] is False
    assert m.pause_requested(tmp_path,pin)
    with pytest.raises(ValueError):m.pause_requested(tmp_path,'wrong')
    f.write_text(json.dumps({'version':'mac-kd-reviewed-treatment-launch-2'}))
    with pytest.raises(ValueError):request(tmp_path,sha(f))
