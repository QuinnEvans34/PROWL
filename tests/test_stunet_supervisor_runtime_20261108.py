import types
import pytest
from scripts.training import supervise_stunet_continuation_20261108_v2 as module


class Client:
    def get_experiment_by_name(self,name):return types.SimpleNamespace(experiment_id='existing')
    def create_run(self,*args,**kwargs):raise AssertionError('Admission must not create a run')


def test_supervisor_and_worker_runtimes_are_separate():
    path=str(module.ROOT/'.venv-prowl-windows/Scripts/python.exe')
    request=dict(supervisor_python=path,python='qualified-model-environment/python.exe')
    assert module.validate_supervisor(request,path,Client())['tracking_import_and_read']
    with pytest.raises(ValueError):module.validate_supervisor(request,request['python'],Client())


def test_runtime_failure_precedes_dispatch(tmp_path,monkeypatch):
    import json
    p=tmp_path/'request.json';p.write_text(json.dumps(dict(supervisor_python='wrong')))
    monkeypatch.setattr(module.sys,'argv',['tool','--request',str(p),'--sha256',module.original.sha(p),'--mode','science'])
    def forbidden():raise AssertionError('Must fail before original dispatcher')
    monkeypatch.setattr(module.original,'main',forbidden)
    with pytest.raises(ValueError):module.main()


def test_missing_tracking_experiment_blocks_admission():
    path=str(module.ROOT/'.venv-prowl-windows/Scripts/python.exe')
    client=types.SimpleNamespace(get_experiment_by_name=lambda name:None)
    with pytest.raises(ValueError):module.validate_supervisor(dict(supervisor_python=path),path,client)


def test_no_automatic_second_attempt(tmp_path,monkeypatch):
    import json
    p=tmp_path/'request.json';p.write_text(json.dumps(dict(corrected_attempt_authorized=False)))
    monkeypatch.setattr(module.sys,'argv',['tool','--request',str(p),'--sha256',module.original.sha(p),'--mode','science'])
    monkeypatch.setattr(module,'validate_supervisor',lambda *args:None)
    def forbidden():raise AssertionError('Must not dispatch without corrected-attempt approval')
    monkeypatch.setattr(module.original,'main',forbidden)
    with pytest.raises(ValueError,match='Explicit approval'):module.main()


def test_failure_accounting_retains_original_total(tmp_path,monkeypatch):
    import json
    p=tmp_path/'failure.json';p.write_text(json.dumps(dict(success=False,workers_reaped=True,seconds=.015)))
    seen=[];monkeypatch.setattr(module,'_verify',lambda r,m:seen.append((r['seconds'],m)))
    r=dict(seconds=143940,failed_attempt_charge_seconds=60,failed_attempt_resources=str(p))
    module.verify_recovery(r,'science');assert seen==[(144000,'science')]
    with pytest.raises(ValueError):module.verify_recovery(dict(r,seconds=144000),'science')
    with pytest.raises(ValueError):module.verify_recovery(r,'producer')
    p.write_text(json.dumps(dict(success=False,workers_reaped=False,seconds=.015)))
    with pytest.raises(ValueError):module.verify_recovery(r,'science')


def test_mock_tracking_parameters_and_worker_argv(tmp_path):
    p=tmp_path/'inputs.json';p.write_text('{}')
    class Mock(Client):
        def __init__(self):self.params={};self.created=0
        def create_run(self,*args,**kwargs):
            self.created+=1;return types.SimpleNamespace(info=types.SimpleNamespace(run_id='mock-only'))
        def log_param(self,run,key,value):self.params[key]=value
        def set_terminated(self,*args,**kwargs):raise AssertionError('Unexpected tracking failure')
    client=Mock()
    r=dict(inputs=str(p),pins={str(p):module.original.sha(p)},title='test',run_id='test',parent_checkpoint_sha256='ed000e1ce25829c29f1efea7bf7a5f3684cddf43b0dbcdc5d9f47e8afc8bfa55',seconds=143940,failed_attempt_charge_seconds=60)
    module.Tracking(r,client=client)
    assert client.created==1 and client.params['steps']==12000
    assert client.params['global_start']==12000 and client.params['global_end']==24000
    assert client.params['remaining_wall_seconds']+client.params['failed_attempt_charge_seconds']==144000
