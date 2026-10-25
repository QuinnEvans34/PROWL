import json
import shutil
import numpy as np
import pytest
from test_pancreas_region_executor import FakeSession, checkpoint, records
from src.training.segmenter_kd_evidence_executor_v1 import execute
from src.training.segmenter_kd_native_evaluation_v1 import components
from src.training.pants_native_evaluation import native_metrics
from src.training.native_error_review_v1 import component_table
from src.data.manifest_records import digest


def evaluate(session, provider, name, progress):
    target = np.zeros((3, 3, 3), np.uint8)
    if name == 'positive':
        target[0, 0, 0] = 1
    pred = target * 2
    return dict(case_id=name, step=session.step,
                metrics=native_metrics(pred, target, target, np.eye(4)),
                component_evidence=dict(case_id=name, target_sha256='a'*64,
                    geometry_sha256='b'*64, components=components(pred, target, np.eye(4))))


def test_selected_terminal_and_scheduled_evidence_backed_up(tmp_path):
    backup = tmp_path/'backup'; backup.mkdir()
    result = execute(FakeSession(2), None, tmp_path/'run', validate_every=1,
        evaluator=evaluate, checkpoint=checkpoint,
        checkpoint_hook=lambda p: shutil.copyfile(p, backup/p.name))
    assert result['selected_step'] == 1
    for name in ('native-000001', 'native-000002', 'native-selected', 'native-terminal'):
        payload = (backup/(name+'.json')).read_bytes()
        sidecar = json.loads((backup/(name+'-components.json')).read_text())
        component_table(sidecar, json.loads(payload), digest(payload))
        assert payload == (tmp_path/'run'/(name+'.json')).read_bytes()


@pytest.mark.parametrize('failure', ['missing_evidence', 'backup'])
def test_evidence_failure_prevents_completion(tmp_path, failure):
    def evaluator(*args):
        row = evaluate(*args)
        if failure == 'missing_evidence':
            del row['component_evidence']
        return row
    def hook(path):
        if failure == 'backup' and path.name.endswith('-components.json'):
            raise OSError('invented backup failure')
    with pytest.raises((KeyError, OSError)):
        execute(FakeSession(1), None, tmp_path/'run', evaluator=evaluator,
                checkpoint=checkpoint, checkpoint_hook=hook)
    events = records(tmp_path/'run/history.jsonl')
    assert events[-1]['event'] == 'failed'
    assert not any(r['event'] in ('native_completed', 'completed') for r in events)
    assert (tmp_path/'run/step-000001.pt').exists()
