import json
from pathlib import Path
import numpy as np
import nibabel as nib
import pytest
from scripts.diagnostics import execute_autonomous_baseline_20261103 as run

def test_new_admission_required_and_old_exception_cannot_authorize(tmp_path,monkeypatch):
    monkeypatch.setattr(run.prep,'OUT',tmp_path);r=dict(limits={'seconds':600})
    with pytest.raises(ValueError,match='NEW HUMAN'):run.admission('pin',r)
    (tmp_path/'admission.json').write_text(json.dumps(dict(approved_request_sha256='pin',scope='four-case')))
    with pytest.raises(ValueError,match='does not match'):run.admission('pin',r)

def test_exact_allowance_and_output_policy_cannot_change(tmp_path,monkeypatch):
    monkeypatch.setattr(run.prep,'OUT',tmp_path);r=dict(limits={'seconds':600});a=dict(approved_request_sha256='pin',scope='autonomous70',limits=r['limits'],output_policy='retain_float32_probabilities',numerical_exception='approved_only_for_this_scope')
    (tmp_path/'admission.json').write_text(json.dumps(a));assert run.admission('pin',r)==a
    with pytest.raises(ValueError,match='Unresolved'):run.admission('pin',dict(r,unresolved_preflight=[dict(case_id='5592')]))
    a['limits']={'seconds':601};(tmp_path/'admission.json').write_text(json.dumps(a))
    with pytest.raises(ValueError):run.admission('pin',r)

def test_worker_skips_all_reference_hash_reads(tmp_path,monkeypatch):
    monkeypatch.setattr(run.prep,'OUT',tmp_path);monkeypatch.setattr(run.q,'environment',lambda:{})
    cases=[dict(case_id=str(i),exposure=dict(role='exposed_development',segmenter_optimizer_overlap=False),files=dict(ct='ct',pancreas='pancreas',lesion='lesion')) for i in range(70)]
    (tmp_path/'request.json').write_text(json.dumps(dict(version='autonomous70-prepared-request-1',arms=['autonomous'],cases=cases,environment={},pins={'ct':'h','pancreas':'h','lesion':'h'})))
    reads=[]
    def digest(p):reads.append(str(p));return 'h'
    monkeypatch.setattr(run.q,'sha',digest);run.request('h',inference_worker=True)
    assert 'ct' in reads and 'pancreas' not in reads and 'lesion' not in reads
    cases[1]['case_id']='0';(tmp_path/'request.json').write_text(json.dumps(dict(version='autonomous70-prepared-request-1',arms=['autonomous'],cases=cases)))
    with pytest.raises(ValueError,match='roles'):run.request('h')

def test_reuse_original_result_bytes_and_reject_mixed_ct(tmp_path,monkeypatch):
    origin=tmp_path/'origin'/'output';origin.mkdir(parents=True);monkeypatch.setattr(run,'BASE',tmp_path/'baseline')
    a=np.eye(4);n=nib.Nifti1Image(np.zeros((2,3,4),np.uint8),a);n.header.set_xyzt_units('mm');nib.save(n,origin/'prediction.nii.gz')
    r=dict(models={},localizer_recipe={},environment={});old=dict(r,ct_sha256='ct-original')
    (origin.parent/'request.json').write_text(json.dumps(old));(origin.parent/'worker.resources.json').write_text(json.dumps(dict(success=True,workers_reaped=True,exit_code=0)))
    result=dict(case_id='one',reference_inputs_used=False,status='LOCAL_DIAGNOSTIC_COMPLETE_REFERENCE_PENDING',artifacts={'prediction.nii.gz':dict(sha256=run.q.sha(origin/'prediction.nii.gz'),bytes=(origin/'prediction.nii.gz').stat().st_size)})
    (origin/'result.json').write_text(json.dumps(result));(origin/'input-access.json').write_text('{}')
    case=dict(case_id='one',identity=dict(source_sha256={'ct':'ct-original'}),expected_native=dict(shape=[2,3,4],affine=a.tolist()),reuse=dict(root=str(origin),kind='matched-diagnostic-native-output',request_sha256=run.q.sha(origin.parent/'request.json'),result_sha256=run.q.sha(origin/'result.json'),input_access_sha256=run.q.sha(origin/'input-access.json')))
    run.reuse_case(case,r,'new-request')
    assert (run.BASE/'one/autonomous/result.json').read_bytes()==(origin/'result.json').read_bytes()
    case['identity']['source_sha256']['ct']='other'
    with pytest.raises(ValueError,match='CT identity'):run.reuse_case(case,r,'new-request')
