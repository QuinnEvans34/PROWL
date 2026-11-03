"""Prepared70-case executor. Every mutation requires a separately approved admission."""
import argparse,json,os,sys,time,shutil,subprocess,tarfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import prepare_autonomous_baseline_20261103 as prep
from scripts.diagnostics import qualify_matched_physical_cascade_20261102 as q
from src.operations.full_training_platform import require_ac,training_guard
BASE=prep.RUN
BACKUP=Path('C:/Users/quinn/PROWL-Backups/week05-autonomous70-20261103-a01')
CASES=[]
ARMS=['autonomous']

def request(pin,*,inference_worker=False):
    global CASES
    if q.sha(prep.OUT/'request.json')!=pin:raise ValueError('Prepared request hash')
    r=json.loads((prep.OUT/'request.json').read_text())
    if r['version']!='autonomous70-prepared-request-1' or r['arms']!=ARMS or len(r['cases'])!=70:raise ValueError('Fixed70 autonomous scope')
    CASES=[c['case_id'] for c in r['cases']]
    if len(set(CASES))!=70 or any(c['exposure']['role']!='exposed_development' or c['exposure']['segmenter_optimizer_overlap'] for c in r['cases']):raise ValueError('Protected roles')
    if q.environment()!=r['environment']:raise ValueError('Runtime changed')
    refs={c['files'][k] for c in r['cases'] for k in ['pancreas','lesion']}
    for p,h in r['pins'].items():
        if inference_worker and p in refs:continue
        if q.sha(p)!=h:raise ValueError('Prepared pin changed: '+p)
    return r

def admission(pin,r):
    path=prep.OUT/'admission.json'
    if not path.exists():raise ValueError('NEW HUMAN SCOPE/RESOURCE ADMISSION REQUIRED; four-case exception does not apply')
    a=json.loads(path.read_text())
    if a.get('approved_request_sha256')!=pin or a.get('scope')!='autonomous70' or a.get('limits')!=r['limits'] or a.get('output_policy')!='retain_float32_probabilities' or a.get('numerical_exception')!='approved_only_for_this_scope':raise ValueError('Admission does not match exact proposed scope/limits')
    if r.get('unresolved_preflight'):raise ValueError('Unresolved preflight decisions require a separately versioned request; no silent exclusion or cap increase')
    return a

def gate(r):
    from scripts.acquisition.download_pants_windows_20261029 import check
    check();require_ac();limits=r['limits']
    if any(shutil.disk_usage(d).free<limits['minimum_free_bytes'] for d in ['C:/','E:/']):raise RuntimeError('Free space floor')
    if q.tree_bytes(BACKUP.parent)>limits['combined_backup_bytes']:raise RuntimeError('Combined backup cap')
    if BASE.exists() and q.tree_bytes(BASE)>limits['output_bytes']:raise RuntimeError('Output cap')

def restore(pin):
    from scripts.acquisition import download_pants_windows_20261029 as download
    from scripts.acquisition.restore_remaining_cts_20261030 import member_case
    r=request(pin);admission(pin,r);gate(r)
    if prep.SOURCES.exists():raise FileExistsError('Restoration already started; no retry')
    wanted={c['case_id']:c for c in r['cases'] if c['needs_restoration']};prep.SOURCES.mkdir();started=time.monotonic();found={}
    inventory=json.loads((ROOT/'docs/capstone/data/acquisition-2026-09-19.json').read_text());receipts={}
    for log in ['events.jsonl','continuation-01.jsonl','continuation-02.jsonl']:
        for line in (download.DEST/log).read_text().splitlines():
            v=json.loads(line)
            if v['event']=='verified_download':receipts[v['name']]=v
    try:
        for item in inventory['pants']['files']:
            if item['kind']!='training_archive':continue
            lo,hi=map(int,item['name'].removesuffix('.tar.gz').split('_')[-2:]);names={n for n in wanted if lo<=int(n.split('_')[-1])<=hi}
            if not names:continue
            archive=download.DEST/item['name'];before=archive.stat()
            if before.st_size!=item['bytes'] or receipts[item['name']]['sha256']!=item['sha256']:raise ValueError('Archive receipt mismatch')
            last=0
            with tarfile.open(archive,'r|gz') as tar:
                for member in tar:
                    if time.monotonic()-started>r['limits']['restore_seconds']:raise TimeoutError('Restore time cap')
                    if time.monotonic()-last>5:gate(r);last=time.monotonic()
                    name=member_case(member)
                    if name not in names:continue
                    case=wanted[name]
                    if name in found or member.size!=case['expected_ct_bytes']:raise ValueError('CT member mismatch')
                    dest=Path(case['files']['ct']);partial=dest.with_suffix('.part');h=hashlib.sha256()
                    with tar.extractfile(member) as src,partial.open('xb') as f:
                        for block in iter(lambda:src.read(1024**2),b''):h.update(block);f.write(block)
                        f.flush();os.fsync(f.fileno())
                    if h.hexdigest()!=case['identity']['source_sha256']['ct']:raise ValueError('CT identity mismatch')
                    partial.rename(dest);found[name]=h.hexdigest()
                    if q.tree_bytes(prep.SOURCES)>r['limits']['restore_output_bytes']:raise RuntimeError('Restore byte cap')
                    with (prep.SOURCES/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(case_id=name,complete=len(found),total=len(wanted),seconds=time.monotonic()-started))+'\n')
                    if names.issubset(found):break
            after=archive.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Archive changed')
        if set(found)!=set(wanted):raise ValueError('Missing source; no exclusion')
        q.write(prep.SOURCES/'restoration.json',dict(request_sha256=pin,status='EXACT_SOURCES_RESTORED',cases=found,seconds=time.monotonic()-started))
    except BaseException as e:q.write(prep.SOURCES/'failure.json',dict(error=repr(e),complete=found,denominator=list(wanted)));raise

def source_admission(pin):
    import nibabel as nib
    import numpy as np
    r=request(pin);admission(pin,r);gate(r)
    resources=json.loads((prep.OUT/'restore.resources.json').read_text())
    if not resources['success'] or not resources['workers_reaped'] or resources['exit_code']!=0:raise ValueError('Restoration not complete')
    evidence=[];pins={}
    for case in r['cases']:
        headers={}
        for role,path in case['files'].items():
            h=q.sha(path)
            if h!=case['identity']['source_sha256'][role]:raise ValueError('Source identity: '+case['case_id']+'/'+role)
            im=nib.load(path);units=im.header.get_xyzt_units()[0]
            if units!='mm' and not (role!='ct' and units=='unknown'):raise ValueError('Unresolved CT/reference units')
            expected=case['expected_native']
            if list(im.shape)!=expected['shape'] or not np.allclose(im.affine,expected['affine'],atol=1e-5,rtol=0):raise ValueError('Source geometry changed')
            headers[role]=dict(shape=list(im.shape),affine=im.affine.tolist(),units=units,interpreted_units='mm' if units=='mm' else 'matched_mm_ct_grid');pins[path]=h
        evidence.append(dict(case_id=case['case_id'],headers=headers))
    q.write(prep.OUT/'ready.json',dict(request_sha256=pin,admission_sha256=q.sha(prep.OUT/'admission.json'),source_pins=pins,evidence=evidence,status='READY_FOR_APPROVED_EXACT_SCOPE'))
    print(json.dumps(dict(ready_sha256=q.sha(prep.OUT/'ready.json'))))

def save_backup(path,r):
    gate(r);dest=BACKUP/path.relative_to(BASE);dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():shutil.copyfile(path,dest)
    if q.sha(path)!=q.sha(dest):raise ValueError('Independent backup mismatch')
    if q.tree_bytes(BACKUP)>r['limits']['backup_bytes']:raise RuntimeError('Independent backup cap')

def reuse_case(case,r,pin):
    import nibabel as nib
    import numpy as np
    origin=Path(case['reuse']['root'])
    if q.sha(origin/'result.json')!=case['reuse']['result_sha256'] or q.sha(origin/'input-access.json')!=case['reuse']['input_access_sha256']:raise ValueError('Retained reuse records changed')
    original=json.loads((origin/'result.json').read_text())
    origin_request=origin.parent/'request.json' if case['reuse']['kind']=='matched-diagnostic-native-output' else Path('E:/PROWL/readiness/week05-four-case-20261102-a01/request.json')
    if q.sha(origin_request)!=case['reuse']['request_sha256']:raise ValueError('Reuse request changed')
    old=json.loads(origin_request.read_text())
    expected_ct=old['ct_sha256'] if 'ct_sha256' in old else next(c['identity']['source_sha256']['ct'] for c in old['cases'] if c['case_id']==case['case_id'])
    if expected_ct!=case['identity']['source_sha256']['ct']:raise ValueError('Reuse CT identity changed')
    resource_path=origin.parent/'worker.resources.json' if case['reuse']['kind']=='matched-diagnostic-native-output' else origin.parents[1]/(case['case_id']+'-autonomous.resources.json')
    resource=json.loads(resource_path.read_text())
    if not resource['success'] or not resource['workers_reaped'] or resource['exit_code']!=0:raise ValueError('Reuse worker did not complete cleanly')
    if old['models']!=r['models'] or old['localizer_recipe']!=r['localizer_recipe'] or old['environment']!=r['environment']:raise ValueError('Reuse model/recipe/runtime changed')
    if original['case_id']!=case['case_id'] or original.get('reference_inputs_used',False) or original['status'] not in ['COMPLETED','LOCAL_DIAGNOSTIC_COMPLETE_REFERENCE_PENDING']:raise ValueError('Reuse is not successful autonomous output')
    out=BASE/case['case_id']/'autonomous';out.mkdir(parents=True)
    for name,value in original['artifacts'].items():
        expected=value['sha256'] if isinstance(value,dict) else value
        if Path(name).name!=name or q.sha(origin/name)!=expected:raise ValueError('Reuse artifact mismatch')
        shutil.copyfile(origin/name,out/name)
    for name in ['result.json','input-access.json']:
        shutil.copyfile(origin/name,out/name)
        if q.sha(origin/name)!=q.sha(out/name):raise ValueError('Immutable reuse copy mismatch')
    shutil.copyfile(origin_request,out/'original-request.json')
    prediction=nib.load(out/'prediction.nii.gz')
    if list(prediction.shape)!=case['expected_native']['shape'] or prediction.header.get_xyzt_units()[0]!='mm' or not np.allclose(prediction.affine,case['expected_native']['affine'],atol=1e-5,rtol=0):raise ValueError('Reuse native geometry')
    q.write(out/'reuse.json',dict(baseline_request_sha256=pin,original_request_sha256=q.sha(origin_request),original_result_sha256=q.sha(origin/'result.json'),original_result_unchanged=True,model_forwards=0))

def launch(ready_pin):
    if q.sha(prep.OUT/'ready.json')!=ready_pin:raise ValueError('Ready hash')
    ready=json.loads((prep.OUT/'ready.json').read_text());pin=ready['request_sha256'];r=request(pin);admission(pin,r);gate(r)
    resource=json.loads((prep.OUT/'source-admission.resources.json').read_text())
    if not resource['success'] or not resource['workers_reaped'] or resource['exit_code']!=0:raise ValueError('Source admission not complete')
    if q.sha(prep.OUT/'admission.json')!=ready['admission_sha256']:raise ValueError('Admission changed')
    for path,h in ready['source_pins'].items():
        if q.sha(path)!=h:raise ValueError('Ready source changed')
    if BASE.exists() or BACKUP.exists():raise FileExistsError('Already started; no automatic retry/resume')
    if subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU owned')
    BASE.mkdir();BACKUP.mkdir();started=time.monotonic();complete=[]
    for name in ['request.json','ready.json','admission.json']:shutil.copyfile(prep.OUT/name,BASE/name);save_backup(BASE/name,r)
    def tick():
        gate(r)
        if time.monotonic()-started>r['limits']['total_evaluation_seconds']:raise TimeoutError('Aggregate evaluation cap')
    try:
        with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
            for case in r['cases']:
                tick();name=case['case_id']
                if case['reuse']:reuse_case(case,r,pin)
                else:q.supervise([sys.executable,__file__,'--worker',pin,name,'autonomous'],log=BASE/(name+'-inference.log'),seconds=min(600,r['limits']['total_evaluation_seconds']-(time.monotonic()-started)),rss_bytes=r['limits']['rss_bytes'],tick=tick)
                for p in (BASE/name/'autonomous').iterdir():
                    if p.is_file():save_backup(p,r)
                q.supervise([sys.executable,__file__,'--score',pin,name,'autonomous'],log=BASE/(name+'-score.log'),seconds=min(600,r['limits']['total_evaluation_seconds']-(time.monotonic()-started)),rss_bytes=r['limits']['rss_bytes'],tick=tick)
                save_backup(BASE/name/'autonomous/score.json',r);complete.append(name)
                with (BASE/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(case_id=name,completed=len(complete),total=70,reused=bool(case['reuse'])))+'\n')
        q.write(BASE/'completion.json',dict(status='COMPLETE_EXPOSED_DEVELOPMENT_BASELINE',cases=complete,seconds=time.monotonic()-started,probability_equivalence='UNQUALIFIED',training=False))
    except BaseException as e:q.write(BASE/'failure.json',dict(error=repr(e),completed=complete,denominator=CASES,pending=[n for n in CASES if n not in complete],automatic_retry=False));raise
    finally:
        for p in BASE.rglob('*'):
            if p.is_file():save_backup(p,r)

# Worker and scorer below are separately frozen copies of the tested four-case paths;
# only source identity admission and original-reuse artifact representation differ.

def worker(pin,name,arm):
    r=request(pin,inference_worker=True)
    admission(pin,r)
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
        n=nib.load(case['files']['ct'])
        if q.sha(case['files']['ct'])!=case['identity']['source_sha256']['ct'] or list(n.shape)!=case['expected_native']['shape'] or not np.allclose(n.affine,case['expected_native']['affine'],atol=1e-5,rtol=0) or n.header.get_xyzt_units()[0]!='mm':raise ValueError('Admitted CT changed')
        image=np.asarray(n.dataobj,dtype=np.float32)
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
    if result['status'] not in ['COMPLETED','LOCAL_DIAGNOSTIC_COMPLETE_REFERENCE_PENDING']:raise ValueError('Cannot score failed prediction')
    from src.inference.saved_prediction_scoring import score_saved
    from src.inference.four_case_metrics_20261102 import components,contour,coverage
    import nibabel as nib
    import numpy as np
    from src.data.segmenter_native_windows_v1 import orient
    files=case['files'];pins=case['identity']['source_sha256']
    scored=score_saved(out/'prediction.nii.gz',files['pancreas'],files['lesion'],expected_prediction_sha256=(result['artifacts']['prediction.nii.gz']['sha256'] if isinstance(result['artifacts']['prediction.nii.gz'],dict) else result['artifacts']['prediction.nii.gz']),expected_pancreas_sha256=pins['pancreas'],expected_lesion_sha256=pins['lesion'],allow_unknown_reference_units=True)
    n=nib.load(out/'prediction.nii.gz');pred=np.asarray(n.dataobj);p=np.asarray(nib.load(files['pancreas']).dataobj,bool);l=np.asarray(nib.load(files['lesion']).dataobj,bool)
    loc=np.asarray(nib.load(out/'localizer.nii.gz').dataobj,bool);ev=result['evidence'];region=np.zeros(ev['parent_geometry']['shape'],bool)
    region[tuple(slice(a,b) for a,b in zip(ev['region_low'],ev['region_high']))]=True;region=orient(region,ev['parent_geometry'],inverse=True)
    scored.update(case_id=name,arm=arm,role='exposed_development',model_quality_acceptance=False,
        lesion_components=components(pred==2,l,n.affine),lesion_contour=contour(pred==2,l,n.affine),
        pancreas_contour=contour(pred>0,p|l,n.affine),localization=dict(predicted_mask_pancreas_coverage=coverage(p,loc),expanded_region_pancreas_coverage=coverage(p,region),expanded_region_lesion_coverage=coverage(l,region),scan_fraction=float(region.mean())),
        measurements=dict(voxel_volume_ml=abs(float(np.linalg.det(n.affine[:3,:3])))/1000,clinical_diameter='not_computed; component bounds and volumes are descriptive'),
        optimizer_updates=0,model_forwards=0)
    q.write(out/'score.json',scored)


if __name__=='__main__':
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--restore-sha256');g.add_argument('--admit-sources-sha256');g.add_argument('--launch-ready-sha256')
    g.add_argument('--restore-worker');g.add_argument('--admission-worker');g.add_argument('--worker',nargs=3);g.add_argument('--score',nargs=3)
    a=parser.parse_args()
    if a.restore_sha256 or a.admit_sources_sha256:
        pin=a.restore_sha256 or a.admit_sources_sha256;r=request(pin);admission(pin,r);gate(r)
        mode='restore' if a.restore_sha256 else 'source-admission';log=prep.OUT/(mode+'.log')
        if log.exists():raise FileExistsError('Stage already started; no retry')
        child='--restore-worker' if a.restore_sha256 else '--admission-worker'
        q.supervise([sys.executable,__file__,child,pin],log=log,seconds=r['limits']['restore_seconds'] if a.restore_sha256 else 600,
            rss_bytes=r['limits']['restore_rss_bytes'],tick=lambda:gate(r))
    elif a.launch_ready_sha256:launch(a.launch_ready_sha256)
    elif os.environ.get('PROWL_MATCHED_PHYSICAL_QUALIFICATION')!='1':raise ValueError('Owned supervisor required')
    elif a.restore_worker:restore(a.restore_worker)
    elif a.admission_worker:source_admission(a.admission_worker)
    elif a.worker:worker(*a.worker)
    else:scoring(*a.score)
