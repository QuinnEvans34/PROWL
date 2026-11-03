"""One authorized matched-runtime CUDA diagnostic with two trace windows; no training or batch."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.operations.full_training_platform import require_ac, training_guard, watch_windows

BUNDLE = Path('E:/PROWL/transfer/week05-cuda-baseline-20261102-a01/extracted/week05-models-provenance')
BASE = Path('E:/PROWL/readiness/week05-matched-qualification-20261102-a01')
BACKUP = Path('C:/Users/quinn/PROWL-Backups/week05-matched-qualification-20261102-a01')
CT_SHA = '90bf329d4a959144dfc453c5f1adce83ac18b1d5493984cb8aaa3911a1f1000f'
MODEL_SHA = dict(localizer='46417801f3d3c37e618d06823027e84f0ce84343f469f24124537167d40198d5',
    segmenter='8b2a104f9830776da7011a759f5dfddbc9750725380bf244f7d292f02aadcd63')
LIMITS = dict(seconds=600, total_qualification_seconds=1800, rss_bytes=12*1024**3,
    gpu_bytes=6*1024**3, output_bytes=2*1024**3, backup_bytes=2*1024**3,
    combined_backups_bytes=40*1024**3, free_floor_bytes=100*1024**3,
    source_voxels=96_000_000, region_voxels=96_000_000, max_tiles=512)
COMPARISON = dict(status='PREDECLARED_ENGINEERING_COMPARISON_NOT_MODEL_ACCEPTANCE',
    affine_atol=1e-5, probability_atol=1e-5, probability_rtol=1e-4,
    maximum_argmax_disagreement=.001, exact_region_bounds=True,
    identity='exact_CT_checkpoint_recipe_shape_and_region', probabilities='float32_all_three_ROI_channels')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.flush(); os.fsync(f.fileno())


EXPECTED_PACKAGES = dict(torch='2.13.0+cu130', monai='1.6.0', numpy='2.5.1', nibabel='5.4.2', scipy='1.18.0')
TRACE_SELECTION = {'0':[0,0,0], '39':[216,0,170]}


def environment():
    observed = {n:importlib.metadata.version(n) for n in EXPECTED_PACKAGES}
    if observed != EXPECTED_PACKAGES or sys.version_info[:3] != (3,12,13):
        raise ValueError('Exact matched runtime required; no substitution')
    return dict(python=sys.version, executable=sys.executable,
        packages={n: importlib.metadata.version(n) for n in ('torch','monai','numpy','nibabel','scipy')})


def tree_bytes(root):
    return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())


def resource_gate():
    from scripts.acquisition.download_pants_windows_20261029 import check
    check()
    require_ac()
    if shutil.disk_usage('C:/').free < LIMITS['free_floor_bytes']:
        raise RuntimeError('C free-space floor')
    if tree_bytes(BACKUP.parent) > LIMITS['combined_backups_bytes']:
        raise RuntimeError('Combined backup ceiling')


def validate_request(r):
    expected = {'version','case_id','ct_path','ct_sha256','source_shape','source_affine','units',
        'models','localizer_recipe','policy','limits','comparison','output','backup','pins','environment','trace_selection'}
    if set(r) != expected or r['version'] != 'matched-physical-cascade-qualification-1':
        raise ValueError('Exact CT-only request schema required')
    if r['case_id'] != 'PanTS_00001070' or r['ct_sha256'] != CT_SHA:
        raise ValueError('Only approved diagnostic case allowed')
    if r['limits'] != LIMITS or r['comparison'] != COMPARISON or r['policy'] != 'all_support':
        raise ValueError('Frozen policy or limits changed')
    if r['output'] != str(BASE/'output') or r['backup'] != str(BACKUP):
        raise ValueError('Output roots changed')
    if set(r['models']) != set(MODEL_SHA) or any(
        set(r['models'][k]) != {'path','sha256'} or r['models'][k]['sha256'] != v for k,v in MODEL_SHA.items()):
        raise ValueError('Wrong model identities')
    if r['trace_selection'] != TRACE_SELECTION:
        raise ValueError('Trace selection changed')
    if r['units'] != 'mm' or math.prod(r['source_shape']) > LIMITS['source_voxels']:
        raise ValueError('Source units/allocation gate')


def check_request(pin):
    if sha(BASE/'request.json') != pin:
        raise ValueError('Request hash mismatch')
    r = json.loads((BASE/'request.json').read_text())
    validate_request(r)
    if environment() != r['environment']:
        raise ValueError('Runtime changed')
    for path, expected in r['pins'].items():
        if sha(path) != expected:
            raise ValueError('Producing pin changed: '+path)
    return r


def prepare(ct):
    import nibabel as nib
    from src.data.localizer_preprocessing_v4 import plan_geometry
    if BASE.exists() or BACKUP.exists():
        raise FileExistsError('Qualification already prepared/started; inspect, do not repeat')
    resource_gate()
    ct = Path(ct).resolve()
    if sha(ct) != CT_SHA:
        raise ValueError('Wrong CT bytes')
    image = nib.load(ct)
    if image.header.get_xyzt_units()[0] != 'mm':
        raise ValueError('Unresolved CT header units; no inferred override')
    recipe = json.loads((BUNDLE/'localizer-recipe.json').read_text())
    plan_geometry(list(image.shape), image.affine, recipe)
    models = {role:dict(path=str(BUNDLE/name),sha256=MODEL_SHA[role]) for role,name in
        [('localizer','localizer.pt'),('segmenter','segmenter-control-020000.pt')]}
    files = list((ROOT/'src').rglob('*.py')) + [Path(__file__),ct]
    files += list(BUNDLE.glob('*.json')) + [Path(m['path']) for m in models.values()]
    files += list((ROOT/'tests').glob('test_week05*.py'))
    setup = Path('E:/PROWL/readiness/week05-matched-runtime-setup-20261102-a01')
    files += [setup/'package-install-report.json',setup/'environment-verification.json',
              setup/'pillow-install-report.json',setup/'corrected-readiness.json',
              setup/'matched-runtime-tests-corrected.xml']
    site = Path(sys.prefix)/'Lib/site-packages'
    for pattern in ('torch/lib/torch_cpu.dll','torch/lib/torch_cuda.dll','torch/lib/c10*.dll',
                    'torch/_C*.pyd','scipy/ndimage/_nd_image*.pyd','scipy/ndimage/_interpolation.py',
                    'numpy/_core/_multiarray_umath*.pyd','monai/networks/nets/segresnet.py',
                    'monai/networks/blocks/segresnet_block.py','monai/networks/blocks/upsample.py'):
        matches=list(site.glob(pattern))
        if not matches:raise ValueError('Required installed runtime source absent: '+pattern)
        files += matches
    files += [Path(sys._base_executable)]
    r = dict(version='matched-physical-cascade-qualification-1',case_id='PanTS_00001070',ct_path=str(ct),
        ct_sha256=CT_SHA,source_shape=list(image.shape),source_affine=image.affine.tolist(),units='mm',
        models=models,localizer_recipe=recipe,policy='all_support',limits=LIMITS,comparison=COMPARISON,
        output=str(BASE/'output'),backup=str(BACKUP),pins={str(p):sha(p) for p in files},environment=environment(),trace_selection=TRACE_SELECTION)
    validate_request(r)
    BASE.mkdir(); write(BASE/'request.json',r)
    print(json.dumps(dict(request_sha256=sha(BASE/'request.json'),status='LOCAL_REQUEST_FROZEN_REFERENCE_PENDING')))


def worker(pin):
    r = check_request(pin)
    import numpy as np
    import nibabel as nib
    import torch
    from src.inference.cascade_models_v1 import load_weights
    from src.inference.cascade_trace_forward_v1 import TraceForward
    from src.data.segmenter_native_windows_v1 import tiles
    from src.inference.physical_cascade_v1 import predict
    from src.inference.ct_access_policy_windows_v1 import CtAccessPolicy
    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(LIMITS['gpu_bytes']/torch.cuda.get_device_properties(0).total_memory)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    models = {k:load_weights(v['path'],expected_sha256=v['sha256'],role=k)[0] for k,v in r['models'].items()}
    out = Path(r['output']); out.mkdir(exist_ok=False)
    traced = TraceForward(models['segmenter'],out,r['trace_selection'])
    models['segmenter'] = traced
    # No model files, sibling masks or reference paths remain readable after this point.
    guard = CtAccessPolicy(r['ct_path'],out,[ROOT/'src',Path(sys.prefix),Path(sys.base_prefix)/'Lib'])
    sys.addaudithook(guard)
    started = time.monotonic()
    report = dict(status='failed',case_id=r['case_id'],request_sha256=pin,
        reference_inputs_used=False,optimizer_updates=0,cross_device_qualified=False)
    try:
        image = nib.load(r['ct_path'])
        if (list(image.shape)!=r['source_shape'] or image.affine.tolist()!=r['source_affine'] or
                image.header.get_xyzt_units()[0]!='mm' or sha(r['ct_path'])!=r['ct_sha256']):
            raise ValueError('CT identity/header changed')
        array = np.asarray(image.dataobj,dtype=np.float32)
        def progress(stage,done,total):
            if time.monotonic()-started>LIMITS['seconds'] or torch.cuda.max_memory_reserved()>LIMITS['gpu_bytes']:
                raise RuntimeError('Worker resource cap')
            with (out/'progress.jsonl').open('a') as f:
                f.write(json.dumps(dict(stage=stage,done=done,total=total,seconds=time.monotonic()-started))+'\n')
        codes,mask,probabilities,info = predict(array,image.affine,**models,localizer_recipe=r['localizer_recipe'],
            device='cuda',max_region_voxels=LIMITS['region_voxels'],max_tiles=LIMITS['max_tiles'],progress=progress)
        traced.finish(tiles(info['reconstruction']['physical_grid']['shape']))
        if codes.shape != image.shape or mask.shape != image.shape or not np.isin(codes,[0,1,2]).all():
            raise ValueError('Invalid native output grid/codes')
        for name,data in [('prediction',codes),('localizer',mask)]:
            target=out/(name+'.nii.gz'); n=nib.Nifti1Image(data,image.affine)
            n.set_sform(image.affine,code=1); n.header.set_xyzt_units('mm'); nib.save(n,target)
            loaded=nib.load(target)
            if not np.array_equal(np.asarray(loaded.dataobj),data) or not np.allclose(loaded.affine,image.affine,atol=1e-5,rtol=0):
                raise ValueError('Native export changed geometry/data')
        np.save(out/'region-probabilities.npy',probabilities,allow_pickle=False)
        if not np.array_equal(np.load(out/'region-probabilities.npy',allow_pickle=False),probabilities):
            raise ValueError('Probability export roundtrip')
        report.update(status='LOCAL_DIAGNOSTIC_COMPLETE_REFERENCE_PENDING',evidence=info,
            source_shape=list(image.shape),source_affine=image.affine.tolist(),units='mm',
            artifacts={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in out.iterdir() if p.is_file()},
            seconds=time.monotonic()-started,peak_gpu_reserved=torch.cuda.max_memory_reserved())
    except BaseException as exc:
        report.update(error_type=type(exc).__name__,error=str(exc));raise
    finally:
        write(out/'input-access.json',dict(ct_reads=guard.ct_reads,reference_paths_allowed=False,
            boundary='Python audit tripwire after strict weight loading; not an OS sandbox'))
        write(out/'result.json',report)


def supervise(command, *, log, seconds, rss_bytes, tick):
    with Path(log).open('x') as f:
        env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_MATCHED_PHYSICAL_QUALIFICATION='1',PYTHONDONTWRITEBYTECODE='1')
        env.pop('CUDA_VISIBLE_DEVICES',None)
        p=subprocess.Popen(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        success=False
        try:
            watch_windows(p,seconds=seconds,rss_bytes=rss_bytes,tick=tick);success=True
        finally:
            write(Path(log).with_suffix('.resources.json'),dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode))


def run(pin):
    r=check_request(pin)
    if (BASE/'worker.log').exists() or (BASE/'output').exists() or BACKUP.exists():
        raise FileExistsError('Already started; no retry')
    resource_gate()
    # Enforce CUDA exclusivity against non-cooperating processes as well as the repository lock.
    running=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
    if running:raise RuntimeError('GPU compute owner already present')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        BACKUP.mkdir()
        shutil.copyfile(BASE/'request.json',BACKUP/'request.json')
        if sha(BACKUP/'request.json')!=pin:raise ValueError('Independent request backup mismatch')
        last_check = [0.]
        def tick():
            if time.monotonic()-last_check[0]<5:
                return
            last_check[0]=time.monotonic()
            resource_gate()
            if tree_bytes(BASE)>LIMITS['output_bytes']:raise RuntimeError('Output ceiling')
        try:
            supervise([sys.executable,__file__,'--worker',pin],log=BASE/'worker.log',seconds=LIMITS['seconds'],rss_bytes=LIMITS['rss_bytes'],tick=tick)
        finally:
            if tree_bytes(BASE)>LIMITS['backup_bytes']:raise RuntimeError('Backup ceiling; original evidence retained')
            pairs=[]
            for path in BASE.rglob('*'):
                if path.is_file():
                    dest=BACKUP/path.relative_to(BASE);dest.parent.mkdir(parents=True,exist_ok=True)
                    if not dest.exists():shutil.copyfile(path,dest)
                    if sha(path)!=sha(dest):raise ValueError('Independent backup mismatch')
                    pairs.append(dict(path=str(path),sha256=sha(dest)))
            write(BASE/'backup-verification.json',dict(pairs=pairs,training=False))
            shutil.copyfile(BASE/'backup-verification.json',BACKUP/'backup-verification.json')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',metavar='CT_PATH');g.add_argument('--run-sha256');g.add_argument('--worker')
    a=p.parse_args()
    if a.prepare:prepare(a.prepare)
    elif a.run_sha256:run(a.run_sha256)
    elif os.environ.get('PROWL_MATCHED_PHYSICAL_QUALIFICATION')=='1':worker(a.worker)
    else:raise ValueError('Owned supervisor required')
