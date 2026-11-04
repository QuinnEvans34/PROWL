import pytest
from scripts import train_verifier_20261031 as launch
from scripts.diagnostics.qualify_verifier_20261031 import equal
import torch

def test_launch_requires_explicit_approval(monkeypatch):
    monkeypatch.setattr(launch,'check',lambda *a:pytest.fail('Must not inspect/launch before approval'))
    with pytest.raises(ValueError,match='approval'):launch.run('hash')

def test_launch_refuses_existing_output(tmp_path,monkeypatch):
    monkeypatch.setattr(launch,'OUT',tmp_path)
    with pytest.raises(ValueError,match='Already'):launch.run('hash',True)

def test_private_science_worker_requires_supervisor(monkeypatch):
    monkeypatch.delenv('PROWL_VERIFIER_SCIENCE_SHA',raising=False)
    with pytest.raises(ValueError,match='supervisor'):launch.worker('unapproved')

def test_private_qualification_requires_supervisor(monkeypatch):
    from scripts.diagnostics import qualify_verifier_20261031 as q
    monkeypatch.delenv('PROWL_VERIFIER_QUAL_STAGE',raising=False)
    monkeypatch.setattr(q.build.pilot,'read',lambda p:{})
    with pytest.raises(ValueError,match='supervisor'):q.worker('producer')

def test_restore_comparator_catches_optimizer_and_rng_changes():
    a=dict(model=torch.tensor([1.,2.]),optimizer={0:dict(step=torch.tensor(4.))},rng=[torch.tensor([2,3])])
    import copy
    b=copy.deepcopy(a);assert equal(a,b)
    b['optimizer'][0]['step']+=1;assert not equal(a,b)
    b=copy.deepcopy(a);b['rng'][0][0]=7;assert not equal(a,b)

def test_cache_build_supervision_roles_fail_closed():
    from types import SimpleNamespace
    from scripts.diagnostics.build_verifier_views_20261031 import read_truth
    p=SimpleNamespace(roles={'c':'verifier_calibration','d':'development','f':'verifier_fit'})
    for n,r in [('c','verifier_calibration'),('d','development'),('f','verifier_tune')]:
        with pytest.raises(ValueError):read_truth(p,n,r,{})

def test_scientific_executor_logs_to_mock_mlflow(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    import mlflow.tracking
    import src.training.verifier_session_20261031 as session_module
    base=tmp_path/'base';base.mkdir();out=tmp_path/'run';backup=tmp_path/'backup'
    (base/'configuration.json').write_text(json.dumps(dict(run=dict(max_updates=2,validate_every=1))))
    (base/'ready.json').write_text('{}')
    (base/'scientific-dispatch.json').write_text(json.dumps(dict(ready_sha256='mockpin')))
    monkeypatch.setenv('PROWL_VERIFIER_SCIENCE_SHA','mockpin')
    monkeypatch.setattr(launch,'BASE',base);monkeypatch.setattr(launch,'OUT',out);monkeypatch.setattr(launch,'BACKUP',backup)
    r=dict(dataset_manifest='mock',dataset_sha256='mock',configuration=dict(seed=1,batch_size=8,learning_rate=.0003,epochs=2,patients=dict(verifier_fit=['fit'])),seconds=60,gpu_bytes=6*1024**3)
    monkeypatch.setattr(launch,'check',lambda p:r);monkeypatch.setattr(launch.qualify,'configure',lambda:None)
    monkeypatch.setattr(launch.build,'resource_check',lambda:None);monkeypatch.setattr(launch,'require_ac',lambda:None)
    copied=[];monkeypatch.setattr(launch,'backup_file',lambda p,d,**kw:copied.append(p.name))
    monkeypatch.setattr(session_module,'Dataset',lambda *a:SimpleNamespace(pin='mock'))
    class FakeSession:
        def __init__(self,dataset,**kw):self.dataset=dataset;self.step=0;self.epoch=0;self.lr=.0003
        def state(self):return dict(step=self.step)
        def update(self):
            self.step+=1;self.epoch+=1
            return dict(loss=.5,gradient_norm=1.,input_sha256='mock')
        def evaluate(self):return dict(patient_balanced_bce=.4/self.epoch,candidate_patients=1)
    monkeypatch.setattr(session_module,'Session',FakeSession)
    metrics=[];statuses=[]
    class Client:
        def __init__(self,**kw):pass
        def get_experiment_by_name(self,n):return SimpleNamespace(experiment_id='exp')
        def create_run(self,*a,**kw):return SimpleNamespace(info=SimpleNamespace(run_id='mockrun'))
        def log_metric(self,*a,**kw):metrics.append((a,kw))
        def log_artifact(self,*a):pass
        def set_terminated(self,*a):statuses.append(a)
    monkeypatch.setattr(mlflow.tracking,'MlflowClient',Client)
    launch.worker('mockpin')
    assert statuses==[('mockrun','FINISHED')] and len(metrics)==4
    assert [a[1] for a,k in metrics]==['train/loss','tune/patient_balanced_bce']*2
    assert 'initial.pt' in copied and 'history.jsonl' in copied
    assert json.loads((out/'result.json').read_text())['selected']['epoch']==2
