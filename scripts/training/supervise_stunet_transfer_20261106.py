"""Exclusive, receipt-bound STU-Net stages. No retry or resume entry point."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.operations.full_training_platform import require_ac,training_guard,watch_windows


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


def check_storage():
    import ctypes
    ids=[]
    for drive,expected in [('C:/','9ed7859f-4768-4f11-9788-792a793f0ee4'),('E:/','424d39a3-ac76-4f41-aa1c-8b9f5ce0b829')]:
        buf=ctypes.create_unicode_buffer(256)
        if not ctypes.windll.kernel32.GetVolumeNameForVolumeMountPointW(drive.replace('/','\\'),buf,256):raise OSError('Volume identity unavailable')
        if expected not in buf.value.lower():raise ValueError('Volume identity changed')
        ids.append(buf.value)
        if shutil.disk_usage(drive).free<100*1024**3:raise RuntimeError('100GiB free-space floor')
    if ids[0]==ids[1]:raise ValueError('Backup volumes are not distinct')
    if size('C:/Users/quinn/PROWL-Backups')>64*1024**3:raise RuntimeError('64GiB backup cap')
    if size('E:/PROWL/cache')>32*1024**3:raise RuntimeError('32GiB cache cap')


def verify(r,mode):
    for path,expected in r['pins'].items():
        if sha(path)!=expected:raise ValueError('Frozen pin mismatch: '+path)
    if r['seconds']!=(216000 if mode=='science' else 1200):raise ValueError('Wall cap changed')
    if r['rss_bytes']!=12*1024**3 or r['cuda_bytes']!=6*1024**3:raise ValueError('Memory cap changed')
    if mode=='science':
        if r['approval']!='Approve a 60-hour cap':raise ValueError('Wall amendment missing')
        for label in ('producer_resources','cold_resources'):
            resource=json.loads(Path(r[label]).read_text())
            if not resource['success'] or not resource['workers_reaped']:raise ValueError('Qualification not complete/reaped')
        for label in ('producer_result','cold_result'):
            if json.loads(Path(r[label]).read_text())['status']!='PASS':raise ValueError('Qualification failed')
    elif mode=='cold':
        resource=json.loads((Path(r['producer']).parent/'resources.json').read_text())
        if not resource['success'] or not resource['workers_reaped']:raise ValueError('Producer not reaped')


class Tracking:
    def __init__(self,request):
        from mlflow.tracking import MlflowClient
        self.client=MlflowClient(tracking_uri='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db')
        exp=self.client.get_experiment_by_name('PROWL capstone lesion outlining')
        if exp is None:raise ValueError('Existing MLflow experiment missing')
        run=self.client.create_run(exp.experiment_id,tags={'mlflow.runName':request['title'],'scope':'exploratory_pretrained_provided_pancreas','training_run_id':request['run_id']})
        self.id=run.info.run_id;self.offset=0;self.losses=0
        for key,value in dict(steps=12000,seed=42,window=128,batch_size=1,precision='fp32',wall_seconds=216000,input_sha256=request['pins'][request['inputs']]).items():
            self.client.log_param(self.id,key,value)

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
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--sha256',required=True);p.add_argument('--mode',required=True,choices=['producer','cold','science']);a=p.parse_args()
    request=Path(a.request)
    if sha(request)!=a.sha256:raise ValueError('Exact request hash required')
    r=json.loads(request.read_text());verify(r,a.mode);require_ac();check_storage()
    out=Path(r['stage_root']);out.mkdir(exist_ok=False);child=None;tracking=None
    write(out/'dispatch.json',dict(request=str(request),sha256=a.sha256,mode=a.mode,supervisor=os.getpid()))
    try:
        with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
            verify(r,a.mode)
            if a.mode=='science':
                # A new root is mandatory, including for failed starts; never resume.
                artifact=Path(r['artifact']);artifact.mkdir(exist_ok=False);(artifact/'splits').mkdir()
                config=json.loads(Path(r['inputs']).read_text());plan=json.loads(Path(config['plan']).read_text())
                (artifact/'splits/train_ids.txt').write_text('\n'.join(sorted(plan['members']))+'\n')
                (artifact/'resolved.yaml').write_text(json.dumps({'_experiment':{'run':{'max_updates':12000,'validate_every':2000}}}))
                output=artifact/'execution'
            else:output=out/'worker'
            command=[r['python'],str(ROOT/'scripts/training/train_stunet_transfer_20261106.py'),'--request',str(request),'--mode',a.mode,'--output',str(output)]
            with (out/'worker.log').open('x') as log:
                child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                write(out/'owner.json',dict(worker=child.pid,supervisor=os.getpid(),command=command))
                last=[0.,0.]
                def tick():
                    import psutil
                    require_ac();now=time.monotonic()
                    # watch_windows accounts for worker descendants; include this supervisor too.
                    root=psutil.Process(child.pid)
                    owned=[root]+root.children(recursive=True);rss=psutil.Process().memory_info().rss
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
                    if tracking.losses!=12000:raise ValueError('MLflow loss count incomplete')
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
