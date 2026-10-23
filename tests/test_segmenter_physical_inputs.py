from types import SimpleNamespace
import numpy as np
import pytest
from tests.test_segmenter_native_inputs import make_inputs
from src.data.segmenter_physical_inputs_v1 import PhysicalInputs,PhysicalOptimizerWindows


def physical(tmp_path):
    make_inputs(tmp_path)
    return PhysicalInputs(manifest=tmp_path/'manifest.csv',review=tmp_path/'review.json',
                          train_file=tmp_path/'train.txt',dev_file=tmp_path/'dev.txt')


def test_actual_physical_provider_upsamples_coarse_axis_only(tmp_path):
    p=physical(tmp_path)
    x,y,t,trace=p.window('t',role='train',operation='optimizer',visit=0,seed=42)
    assert trace['geometry']['factors']==[1,1,2]
    assert (y==2).sum()==2  # one native annotated voxel, two subdivided cells
    assert x.dtype==np.float32 and x.shape==(1,144,144,144)
    assert t['normalized_shape']==[20,22,36]
    assert max(trace['geometry']['spacing_mm'])<=1.00001


def test_physical_optimizer_adapter_seals_correct_control_and_padding(tmp_path):
    p=physical(tmp_path)
    raw=SimpleNamespace(config={'seed':42},exposure={'t':0},step=0)
    adapter=PhysicalOptimizerWindows(p,raw)
    batch=adapter.get('t',role='train',operation='optimizer')
    x,y=batch.checked(p.pin,'optimizer','t')
    assert (y==2).sum()==2 and np.isfinite(x).all()
    assert adapter.trace['window']['geometry']['version']=='physical-detail-windows-1'


def test_physical_evaluator_cannot_use_annotation_windows(tmp_path):
    p=physical(tmp_path)
    with pytest.raises(ValueError):p.window('d',role='validation',operation='evaluator',visit=0,seed=42)
