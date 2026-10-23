import json
from src.training.segmenter_distillation_tracking_v1 import DistillationTracker


class Client:
    def __init__(self):self.calls=[];self.fail_kd=False
    def log_batch(self,run_id,metrics,synchronous):
        assert synchronous is True
        if self.fail_kd and any(m.key=='train/kd_loss' for m in metrics):raise OSError('simulated tracking failure')
        self.calls.append((run_id,metrics))


def row(step):
    return dict(event='update',step=step,utc_ms=1234,loss=1.2,learning_rate=1e-4,elapsed_seconds=3.,
        supervised_loss=1.1,kd_loss=1.,kd_weight=.1,eligible_voxels=50,conflict_or_tie_voxels=25,valid_voxels=75)


def test_existing_run_total_and_separate_kd_metrics_and_cadence(tmp_path):
    client=Client();tracker=DistillationTracker('existing-run',tmp_path,client)
    for step in (1,2,25):tracker(row(step))
    assert len(client.calls)==4
    metrics=[m for _,batch in client.calls for m in batch]
    assert {m.step for m in metrics}=={1,25}
    assert {'train/loss','train/supervised_loss','train/kd_loss','train/kd_weight','train/eligible_voxels'}<={m.key for m in metrics}
    assert all(run=='existing-run' for run,_ in client.calls)


def test_tracking_failure_durable_warning_not_swallowed_or_retry(tmp_path):
    client=Client();client.fail_kd=True;tracker=DistillationTracker('existing-run',tmp_path,client)
    tracker(row(1));tracker(row(25))
    report=json.loads((tmp_path/'tracking-warning.json').read_text())
    assert tracker.disabled and report['component']=='distillation_metrics' and report['step']==1
    assert len(client.calls)==1
