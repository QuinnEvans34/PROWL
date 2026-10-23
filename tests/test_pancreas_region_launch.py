"""Admission gates must fail before allocating a scientific output directory."""
import pytest
from scripts import train_pancreas_region as launch


def test_proposed_recipe_retains_original_horizon_and_optimizer():
    config=launch.cfg()['session']
    assert config['max_steps']==config['lr_horizon_steps']==24000
    assert config['warmup_steps']==500 and config['learning_rate']==1e-4
    assert config['tensor_shape']==[144,144,144] and config['seed']==42


def test_incomplete_coverage_blocks_prepare(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'COHORT',tmp_path)
    monkeypatch.setattr(launch,'read',lambda p: {'completed':True,'all_pass':False,'cases':1403} if p.name=='result.json' else {'workers_reaped':True})
    with pytest.raises(ValueError,match='not qualified'):launch.prepare()
    assert list(tmp_path.iterdir())==[]


def test_active_audit_workers_block_prepare(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'COHORT',tmp_path)
    monkeypatch.setattr(launch,'read',lambda p: {'completed':True,'all_pass':True,'cases':1403} if p.name=='result.json' else {'workers_reaped':False})
    with pytest.raises(ValueError,match='not qualified'):launch.prepare()


def test_bad_receipt_blocks_launch(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path)
    monkeypatch.setattr(launch,'sha256',lambda p:'actual')
    with pytest.raises(ValueError,match='Receipt mismatch'):launch.launch('different')
    assert list(tmp_path.iterdir())==[]
