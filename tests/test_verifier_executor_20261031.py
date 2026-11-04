import json
from types import SimpleNamespace
from src.training.verifier_executor_20261031 import execute

class Fake:
    step=0;epoch=0;lr=.001;dataset=SimpleNamespace(pin='fake')
    def update(self):
        self.step+=1;self.epoch+=1
        return dict(loss=.5,gradient_norm=1.,input_sha256='input')
    def evaluate(self):return dict(patient_balanced_bce={1:.4,2:.3,3:.35}[self.epoch],candidate_patients=2)
    def state(self):return dict(step=self.step)

def test_checkpoint_selection_backup_and_journal(tmp_path):
    saved=[];tracked=[];s=Fake();r=execute(s,tmp_path/'out',epochs=3,backup=lambda p:saved.append(p.name),track=tracked.append)
    assert r['selected']['epoch']==2 and r['completed_updates']==3
    assert saved==['initial.pt','selected-epoch-001.pt','selected-epoch-002.pt','terminal.pt','result.json','history.jsonl']
    assert tracked[-1]['event']=='completed' and r['calibration_cases_evaluated']==0

def test_failure_preserved(tmp_path):
    import pytest
    class Broken(Fake):
        def update(self):raise ValueError('deliberate')
    with pytest.raises(ValueError):execute(Broken(),tmp_path/'out')
    events=[json.loads(l) for l in (tmp_path/'out/history.jsonl').read_text().splitlines()]
    assert events[-1]['event']=='failed' and 'deliberate' in events[-1]['message']
