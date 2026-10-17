"""Explicit selected-checkpoint native evaluation; preserves the frozen 72k experiment."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.experiment_config import sha256
from src.data.source_inventory_records import require
from src.data.manifest_records import canonical
SETUP=Path('E:/PROWL/readiness/pants-ema-72k-20261013-a01')
RUN=Path('E:/PROWL/artifacts/pants_only_ema_72k_20261013')
OUT=Path('E:/PROWL/readiness/pants-selected-native-20261017-a01')
MODELS={'raw':('best-raw.pt',28000),'ema':('best-ema.pt',8000)}

def validate(r):
    for p,h in r['pins'].items():require(sha256(p)==h,'Evidence changed: '+p)
    for v,(name,step) in MODELS.items():
        require(r['models'][v]['step']==step and r['models'][v]['checkpoint']==str(RUN/'execution'/name),'Wrong checkpoint selection')
        require(sha256(r['models'][v]['checkpoint'])==r['models'][v]['sha256'],'Checkpoint changed')

def worker(variant,r,run_id):
    import torch
    from mlflow import MlflowClient
    from scripts.diagnostics.backfill_full_runs_mlflow import URI,summarize
    from src.training import experiment_config as E
    from scripts.train_full_segmenter import session_config
    from src.training.segmenter_full_session_v1 import identity_for
    from src.training.segmenter_ema_v1 import EMASession
    from src.training.segmenter_native_case_v1 import native_case
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    cfg=E.load_experiment(SETUP/'experiment.yaml');p=PreparedInputs(cfg,cfg['full_segmenter']['geometry'])
    identity=dict(version='segmenter-ema-1',raw=identity_for(session_config(cfg),p.control,cfg['device'],cfg['_experiment']['initialization']),alpha=.99,start_step=500)
    torch.set_num_threads(2);m=r['models'][variant]
    s=EMASession.restore(torch.load(m['checkpoint'],map_location='cpu',weights_only=True)['session'],identity)
    require(s.step==m['step'] and p.control['validation']==r['development'],'Step/cohort changed')
    client=MlflowClient(tracking_uri=URI);rows=[];directory=OUT/variant
    with (directory/'cases.jsonl').open('x') as journal,s.weights(variant):
        for index,name in enumerate(r['development'],1):
            row=dict(variant=variant,**native_case(s.raw,p,name));rows.append(row)
            journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush();os.fsync(journal.fileno())
            client.log_metric(run_id,'progress/evaluated_development_cases',index,step=index)
    require(len(rows)==70 and len({x['case_id'] for x in rows})==70,'Incomplete cohort')
    summary=summarize(rows,native=True)
    report=dict(variant=variant,step=s.step,checkpoint_sha256=m['sha256'],identity_sha256=s.identity_pin,
        cases=rows,summary=summary,optimizer_updates=0,test_reads=0,complete_development_cohort=True,
        scope='posthoc_selected_checkpoint_native_development_provided_pancreas',
        size_bands={band:dict(cases=len(v),dice=sum(x['metrics']['lesion']['dice'] for x in v)/len(v),detected=sum(x['metrics']['case_detected'] for x in v))
            for band in ('small','medium','large') if (v:=[x for x in rows if x['metrics']['reference_positive'] and x['metrics']['size_band']==band])})
    (directory/'report.json').write_bytes(canonical(report))
    for k,v in summary.items():client.log_metric(run_id,'native/dev70/'+k,v,step=s.step)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--launch',action='store_true');p.add_argument('--worker',choices=MODELS)
    p.add_argument('--request-sha');p.add_argument('--mlflow-run');a=p.parse_args()
    if a.worker:
        require(a.request_sha==sha256(OUT/'request.json'),'Request changed');r=json.loads((OUT/'request.json').read_text());validate(r)
        return worker(a.worker,r,a.mlflow_run)
    require(a.launch,'Explicit --launch required')
    from src.operations.full_training_platform import training_guard,watch_windows,require_ac
    from scripts.diagnostics.backfill_full_runs_mlflow import URI
    from mlflow import MlflowClient
    receipt=json.loads((SETUP/'ready.json').read_text())
    require(sha256(SETUP/'ready.json')=='8e20da25466bf1fe27205fdbb89633dbe02680a552c61d828cebdf390fb3fee6','Receipt changed')
    for path,h in receipt['file_sha256'].items():require(sha256(path)==h,'Frozen producer changed: '+path)
    control=json.loads((RUN/'input-control.json').read_text());names=control['validation']
    require(len(names)==70 and sum(control['target_states'][n]=='positive' for n in names)==36,'Wrong dev cohort')
    events=[json.loads(s) for s in (RUN/'execution/history.jsonl').read_text().splitlines()]
    require(events[-1]['event']=='completed','Training not complete')
    models={}
    for variant,(name,step) in MODELS.items():
        selected=max((e for e in events if e['event']=='validation' and e['variant']==variant),key=lambda e:e['lesion_positive_macro_dice'])
        require(selected['step']==step,'Selection mismatch')
        checkpoint=RUN/'execution'/name;pin=sha256(checkpoint)
        require(pin==sha256(Path('C:/Users/quinn/PROWL-Backups')/RUN.name/name),'Independent backup mismatch')
        models[variant]=dict(step=step,checkpoint=str(checkpoint),sha256=pin,selection='maximum tensor positive macro Dice within weight variant')
    request=dict(models=models,development=names,pins=dict(receipt['file_sha256']),resources=dict(seconds_per_model=3600,rss_bytes=12*1024**3,free_bytes=100*1024**3,output_bytes=256*1024**2),
        scope='Selected checkpoint diagnostic; no change to fixed endpoint verdicts; no automatic successor')
    for path in (Path(__file__).resolve(),RUN/'input-control.json',RUN/'execution/history.jsonl'):
        request['pins'][str(path)]=sha256(path)
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        OUT.mkdir(exist_ok=False);(OUT/'request.json').write_bytes(canonical(request));pin=sha256(OUT/'request.json')
        client=MlflowClient(tracking_uri=URI);exp=client.get_experiment_by_name('PROWL capstone lesion outlining')
        def tick():
            require_ac()
            for drive in (OUT,Path('C:/')):require(shutil.disk_usage(drive).free>=request['resources']['free_bytes'],'Storage floor')
            require(sum(x.stat().st_size for x in OUT.rglob('*') if x.is_file())<=request['resources']['output_bytes'],'Output ceiling')
        for variant,(_,step) in MODELS.items():
            directory=OUT/variant;directory.mkdir()
            run=client.create_run(exp.experiment_id,tags={'mlflow.runName':f'Native selected PanTS checkpoint: {variant} at {step:,} steps',
                'source_model_run_id':'38cdd18be83449da87275f5ef8b12898','scope':request['scope'],'weight_variant':variant,'request_sha256':pin})
            rid=run.info.run_id;(directory/'tracking.json').write_bytes(canonical(dict(run_id=rid)))
            client.log_artifact(rid,str(OUT/'request.json'),'provenance');process=None
            try:
                tick()
                with (directory/'worker.log').open('x') as log:
                    process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',variant,'--request-sha',pin,'--mlflow-run',rid],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                    watch_windows(process,seconds=3600,rss_bytes=12*1024**3,tick=tick)
                for file in ('report.json','cases.jsonl'):client.log_artifact(rid,str(directory/file),'results')
                client.set_terminated(rid,'FINISHED');print(variant+' complete',flush=True)
            except BaseException:
                client.set_terminated(rid,'FAILED');raise
            finally:
                (directory/'resources.json').write_bytes(canonical(getattr(process,'duration_resources',{})))
                client.log_artifact(rid,str(directory/'resources.json'),'results')

if __name__=='__main__':main()
