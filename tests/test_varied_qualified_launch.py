import xml.etree.ElementTree as ET
import pytest
from scripts import train_varied_qualified as launch
from scripts import train_fast_varied_region as previous


def test_same_scientific_configuration_and_single_output():
    assert launch.cfg()==previous.cfg()
    assert launch.OUT==previous.OUT
    assert launch.BACKUP==previous.BACKUP
    assert launch.SETUP!=previous.SETUP
    assert launch.cfg()['session']['max_steps']==24000


@pytest.mark.parametrize('resource',[
    {'success':False,'exit_code':1,'workers_reaped':True},
    {'success':True,'exit_code':0,'workers_reaped':False},
    {'success':True,'exit_code':1,'workers_reaped':True}])
def test_success_requires_every_resource_gate(monkeypatch,tmp_path,resource):
    monkeypatch.setattr(launch,'read',lambda _:resource)
    with pytest.raises(ValueError,match='succeed/reap'): launch.successful_stage(tmp_path,'producer')


def test_bad_hash_blocks_launch_before_any_mutation(monkeypatch):
    monkeypatch.setattr(launch,'sha256',lambda _:'correct')
    with pytest.raises(ValueError,match='Receipt mismatch'): launch.check_ready('wrong',user_launch=True)


def test_explicit_one_run_gate_required(monkeypatch):
    monkeypatch.setattr(launch,'sha256',lambda _:'correct')
    monkeypatch.setattr(launch,'read',lambda _:{'status':'READY_AUTHORIZED_ONE_RUN'})
    with pytest.raises(ValueError,match='Explicit'): launch.check_ready('correct',user_launch=False)


def test_duplicate_scientific_output_refused(monkeypatch,tmp_path):
    monkeypatch.setattr(launch,'SETUP',tmp_path);monkeypatch.setattr(launch,'OUT',tmp_path)
    monkeypatch.setattr(launch,'sha256',lambda _:'correct')
    monkeypatch.setattr(launch,'read',lambda _:{'status':'READY_AUTHORIZED_ONE_RUN'})
    monkeypatch.setattr(launch.setup.parent,'check',lambda _:None)
    monkeypatch.setattr(launch,'gates',lambda:None)
    with pytest.raises(ValueError,match='No duplicate'): launch.check_ready('correct',user_launch=True)


def test_failed_or_empty_test_report_cannot_admit(tmp_path):
    for index,attributes in enumerate([dict(tests='0'),dict(tests='1',failures='1'),dict(tests='1',skipped='1')]):
        root=ET.Element('testsuites');ET.SubElement(root,'testsuite',attributes)
        path=tmp_path/f'{index}.xml';ET.ElementTree(root).write(path)
        with pytest.raises(ValueError,match='Regression'):launch.passed_tests(path)


def test_amendment_keeps_production_architecture_and_numerics():
    spec=launch.read(launch.AMENDMENT)
    assert not spec['scientific_recipe_changed']
    assert not spec['scientific_execution']['qualification_adapter_installed']
    assert spec['scientific_execution']['unchanged_original_cuda_numerics']
    assert spec['qualification']['rtol']==1.3e-6
    assert spec['qualification']['atol']==1e-5
