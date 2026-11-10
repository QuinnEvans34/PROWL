"""Exclusive, receipt-bound STU-Net stages. No retry or resume entry point."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.operations.full_training_platform import require_ac,training_guard,watch_windows
from scripts.training.supervise_stunet_transfer_20261106_v2 import input_pin


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def write(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2);f.flush();os.fsync(f.fileno())


def size(path):
    return sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file())


from src.operations.stunet_recovery_20261110 import check_storage


def verify(r,mode):
    for path,expected in r['pins'].items():
        if sha(path)!=expected:raise ValueError('Frozen pin mismatch: '+path)
    failure=json.loads(Path(r['failed_resources']).read_text())
    if failure.get('success') is not False or not failure['workers_reaped'] or failure['error']!="RuntimeError('100GiB free-space floor')":raise ValueError('Failure gate')
    if r['approval']!='User approves 50GiB floor and continuation from26k':raise ValueError('Explicit amendment missing')
    if r['rss_bytes']!=12*1024**3 or r['cuda_bytes']!=6*1024**3:raise ValueError('Memory cap changed')
    if mode=='restore':
        if r['seconds']!=300:raise ValueError('Restore cap')
    else:
        qual=json.loads(Path(r['restore_resources']).read_text());proof=json.loads(Path(r['restore_result']).read_text())
        if not qual['success'] or not qual['workers_reaped'] or proof['status']!='PASS' or proof['scientific_updates']!=0:raise ValueError('Restore qualification')
        if r['seconds']!=144000-failure['seconds']-qual['seconds']:raise ValueError('Cumulative budget')


class Tracking:
    def __init__(self,request,client=None):
        digest=input_pin(request)  # Validate before creating a tracking record.
        if client is None:
            from mlflow.tracking import MlflowClient
            client=MlflowClient(tracking_uri='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db')
        self.client=client
        exp=client.get_experiment_by_name('PROWL capstone lesion outlining')
        if exp is None:raise ValueError('Existing MLflow experiment missing')
        run=client.create_run(exp.experiment_id,tags={'mlflow.runName':request['title'],'scope':'exploratory_pretrained_provided_pancreas','training_run_id':request['run_id']})
        self.id=run.info.run_id;self.offset=0;self.losses=0
        try:
            for key,value in dict(steps=10000,global_start=26000,global_end=36000,parent_mlflow='dc0b189042704f51af9dbb2deed5f5a6',parent_checkpoint_sha256=request['restore_checkpoint_sha256'],annotation_policy='pants-issue12-local-normal-mask-1',peak_learning_rate=2e-5,seed=42,window=128,batch_size=1,precision='fp32',wall_seconds=request['seconds'],input_sha256=digest).items():
                client.log_param(self.id,key,value)
        except BaseException:
            client.set_terminated(self.id,status='FAILED');raise

    def sync(self,path):
        from mlflow.entities import Metric
        if not Path(path).exists():return
        metrics=[]
        with Path(path).open(encoding='utf-8') as f:
            f.seek(self.offset)
            while True:
                pos=f.tell();line=f.readline()
                if not line or not line.endswith('\n'):f.seek(pos);break
                row=json.loads(line);kind=row['event'];step=row.get('step',0);now=row['utc_ms']
                if kind=='update':
                    metrics.extend([Metric('train/loss',row['loss'],now,step),Metric('train/learning_rate',row['learning_rate'],now,step)]);self.losses+=1
                elif kind=='native_completed':
                    metrics.extend(Metric('native/'+k,row[k],now,step) for k in ('lesion_dice','detected','alarms','positive','empty'))
                self.offset=f.tell()
        for i in range(0,len(metrics),500):self.client.log_batch(self.id,metrics=metrics[i:i+500])


def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--sha256',required=True);p.add_argument('--mode',required=True,choices=['restore','science']);a=p.parse_args()
    request=Path(a.request)
    if sha(request)!=a.sha256:raise ValueError('Exact request hash required')
    r=json.loads(request.read_text());verify(r,a.mode);require_ac();check_storage()
    if os.path.normcase(os.path.abspath(sys.executable))!=os.path.normcase(os.path.abspath(r['supervisor_base_python'])):raise ValueError('Wrong supervisor interpreter')
    if a.mode=='science':
        from mlflow.tracking import MlflowClient
        if MlflowClient(tracking_uri='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db').get_experiment_by_name('PROWL capstone lesion outlining') is None:raise ValueError('Tracking preflight failed')
        input_pin(r)
    out=Path(r['stage_root']);out.mkdir(exist_ok=False);child=None;tracking=None
    write(out/'dispatch.json',dict(request=str(request),sha256=a.sha256,mode=a.mode,supervisor=os.getpid()))
    try:
        with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
            verify(r,a.mode)
            gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
            if gpu:raise RuntimeError('Foreign GPU compute owner')
            reserve=(5 if a.mode=='science' else 0)*698166891+64*1024**2
            if size('C:/Users/quinn/PROWL-Backups')+reserve>88*1024**3 or shutil.disk_usage('C:/').free-reserve<50*1024**3:raise RuntimeError('Projected backup admission')
            if a.mode=='science':
                # A new root is mandatory, including for failed starts; never resume.
                artifact=Path(r['artifact']);artifact.mkdir(exist_ok=False);(artifact/'splits').mkdir()
                config=json.loads(Path(r['inputs']).read_text());plan=json.loads(Path(config['plan']).read_text())
                (artifact/'splits/train_ids.txt').write_text('\n'.join(sorted(plan['members']))+'\n')
                (artifact/'resolved.yaml').write_text(json.dumps({'_experiment':{'run':{'max_updates':36000,'start_update':26000,'validate_every':2000}}}))
                output=artifact/'execution'
            else:output=out/'worker'
            command=[r['python'],str(ROOT/'scripts/training/recover_stunet_longer_20261110.py'),'--request',str(request),'--mode',a.mode,'--output',str(output)]
            with (out/'worker.log').open('x') as log:
                child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                write(out/'owner.json',dict(worker=child.pid,supervisor=os.getpid(),command=command))
                last=[0.,0.]
                def tick():
                    import psutil
                    require_ac();now=time.monotonic()
                    # watch_windows accounts for worker descendants; include this supervisor too.
                    try:
                        root=psutil.Process(child.pid);owned=[root]+root.children(recursive=True)
                    except psutil.NoSuchProcess:owned=[]
                    rss=psutil.Process().memory_info().rss
                    for process in owned:
                        try:rss+=process.memory_info().rss
                        except psutil.NoSuchProcess:pass
                    if rss>12*1024**3:raise RuntimeError('Combined owned RSS cap')
                    if now-last[0]>60:check_storage();last[0]=now
                    if tracking is not None and now-last[1]>10:tracking.sync(output/'history.jsonl');last[1]=now
                # Tracking initialization happens inside supervision so any failure reaps worker.
                def initialize_tick():
                    nonlocal tracking
                    if a.mode=='science' and tracking is None:
                        tracking=Tracking(r);write(out/'mlflow.json',dict(run_id=tracking.id))
                    tick()
                result=watch_windows(child,seconds=r['seconds'],rss_bytes=r['rss_bytes'],tick=initialize_tick)
                if tracking:
                    tracking.sync(output/'history.jsonl')
                    if tracking.losses!=10000:raise ValueError('MLflow loss count incomplete')
                    tracking.client.log_artifact(tracking.id,str(output/'result.json'))
                    tracking.client.set_terminated(tracking.id,status='FINISHED')
                write(out/'resources.json',dict(result,success=True,exit_code=child.returncode))
    except BaseException as e:
        if child is not None and child.poll() is None:
            # Failures before watch_windows starts must not leave an unowned worker.
            import psutil
            parent=psutil.Process(child.pid);children=parent.children(recursive=True)
            for process in children+[parent]:
                try:process.kill()
                except psutil.NoSuchProcess:pass
            child.wait(timeout=10);psutil.wait_procs(children,timeout=10)
        if tracking:
            tracking.client.set_terminated(tracking.id,status='FAILED')
        write(out/'resources.json',dict(getattr(child,'duration_resources',{}),success=False,error=repr(e)))
        raise


if __name__=='__main__':main()
