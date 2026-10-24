import json
import numpy as np
import pytest
from scripts.diagnostics.qualify_distillation_mac import write


def test_report_converts_numpy_metrics_without_losing_values(tmp_path):
    path=tmp_path/'report.json'
    write(path,{'loss':np.float32(.125),'count':np.int64(12),'nested':[np.bool_(True)]})
    assert json.loads(path.read_text())=={'loss':.125,'count':12,'nested':[True]}


def test_report_refuses_overwrite(tmp_path):
    path=tmp_path/'report.json';write(path,{'first':1})
    with pytest.raises(FileExistsError):write(path,{'second':2})
    assert json.loads(path.read_text())=={'first':1}


@pytest.mark.parametrize('value',[float('nan'),np.float32(float('inf')),object()])
def test_invalid_report_leaves_no_empty_artifact(tmp_path,value):
    path=tmp_path/'report.json'
    with pytest.raises((TypeError,ValueError)):write(path,{'bad':value})
    assert not path.exists()


from scripts.diagnostics.qualify_distillation_mac import check_storage_budget


def test_storage_accepts_exact_projected_limits():
    gib = 1024**3
    result = check_storage_budget(50_000_000_000 + 4*gib + 7,
                                 100*gib + 9, 22*gib,
                                 planned_internal_bytes=7,
                                 planned_external_bytes=9, new_backup_bytes=4*gib)
    assert result['internal_reserve_bytes'] == 50_000_000_000


@pytest.mark.parametrize('overrides, message', [
    ({'internal_free': 49_999_999_999}, 'Mac internal reserve'),
    ({'planned_internal_bytes': 1}, 'Mac internal reserve'),
    ({'new_backup_bytes': 1}, 'Mac internal reserve'),
    ({'external_free': 100*1024**3-1}, 'External reserve'),
    ({'planned_external_bytes': 1}, 'External reserve'),
    ({'internal_free': 100_000_000_000, 'new_backup_bytes': 4*1024**3+1}, 'New backup'),
    ({'backup_bytes': 26*1024**3+1}, 'Total backup'),
    ({'internal_free': 100_000_000_000, 'backup_bytes': 26*1024**3,
      'new_backup_bytes': 1}, 'Total backup'),
    ({'new_backup_bytes': -1}, 'nonnegative'),
])
def test_storage_rejects_budget_violation(overrides, message):
    args = dict(internal_free=50_000_000_000, external_free=100*1024**3,
                backup_bytes=0)
    args.update(overrides)
    with pytest.raises(ValueError, match=message):
        check_storage_budget(**args)
