"""Explicit-launch, supervised native TRAINING evaluation; zero optimizer updates."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.source_inventory_records import require
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256


def validate(request):
    require(request['version']=='training-fit-1' and len(request['models'])==2,'Wrong request')
    require(len(request['cases'])==100 and len(set(request['cases']))==100,'Invalid sample')
    for p,h in request['pins'].items():require(sha256(p)==h,'Producing evidence changed: '+p)
    for m in request['models']:
        require(sha256(m['experiment'])==m['experiment_sha256'],'Configuration changed')
        require(sha256(m['checkpoint'])==m['checkpoint_sha256'],'Checkpoint changed')


def worker(a,r):
    import nibabel as nib
    import numpy as np
    import torch
    from src.training import experiment_config as E
    from src.training.segmenter_full_session_v1 import Session, identity_for
    from src.training.pants_native_evaluation import native_metrics
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.data.segmenter_full_inputs_v1 import Inputs
    from src.data.segmenter_content_v1 import target_content
    from src.data.segmenter_geometry_v2 import restore_codes
    from scripts.train_full_segmenter import session_config
    from scripts.diagnostics.backfill_full_runs_mlflow import URI, summarize
    from mlflow import MlflowClient
    m=r['models'][a.worker];cfg=E.load_experiment(m['experiment'])
    p=PreparedInputs(cfg,cfg['full_segmenter']['geometry'])
    require(p.pin==m['control_sha256'],'Input identity changed')
    require(set(r['cases'])<=set(p.control['train']) and not set(r['cases'])&set(p.control['validation']),'Wrong case roles')
    require(sum(p.control['target_states'][n]=='positive' for n in r['cases'])==50,'Sample class count changed')
    saved=torch.load(m['checkpoint'],map_location='cpu',weights_only=True)
    s=Session.restore(saved['session'],identity_for(session_config(cfg),p.control,cfg['device'],cfg['_experiment']['initialization']))
    require(s.step==m['step'],'Checkpoint step differs');torch.set_num_threads(2)
    client=MlflowClient(tracking_uri=URI);rows=[]
    with (a.output/'cases.jsonl').open('x') as journal:
        for index,name in enumerate(r['cases'],1):
            _,x,_=s._batch(p,name,'train','evaluator')
            meta=json.loads((p.root/(name+'.json')).read_text());affine=np.asarray(meta['transform']['source_affine'])
            with torch.no_grad(),s.rng_scope():
                s.model.eval();logits=s.model(x[None].to(s.device))
                require(torch.isfinite(logits).all().item(),'Nonfinite prediction')
                codes=logits.argmax(1)[0].cpu().numpy().astype(np.uint8)
            restored=restore_codes(codes,meta['transform'],trusted_record_sha256=meta['transform_sha256'])
            labels={}
            for kind in ('pancreas','lesion'):
                path=Path(p.rows[name][kind+'_path']);require(E.sha256(path)==meta['source_sha256'][kind],'Native reference changed')
                obj=nib.load(path);require(obj.shape==restored.shape and np.allclose(obj.affine,affine,atol=1e-5,rtol=0),'Native geometry differs')
                proxy=obj.dataobj;labels[kind],_=target_content(proxy.get_unscaled(),dict(slope=float(proxy.slope),intercept=float(proxy.inter)))
                require(Inputs.observe(path)==p.source['observations'][name][kind],'Reference changed during evaluation')
            row=dict(case_id=name,step=s.step,metrics=native_metrics(restored,labels['pancreas'],labels['lesion'],affine))
            journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush();rows.append(row)
            client.log_metric(a.mlflow_run,'progress/evaluated_training_cases',index,step=index)
    summary=summarize(rows,native=True)
    report=dict(scope=r['scope'],checkpoint_sha256=m['checkpoint_sha256'],step=s.step,cases=rows,summary=summary,
        optimizer_updates=0,test_reads=0,complete_training_sample=True,
        size_bands={band:dict(cases=len(v),lesion_dice=sum(x['metrics']['lesion']['dice'] for x in v)/len(v))
            for band in ('small','medium','large') if (v:=[x for x in rows if x['metrics']['reference_positive'] and x['metrics']['size_band']==band])})
    (a.output/'report.json').write_bytes(canonical(report))
    for key,value in summary.items():client.log_metric(a.mlflow_run,'native/train100/'+key,value,step=s.step)
    dev=json.loads(Path(r['development_references'][a.worker]).read_text())
    cases=dev['reports']['best']['cases'] if a.worker==0 else dev['cases']
    dev_summary=summarize(cases,native=True)
    for key,value in dev_summary.items():client.log_metric(a.mlflow_run,'native/dev70/'+key,value,step=s.step)
    for key in ('lesion_positive_macro_dice','empty_alarm_fraction','detected_case_fraction'):
        client.log_metric(a.mlflow_run,'descriptive_train_minus_dev/'+key,summary[key]-dev_summary[key],step=s.step)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True)
    p.add_argument('--sha256',required=True);p.add_argument('--launch',action='store_true')
    p.add_argument('--worker',type=int,choices=[0,1]);p.add_argument('--output',type=Path);p.add_argument('--mlflow-run')
    a=p.parse_args();require(sha256(a.request)==a.sha256,'Request changed');r=json.loads(a.request.read_text());validate(r)
    if a.worker is not None:
        require(a.launch and a.output and a.mlflow_run,'Worker requires explicit dispatch');return worker(a,r)
    if not a.launch:print('Read-only preflight passed; no inference or training started.');return
    from mlflow import MlflowClient
    from scripts.diagnostics.backfill_full_runs_mlflow import URI
    from src.operations.full_training_platform import training_guard,watch_windows,require_ac
    output=a.request.parent/'execution';output.mkdir(exist_ok=False)
    client=MlflowClient(tracking_uri=URI);experiment=client.get_experiment_by_name('PROWL capstone lesion outlining')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        for index,m in enumerate(r['models']):
            directory=output/str(index);directory.mkdir()
            run=client.create_run(experiment.experiment_id,tags={'mlflow.runName':'Training-fit diagnostic — '+m['title'],
                'stage':'native_training_evaluation','source_model_run_id':m['parent_mlflow_run_id'],
                'request_sha256':a.sha256,'scope':r['scope'],'optimizer_updates':'0','test_reads':'0'})
            run_id=run.info.run_id;(directory/'tracking.json').write_bytes(canonical(dict(run_id=run_id,tracking_uri=URI)))
            client.log_artifact(run_id,str(a.request),'evidence')
            def tick():
                require_ac()
                for drive in (output,Path('C:/')):require(shutil.disk_usage(drive).free>=r['resources']['free_floor_bytes'],'Storage floor')
                require(sum(f.stat().st_size for f in output.rglob('*') if f.is_file())<=r['resources']['output_bytes'],'Output ceiling')
            process=None
            try:
                tick()
                with (directory/'worker.log').open('x') as log:
                    process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--request',str(a.request),
                        '--sha256',a.sha256,'--launch','--worker',str(index),'--output',str(directory),'--mlflow-run',run_id],
                        cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                    watch_windows(process,seconds=r['resources']['seconds_per_model'],rss_bytes=r['resources']['rss_bytes'],tick=tick)
                client.log_artifact(run_id,str(directory/'cases.jsonl'),'evidence');client.log_artifact(run_id,str(directory/'report.json'),'evidence')
                client.set_terminated(run_id,'FINISHED')
            except BaseException:
                client.set_terminated(run_id,'FAILED');raise
            finally:
                (directory/'resources.json').write_bytes(canonical(getattr(process,'duration_resources',{})))
                client.log_artifact(run_id,str(directory/'resources.json'),'evidence')
    print('Both training-fit evaluations complete. No training updates performed.')


if __name__=='__main__':main()
