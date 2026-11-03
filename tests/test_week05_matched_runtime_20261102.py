import copy
import sys
import numpy as np
import pytest
from scripts.diagnostics import qualify_matched_physical_cascade_20261102 as new
from scripts.diagnostics import qualify_physical_cascade_20261102 as old
from src.inference.physical_cascade_comparison_v1 import RULE as old_rule
from src.inference.matched_cascade_comparison_v1 import RULE as new_rule,compare_arrays


def data():
    p=np.zeros((3,2,3,4),np.float32);p[0]=.5;p[1]=.3;p[2]=.2
    codes=np.zeros((2,3,4),np.uint8)
    return p,codes,codes.copy()


def test_matched_limits_and_comparison_unchanged():
    assert new.LIMITS==old.LIMITS and new_rule==old_rule
    assert new.BASE!=old.BASE and new.BACKUP!=old.BACKUP
    a,c,m=data();b=a.copy();b[1]+=.001;b[0]-=.001
    assert not compare_arrays(a,b,c,c,m,m)['passed']


def test_exact_environment_no_silent_substitution(monkeypatch):
    monkeypatch.setattr(new.sys,'version_info',(3,12,13))
    monkeypatch.setattr(new.importlib.metadata,'version',lambda name:new.EXPECTED_PACKAGES[name])
    assert new.environment()['packages']==new.EXPECTED_PACKAGES
    monkeypatch.setattr(new.importlib.metadata,'version',lambda name:'wrong')
    with pytest.raises(ValueError,match='no substitution'):new.environment()


def test_matched_trace_fields_required():
    r=dict(version='matched-physical-cascade-qualification-1',case_id='PanTS_00001070',ct_path='ct',
        ct_sha256=new.CT_SHA,source_shape=[1,2,3],source_affine=[],units='mm',
        models={k:dict(path=k,sha256=v) for k,v in new.MODEL_SHA.items()},localizer_recipe={},
        policy='all_support',limits=new.LIMITS,comparison=new.COMPARISON,output=str(new.BASE/'output'),
        backup=str(new.BACKUP),pins={},environment={},trace_selection=copy.deepcopy(new.TRACE_SELECTION))
    new.validate_request(r)
    r['trace_selection']['39']=[0,0,0]
    with pytest.raises(ValueError):new.validate_request(r)
