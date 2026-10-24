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
