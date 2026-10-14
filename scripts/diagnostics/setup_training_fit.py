"""Freeze a shared PanTS training-fit sample and register setup in local MLflow. No inference."""
import json
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require
from src.training.experiment_config import sha256
from scripts.diagnostics.backfill_full_runs_mlflow import URI, TRACKING

OUT=Path('E:/PROWL/readiness/training-fit-20261013-a01')
SEED=20261013


def select_cases(a,b,n=50,seed=SEED):
    require(set(a['train'])==set(b['train']), 'PanTS training membership differs')
    require(not set(a['train']).intersection(set(a['validation'])|set(b['validation'])), 'Training/development overlap')
    require(all(a['target_states'][x]==b['target_states'][x] for x in a['train']), 'Target semantics differ')
    rng=random.Random(seed);chosen=[]
    for state in ('positive','reference_empty'):
        pool=sorted(x for x in a['train'] if a['target_states'][x]==state)
        require(len(pool)>=n, 'Insufficient training members')
        chosen.extend(rng.sample(pool,n))
    return chosen


def main():
    from mlflow import MlflowClient
    require(not OUT.exists(),'Setup already exists; inspect it, do not overwrite/reselect')
    parent=Path('E:/PROWL/artifacts/pants_course_reference_dicefocal_24k_20261011')
    mixed=Path('E:/PROWL/artifacts/pants_plus_expert_panorama_dicefocal_24k_20261012')
    def control(path):
        with (path/'execution/history.jsonl').open() as f:return json.loads(next(f))['identity']['control']
    a,b=control(parent),control(mixed)
    require(set(a['train'])=={x for x in b['train'] if not x.startswith('panorama:')},'Unexpected PanTS membership')
    reduced_b=dict(b,train=[x for x in b['train'] if not x.startswith('panorama:')])
    names=select_cases(a,reduced_b)
    models=[]
    for title,run,config,step,tracking in [
        ('PanTS-only selected model',parent,'pants-course-reference-20261011-a01',14000,'67d11609cc78406b86145f13e24ec61b'),
        ('PANORAMA-added selected model',mixed,'panorama-positive-run-20261012-a01',8000,'c038332411df4f38bf52d650810c77c0')]:
        path=Path('E:/PROWL/readiness')/config/'experiment.yaml';checkpoint=run/'execution/best.pt'
        models.append(dict(title=title,experiment=str(path),checkpoint=str(checkpoint),step=step,
            experiment_sha256=sha256(path),checkpoint_sha256=sha256(checkpoint),control_sha256=digest(canonical(control(run))),
            parent_mlflow_run_id=tracking))
    files=[*list((ROOT/'src').rglob('*.py')),ROOT/'scripts/train_full_segmenter.py',
        Path(__file__),ROOT/'scripts/diagnostics/run_training_fit.py',ROOT/'scripts/diagnostics/backfill_full_runs_mlflow.py',
        ROOT/'docs/capstone/operations/TRAINING-FIT-EMA-HORIZON-20261013.md']
    references=[Path('E:/PROWL/readiness/panorama-positive-run-20261012-a01/parent-reduced-comparison.json'),
        Path('E:/PROWL/readiness/panorama-positive-review-20261013-a01/native-best/report.json')]
    request=dict(version='training-fit-1',title='Do our completed models fit their own training scans?',
        status='setup_complete_not_executed',seed=SEED,cases=names,positive=50,reference_empty=50,models=models,
        scope='PanTS_training_only_native_provided_ROI',optimizer_updates=0,test_reads=0,
        development_references=[str(p) for p in references],
        pins={str(p):sha256(p) for p in files+references},
        resources=dict(seconds_per_model=3600,rss_bytes=12*1024**3,output_bytes=1024**3,free_floor_bytes=100*1024**3),
        interpretation='Descriptive training/development gap; no causal capacity verdict or hypothesis acceptance. PANORAMA training fit not assessed.')
    OUT.mkdir(parents=True);(OUT/'request.json').write_bytes(canonical(request))
    client=MlflowClient(tracking_uri=URI);exp=client.get_experiment_by_name('PROWL capstone lesion outlining')
    require(exp is not None,'Existing private experiment missing')
    run=client.create_run(exp.experiment_id,tags={'mlflow.runName':'SETUP — training-fit diagnostic before EMA / longer training',
        'stage':'setup_only','scientific_execution':'not_started','request_sha256':sha256(OUT/'request.json'),
        'scope':'no_inference_no_optimizer_updates_no_test_reads'})
    for k,v in {'sample_seed':SEED,'positive_cases':50,'reference_empty_cases':50,'models':2}.items():client.log_param(run.info.run_id,k,v)
    client.log_artifact(run.info.run_id,str(OUT/'request.json'),'setup')
    client.log_artifact(run.info.run_id,str(files[-1]),'setup')
    client.set_terminated(run.info.run_id,'FINISHED')
    receipt=dict(request_sha256=sha256(OUT/'request.json'),setup_mlflow_run_id=run.info.run_id,tracking_uri=URI,
        status='setup_complete_not_executed')
    (OUT/'setup-receipt.json').write_bytes(canonical(receipt));print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
