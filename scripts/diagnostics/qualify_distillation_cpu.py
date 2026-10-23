"""CPU-only teacher/runtime/unit qualification; no patient reads or scientific launch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.operations.full_training_platform import watch_windows
from src.data.manifest_records import canonical,digest

OUT=Path('E:/PROWL/readiness/distillation-engineering-20261023-a01')
BASE=Path('E:/PROWL/teachers/medformer-pants-b854c824')
CONVERSION=Path('E:/PROWL/readiness/distillation-teacher-conversion-20261023-a01/conversion.json')


def write(path,value):
    with path.open('xb') as stream:stream.write(canonical(value))


def model_worker(destination):
    import torch
    from src.training.teacher_medformer_v1 import bundle_identity,FrozenTeacher
    torch.set_num_threads(1)
    identity=bundle_identity(BASE,CONVERSION,variant='ema')
    write(destination/'teacher-bundle.json',identity)
    teacher=FrozenTeacher(identity,digest(canonical(identity)),device='cpu')
    before={k:v.detach().clone() for k,v in teacher.model.state_dict().items()}
    rng=torch.get_rng_state().clone()
    x=torch.randn((1,1,32,32,32),generator=torch.Generator().manual_seed(42))
    a=teacher.lesion_probability(x);b=teacher.lesion_probability(x)
    if not torch.equal(a,b) or not torch.equal(rng,torch.get_rng_state()):raise ValueError('Teacher repeatability/RNG')
    if not all(torch.equal(before[k],v) for k,v in teacher.model.state_dict().items()):raise ValueError('Teacher mutated')
    if torch.cuda.is_initialized():raise ValueError('CPU isolation')
    write(destination/'result.json',dict(success=True,teacher_identity_sha256=digest(canonical(identity)),
        strict_state_loading=True,params=sum(p.numel() for p in teacher.model.parameters()),
        synthetic_shape=list(x.shape),probability_shape=list(a.shape),minimum=float(a.min()),maximum=float(a.max()),
        exact_repeated_forward=True,parameters_unchanged=True,global_rng_unchanged=True,
        cpu_only=True,ct_reads=0,scientific_updates=0,real_quality_qualified=False,real_resource_qualified=False))


def launch(stage,attempt):
    if len(attempt)!=2 or not attempt.isascii() or not attempt.isdecimal():raise ValueError('Two digit attempt')
    OUT.mkdir(exist_ok=True);destination=OUT/(stage+'-'+attempt)
    destination.mkdir(exist_ok=False)
    paths=[Path(__file__),ROOT/'src/training/teacher_medformer_v1.py',ROOT/'src/training/teacher_checkpoint_v1.py']
    if stage=='tests':
        paths+=list((ROOT/'tests').glob('test_distillation_*v1.py'))
        paths+=list((ROOT/'src/training').glob('*distillation*v1.py'))
        paths+=list((ROOT/'src/data').glob('*teacher*v1.py'))
    write(destination/'request.json',dict(stage=stage,seconds=240,rss_bytes=4*1024**3,
        pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        scope='CPU synthetic/model engineering only',scientific=False))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
        PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PROWL_DISTILLATION_CPU='1')
    if stage=='model':cmd=[sys.executable,__file__,'--worker',str(destination)]
    else:
        files=['tests/test_segmenter_distillation_v1.py','tests/test_segmenter_teacher_targets_v1.py']
        files+=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'tests').glob('test_distillation_*v1.py'))]
        cmd=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider',*files,'--junitxml',str(destination/'tests.xml')]
    success=False;error=None
    with (destination/'worker.log').open('x',encoding='utf-8') as stream:
        p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW)
        try:watch_windows(p,seconds=240,rss_bytes=4*1024**3);success=True
        except Exception as exc:error=f'{type(exc).__name__}: {exc}'
        finally:
            result=dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode,error=error)
            write(destination/'resources.json',result);print(json.dumps(result))
    if not success:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['model','tests']);p.add_argument('--attempt',default='01')
    p.add_argument('--worker');a=p.parse_args()
    if a.worker:
        if os.environ.get('PROWL_DISTILLATION_CPU')!='1':raise ValueError('Supervisor required')
        model_worker(Path(a.worker))
    elif a.stage:launch(a.stage,a.attempt)
    else:p.error('stage required')
