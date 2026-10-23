from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts import train_fast_varied_region as launch


def test_scientific_recipe_unchanged_by_throughput_wrapper():
    original=launch.setup.varied.cfg();candidate=launch.cfg()
    assert {k:v for k,v in candidate.items() if k!='throughput_policy'}==original
    assert candidate['session']['max_steps']==24000
    assert candidate['session']['learning_rate']==1e-4
    assert candidate['_experiment']['run']['validate_every']==2000


def test_single_scientific_successor_same_output_new_setup():
    assert launch.OUT==launch.setup.varied.OUT
    assert launch.SETUP!=launch.setup.varied.SETUP
    assert launch.BACKUP==launch.setup.varied.BACKUP
    assert launch.OUT!=launch.setup.parent.OUT


def test_bad_receipt_blocks_before_writes(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path)
    monkeypatch.setattr(launch,'sha256',lambda path:'correct')
    with pytest.raises(ValueError,match='Receipt mismatch'):launch.check_ready('wrong',user_launch=True)
    assert not list(tmp_path.iterdir())


def test_setup_receipt_is_not_launch_authority(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path)
    monkeypatch.setattr(launch,'sha256',lambda path:'correct')
    monkeypatch.setattr(launch,'read',lambda path:{'status':'READY_AWAITING_USER_LAUNCH'})
    with pytest.raises(ValueError,match='Explicit subsequent user'):launch.check_ready('correct')
    assert not list(tmp_path.iterdir())


def test_duplicate_dispatch_rejected(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path);monkeypatch.setattr(launch,'OUT',tmp_path/'output')
    monkeypatch.setattr(launch,'BACKUP',tmp_path/'backup');(tmp_path/'dispatch.json').write_text('{}')
    monkeypatch.setattr(launch,'sha256',lambda path:'correct')
    monkeypatch.setattr(launch,'read',lambda path:{'status':'READY_AWAITING_USER_LAUNCH'})
    monkeypatch.setattr(launch.setup.parent,'check',lambda receipt:None);monkeypatch.setattr(launch,'gates',lambda:None)
    with pytest.raises(ValueError,match='No duplicate'):launch.check_ready('correct',user_launch=True)
    assert not (tmp_path/'output').exists()


def test_unreaped_stage_blocks_readiness(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path)
    monkeypatch.setattr(launch.setup,'check_pins',lambda:None);monkeypatch.setattr(launch.setup,'resources',lambda:None)
    monkeypatch.setattr(launch,'read',lambda path:{'workers_reaped':False})
    with pytest.raises(ValueError,match='Unreaped'):launch.gates()


def test_speed_gate_or_cold_failure_cannot_freeze(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path)
    monkeypatch.setattr(launch.setup,'check_pins',lambda:None);monkeypatch.setattr(launch.setup,'resources',lambda:None)
    def read(path):
        if path.name.endswith('resources.json'):return {'workers_reaped':True,'success':True,'exit_code':0}
        if path.name=='result.json':return {'passed':True,'completed':True}
        return {'speed_gate_passed':False,'exact_next_input':True}
    monkeypatch.setattr(launch,'read',read)
    with pytest.raises(ValueError,match='CUDA qualification failed'):launch.gates()


def test_budget_is_combined_cache_not_an_extra_32gib():
    spec=launch.read(launch.SPEC)
    assert spec['combined_cache_cap_bytes']==32*1024**3
    assert not spec['automatic_retry']
    assert spec['qualification']['reference_updates_maximum']==40
