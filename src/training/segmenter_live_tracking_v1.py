"""Local MLflow live mirror; a tracking fault never discards the durable training journal."""
import json
from pathlib import Path
from mlflow import MlflowClient
from mlflow.entities import Metric
from scripts.diagnostics.backfill_full_runs_mlflow import summarize,URI


class Tracker:
    def __init__(self,run_id,output,client=None):
        self.client=client or MlflowClient(tracking_uri=URI);self.run_id=run_id
        self.output=Path(output);self.disabled=False;self.groups={}

    def __call__(self,row):
        if self.disabled:return
        try:
            event=row['event'];step=row.get('step',0);values={}
            if event=='update' and (step==1 or step%25==0):
                values={f'train/{k}':row[k] for k in ('loss','learning_rate','elapsed_seconds')}
            if event in ('validation_case','native_case'):
                self.groups.setdefault((event,row['variant'],step),[]).append(row)
            if event in ('validation','native_completed'):
                native=event=='native_completed';case_event='native_case' if native else 'validation_case'
                rows=self.groups.pop((case_event,row['variant'],step))
                prefix=('native' if native else 'tensor')+'/dev70/'+row['variant']+'/'
                values={prefix+k:v for k,v in summarize(rows,native=native).items()}
            if values:
                self.client.log_batch(self.run_id,metrics=[Metric(k,float(v),row['utc_ms'],step) for k,v in values.items()],synchronous=True)
        except Exception as exc:
            self.disabled=True
            with (self.output/'tracking-warning.json').open('x') as f:
                json.dump(dict(status='degraded_requires_journal_backfill',step=row.get('step'),error=repr(exc)),f,indent=2)
