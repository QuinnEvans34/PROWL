"""One bounded CPU input pilot, reusing coverage admission. No optimizer/model."""
import argparse,hashlib,json,os,subprocess,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
BASE=Path('E:/PROWL/readiness/verifier-generator-20261023-a01')
OUT=BASE/'cpu-pilot-01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with Path(p).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())

def provider():
    from scripts.diagnostics import setup_fast_varied as parent
    from src.data.verifier_generator_inputs_v1 import GeneratorInputs
    setup=read(BASE/'restricted-inputs-01/setup.json')
    p=GeneratorInputs(partitions=read(BASE/'partitions.json'),partition_sha256=sha(BASE/'partitions.json'),
        focused_counts=setup['focused_counts'],expected_parent_pin=setup['parent_control_sha256'],
        target_cache=parent.CACHE,cache_manifest_sha256=sha(parent.CACHE/'manifest.json'),
        planned_counts=read(parent.varied.SETUP/'schedule.json')['focused_counts'],manifest=parent.parent.MANIFEST,
        review=parent.parent.SOURCE_SETUP/'cohort-review.json',train_file=parent.parent.TRAIN,
        dev_file=parent.parent.SOURCE_SETUP/'development.txt')
    if p.pin!=setup['control_sha256']:p.close();raise ValueError('Restricted control changed')
    return p

def selection():
    setup=read(BASE/'restricted-inputs-01/setup.json');rows=[]
    for name in setup['control']['train']:
        m=read(Path('E:/PROWL/cache/varied-targets-20261022-a01')/(name+'.json'))
        rows.append((name,m))
    selected=[]
    def add(seq):
        for n,m in seq:
            if n not in selected:selected.append(n);break
    positives=[r for r in rows if r[1]['positive']];empty=[r for r in rows if not r[1]['positive']]
    add(sorted(positives,key=lambda r:r[1]['lesion_voxels']))
    add(sorted(positives,key=lambda r:-r[1]['lesion_voxels']))
    add(sorted(positives,key=lambda r:-len(r[1]['cover'])))
    add(sorted(positives,key=lambda r:-len(r[1]['parts'])))
    add(sorted(empty,key=lambda r:-len(r[1]['cover'])))
    add(sorted(empty,key=lambda r:r[0]))
    while len(selected)<12:add(sorted(rows,key=lambda r:hashlib.sha256(r[0].encode()).hexdigest()))
    return selected

def worker():
    import numpy as np,torch
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.data.segmenter_physical_windows_v1 import sample_window,native_destination
    from src.data.segmenter_varied_region_v1 import choose
    from src.training.segmenter_augmentation_v1 import augment
    from scipy import ndimage
    request=read(OUT/'request.json')
    for path,pin in request['pins'].items():
        if sha(path)!=pin:raise ValueError('Pilot producing pin changed')
    if torch.cuda.is_available():raise ValueError('CPU isolation required')
    torch.set_num_threads(2);p=provider();reports=[];began=time.monotonic()
    try:
        for index,name in enumerate(request['cases']):
            case=p.load(name,role='train',operation='audit')
            _,meta=p.cache_member(name);target=case['target'];record=meta['record']
            if int((target==2).sum())!=meta['lesion_voxels']:raise ValueError('Cached lesion coverage changed')
            for origin in meta['cover']:
                patch,_=sample_window(target,record,origin,order=0)
                dst,coords=native_destination(record,origin)
                recovered=ndimage.map_coordinates(patch.astype(np.float32),coords,order=1,mode='nearest',prefilter=False)
                if not np.array_equal(recovered,target[dst]):raise ValueError('Window detail roundtrip')
            # Exercise coverage, jitter and context using allowed focus counters.
            traces=[];display=None
            for step,visit in ((0,0),(1,1),(3,1)):
                image,t,transform,trace=p.from_case(case,step=step,focused_visit=visit,seed=42)
                if image.shape!=(1,144,144,144) or t.shape!=(144,144,144) or not np.isfinite(image).all():raise ValueError('Actual window invalid')
                expected,expected_trace=choose(record,meta['cover'],meta['parts'],step=step,focused_visit=visit,total=p.planned_counts[name],seed=42,name=name)
                if trace['origin']!=list(expected) or trace['kind']!=expected_trace['kind']:raise ValueError('Sampler trace mismatch')
                ai,at,atrc=augment(image,t,transform,seed=42,update=step+1,case_id=name)
                if not np.isfinite(ai).all() or sorted(np.unique(at).tolist())!=sorted(np.unique(t).tolist()):raise ValueError('Augmentation invalid')
                traces.append(dict(step=step,kind=trace['kind'],origin=trace['origin'],lesion_voxels=int((t==2).sum())))
                if step==0:display=(image[0].copy(),t.copy())
            image,t=display;support=t==2 if (t==2).any() else t>0
            center=[int(np.argmax(support.sum(axis=tuple(k for k in range(3) if k!=axis)))) for axis in range(3)]
            fig,axes=plt.subplots(1,3,figsize=(12,4))
            for axis,ax in enumerate(axes):
                ct=np.take(image,center[axis],axis=axis).T;mask=np.take(t,center[axis],axis=axis).T
                ax.imshow(ct,cmap='gray',vmin=0,vmax=1,origin='lower')
                ax.imshow(np.ma.masked_where(mask==0,mask),cmap=matplotlib.colors.ListedColormap(['#44cc88','#ff5566']),vmin=1,vmax=2,alpha=.45,origin='lower')
                ax.set_title(f'Axis {axis}, index {center[axis]}');ax.axis('off')
            fig.suptitle(f'{name}: actual reserved-cover training window (green pancreas / red lesion)')
            fig.tight_layout();figure=OUT/(name+'.png');fig.savefig(figure,dpi=100);plt.close(fig)
            reports.append(dict(case_id=name,lesion_voxels=meta['lesion_voxels'],coverage_windows=len(meta['cover']),roundtrip_exact=True,traces=traces,figure=figure.name,figure_sha256=sha(figure)))
            print(json.dumps(dict(completed=len(reports),total=12,seconds=time.monotonic()-began)),flush=True)
            del case,target,image,t,display
        write(OUT/'result.json',dict(passed=True,cases=reports,seconds=time.monotonic()-began,scientific=False,optimizer_updates=0,visual_review_pending=True))
    finally:p.close()

def run():
    from src.operations.full_training_platform import watch_windows,require_ac
    require_ac()
    if OUT.exists():raise ValueError('Pilot already started; no retry')
    if any(shutil.disk_usage(d).free<100*1024**3 for d in ('C:/','E:/')):raise ValueError('Free space floor')
    files=list((ROOT/'src').rglob('*.py'))+[Path(__file__),BASE/'partitions.json',BASE/'restricted-inputs-01/setup.json']
    names=selection();OUT.mkdir()
    write(OUT/'request.json',dict(cases=names,pins={str(f):sha(f) for f in files},seconds=1200,rss_bytes=8*1024**3,CPU_only=True))
    with (OUT/'worker.log').open('x') as log:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
        p=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:watch_windows(p,seconds=1200,rss_bytes=8*1024**3,tick=require_ac)
        finally:write(OUT/'resources.json',getattr(p,'duration_resources',{}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if a.run:run()
    elif a.worker:worker()
    else:ap.error('Choose --run or --worker')
