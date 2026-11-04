import copy,json
import numpy as np
import pytest
import torch
from src.training.verifier_session_20261031 import Session,Dataset
from src.training.experiment_config import sha256

class TinyDataset:
    pin='synthetic-only'
    fit=list(range(5));weights={i:1. for i in range(5)}
    def get(self,i,operation):
        assert operation=='optimizer'
        return np.full((2,4,16,16,16),i/5,np.float32),np.ones(4,np.float32),float(i%2)

def test_actual_network_update_and_exact_cpu_restore(tmp_path):
    torch.set_num_threads(2);d=TinyDataset();s=Session(d,device='cpu',batch_size=2)
    for _ in range(4):s.update()
    path=tmp_path/'checkpoint.pt';torch.save(s.state(),path)
    expected=s.update();state=copy.deepcopy(s.model.state_dict())
    r=Session.restore(torch.load(path,weights_only=True),d,device='cpu');actual=r.update()
    assert expected==actual and all(torch.equal(state[k],r.model.state_dict()[k]) for k in state)
    assert r.epoch==1 and r.position==4

def test_restore_identity_refused():
    with pytest.raises(ValueError,match='identity'):Session.restore(dict(dataset_sha256='different'),TinyDataset(),'cpu')

def test_patient_weights_and_role_gates(tmp_path):
    rows=[dict(case_id=n,component_id=i,role=role) for i,(n,role) in enumerate([('a','verifier_fit'),('a','verifier_fit'),('b','verifier_fit'),('t','verifier_tune')])]
    p=tmp_path/'manifest.json';p.write_text(json.dumps(dict(status='QUALIFIED_FIT_TUNE_VIEWS',candidates=rows,patients=dict(verifier_fit=['a','b'],verifier_tune=['t']))))
    d=Dataset(p,sha256(p));assert sum(d.weights[i] for i in (0,1))==d.weights[2]
    with pytest.raises(ValueError,match='Protected'):d.get(3,'optimizer')
    with pytest.raises(ValueError,match='Protected'):d.get(0,'tune')

def test_bad_role_manifest_rejected(tmp_path):
    p=tmp_path/'manifest.json';p.write_text(json.dumps(dict(status='QUALIFIED_FIT_TUNE_VIEWS',candidates=[],patients=dict(verifier_fit=['same'],verifier_tune=['same']))))
    with pytest.raises(ValueError):Dataset(p,sha256(p))
