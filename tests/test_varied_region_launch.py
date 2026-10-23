import json
from pathlib import Path
import pytest
from scripts import train_varied_region as launch


def test_only_training_sampler_config_changes():
    current=launch.parent.cfg();new=launch.cfg()
    assert current['session']==new['session']
    assert current['initialization']==new['initialization']
    assert current['region_policy']==new['region_policy']
    assert current['_experiment']['run']==new['_experiment']['run']
    assert new['session']['max_steps']==24000 and new['session']['learning_rate']==1e-4


def test_new_outputs_are_separate():
    assert launch.SETUP!=launch.parent.SETUP and launch.OUT!=launch.parent.OUT
    assert launch.BACKUP!=launch.parent.BACKUP


def test_stopped_parent_cannot_admit_successor(tmp_path):
    (tmp_path/'operator-stop.json').write_text('{}')
    with pytest.raises(ValueError,match='stopped or failed'):
        launch.completion_evidence(tmp_path,tmp_path,[])


def test_unreaped_parent_cannot_admit_successor(tmp_path):
    (tmp_path/'result.json').write_text(json.dumps({'completed_updates':24000}))
    (tmp_path/'scientific-resources.json').write_text(json.dumps({'workers_reaped':False}))
    with pytest.raises(ValueError,match='workers active'):
        launch.completion_evidence(tmp_path,tmp_path,[])


def test_incomplete_parent_cannot_admit_successor(tmp_path):
    (tmp_path/'result.json').write_text(json.dumps({'completed_updates':22000}))
    (tmp_path/'scientific-resources.json').write_text(json.dumps({'workers_reaped':True}))
    with pytest.raises(ValueError,match='incomplete'):
        launch.completion_evidence(tmp_path,tmp_path,[])


def test_corrupt_receipt_cannot_dispatch(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path)
    monkeypatch.setattr(launch,'sha256',lambda p:'actual')
    with pytest.raises(ValueError,match='Receipt mismatch'):launch.launch('other')
    assert list(tmp_path.iterdir())==[]


def test_parent_pins_checked_before_preparation_writes(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path/'new')
    def fail():raise ValueError('Parent receipt changed')
    monkeypatch.setattr(launch,'parent_pins',fail)
    with pytest.raises(ValueError,match='Parent receipt'):launch.prepare()
    assert not (tmp_path/'new').exists()


def test_scientific_null_and_guards_are_preregistered():
    spec=launch.read(launch.SPEC)
    assert spec['acceptance']['minimum_dice_delta']==.02
    assert spec['acceptance']['minimum_positive_macro_voxel_recall_delta']==-.03
    assert spec['resources']==launch.read(launch.parent.SPEC)['resources']
    assert spec['bootstrap']['replicates']==10000
    assert 'current' not in spec['parent']  # Exact immutable parent run, not a moving alias.


def complete_fixture(tmp_path):
    execution=tmp_path/'execution';execution.mkdir()
    names=[f'case-{i}' for i in range(70)]
    (tmp_path/'result.json').write_text(json.dumps({'completed_updates':24000}))
    (tmp_path/'scientific-resources.json').write_text(json.dumps({'workers_reaped':True}))
    rows=[{'event':'update','step':s} for s in range(1,24001)]
    for step in range(2000,24001,2000):
        cases=[dict(case_id=n,step=step,metrics={'lesion':{'dice':.4,'target_voxels':1 if i<36 else 0}})
               for i,n in enumerate(names)]
        report=dict(step=step,cases=cases,scope='native_provided_pancreas_region_development',lesion_positive_macro_dice=.4)
        (execution/f'native-{step:06d}.json').write_text(json.dumps(report))
        rows.append(dict(event='native_completed',step=step))
    (execution/'native-selected.json').write_text((execution/'native-002000.json').read_text())
    (execution/'native-terminal.json').write_text((execution/'native-024000.json').read_text())
    rows.append(dict(event='completed',step=24000))
    (execution/'history.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    return names


def test_complete_parent_binds_earliest_tie(tmp_path):
    names=complete_fixture(tmp_path)
    result=launch.completion_evidence(tmp_path,tmp_path,names)
    assert result['selected_step']==2000 and result['complete_evaluations']==12


def test_parent_selection_cannot_be_replaced_by_later_tie(tmp_path):
    names=complete_fixture(tmp_path)
    (tmp_path/'execution/native-selected.json').write_text((tmp_path/'execution/native-024000.json').read_text())
    with pytest.raises(ValueError,match='selection changed'):launch.completion_evidence(tmp_path,tmp_path,names)


def test_missing_development_case_blocks_handoff(tmp_path):
    names=complete_fixture(tmp_path);file=tmp_path/'execution/native-024000.json'
    report=json.loads(file.read_text());report['cases'].pop();file.write_text(json.dumps(report))
    with pytest.raises(ValueError,match='Incomplete parent native'):launch.completion_evidence(tmp_path,tmp_path,names)


def test_duplicate_dispatch_is_rejected_even_with_good_receipt(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path);monkeypatch.setattr(launch,'OUT',tmp_path/'output')
    monkeypatch.setattr(launch,'BACKUP',tmp_path/'backup');(tmp_path/'dispatch.json').write_text('{}')
    monkeypatch.setattr(launch,'sha256',lambda p:'match')
    monkeypatch.setattr(launch,'read',lambda p:dict(status='READY',scientific_launch_authorized=True))
    for name in ('check','verify_parent_binding','resource_check'):
        monkeypatch.setattr(launch,name,lambda *args:None)
    with pytest.raises(ValueError,match='No retry or resume'):launch.launch('match')
    assert not (tmp_path/'output').exists()


def test_production_and_smoke_provider_plan_roles(monkeypatch):
    from src.data.manifest_records import canonical,digest
    class Fake:
        def __init__(self,**kwargs):
            self.control={'train':['a','b','c'],'validation':['dev'],'policy':{'source':'old'}}
    def read(path):
        return {'focused_counts':{'a':12,'b':13,'c':12}} if path.name=='schedule.json' else {'cuda_train':['a','b']}
    monkeypatch.setattr(launch,'read',read);monkeypatch.setattr(launch,'VariedInputs',Fake)
    ordinary=launch.provider();smoke=launch.provider(True)
    assert ordinary.control['train']==['a','b','c'] and smoke.control['train']==['a','b']
    assert smoke.control['validation']==['dev'] and smoke.control['qualification_only']
    assert ordinary.pin==digest(canonical(ordinary.control)) and ordinary.pin!=smoke.pin
