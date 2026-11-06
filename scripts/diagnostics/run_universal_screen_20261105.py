"""One permit-bound inference-only Universal screen. No resume or retry path."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.inference.universal_model_loading_20261105 import digest
PREP=Path('E:/PROWL/readiness/universal-swin-20261105-a01')
MODEL=Path('E:/PROWL/teachers/clip-universal-76f0304-20261105')
OUT=Path('E:/PROWL/artifacts/universal-swin-screen-20261105-a01')
BACKUP=Path('C:/Users/quinn/PROWL-Backups/universal-swin-screen-20261105-a01')
PYTHON=Path('C:/Users/quinn/.cache/prowl-week05-matched-20261102-a01/venv/Scripts/python.exe')
EINOPS=Path('E:/PROWL/teachers/medformer-pants-b854c824/dependencies')


def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


def tree_bytes(path):
    return sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file()) if Path(path).exists() else 0


def validate_permit(permit, request_hash, spec_hash):
    expected={'schema':'prowl.post-kd-trial-permit.v1','action':'one_fresh_exploratory_universal_swin_trial',
              'trial_request_sha256':request_hash,'specification_sha256':spec_hash,
              'kd_execution_closeout_verified':True,'automatic_retry':False,
              'authorizes_additional_experiments':False,'maximum_dispatches':1}
    if any(permit.get(k)!=v for k,v in expected.items()):raise ValueError('Invalid or wrong-request KD completion permit')
    for k in ('kd_ready_sha256','kd_report_sha256'):
        v=permit.get(k,'')
        if len(v)!=64 or any(c not in '0123456789abcdef' for c in v):raise ValueError('Missing KD evidence identity')


def read_request(pin, *, full=False):
    p=PREP/'request.json'
    if digest(p)!=pin:raise ValueError('Wrong request hash')
    r=json.loads(p.read_text())
    for path,sha in r['pins'].items():
        stat=Path(path).stat()
        if [stat.st_size,stat.st_mtime_ns]!=r['pin_observations'][path]:raise ValueError('Producing file observation changed: '+path)
        # All bytes are verified before dispatch. Large unchanged dependency files
        # then use bound size/mtime observations; code/data source checks remain exact.
        if full or path not in r['environment_dependency_paths']:
            if digest(path)!=sha:raise ValueError('Producing pin changed: '+path)
    if r['cases']!=['PanTS_00002028','PanTS_00001347','PanTS_00002514','PanTS_00008743'] or r['training_admission']!='NOT_ADMITTED':
        raise ValueError('Frozen inference scope mismatch')
    return r


def gate():
    from src.operations.full_training_platform import require_ac
    require_ac()
    for path in ('C:/','E:/'):
        if shutil.disk_usage(path).free<100*1024**3:raise RuntimeError('Free space floor')
    if tree_bytes(OUT)>8*1024**3 or tree_bytes(BACKUP)>8*1024**3 or tree_bytes(BACKUP.parent)>64*1024**3:
        raise RuntimeError('Storage cap')


def backup_file(path):
    dest=BACKUP/Path(path).relative_to(OUT);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise FileExistsError('Backup already exists')
    shutil.copyfile(path,dest)
    if digest(path)!=digest(dest):raise ValueError('Independent backup differs')


def journal(event,**fields):
    with (OUT/'journal.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'event':event,'utc':time.time(),**fields},allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())


def worker(stage,pin,case_id):
    r=read_request(pin);gate()
    dispatch=json.loads((PREP/'dispatch.json').read_text())
    if dispatch['request_sha256']!=pin or digest(OUT/'permit.json')!=dispatch['permit_sha256']:
        raise ValueError('Worker requires the owned permit-bound dispatch')
    validate_permit(json.loads((OUT/'permit.json').read_text()),pin,r['specification_sha256'])
    sys.path.insert(0,str(EINOPS))
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.manual_seed(42)
    torch.backends.cudnn.benchmark=False;torch.backends.cudnn.allow_tf32=False
    torch.backends.cuda.matmul.allow_tf32=False
    stage_dir=OUT/(stage if case_id is None else stage+'-'+case_id)
    if stage=='score':
        import nibabel as nib
        import numpy as np
        from src.inference.saved_prediction_scoring import score_saved
        from src.inference.four_case_metrics_20261102 import components
        case=next(c for c in r['inputs'] if c['case_id']==case_id)
        prediction=json.loads((OUT/('infer-'+case_id)/'result.json').read_text())
        p=prediction['files']['prediction']
        score=score_saved(p['path'],case['files']['pancreas'],case['files']['lesion'],
            expected_prediction_sha256=p['sha256'],expected_pancreas_sha256=case['source_sha256']['pancreas'],
            expected_lesion_sha256=case['source_sha256']['lesion'],allow_unknown_reference_units=False)
        pred=nib.load(p['path']); target=nib.load(case['files']['lesion'])
        score['lesion_components']=components(np.asarray(pred.dataobj)==2,np.asarray(target.dataobj)==1,pred.affine)
        for metric in score['metrics'].values():
            metric['precision']=metric['true_positive']/metric['predicted_voxels'] if metric['predicted_voxels'] else None
        score['case_id']=case_id;write(stage_dir/'result.json',score);return
    from src.inference.universal_model_loading_20261105 import load_cpu
    checkpoint=BACKUP/'initial.pth' if stage=='restore' else MODEL/'checkpoint.pth'
    model,loaded=load_cpu(MODEL/'source',checkpoint,json.loads((MODEL/'source-receipt.json').read_text()))
    if stage=='restore':
        original=json.loads((OUT/'pilot'/'result.json').read_text())['loaded']
        if loaded['loaded_state_sha256']!=original['loaded_state_sha256']:raise ValueError('Independent cold reload differs')
        write(stage_dir/'result.json',{'strict_cpu_restore_equal':True,'loaded':loaded});return
    torch.cuda.set_per_process_memory_fraction((6*1024**3)/torch.cuda.get_device_properties(0).total_memory)
    torch.cuda.reset_peak_memory_stats();model.to('cuda').eval()
    if stage=='pilot':
        with torch.inference_mode():
            x=torch.linspace(0,1,96**3,device='cuda').reshape(1,1,96,96,96)
            y=model(x)
            if tuple(y.shape)!=(1,32,96,96,96) or not torch.isfinite(y).all():raise ValueError('Pilot output')
            selected=y[:,[10,27]]
            if not torch.equal(selected[:,0],y[:,10]) or not torch.equal(selected[:,1],y[:,27]):raise ValueError('Pilot head selection')
        peak=max(torch.cuda.max_memory_allocated(),torch.cuda.max_memory_reserved())
        if peak>6*1024**3:raise RuntimeError('Pilot GPU cap')
        write(stage_dir/'result.json',{'loaded':loaded,'shape':list(y.shape),'finite':True,
            'head_mapping_verified':True,'peak_cuda_allocated':torch.cuda.max_memory_allocated(),
            'peak_cuda_reserved':torch.cuda.max_memory_reserved(),'optimizer_updates':0,
            'input':'deterministic synthetic96cube; actual upstream CUDA forward'});return
    if stage!='infer':raise ValueError('Unsupported stage')
    from src.inference.universal_native_20261105 import prepare_ct,run_raw
    case=next(c for c in r['inputs'] if c['case_id']==case_id)
    image,geometry=prepare_ct(case['files']['ct'],case['source_sha256']['ct'],case['headers']['ct'])
    # This worker never opens the reference files. Scoring is a separate CPU process.
    result=run_raw(model,image,geometry,stage_dir/'prediction',remaining_seconds=r['case_seconds'],
                   on_patch=lambda p:journal('inference_patch',case_id=case_id,**p))
    write(stage_dir/'result.json',result)


def launch(pin,permit_path,permit_sha):
    from src.operations.full_training_platform import training_guard,watch_windows
    r=read_request(pin,full=True)
    if digest(permit_path)!=permit_sha:raise ValueError('Permit hash mismatch')
    permit=json.loads(Path(permit_path).read_text());validate_permit(permit,pin,r['specification_sha256'])
    if OUT.exists() or BACKUP.exists() or (PREP/'dispatch.json').exists():raise FileExistsError('One-shot already started')
    gate()
    processes=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
    if processes:raise RuntimeError('GPU already owned')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        OUT.mkdir();BACKUP.mkdir();start=time.monotonic()
        write(PREP/'dispatch.json',{'request_sha256':pin,'permit_sha256':permit_sha,'pid':os.getpid(),'started_utc':time.time()})
        shutil.copyfile(PREP/'request.json',OUT/'request.json');backup_file(OUT/'request.json')
        shutil.copyfile(permit_path,OUT/'permit.json');backup_file(OUT/'permit.json')
        from mlflow.tracking import MlflowClient
        from scripts.diagnostics.backfill_full_runs_mlflow import URI
        client=MlflowClient(tracking_uri=URI);name='PROWL exploratory pretrained inference'
        exp=client.get_experiment_by_name(name);eid=exp.experiment_id if exp else client.create_experiment(name)
        run=client.create_run(eid,tags={'mlflow.runName':'Larger Universal Swin: four positive native cases',
            'scope':'EXPLORATORY_EXTERNAL_EXPOSURE_UNKNOWN','kind':'inference_only','training_admission':'NOT_ADMITTED',
            'request_sha256':pin,'training_hours':'0','empty_alarm_rate':'NOT_MEASURED'})
        runid=run.info.run_id;write(OUT/'mlflow.json',{'run_id':runid,'tracking_uri':URI});backup_file(OUT/'mlflow.json')
        try:
            pilot_started=time.monotonic()
            shutil.copyfile(MODEL/'checkpoint.pth',OUT/'initial.pth');backup_file(OUT/'initial.pth')
            stages=[('pilot',None),('restore',None)]
            for case in r['cases']:stages.extend([('infer',case),('score',case)])
            scores=[]
            for stage,case in stages:
                read_request(pin);gate()
                remaining=21600-r['charged_preparation_seconds']-(time.monotonic()-start)
                if stage in ('pilot','restore'):remaining=min(remaining,600-(time.monotonic()-pilot_started))
                if remaining<=0:raise RuntimeError('Cumulative experiment budget')
                folder=OUT/(stage if case is None else stage+'-'+case);folder.mkdir(exist_ok=False)
                journal('stage_started',stage=stage,case_id=case)
                command=[str(PYTHON),str(Path(__file__).resolve()),'--worker',stage,'--request-sha256',pin]
                if case:command+=['--case-id',case]
                with (folder/'worker.log').open('w') as log:
                    env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
                    if stage in ('restore','score'):env['CUDA_VISIBLE_DEVICES']=''
                    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT,env=env)
                    last_gate=[0.]
                    def tick():
                        if time.monotonic()-last_gate[0]>10:gate();last_gate[0]=time.monotonic()
                    try:
                        resources=watch_windows(process,seconds=min(600 if stage in ('pilot','restore','score') else r['case_seconds'],remaining),rss_bytes=12*1024**3,tick=tick)
                    finally:
                        write(folder/'resources.json',dict(getattr(process,'duration_resources',{}),exit_code=process.poll()))
                if not resources['workers_reaped']:raise RuntimeError('Workers not reaped')
                for path in folder.rglob('*'):
                    if path.is_file():backup_file(path)
                client.log_metric(runid,'stage_seconds',resources['seconds'],step=len(scores))
                journal('stage_completed',stage=stage,case_id=case,resources=resources)
                if stage=='score':
                    score=json.loads((folder/'result.json').read_text());scores.append(score)
                    for key,value in score['metrics']['lesion'].items():
                        if value is not None:client.log_metric(runid,'lesion_'+key,float(value),step=len(scores))
            summary={'status':'COMPLETED_DESCRIPTIVE_ONLY','cases':r['cases'],
                'positive_lesion_macro_dice':sum(s['metrics']['lesion']['dice'] for s in scores)/4,
                'training_admission':'NOT_ADMITTED','optimizer_updates':0,'empty_alarm_rate':None,
                'empty_alarm_reason':'No admitted negative cases','hypothesis_verdict':'NOT_TESTED',
                'elapsed_seconds':time.monotonic()-start,'charged_preparation_seconds':r['charged_preparation_seconds'],
                'request_sha256':pin,'scores':scores}
            write(OUT/'summary.json',summary);backup_file(OUT/'summary.json')
            client.log_metric(runid,'positive_lesion_macro_dice',summary['positive_lesion_macro_dice'])
            client.log_artifact(runid,str(OUT/'summary.json'))
            client.set_terminated(runid,'FINISHED')
            if client.get_run(runid).info.status!='FINISHED':raise RuntimeError('Tracking closeout')
            journal('completed',run_id=runid);backup_file(OUT/'journal.jsonl')
        except BaseException as exc:
            write(OUT/'failure.json',{'type':type(exc).__name__,'message':str(exc),'seconds':time.monotonic()-start})
            client.set_terminated(runid,'FAILED')
            for path in OUT.rglob('*'):
                if path.is_file() and not (BACKUP/path.relative_to(OUT)).exists():backup_file(path)
            raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request-sha256',required=True)
    p.add_argument('--worker',choices=['pilot','restore','infer','score']);p.add_argument('--case-id')
    p.add_argument('--permit');p.add_argument('--permit-sha256');a=p.parse_args()
    if a.worker:worker(a.worker,a.request_sha256,a.case_id)
    elif a.permit and a.permit_sha256:launch(a.request_sha256,a.permit,a.permit_sha256)
    else:p.error('Exact permit path/hash required')
