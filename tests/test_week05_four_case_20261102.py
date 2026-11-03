import json
from pathlib import Path
import numpy as np
import pytest
from src.inference.four_case_metrics_20261102 import components,contour,coverage
from scripts.diagnostics import evaluate_four_case_exception_20261102 as batch

def test_component_detection_is_not_voxel_recall_and_counts_false_positives():
    ref=np.zeros((10,10,10),bool);pred=ref.copy();ref[1:4,1:4,1:4]=1;ref[7,7,7]=1
    pred[1,1,1]=1;pred[8,1,1]=1
    r=components(pred,ref,np.diag([2,2,2,1]))
    assert r['reference_count']==2 and r['reference_hit_count']==1 and r['false_positive_components']==1
    assert r['reference'][0]['overlap_fraction']==1/27
    assert r['reference'][0]['volume_ml']==pytest.approx(27*.008)

def test_empty_and_contour_physical_distance():
    a=np.zeros((5,5,5),bool);b=a.copy();a[1,2,2]=1;b[2,2,2]=1
    r=contour(a,b,np.diag([2,1,1,1]));assert r['hausdorff95_mm']==2 and r['mean_symmetric_surface_distance_mm']==2
    assert contour(a,a,np.eye(4))['hausdorff95_mm']==0
    assert contour(a,np.zeros_like(a),np.eye(4))['state']=='undefined_empty_mask'
    assert coverage(a,b)['outside_voxels']==1
    assert coverage(np.zeros_like(a),b)['fraction'] is None

def test_sheared_metric_not_silently_reported():
    a=np.ones((2,2,2),bool);aff=np.eye(4);aff[0,1]=.3
    assert contour(a,a,aff)['state']=='not_computed_oblique_shear'

def test_exception_fixed_cohort_and_failed_gate_remain():
    spec=json.loads(batch.SPEC.read_text())
    assert spec['cross_device_probability_equivalence']=='UNQUALIFIED'
    assert spec['original_comparison_status']=='FAIL_ENGINEERING_COMPARISON'
    assert not spec['tolerances_changed'] and not spec['automatic_retry']
    r=dict(version='four-case-exception-1',cases=[dict(case_id=n) for n in batch.CASES],arms=batch.ARMS,
        qualification=batch.QUAL,probability_equivalence='UNQUALIFIED',limits=spec['inference_limits'],exception_sha256=batch.q.sha(batch.SPEC))
    batch.validate(r);r['cases'].reverse()
    with pytest.raises(ValueError,match='cohort'):batch.validate(r)

def test_one_shot_and_all_eight_arms_then_separate_scoring(tmp_path,monkeypatch):
    monkeypatch.setattr(batch,'BASE',tmp_path);monkeypatch.setattr(batch,'BACKUP',tmp_path/'backup')
    monkeypatch.setattr(batch,'request',lambda pin:{})
    monkeypatch.setattr(batch.q,'resource_gate',lambda:None)
    monkeypatch.setattr(batch,'backup',lambda:None)
    monkeypatch.setattr(batch.subprocess,'check_output',lambda *a,**k:'')
    from contextlib import nullcontext
    monkeypatch.setattr(batch,'training_guard',lambda *a:nullcontext())
    calls=[]
    monkeypatch.setattr(batch.q,'supervise',lambda command,**kwargs:calls.append((command,kwargs)))
    batch.run('test')
    assert len(calls)==16
    assert all(c[0][2]=='--worker' for c in calls[:8]) and all(c[0][2]=='--score' for c in calls[8:])
    assert all(0<c[1]['seconds']<=600 for c in calls)
    assert json.loads((tmp_path/'completion.json').read_text())['cases']==batch.CASES
    with pytest.raises(FileExistsError):batch.run('test')

def test_failure_preserved_without_retry_or_omitting_denominator(tmp_path,monkeypatch):
    monkeypatch.setattr(batch,'BASE',tmp_path);monkeypatch.setattr(batch,'BACKUP',tmp_path/'backup')
    monkeypatch.setattr(batch,'request',lambda pin:{})
    monkeypatch.setattr(batch.q,'resource_gate',lambda:None);monkeypatch.setattr(batch,'backup',lambda:None)
    monkeypatch.setattr(batch.subprocess,'check_output',lambda *a,**k:'')
    from contextlib import nullcontext
    monkeypatch.setattr(batch,'training_guard',lambda *a:nullcontext())
    calls=[]
    def fail(*a,**k):calls.append(a);raise RuntimeError('bounded worker failure')
    monkeypatch.setattr(batch.q,'supervise',fail)
    with pytest.raises(RuntimeError):batch.run('test')
    assert len(calls)==1
    assert json.loads((tmp_path/'failure.json').read_text())['all_case_denominator']==batch.CASES

def test_inference_request_does_not_hash_reference_bytes(tmp_path,monkeypatch):
    monkeypatch.setattr(batch,'BASE',tmp_path);monkeypatch.setattr(batch,'validate',lambda r:None)
    monkeypatch.setattr(batch.q,'environment',lambda:{})
    r=dict(environment={},cases=[dict(files=dict(ct='ct',pancreas='pancreas',lesion='lesion'))],pins={'ct':'h','pancreas':'h','lesion':'h'})
    (tmp_path/'request.json').write_text(json.dumps(r));reads=[]
    def digest(p):reads.append(str(p));return 'h'
    monkeypatch.setattr(batch.q,'sha',digest)
    batch.request('h',inference_worker=True)
    assert 'ct' in reads and 'pancreas' not in reads and 'lesion' not in reads
    reads.clear();batch.request('h');assert 'pancreas' in reads and 'lesion' in reads
