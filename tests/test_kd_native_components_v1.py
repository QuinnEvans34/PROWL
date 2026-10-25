import json
import numpy as np
import pytest
from src.training.segmenter_kd_native_evaluation_v1 import components,bind_sidecar
from src.training.pants_native_evaluation import native_metrics
from src.training.native_error_review_v1 import component_table
from src.data.manifest_records import canonical,digest

def test_small_components_are_not_patient_size_bins(tmp_path):
    target=np.zeros((30,30,30),np.uint8);target[:10,:10,:10]=1;target[20:23,20:23,20:23]=1
    pred=np.zeros_like(target);pred[20,20,20]=2
    affine=np.eye(4);parts=components(pred,target,affine)
    assert [(x['voxels'],x['detected']) for x in parts]==[(1000,False),(27,True)]
    metrics=native_metrics(pred,np.zeros_like(target),target,affine)
    assert metrics['size_band']=='medium' and parts[1]['volume_mm3']<1000
    report=dict(cases=[dict(case_id='invented',metrics=metrics,component_evidence=dict(case_id='invented',target_sha256='a'*64,geometry_sha256='b'*64,components=parts))])
    path=tmp_path/'native.json';path.write_bytes(canonical(report));out=bind_sidecar(path)
    component_table(json.loads(out.read_text()),report,digest(path.read_bytes()))
    with pytest.raises(ValueError):component_table(json.loads(out.read_text()),report,'0'*64)

def test_empty_and_anisotropic_native_grid():
    y=np.zeros((3,3,3),np.uint8);p=y.copy();p[0,0,0]=2
    assert components(p,y,np.eye(4))==[]
    y[0,0,0]=1;y[1,1,1]=1 # diagonal adjacency is26connected
    r=components(p,y,np.diag([2,3,4,1]))
    assert len(r)==1 and r[0]['volume_mm3']==pytest.approx(48) and r[0]['detected']
