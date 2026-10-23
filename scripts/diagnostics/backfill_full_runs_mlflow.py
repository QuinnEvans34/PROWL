"""Repeat-safe local MLflow import of immutable full-session histories and native reports.

No source images, labels, predictions, checkpoint payloads, inference, or model registration.
Metric timestamps represent IMPORT time; original steps and elapsed seconds are preserved.
"""
import argparse
from collections import defaultdict, Counter
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.source_inventory_records import require
from src.data.manifest_records import canonical, digest
from src.training.experiment_config import sha256

TRACKING=Path('C:/Users/quinn/PROWL-Tracking')
URI='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db'
REVIEW=Path('E:/PROWL/readiness/panorama-positive-review-20261013-a01')
SETUP=Path('E:/PROWL/readiness/panorama-positive-run-20261012-a01')


def read(path):return json.loads(Path(path).read_text())
def records(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]


def summarize(rows,native=False):
    data=[r['metrics'] for r in rows]
    pos=[m for m in data if m['reference_positive']] if native else [m for m in data if m['lesion']['target_voxels']]
    empty=[m for m in data if not m['reference_positive']] if native else [m for m in data if not m['lesion']['target_voxels']]
    require(pos and empty,'Both reference groups required')
    detected=sum(m['case_detected'] if native else m['lesion']['true_positive']>0 for m in pos)
    alarms=sum(m['false_alarm_any'] if native else m['lesion']['predicted_voxels']>0 for m in empty)
    result=dict(lesion_positive_macro_dice=sum(m['lesion']['dice'] for m in pos)/len(pos),
        pancreas_macro_dice=sum(m['pancreas']['dice'] for m in data)/len(data),
        positive_cases=len(pos),reference_empty_cases=len(empty),detected_cases=detected,
        detected_case_fraction=detected/len(pos),empty_alarm_cases=alarms,empty_alarm_fraction=alarms/len(empty))
    if native:
        result.update(reference_components=sum(m['reference_components'] for m in pos),
            detected_components=sum(m['detected_components'] for m in pos),
            empty_predicted_volume_mm3=sum(m['predicted_volume_mm3'] for m in empty),
            empty_alerts_50mm3=sum(m['case_alert_50mm3'] for m in empty))
    return result


def build_metrics(history,retained):
    require(history and history[-1]['event']=='completed','Only completed histories can be backfilled here')
    updates=[r for r in history if r['event']=='update']
    require([r['step'] for r in updates]==list(range(1,history[-1]['step']+1)),'Noncontiguous history')
    result=[];groups=defaultdict(list)
    for r in history:
        if r['event']=='update':
            result.extend((key,r['step'],float(r[field])) for key,field in
                [('train/loss','loss'),('train/learning_rate','learning_rate'),('train/elapsed_seconds','elapsed_seconds')])
        elif r['event']=='validation_case':groups[r['step']].append(r)
    for step,rows in sorted(groups.items()):
        require(len({r['case_id'] for r in rows})==len(rows),'Duplicate validation case')
        versions=[(len(rows),rows)]
        reduced=[r for r in rows if r['case_id'] in retained]
        require({r['case_id'] for r in reduced}==set(retained),'Incomplete matched development metrics')
        if len(reduced)!=len(rows):versions.append((len(reduced),reduced))
        for count,values in versions:
            result.extend((f'tensor/dev{count}/{k}',step,float(v)) for k,v in summarize(values).items())
    require(all(math.isfinite(v) for _,_,v in result),'Nonfinite metrics')
    return result


def import_metrics(client,run_id,values,timestamp):
    """History-aware idempotence also covers a partially completed earlier import."""
    from mlflow.entities import Metric
    desired=defaultdict(dict)
    for key,step,value in values:
        require(step not in desired[key] or desired[key][step]==value,'Conflicting desired metric')
        desired[key][step]=value
    pending=[]
    for key,steps in desired.items():
        existing={}
        for m in client.get_metric_history(run_id,key):
            require(m.step not in existing,'Duplicate stored metric step')
            existing[m.step]=m.value
        require(all(step in steps and steps[step]==value for step,value in existing.items()),'Stored metrics disagree with source')
        pending.extend(Metric(key,value,timestamp,step) for step,value in steps.items() if step not in existing)
    for offset in range(0,len(pending),500):client.log_batch(run_id,metrics=pending[offset:offset+500],synchronous=True)
    for key,steps in desired.items():
        actual=client.get_metric_history(run_id,key)
        require(len(actual)==len(steps) and {m.step:m.value for m in actual}==steps,'MLflow metric readback mismatch')
    return len(pending),sum(len(v) for v in desired.values())


def main():
    from mlflow import MlflowClient
    from mlflow.entities import Param
    from src.operations.full_training_platform import training_guard
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--include-native',action='store_true');a=p.parse_args()
    TRACKING.mkdir(parents=True,exist_ok=True)
    client=MlflowClient(tracking_uri=URI)
    experiment=client.get_experiment_by_name('PROWL capstone lesion outlining')
    experiment_id=experiment.experiment_id if experiment else client.create_experiment('PROWL capstone lesion outlining',
        artifact_location=(TRACKING/'artifacts').as_uri(),tags={'scope':'private_local_exploratory_development'})
    reduced=read(SETUP/'parent-reduced-comparison.json');retained=reduced['development']
    runs=[('CAP-EXP-016','pants_course_reference_dicefocal_24k_20261011','PanTS-only long run: recover the course recipe before adding PANORAMA'),
          ('CAP-EXP-017','pants_plus_expert_panorama_dicefocal_24k_20261012','Add expert PANORAMA lesions: does more positive training data improve outlining?')]
    receipts=[]
    with training_guard(TRACKING/'.backfill.lock'):
        for exp_id,name,title in runs:
            directory=Path('E:/PROWL/artifacts')/name;journal=directory/'execution/history.jsonl';history=records(journal)
            journal_pin=sha256(journal);identity=history[0]['identity'];control=identity['control']
            values=build_metrics(history,retained)
            matches=client.search_runs([experiment_id],filter_string=f"tags.prowl_run_key = '{name}'")
            require(len(matches)<=1,'Duplicate MLflow run identity')
            if matches:
                run=matches[0];require(run.data.tags.get('source_history_sha256')==journal_pin,'Source journal changed since prior import')
                timestamp=int(run.data.tags['import_timestamp_ms'])
            else:
                timestamp=int(time.time()*1000)
                run=client.create_run(experiment_id,start_time=timestamp,tags={'mlflow.runName':title,'prowl_run_key':name,
                    'experiment_id':exp_id,'backfilled':'true','source_history_sha256':journal_pin,'import_timestamp_ms':str(timestamp),
                    'timestamp_semantics':'MLflow timestamps are import time; train/elapsed_seconds and original steps preserve recorded timing',
                    'scope':'exploratory_reused_development_provided_ROI','promotion':'not_promoted','source_directory':str(directory)})
            run_id=run.info.run_id
            params=dict(identity['config']);params.update(train_cases=len(control['train']),development_cases=len(control['validation']),
                train_positive=sum(control['target_states'][n]=='positive' for n in control['train']),
                train_reference_empty=sum(control['target_states'][n]=='reference_empty' for n in control['train']),
                initialization_kind=identity['initialization']['kind'],initialization_sha256=identity['initialization']['sha256'],
                cohort_control_sha256=digest(canonical(control)),
                actual_updates=history[-1]['step'],matched_comparison_cases=len(retained),
                loss=identity['loss'],device=identity['device'])
            client.log_batch(run_id,params=[Param(k,json.dumps(v) if isinstance(v,(list,dict)) else str(v)) for k,v in params.items()],synchronous=True)
            exposures=Counter('PANORAMA' if r['member_id'].startswith('panorama:') else 'PanTS' for r in history if r['event']=='update')
            values.extend((f'summary/exposure/{k}',24000,float(v)) for k,v in exposures.items())
            validation=[r for r in history if r['event']=='validation']
            best=max(validation,key=lambda r:r['lesion_positive_macro_dice'])
            client.set_tag(run_id,'selected_step',str(best['step']))
            client.set_tag(run_id,'selected_tensor_cohort',str(len(control['validation']))+' development cases')
            values.extend([('summary/selected/tensor_lesion_dice',best['step'],best['lesion_positive_macro_dice'])])
            artifacts=[journal,directory/'resolved.yaml',directory/'result.json',directory/'input-control.json',directory/'cohort-review.json',directory/'source-review.json']
            ready=(Path('E:/PROWL/readiness/pants-course-reference-20261011-a01') if exp_id=='CAP-EXP-016' else SETUP)/'ready.json'
            spec=ROOT/'docs/capstone/operations'/('PANTS-COURSE-REFERENCE-LONG-RUN-20261011.json' if exp_id=='CAP-EXP-016' else 'PANORAMA-POSITIVE-EXPERIMENT-20261012.json')
            artifacts.extend([ready,spec,Path(__file__)])
            client.set_tag(run_id,'frozen_receipt_sha256',sha256(ready))
            reports=[]
            if a.include_native:
                if exp_id=='CAP-EXP-016':
                    for label in ('008000','best','024000'):
                        path=Path('E:/PROWL/readiness/pants-course-retrospective-20261012')/('native-'+label)/'report.json'
                        reports.append((75,read(path),None));artifacts.append(path)
                    for label,source in [('selected','best'),('final','024000')]:
                        reports.append((70,dict(step=reduced['reports'][source]['step'],cases=reduced['reports'][source]['cases']),label))
                    artifacts.append(SETUP/'parent-reduced-comparison.json')
                else:
                    for label,source in [('selected','best'),('final','final')]:
                        path=REVIEW/('native-'+source)/'report.json';report=read(path)
                        require(report['complete_development_cohort'] and {r['case_id'] for r in report['cases']}==set(retained),'Native membership differs')
                        reports.append((70,report,label));artifacts.append(path)
                    artifacts.extend([REVIEW/'audit.json',REVIEW/'results.json'])
                    outcome=read(REVIEW/'results.json')['primary'];client.set_tag(run_id,'intervention_decision',outcome['status'])
                    client.set_tag(run_id,'null_hypothesis_evidence',outcome['null_evidence'])
                for count,report,label in reports:
                    metrics=summarize(report['cases'],native=True)
                    values.extend((f'native/dev{count}/{k}',report['step'],float(v)) for k,v in metrics.items())
                    if label:values.extend((f'summary/{label}/native_dev{count}/{k}',report['step'],float(v)) for k,v in metrics.items())
                    if 'checkpoint_sha256' in report:
                        client.set_tag(run_id,f'checkpoint_step_{report["step"]}_sha256',report['checkpoint_sha256'])
            written,total=import_metrics(client,run_id,values,timestamp)
            for artifact in artifacts:
                # A content-addressed folder makes a repeated copy harmless and prevents name collisions.
                pin=sha256(artifact);client.log_artifact(run_id,str(artifact),artifact_path='evidence/'+pin[:16])
            client.set_tag(run_id,'import_scope','history_and_native' if a.include_native else 'history_only_native_pending')
            client.set_tag(run_id,'import_complete','true')
            client.set_terminated(run_id,status='FINISHED',end_time=int(time.time()*1000))
            receipt=dict(experiment_id=exp_id,mlflow_run_id=run_id,source_run=name,new_metric_points=written,
                verified_metric_points=total,tracking_uri=URI,source_history_sha256=journal_pin,include_native=a.include_native)
            receipts.append(receipt);print(json.dumps(receipt),flush=True)
    destination=REVIEW/('mlflow-backfill-native.json' if a.include_native else 'mlflow-backfill-history.json')
    if destination.exists():
        old=read(destination)
        require([r['mlflow_run_id'] for r in old]==[r['mlflow_run_id'] for r in receipts],'Run identity changed')
    else:
        with destination.open('x') as f:json.dump(receipts,f,indent=2)


if __name__=='__main__':main()
