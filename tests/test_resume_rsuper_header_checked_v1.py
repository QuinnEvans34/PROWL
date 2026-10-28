from pathlib import Path
import pytest
from scripts.diagnostics.resume_rsuper_header_checked_v1 import remaining


def test_only_geometry_validation_changed_in_worker():
    old=Path('scripts/diagnostics/build_rsuper_full_targets_v2.py').read_text().split("if __name__=='__main__':")[0]
    new=Path('scripts/diagnostics/build_rsuper_header_checked_v1.py').read_text()
    old=old.replace('"""Bounded full-cohort offline teacher preparation; never starts student training."""','"""Unchanged v2 teacher computation with validated header-derived geometry checks."""')
    old=old.replace('from src.data.segmenter_teacher_geometry_v2 import preprocess,predict,reconstruct,metadata_grid','from src.data.segmenter_teacher_geometry_v2 import preprocess,predict,reconstruct\n    from src.data.teacher_header_geometry_v1 import checked_header_grid')
    old=old.replace("expected=metadata_grid(meta['parent_geometry']);",'expected=checked_header_grid(image,meta);')
    assert old==new


def fixture():
    return {'limits':{'seconds':100}},dict(workers_reaped=True,success=False,exit_code=1,error="ValueError('Duration worker failed')",seconds=10.2),"expected=metadata_grid(meta['parent_geometry'])\nAssertionError\n"


def test_elapsed_charged():
    assert remaining(*fixture())==89


@pytest.mark.parametrize('field,value',[('workers_reaped',False),('exit_code',-15),('success',True),('seconds',float('nan')),('seconds',101),('seconds',-1)])
def test_invalid_failure_rejected(field,value):
    req,res,log=fixture();res[field]=value
    with pytest.raises(ValueError):remaining(req,res,log)


def test_other_assertion_rejected():
    req,res,_=fixture()
    with pytest.raises(ValueError):remaining(req,res,'AssertionError')
