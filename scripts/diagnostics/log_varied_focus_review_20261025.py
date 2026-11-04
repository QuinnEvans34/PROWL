"""Add verified retrospective metrics/artifacts to the existing FINISHED run."""
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.review_varied_focus_20261025 import OUT,RUN,read,sha256


def main():
    from mlflow import MlflowClient
    from mlflow.entities import Metric,RunTag
    receipt=OUT/'mlflow-review.json'
    if receipt.exists():raise ValueError('Retrospective already logged; do not duplicate')
    r=read(OUT/'results.json')
    for path,pin in r['evidence_sha256'].items():
        if sha256(path)!=pin:raise ValueError('Review evidence changed')
    client=MlflowClient(tracking_uri='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db')
    run_id='a84c0a6ae0cb424ca182350425adc7aa'
    if client.get_run(run_id).info.status!='FINISHED':raise ValueError('Run not FINISHED')
    now=int(time.time()*1000);metrics=[];tags={}
    for endpoint in ('primary','secondary'):
        c=r[endpoint];s=c['treatment']
        values=dict(lesion_dice=s['dice'],dice_delta=c['delta'],ci95_lower=c['ci95'][0],ci95_upper=c['ci95'][1],
            detected_cases=s['detected'],negative_alarm_cases=s['alarms'],negative_predicted_voxels=s['empty_voxels'],
            negative_predicted_mL=s['empty_mL'],positive_macro_recall=s['positive_macro_recall'])
        metrics += [Metric('review/varied_focus_20261025/'+endpoint+'/'+k,v,now,24000) for k,v in values.items()]
        tags['review_varied_20261025_'+endpoint+'_h0']=c['null']
        tags['review_varied_20261025_'+endpoint+'_practical']=c['practical']
    tags.update(review_varied_20261025_scope=r['scope'],review_varied_20261025_sha256=sha256(OUT/'results.json'))
    client.log_batch(run_id,metrics=metrics,tags=[RunTag(k,v) for k,v in tags.items()])
    files=[OUT/'results.json',ROOT/'docs/capstone/operations/PANTS-VARIED-FOCUS-RESULTS-20261025.md']
    for path in files:client.log_artifact(run_id,str(path),'retrospective/varied-focus-20261025')
    saved=client.get_run(run_id)
    if saved.info.status!='FINISHED' or any(saved.data.metrics[m.key]!=m.value for m in metrics) or any(saved.data.tags[k]!=v for k,v in tags.items()):
        raise ValueError('Retrospective readback mismatch')
    with receipt.open('x') as stream:json.dump(dict(run_id=run_id,status=saved.info.status,metrics_verified=len(metrics),tags_verified=len(tags),artifact_files=[str(p) for p in files]),stream,indent=2)
    print(receipt.read_text())


if __name__=='__main__':main()
