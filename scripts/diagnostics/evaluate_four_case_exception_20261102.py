"""Exactly four exposed-development cases, explicit exception, one shot, separate scoring."""
import argparse,csv,json,os,sys,time,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import qualify_matched_physical_cascade_20261102 as q
from scripts.acquisition.restore_remaining_cts_20261030 import CACHE
from src.operations.full_training_platform import training_guard
BASE=Path('E:/PROWL/readiness/week05-four-case-20261102-a01')
BACKUP=Path('C:/Users/quinn/PROWL-Backups/week05-four-case-20261102-a01')
RESTORE=Path('E:/PROWL/sources/pants/week05-batch-20261102-a01')
SPEC=ROOT/'docs/capstone/operations/WEEK-05-FOUR-CASE-EXCEPTION-20261102.json'
MANIFEST=Path('E:/PROWL/readiness/data-setup-20261010-a01/pants-manifest.csv')
CASES=['PanTS_00002028','PanTS_00000909','PanTS_00004681','PanTS_00006755']
ARMS=['autonomous','provided_region']
QUAL='641b6db57245c91f682e060c55ca9678f320ca0c1394e0e4d0a2f98c40568a12'

def validate(r):
    if r['version']!='four-case-exception-1' or [v['case_id'] for v in r['cases']]!=CASES or r['arms']!=ARMS:raise ValueError('Fixed cohort/arms')
    if r['qualification']!=QUAL or r['probability_equivalence']!='UNQUALIFIED':raise ValueError('Qualification exception changed')
    limits=json.loads(SPEC.read_text())['inference_limits']
    if r['limits']!=limits or r['exception_sha256']!=q.sha(SPEC):raise ValueError('Limits/exception changed')

def request(pin,*,inference_worker=False):
    if q.sha(BASE/'request.json')!=pin:raise ValueError('Request hash')
    r=json.loads((BASE/'request.json').read_text());validate(r)
    if q.environment()!=r['environment']:raise ValueError('Environment changed')
    reference_paths={c['files'][k] for c in r['cases'] for k in ('pancreas','lesion')}
    for p,h in r['pins'].items():
        # Controller verifies every source. Autonomous workers never read label bytes,
        # including for hashing; scoring and the explicit assisted arm are separate.
        if inference_worker and p in reference_paths:continue
        if q.sha(p)!=h:raise ValueError('Pin changed: '+p)
    return r

def prepare():
    import xml.etree.ElementTree as ET
    import nibabel as nib
    import numpy as np
    from src.data.localizer_preprocessing_v4 import plan_geometry
    from src.data.segmenter_native_windows_v1 import geometry,tiles
    from src.data.segmenter_physical_windows_v1 import physical_geometry
    if (BASE/'request.json').exists() or BACKUP.exists():raise FileExistsError('Already prepared/started')
    old=q.check_request(QUAL);q.resource_gate()
    tests=ET.parse(BASE/'cpu-tests-final.xml').getroot().find('testsuite').attrib
    if int(tests['tests'])!=52 or int(tests['errors']) or int(tests['failures']):raise ValueError('CPU qualification failed')
    resources=json.loads((BASE/'restore.resources.json').read_text())
    if not resources['success'] or not resources['workers_reaped'] or resources['exit_code']!=0:raise ValueError('Restoration unfinished')
    restored=json.loads((RESTORE/'restoration.json').read_text())['cases']
    identities={v['case_id']:v for v in json.loads((q.BUNDLE/'development-identities.json').read_text())['cases']}
    with MANIFEST.open(newline='') as f:rows={v['case_id']:v for v in csv.DictReader(f) if v['case_id'] in CASES}
    cases=[];pins=dict(old['pins'])
    for name in CASES:
        identity=identities[name];meta=CACHE/(name+'.json')
        if q.sha(meta)!=identity['metadata_sha256']:raise ValueError('Metadata changed')
        files=dict(ct=restored[name]['path'],pancreas=rows[name]['pancreas_path'],lesion=rows[name]['lesion_path'])
        header={}
        for role,path in files.items():
            if q.sha(path)!=identity['source_sha256'][role]:raise ValueError('Source identity mismatch')
            n=nib.load(path);units=n.header.get_xyzt_units()[0]
            if len(n.shape)!=3 or np.prod(n.shape)>q.LIMITS['source_voxels']:raise ValueError('Native allocation')
            if units!='mm' and not (role!='ct' and units=='unknown'):raise ValueError('Unresolved source units: '+name+'/'+role+'/'+units)
            header[role]=dict(shape=list(n.shape),affine=n.affine.tolist(),units=units)
            pins[path]=q.sha(path)
        for role in ('pancreas','lesion'):
            if header[role]['shape']!=header['ct']['shape'] or not np.allclose(header[role]['affine'],header['ct']['affine'],atol=1e-5,rtol=0):raise ValueError('Reference geometry mismatch')
            header[role]['interpreted_units']='mm' if header[role]['units']=='mm' else 'matched_mm_ct_grid'
        plan_geometry(header['ct']['shape'],header['ct']['affine'],old['localizer_recipe'])
        full_grid=physical_geometry(geometry(header['ct']['shape'],header['ct']['affine']))
        count=len(tiles(full_grid['shape']))
        if count>q.LIMITS['max_tiles']:raise ValueError('Full-volume tile cap')
        cases.append(dict(case_id=name,files=files,header=header,identity=identity,maximum_full_ct_tiles=count))
        pins[str(meta)]=q.sha(meta)
    extra=list((ROOT/'src').rglob('*.py'))+[Path(__file__),SPEC,MANIFEST,RESTORE/'restoration.json',BASE/'restore.resources.json',BASE/'cpu-tests.xml',BASE/'cpu-tests-final.xml',ROOT/'tests/test_week05_four_case_20261102.py']
    for p in extra:pins[str(p)]=q.sha(p)
    r=dict(version='four-case-exception-1',cases=cases,arms=ARMS,qualification=QUAL,
        exception_sha256=q.sha(SPEC),probability_equivalence='UNQUALIFIED',limits=json.loads(SPEC.read_text())['inference_limits'],
        models=old['models'],localizer_recipe=old['localizer_recipe'],environment=q.environment(),pins=pins)
    validate(r);q.write(BASE/'request.json',r);print(json.dumps(dict(request_sha256=q.sha(BASE/'request.json'),tiles=[c['maximum_full_ct_tiles'] for c in cases])))

def worker(pin,name,arm):
    r=request(pin,inference_worker=True)
    if name not in CASES or arm not in ARMS:raise ValueError('Unapproved worker')
    case=next(c for c in r['cases'] if c['case_id']==name)
    import numpy as np
    import nibabel as nib
    import torch
    from src.inference.cascade_models_v1 import load_weights
    from src.inference.ct_access_policy_windows_v1 import CtAccessPolicy
    from src.inference.physical_cascade_v1 import predict,segment
    from src.inference.predicted_physical_region_v1 import prepare as region_prepare
    torch.set_num_threads(2);torch.backends.cudnn.benchmark=False
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    torch.cuda.set_per_process_memory_fraction(r['limits']['gpu_bytes']/torch.cuda.get_device_properties(0).total_memory)
    models={k:load_weights(v['path'],expected_sha256=v['sha256'],role=k)[0] for k,v in r['models'].items()}
    # Only the explicitly assisted process reads pancreas reference, before its CT-only tripwire.
    provided=None
    if arm=='provided_region':
        if q.sha(case['files']['pancreas'])!=case['identity']['source_sha256']['pancreas']:raise ValueError('Provided reference changed')
        n=nib.load(case['files']['pancreas']);provided=np.asarray(n.dataobj)
        if not np.isin(provided,[0,1]).all():raise ValueError('Invalid provided pancreas codes')
    out=BASE/name/arm;out.mkdir(parents=True,exist_ok=False)
    guard=CtAccessPolicy(case['files']['ct'],out,[ROOT/'src',Path(sys.prefix),Path(sys.base_prefix)/'Lib'])
    sys.addaudithook(guard);started=time.monotonic();result=dict(status='failed',case_id=name,arm=arm,request_sha256=pin,optimizer_updates=0)
    try:
        n=nib.load(case['files']['ct']);image=np.asarray(n.dataobj,dtype=np.float32)
        def progress(stage,done,total):
            if time.monotonic()-started>600 or torch.cuda.max_memory_reserved()>r['limits']['gpu_bytes']:raise RuntimeError('Worker cap')
            with (out/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(stage=stage,done=done,total=total,seconds=time.monotonic()-started))+'\n')
        if arm=='autonomous':
            codes,mask,probs,info=predict(image,n.affine,**models,localizer_recipe=r['localizer_recipe'],device='cuda',max_region_voxels=q.LIMITS['region_voxels'],max_tiles=q.LIMITS['max_tiles'],progress=progress)
        else:
            region=region_prepare(image,provided,n.affine,base_margin_mm=10.,extra_margin_mm=[81.,43.,71.],max_region_voxels=q.LIMITS['region_voxels'])
            codes,probs,reconstruction=segment(models['segmenter'],region,device='cuda',max_tiles=q.LIMITS['max_tiles'],progress=progress)
            info={k:v for k,v in region.items() if k!='image'};info.update(reference_inputs_used=True,region_origin='provided_pancreas_reference',reconstruction=reconstruction)
            mask=provided.astype(np.uint8)
        if info['reconstruction']['gap_voxels']!=0:raise ValueError('Reconstruction gap')
        for key,data in [('prediction',codes),('localizer',mask)]:
            target=out/(key+'.nii.gz');saved=nib.Nifti1Image(data,n.affine);saved.header.set_xyzt_units('mm');saved.set_sform(n.affine,code=1);nib.save(saved,target)
            loaded=nib.load(target)
            if not np.array_equal(np.asarray(loaded.dataobj),data) or not np.allclose(loaded.affine,n.affine,atol=1e-5,rtol=0):raise ValueError('Saved geometry/data changed')
        np.save(out/'region-probabilities.npy',probs,allow_pickle=False)
        if not np.array_equal(probs,np.load(out/'region-probabilities.npy',mmap_mode='r',allow_pickle=False)):raise ValueError('Probability roundtrip')
        result.update(status='COMPLETED',source_shape=list(n.shape),source_affine=n.affine.tolist(),units='mm',evidence=info,reference_inputs_used=arm!='autonomous',seconds=time.monotonic()-started,peak_gpu_reserved=torch.cuda.max_memory_reserved(),artifacts={p.name:q.sha(p) for p in out.iterdir() if p.is_file()})
    except BaseException as e:result.update(error=repr(e));raise
    finally:
        q.write(out/'input-access.json',dict(ct_reads=guard.ct_reads,pancreas_reference_loaded=arm=='provided_region',lesion_reference_loaded=False,boundary='audit tripwire, not OS sandbox'))
        q.write(out/'result.json',result)

def scoring(pin,name,arm):
    r=request(pin);case=next(c for c in r['cases'] if c['case_id']==name);out=BASE/name/arm
    result=json.loads((out/'result.json').read_text())
    if result['status']!='COMPLETED':raise ValueError('Cannot score failed prediction')
    from src.inference.saved_prediction_scoring import score_saved
    from src.inference.four_case_metrics_20261102 import components,contour,coverage
    import nibabel as nib
    import numpy as np
    from src.data.segmenter_native_windows_v1 import orient
    files=case['files'];pins=case['identity']['source_sha256']
    scored=score_saved(out/'prediction.nii.gz',files['pancreas'],files['lesion'],expected_prediction_sha256=result['artifacts']['prediction.nii.gz'],expected_pancreas_sha256=pins['pancreas'],expected_lesion_sha256=pins['lesion'],allow_unknown_reference_units=True)
    n=nib.load(out/'prediction.nii.gz');pred=np.asarray(n.dataobj);p=np.asarray(nib.load(files['pancreas']).dataobj,bool);l=np.asarray(nib.load(files['lesion']).dataobj,bool)
    loc=np.asarray(nib.load(out/'localizer.nii.gz').dataobj,bool);ev=result['evidence'];region=np.zeros(ev['parent_geometry']['shape'],bool)
    region[tuple(slice(a,b) for a,b in zip(ev['region_low'],ev['region_high']))]=True;region=orient(region,ev['parent_geometry'],inverse=True)
    scored.update(case_id=name,arm=arm,role='exposed_development',model_quality_acceptance=False,
        lesion_components=components(pred==2,l,n.affine),lesion_contour=contour(pred==2,l,n.affine),
        pancreas_contour=contour(pred>0,p|l,n.affine),localization=dict(predicted_mask_pancreas_coverage=coverage(p,loc),expanded_region_pancreas_coverage=coverage(p,region),expanded_region_lesion_coverage=coverage(l,region),scan_fraction=float(region.mean())),
        measurements=dict(voxel_volume_ml=abs(float(np.linalg.det(n.affine[:3,:3])))/1000,clinical_diameter='not_computed; component bounds and volumes are descriptive'),
        optimizer_updates=0,model_forwards=0)
    q.write(out/'score.json',scored)

def backup():
    q.resource_gate()
    if q.tree_bytes(BASE)>8*1024**3:raise ValueError('Output cap')
    BACKUP.mkdir(exist_ok=True)
    for p in BASE.rglob('*'):
        if not p.is_file():continue
        dest=BACKUP/p.relative_to(BASE);dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():shutil.copyfile(p,dest)
        if q.sha(p)!=q.sha(dest):raise ValueError('Independent backup mismatch')
    if q.tree_bytes(BACKUP)>8*1024**3:raise ValueError('Backup cap')

def run(pin):
    r=request(pin);q.resource_gate()
    if (BASE/'dispatch.json').exists() or BACKUP.exists():raise FileExistsError('Already dispatched; no retry')
    if subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU owned')
    q.write(BASE/'dispatch.json',dict(request_sha256=pin,started=time.time(),pid=os.getpid()))
    start=time.monotonic();records=[]
    def tick():
        q.resource_gate()
        if time.monotonic()-start>4800 or q.tree_bytes(BASE)>8*1024**3:raise RuntimeError('Aggregate cap')
    try:
        with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
            for arm in ARMS:
                for name in CASES:
                    tick();log=BASE/(name+'-'+arm+'.log')
                    q.supervise([sys.executable,__file__,'--worker',pin,name,arm],log=log,seconds=min(600,4800-(time.monotonic()-start)),rss_bytes=12*1024**3,tick=tick)
                    records.append(dict(case_id=name,arm=arm,status='inference_completed'));backup()
            # Scoring is a different CPU process, only after autonomous outputs are frozen.
            for arm in ARMS:
                for name in CASES:
                    tick();q.supervise([sys.executable,__file__,'--score',pin,name,arm],log=BASE/(name+'-'+arm+'-score.log'),seconds=min(600,4800-(time.monotonic()-start)),rss_bytes=12*1024**3,tick=tick);backup()
        q.write(BASE/'completion.json',dict(status='COMPLETED_EXPLORATORY_EXCEPTION',cases=CASES,arms=ARMS,records=records,seconds=time.monotonic()-start,probability_equivalence='UNQUALIFIED',training=False))
    except BaseException as e:
        q.write(BASE/'failure.json',dict(status='STOPPED_NO_RETRY',error=repr(e),completed=records,all_case_denominator=CASES,seconds=time.monotonic()-start));raise
    finally:backup()

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--run-sha256');g.add_argument('--worker',nargs=3);g.add_argument('--score',nargs=3);a=p.parse_args()
    if a.prepare:prepare()
    elif a.run_sha256:run(a.run_sha256)
    elif os.environ.get('PROWL_MATCHED_PHYSICAL_QUALIFICATION')!='1':raise ValueError('Owned supervisor required')
    elif a.worker:worker(*a.worker)
    else:scoring(*a.score)
