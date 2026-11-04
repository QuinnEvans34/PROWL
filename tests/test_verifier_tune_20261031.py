import copy
import numpy as np
import torch
from src.training.verifier_session_20261031 import Session
from scripts.diagnostics.qualify_verifier_20261031 import equal

class Inputs:
    pin='synthetic';fit=[0];weights={0:1.};tune=[1,2,3]
    rows=[{},dict(case_id='a',component_id=1),dict(case_id='a',component_id=2),dict(case_id='b',component_id=1)]
    def get(self,i,operation):
        assert operation=='tune'
        return np.full((2,4,16,16,16),i/5,np.float32),np.ones(4,np.float32),float(i%2)

def test_real_tune_path_patient_balance_and_state_unchanged():
    torch.set_num_threads(2);d=Inputs();s=Session(d,device='cpu');before=copy.deepcopy(s.state())
    result=s.evaluate();assert equal(before,s.state())
    scores=np.asarray([r['score'] for r in result['scores']]);truth=np.array([1,0,1])
    losses=-(truth*np.log(scores)+(1-truth)*np.log(1-scores))
    expected=(losses[:2].mean()+losses[2])/2
    assert abs(result['patient_balanced_bce']-expected)<1e-6
    assert result['candidate_patients']==2 and len(scores)==3
