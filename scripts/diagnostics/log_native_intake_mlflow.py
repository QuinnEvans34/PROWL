"""Backfill engineering qualification, never present oracle Dice as model Dice."""
import argparse
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_native_intake import OUT
from src.training.experiment_config import sha256
from src.data.manifest_records import canonical


def main():
    from mlflow import MlflowClient
    from mlflow.entities import Metric, Param, RunTag
    saved=OUT/'mlflow.json'
    if saved.exists():raise ValueError('Existing MLflow receipt; inspect rather than duplicate')
    ready=json.loads((OUT/'ready.json').read_text());summary=json.loads((OUT/'summary.json').read_text())
    if ready['status']!='INTAKE_VERIFIED_REVIEW_REQUIRED' or sha256(OUT/'summary.json')!=ready['summary_sha256']:
        raise ValueError('Qualification receipt mismatch')
    client=MlflowClient(tracking_uri='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db')
    name='PROWL input engineering'
    experiment=client.get_experiment_by_name(name)
    artifact_root=Path('C:/Users/quinn/PROWL-Tracking/artifacts/input-engineering').as_uri()
    if experiment and experiment.artifact_location.rstrip('/')!=artifact_root:
        raise ValueError('Existing engineering experiment has an unexpected artifact destination')
    eid=experiment.experiment_id if experiment else client.create_experiment(name,artifact_location=artifact_root)
    existing=client.search_runs([eid],filter_string="tags.qualification_receipt_sha256 = '"+sha256(OUT/'ready.json')+"'")
    if existing:raise ValueError('Already logged receipt; reconcile existing run')
    run=client.create_run(eid,tags={'mlflow.runName':'Preserve every annotated lesion voxel — input qualification',
        'purpose':'engineering_qualification','nonpromotable':'true','scientific_training':'false',
        'backfilled':'true','qualification_receipt_sha256':sha256(OUT/'ready.json'),
        'metric_scope':'target fidelity and engineering only; not learned-model Dice',
        'initial_cohort_parser_failure':'preserved; zero cases read; corrected under explicit amendment'})
    rid=run.info.run_id;now=int(time.time()*1000)
    # Write the run identity immediately so a later failure cannot silently duplicate it.
    with saved.open('xb') as f:f.write(canonical(dict(run_id=rid,status='CREATED',experiment_id=eid)))
    values={'engineering/train_cases':1333,'engineering/development_cases':70,
            'engineering/min_field_coverage':summary['field_coverage_min'],
            'engineering/min_target_roundtrip_dice':summary['positive_target_roundtrip_dice_min'],
            'engineering/min_scheduled_annotation_coverage':summary['annotated_field_training_exposure_min'],
            'engineering/new_exclusions':0,'engineering/regression_passed':summary['tests']['tests']-summary['tests']['skipped'],
            'engineering/cold_next_update_max_difference':summary['cuda']['next_update_max_absolute_difference'],
            'engineering/nonpromotable_producer_updates':4,'engineering/nonpromotable_cold_updates':1}
    client.log_batch(rid,metrics=[Metric(k,float(v),now,0) for k,v in values.items()],
        params=[Param('input_policy',summary['input_policy']['version']),Param('window_voxels','144x144x144'),Param('stride_voxels','72'),
                Param('physical_spacing','upsample-only to <=1.00001mm; preserve finer axes' if summary['input_kind']=='physical' else 'acquired'),
                Param('inference_scope','full_CT_no_annotation_cropping')],
        tags=[RunTag('readiness',ready['status'])])
    client.log_artifact(rid,str(OUT/'summary.json'),'qualification')
    client.log_artifact(rid,str(OUT/'ready.json'),'qualification')
    client.set_terminated(rid,status='FINISHED')
    result=client.get_run(rid)
    if result.info.status!='FINISHED' or any(result.data.metrics.get(k)!=float(v) for k,v in values.items()):
        raise ValueError('MLflow readback mismatch')
    # Completion is a separate immutable receipt; retain the creation receipt.
    with (OUT/'mlflow-finished.json').open('xb') as f:f.write(canonical(dict(run_id=rid,status='FINISHED',metrics_verified=len(values))))
    print(json.dumps(dict(run_id=rid,status='FINISHED',metrics_verified=len(values))))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--kind',choices=['native','physical'],default='native');a=ap.parse_args()
    if a.kind=='physical':
        from scripts.diagnostics.qualify_physical_intake import OUT
    main()
