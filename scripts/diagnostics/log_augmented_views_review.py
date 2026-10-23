"""Explicit local MLflow retrospective logging; completed run and saved audit required."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.diagnostics.review_augmented_views import OUT, RUN
from src.training.experiment_config import sha256


def main():
    from mlflow import MlflowClient
    from mlflow.entities import Metric, RunTag
    import time
    client = MlflowClient(tracking_uri='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db')
    run_id = 'dbf1a562e9eb4d5a96301718a19d07a8'
    assert client.get_run(run_id).info.status == 'FINISHED', 'Do not close or relabel an active run'
    result = json.loads((OUT/'results.json').read_text())
    assert sha256(RUN/'execution/history.jsonl') == result['evidence_sha256'][str(RUN/'execution/history.jsonl')]
    timestamp = int(time.time()*1000)
    metrics = []
    for endpoint, key in [('selected', 'primary'), ('terminal', 'mandatory_secondary')]:
        step = result['selected_step'] if endpoint == 'selected' else 24000
        comparison = result[key]
        summary = result['summaries']['augmented_'+('selected' if endpoint == 'selected' else 'final')]
        values = dict(lesion_dice=summary['lesion_dice'], detected_cases=summary['detected'],
            empty_alarm_cases=summary['alarms'], pancreas_dice=summary['pancreas_dice'],
            empty_predicted_voxels=comparison['empty_predicted_voxels']['treatment'],
            dice_delta=comparison['metrics']['dice']['difference'],
            dice_delta_ci95_lower=comparison['metrics']['dice']['ci95'][0],
            dice_delta_ci95_upper=comparison['metrics']['dice']['ci95'][1])
        metrics.extend(Metric('review/native/'+endpoint+'/'+k, v, timestamp, step) for k, v in values.items())
    tags = dict(review_primary_decision=result['primary']['decision'],
        review_primary_h0=result['primary']['null_hypothesis'],
        review_terminal_decision=result['mandatory_secondary']['decision'],
        review_scope=result['scope'], review_sha256=sha256(OUT/'results.json'))
    client.log_batch(run_id, metrics=metrics, tags=[RunTag(k, v) for k, v in tags.items()])
    for path in [OUT/'results.json', ROOT/'docs/capstone/operations/PANTS-AUGMENTED-VIEWS-RESULTS-20261018.md']:
        client.log_artifact(run_id, str(path), 'retrospective')
    saved = client.get_run(run_id)
    assert saved.info.status == 'FINISHED'
    assert all(saved.data.tags[k] == v for k, v in tags.items())
    assert all(saved.data.metrics[m.key] == m.value for m in metrics)
    print(json.dumps(dict(run_id=run_id, status=saved.info.status, metrics_verified=len(metrics), tags=tags), indent=2))


if __name__ == '__main__':
    main()
