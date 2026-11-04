"""Five real CUDA updates and one independent-backup cold replay; nonpromotable."""
import argparse,json,os,sys,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import build_verifier_views_20261031 as build
from src.operations.verifier_candidate_archive_v1 import write_json,backup_file
from src.operations.full_training_platform import watch_windows,require_ac,training_guard
from src.training.experiment_config import sha256
OUT=build.BASE/'qualification';BACKUP=Path('C:/Users/quinn/PROWL-Backups/verifier-qualification-20261031-a01')

def configure():
    import torch
    torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    if not torch.cuda.is_available():raise ValueError('Actual CUDA required')
    torch.cuda.set_per_process_memory_fraction(min(1.,6*1024**3/torch.cuda.get_device_properties(0).total_memory))

def equal(a,b):
    import torch
    if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a.cpu(),b.cpu())
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(v,b[k]) for k,v in a.items())
    if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b

def worker(stage):
    import torch
    from src.training.verifier_session_20261031 import Dataset,Session
    r=build.pilot.read(OUT/'request.json')
    if os.environ.get('PROWL_VERIFIER_QUAL_STAGE')!=stage:raise ValueError('Qualification supervisor required')
    write_json(OUT/(stage+'-started.json'),dict(request_sha256=sha256(OUT/'request.json'),nonpromotable=True))
    for path,pin in r['pins'].items():
        if sha256(path)!=pin:raise ValueError('Qualification pin changed')
    configure();d=Dataset(r['dataset_manifest'],r['dataset_sha256'])
    if stage=='producer':
        s=Session(d);trace=[];update_seconds=[]
        for _ in range(5):
            began=time.monotonic();trace.append(s.update());update_seconds.append(time.monotonic()-began)
            if s.step==4:
                torch.save(s.state(),OUT/'step4.pt');backup_file(OUT/'step4.pt',BACKUP/'step4.pt',reserve=lambda _:build.resource_check())
        if any(t['gradient_norm']<=0 for t in trace):raise ValueError('Zero diagnostic gradient')
        torch.save(s.state(),OUT/'step5.pt')
        began=time.monotonic();tuning=s.evaluate();tune_seconds=time.monotonic()-began
        if not equal(torch.load(OUT/'step5.pt',map_location='cpu',weights_only=True),s.state()):raise ValueError('Tuning mutated checkpoint state')
        if len(tuning['scores'])!=len(d.tune):raise ValueError('Incomplete tune inference')
        write_json(OUT/'producer.json',dict(passed=True,trace=trace,update_seconds=update_seconds,tune_seconds=tune_seconds,tuning=tuning,nonpromotable=True,peak_gpu_reserved=torch.cuda.max_memory_reserved()))
    else:
        if sha256(BACKUP/'step4.pt')!=sha256(OUT/'step4.pt'):raise ValueError('Independent checkpoint identity')
        state=torch.load(BACKUP/'step4.pt',map_location='cpu',weights_only=True);s=Session.restore(state,d)
        if not equal(state,s.state()):raise ValueError('Cold restoration mismatch')
        actual=s.update();expected=build.pilot.read(OUT/'producer.json')['trace'][-1]
        if actual!=expected or not equal(torch.load(OUT/'step5.pt',map_location='cpu',weights_only=True),s.state()):raise ValueError('Cold next-update mismatch')
        write_json(OUT/'cold.json',dict(passed=True,nonpromotable=True,exact_restore=True,exact_next_update=True,trace=actual,backup_sha256=sha256(BACKUP/'step4.pt'),peak_gpu_reserved=torch.cuda.max_memory_reserved()))
    if torch.cuda.max_memory_reserved()>6*1024**3:raise ValueError('GPU resource cap')

def prepare():
    if OUT.exists() or BACKUP.exists():raise ValueError('Qualification already prepared')
    v=build.pilot.read(build.BASE/'pilot/visual-review.json');s=build.pilot.read(build.BASE/'pilot/resources.json')
    if not v['passed'] or v['manifest_sha256']!=sha256(build.BASE/'pilot/manifest.json') or not s['success'] or not s['workers_reaped']:raise ValueError('Pilot review gate')
    complete=build.pilot.read(build.BASE/'build/resources.json')
    if not complete['success'] or not complete['workers_reaped']:raise ValueError('Full intake incomplete')
    manifest=build.BASE/'build/manifest.json'
    files=[Path(__file__),ROOT/'src/training/verifier_session_20261031.py',build.DESIGN,manifest,build.BASE/'pilot/manifest.json',build.BASE/'pilot/visual-review.json']
    m=build.pilot.read(manifest)
    if m['status']!='QUALIFIED_FIT_TUNE_VIEWS':raise ValueError('Full intake unqualified')
    files += [Path(r['path']) for r in m['candidates']]
    OUT.mkdir();BACKUP.mkdir();write_json(OUT/'request.json',dict(pins={str(p):sha256(p) for p in files},dataset_manifest=str(manifest),dataset_sha256=sha256(manifest),seconds=1200,rss_bytes=12*1024**3,optimizer_updates=5,cold_updates=1,nonpromotable=True))

def run(stage):
    if any((OUT/(stage+suffix)).exists() for suffix in ('.log','.json','-resources.json','-started.json')):raise ValueError('Qualification stage already started')
    if stage=='cold':
        p=build.pilot.read(OUT/'producer-resources.json')
        if not p['success'] or not p['workers_reaped'] or not build.pilot.read(OUT/'producer.json')['passed']:raise ValueError('Producer incomplete')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        with (OUT/(stage+'.log')).open('x') as log:
            env=dict(os.environ,CUBLAS_WORKSPACE_CONFIG=':4096:8',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_VERIFIER_QUAL_STAGE=stage);env.pop('CUDA_VISIBLE_DEVICES',None)
            p=subprocess.Popen([sys.executable,__file__,'--worker',stage],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            success=False
            try:watch_windows(p,seconds=1200,rss_bytes=12*1024**3,tick=require_ac);success=True
            finally:write_json(OUT/(stage+'-resources.json'),dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','producer','cold']);ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if a.worker:worker(a.stage)
    elif a.stage=='prepare':prepare()
    else:run(a.stage)
