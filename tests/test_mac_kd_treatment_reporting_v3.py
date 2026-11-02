import json
import numpy as np
from scripts.diagnostics.qualify_mac_kd_treatment_v3 import exercise


class Session:
    identity={'invented':True}
    def __init__(self,state=None):self.counter=state['counter'] if state else 0
    def state(self):return {'counter':self.counter}


def test_numpy_update_metadata_survives_producer_and_cold(tmp_path):
    for name in ('producer','cold'):(tmp_path/name).mkdir()
    request={'backup':str(tmp_path/'backup')}
    def update(s):
        s.counter+=1
        return dict(step=s.counter,batch_sha256={'image':'invented'},member_id='A',
                    learning_rate=np.float32(.125),kd_weight=np.float32(.25),
                    teacher_accessed=True,augmentation={'scale':np.float32(1.125)})
    def compare(a,b):assert a==b
    for stage in ('producer','cold'):
        exercise(tmp_path,stage,request,None,lambda state,identity:Session(state),update,compare,lambda:None,lambda size:None)
        result=json.loads((tmp_path/stage/'result.json').read_text())
        assert result['success'] and result['scientific_updates']==0
    rows=json.loads((tmp_path/'producer/updates.json').read_text())
    assert rows[1]['augmentation']['scale']==1.125
    assert json.loads((tmp_path/'cold/updates.json').read_text())[0]==rows[1]
