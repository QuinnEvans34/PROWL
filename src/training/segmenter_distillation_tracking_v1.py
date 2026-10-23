"""Additional KD metrics on the existing live MLflow contract; no run creation."""
import json
from mlflow.entities import Metric
from src.training.segmenter_live_tracking_v1 import Tracker
from src.training.segmenter_distillation_session_v1 import live_metrics


class DistillationTracker(Tracker):
    def __call__(self,row):
        super().__call__(row)
        if self.disabled:return
        try:
            values=live_metrics(row)
            if values:
                self.client.log_batch(self.run_id,metrics=[Metric(k,v,row['utc_ms'],row['step'])
                    for k,v in values.items()],synchronous=True)
        except Exception as exc:
            self.disabled=True
            with (self.output/'tracking-warning.json').open('x') as stream:
                json.dump(dict(status='degraded_requires_journal_backfill',step=row.get('step'),
                    error=repr(exc),component='distillation_metrics'),stream,indent=2)
