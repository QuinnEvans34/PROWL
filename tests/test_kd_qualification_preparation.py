"""Metadata-only full-cohort qualification preparation with invented source records."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from src.data.manifest_records import canonical, digest
from src.data.segmenter_teacher_cache_v1 import SCHEMA, sha
from src.data.pants_errata_kd_inputs_v1 import THROUGHPUT
from scripts.diagnostics.prepare_kd_executor_qualification import prepare


def fixture(tmp_path):
    root=tmp_path/'admitted'; root.mkdir()
    producer=tmp_path/'producer'; producer.mkdir()
    designs=Path('configs/experiments/mac-kd-comparison-20261023')
    cfg=json.loads((designs/'control.json').read_text())['student_configuration']
    control=dict(train=[f'Train_{i}' for i in range(1333)],validation=[f'Dev_{i}' for i in range(70)],
                 throughput=THROUGHPUT,label_revision={'synthetic':True},
                 region_policy=cfg['region_policy'],training_view_policy=cfg['training_view_policy'])
    membership=json.loads((designs/'control.json').read_text())['membership']
    control['bindings']=dict(train_file=membership['train'],dev_file=membership['development'])
    pin=digest(canonical(control))
    teacher=dict(weights={'sha256':'a'*64},config={},labels={})
    records={'request.json':dict(train=control['train'],teacher=teacher,preprocessing_policy={}),
             'result.json':dict(success=True,complete=True),
             'resources.json':dict(success=True,workers_reaped=True,exit_code=0)}
    pins={}
    for name,value in records.items():
        (producer/name).write_bytes(canonical(value));pins[name]=sha(producer/name)
    common=dict(teacher_sha256='a'*64,teacher_config_sha256=digest(canonical({})),
                teacher_mapping_sha256=digest(canonical({})),preprocessing_sha256=digest(canonical({})),
                control_sha256=pin)
    manifest=dict(schema=SCHEMA,control_sha256=pin,complete=True,qualification_only=False,
                  members={n:{} for n in control['train']},
                  **{f'producer_{k}_sha256':digest(canonical(records[k+'.json'])) for k in ('request','result','resources')})
    for name,value in [('provider-control.json',control),('common-identity.json',common),('manifest.json',manifest)]:
        (root/name).write_bytes(canonical(value))
    receipt=dict(version='full-teacher-admission-1',members=1333,provider_sha256=pin,
                 producer_root=str(producer),source_record_hashes=pins,manifest_sha256=sha(root/'manifest.json'))
    (root/'admission.json').write_bytes(canonical(receipt))
    for arm in ('control','treatment'):
        (tmp_path/(arm+'.json')).write_bytes((designs/(arm+'.json')).read_bytes())
    kwargs=dict(admission_sha256=sha(root/'admission.json'),control_design=tmp_path/'control.json',kd_design=tmp_path/'treatment.json')
    return root,kwargs


def test_prepare_only_binds_operational_pair_and_preserves_sources(tmp_path):
    root,kwargs=fixture(tmp_path)
    before={p:sha(p) for p in tmp_path.rglob('*.json')}
    out=tmp_path/'prepared';result=prepare(root,out,**kwargs)
    assert result['scientific_ready'] is False and result['status']=='PREPARED_NOT_GPU_QUALIFIED'
    a,b=result['operational_designs'];a=deepcopy(a);a['distillation']['max_weight']=.1
    assert a==b
    assert a['student_configuration']['throughput_policy']==THROUGHPUT['version']
    assert all(sha(p)==h for p,h in before.items())
    assert list(out.iterdir())==[out/'preparation.json']
    with pytest.raises(FileExistsError):prepare(root,out,**kwargs)


@pytest.mark.parametrize('fault',['receipt','control','common','manifest','producer','design','partial','nested'])
def test_fail_closed_before_output(tmp_path,fault):
    root,kwargs=fixture(tmp_path);out=tmp_path/'prepared'
    if fault=='receipt':kwargs['admission_sha256']='0'*64
    elif fault in ('control','common','manifest'):
        name={'control':'provider-control.json','common':'common-identity.json','manifest':'manifest.json'}[fault]
        (root/name).write_bytes(b'{}')
    elif fault=='producer':(tmp_path/'producer/resources.json').write_bytes(b'{}')
    elif fault=='design':
        path=kwargs['kd_design'];value=json.loads(path.read_text());value['student_configuration']['session']['seed']=99
        path.write_bytes(canonical(value))
    elif fault=='nested':out=root/'prepared'
    else:
        path=root/'manifest.json';value=json.loads(path.read_text());value['qualification_only']=True
        path.write_bytes(canonical(value));receipt=json.loads((root/'admission.json').read_text())
        receipt['manifest_sha256']=sha(path);(root/'admission.json').write_bytes(canonical(receipt))
        kwargs['admission_sha256']=sha(root/'admission.json')
    with pytest.raises((ValueError,KeyError)):prepare(root,out,**kwargs)
    assert not out.exists()


def test_matching_arms_with_wrong_split_are_not_sufficient(tmp_path):
    root,kwargs=fixture(tmp_path)
    for key in ('control_design','kd_design'):
        path=kwargs[key];value=json.loads(path.read_text());value['membership']['train']='0'*64
        path.write_bytes(canonical(value))
    with pytest.raises(ValueError,match='split bindings'):
        prepare(root,tmp_path/'prepared',**kwargs)
    assert not (tmp_path/'prepared').exists()
