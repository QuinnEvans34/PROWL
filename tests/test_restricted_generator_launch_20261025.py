import json
from types import SimpleNamespace
import shutil
import pytest
from scripts import train_restricted_generator_20261025 as launch


def test_configuration_preserves_recipe(monkeypatch):
    original={'session':{'max_steps':24000,'warmup_steps':500},'_experiment':{'old':True},'initialization':{'kind':'suprem'}}
    monkeypatch.setattr(launch,'read',lambda p:original)
    c=launch.configuration()
    assert c['session']==original['session'] and c['initialization']==original['initialization']
    assert c['_experiment']['run']['validate_every'] is None
    assert c['restricted_generator']['selection']=='fixed_terminal_no_heldout_selection'
    assert c['restricted_generator']['evaluation_enabled'] is False
    assert original['_experiment']=={'old':True}


def test_dashboard_preserves_history_and_no_fake_dice():
    old={'id':'old','root':'old-root'};r={'pending_run':old,'runs':[{'root':'older-root'}]}
    active,new=launch.dashboard_configs({},r)
    assert new['runs']==[old,{'root':'older-root'}] and r['runs']==[{'root':'older-root'}]
    assert new['pending_run']['native_files']==[]
    assert active['metric_scope']=='generator_no_development_selection'
    assert 'dice' not in active and active['target_steps']==24000


def test_dashboard_no_duplicate_history():
    old={'root':'old-root'}
    _,r=launch.dashboard_configs({},dict(pending_run=old,runs=[old]))
    assert len(r['runs'])==1


@pytest.fixture
def gate(tmp_path,monkeypatch):
    setup=tmp_path/'setup';setup.mkdir()
    monkeypatch.setattr(launch,'SETUP',setup);monkeypatch.setattr(launch,'OUT',tmp_path/'run')
    monkeypatch.setattr(launch,'BACKUP',tmp_path/'backup')
    receipt={'status':'READY_REQUIRES_EXPLICIT_USER_LAUNCH'}
    (setup/'ready.json').write_text(json.dumps(receipt))
    monkeypatch.setattr(launch.shared.parent,'check',lambda r:None)
    monkeypatch.setattr(launch,'qualification_gate',lambda:None)
    monkeypatch.setattr(launch.shared,'resources',lambda:None)
    return launch.sha256(setup/'ready.json')


def test_explicit_approval_required(gate):
    with pytest.raises(ValueError,match='approval'):launch.admission(gate,False)


def test_wrong_receipt_rejected(gate):
    with pytest.raises(ValueError,match='hash'):launch.admission('wrong',True)


@pytest.mark.parametrize('path',['OUT','BACKUP','dispatch'])
def test_no_duplicate_retry_resume(gate,path):
    if path=='dispatch':(launch.SETUP/'dispatch.json').write_text('{}')
    else:getattr(launch,path).mkdir()
    with pytest.raises(ValueError,match='duplicate'):launch.admission(gate,True)


def test_qualification_failure_blocks_launch(gate,monkeypatch):
    def bad():raise ValueError('Cold gate failed')
    monkeypatch.setattr(launch,'qualification_gate',bad)
    with pytest.raises(ValueError,match='Cold'):launch.admission(gate,True)
    assert not (launch.SETUP/'dispatch.json').exists()


def test_successful_admission_no_side_effects(gate):
    assert launch.admission(gate,True)['status']=='READY_REQUIRES_EXPLICIT_USER_LAUNCH'
    assert not launch.OUT.exists()


def synthetic():
    control=dict(train=['allowed'],validation=['never-read'],restricted_generator=dict(selection='fixed_terminal_no_heldout_selection',evaluation_enabled=False))
    p=SimpleNamespace(control=control,pin='pin',closed=False)
    p.close=lambda:setattr(p,'closed',True)
    s=SimpleNamespace(control=control,control_pin='pin',step=0,config={'max_steps':5},identity={'synthetic':True})
    s.state=lambda:dict(step=s.step)
    def update(provider):
        s.step+=1
        return dict(step=s.step,member_id='allowed',loss=1/s.step,learning_rate=.0001)
    s.update=update
    return s,p


def test_actual_executor_tracking_and_backup_integration(tmp_path):
    from src.training.segmenter_live_tracking_v1 import Tracker
    stored=[]
    client=SimpleNamespace(log_batch=lambda rid,metrics,**kw:stored.extend(metrics))
    s,p=synthetic();backup_dir=tmp_path/'backup';backup_dir.mkdir();copied=[]
    def backup(path):shutil.copyfile(path,backup_dir/path.name);copied.append(path.name)
    result=launch.run_session(s,p,tmp_path/'run',Tracker('synthetic',tmp_path,client=client),backup,lambda:None)
    assert result['selected_step']==5 and result['development_cases_evaluated']==0 and p.closed
    assert {'initial.pt','last.pt','terminal.pt','history.jsonl'}<=set(copied)
    assert any(m.key=='train/loss' and m.step==1 and m.value==1 for m in stored)
    assert not (tmp_path/'tracking-warning.json').exists()


def test_actual_executor_backup_failure_not_completed(tmp_path):
    s,p=synthetic()
    def backup(path):raise OSError('independent copy unavailable')
    with pytest.raises(OSError):launch.run_session(s,p,tmp_path/'run',lambda row:None,backup,lambda:None)
    rows=[json.loads(x) for x in (tmp_path/'run/history.jsonl').read_text().splitlines()]
    assert rows[-1]['event']=='failed' and p.closed


def test_phone_parser_no_development_dice_and_actual_time(tmp_path,monkeypatch):
    import importlib.util
    import time
    import yaml
    spec=importlib.util.spec_from_file_location('generator_monitor_test',launch.MONITOR/'experiments.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    root=tmp_path/'run';(root/'execution').mkdir(parents=True);(root/'splits').mkdir()
    (root/'resolved.yaml').write_text(yaml.safe_dump({'_experiment':{'run':{'max_updates':24000,'validate_every':None}}}))
    (root/'splits/train_ids.txt').write_text('allowed\n')
    journal=root/'execution/history.jsonl'
    row=dict(event='update',step=25,elapsed_seconds=123.5,loss=.8,learning_rate=1e-4,utc_ms=int(time.time()*1000))
    journal.write_text(json.dumps(row)+'\n')
    entry=dict(id='test',title='Generator',root=str(root),metric_scope='generator_no_development_selection',native_files=[])
    r=module.experiment(entry,{'protected'}, {},time.time())
    assert r['steps']==25 and r['seconds']==123.5 and r['development_cases']==0
    assert r['best'] is None and r['native']==[] and r['next_validation'] is None
    row.update(step=26,elapsed_seconds=127.5)
    with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    r=module.experiment(entry,{'protected'},{},time.time())
    assert r['steps']==26 and r['seconds']==127.5


@pytest.mark.parametrize('failure',[False,True])
def test_supervisor_mlflow_lifecycle(gate,tmp_path,monkeypatch,failure):
    from contextlib import nullcontext
    import mlflow
    statuses=[];metrics=[]
    (launch.SETUP/'configuration.json').write_text(json.dumps({'session':{'max_steps':24000}}))
    monkeypatch.setattr(launch,'admission',lambda pin,approved:dict(seconds=345600,rss_bytes=12*1024**3))
    monkeypatch.setattr(launch,'training_guard',lambda path:nullcontext())
    client=SimpleNamespace(get_experiment_by_name=lambda name:SimpleNamespace(experiment_id='test'),
        create_run=lambda *a,**kw:SimpleNamespace(info=SimpleNamespace(run_id='fake')),
        log_batch=lambda *a,**kw:metrics.append(kw),log_artifact=lambda *a,**kw:None,
        set_tag=lambda *a,**kw:None,set_terminated=lambda rid,state:statuses.append(state))
    monkeypatch.setattr(mlflow,'MlflowClient',lambda **kw:client)
    process=SimpleNamespace(returncode=0,duration_resources={'workers_reaped':True})
    monkeypatch.setattr(launch.subprocess,'Popen',lambda *a,**kw:process)
    def watch(p,**kw):
        assert kw['seconds']==345600 and kw['rss_bytes']==12*1024**3
        if failure:raise RuntimeError('synthetic supervisor failure')
        launch.OUT.mkdir();(launch.OUT/'execution').mkdir()
        (launch.OUT/'result.json').write_text(json.dumps(dict(completed_updates=24000,development_cases_evaluated=0)))
        (launch.OUT/'execution/history.jsonl').write_text('')
    monkeypatch.setattr(launch,'watch_windows',watch)
    if failure:
        with pytest.raises(RuntimeError):launch.launch(gate,True)
    else:launch.launch(gate,True)
    assert statuses==['FAILED' if failure else 'FINISHED'] and metrics
