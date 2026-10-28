from pathlib import Path
import ast
from scripts.diagnostics.resume_rsuper_affine_checked_v1 import remaining


def test_prediction_and_reconstruction_remain_identical():
    old=Path('scripts/diagnostics/build_rsuper_header_checked_v1.py').read_text()
    new=Path('scripts/diagnostics/build_rsuper_affine_checked_v1.py').read_text()
    start='            def tick(info):'
    end='        row=dict('
    assert old[old.index(start):old.index(end)]==new[new.index(start):new.index(end)]
    for source in (old,new):ast.parse(source)
    assert 'source_loading=loading' in new
    assert 'load(p,meta,name,max_voxels=' in new


def test_prior_budget_is_preserved():
    request={'limits':{'seconds':203341}}
    resources=dict(workers_reaped=True,success=False,exit_code=1,error="ValueError('Duration worker failed')",seconds=29372.424736)
    assert remaining(request,resources,"expected=metadata_grid(meta['parent_geometry'])\nAssertionError")==173968
