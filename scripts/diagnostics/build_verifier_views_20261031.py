"""Bounded, design-bound fit/tune views; candidate labels never select views."""
import argparse,json,sys,os,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import pilot_verifier_candidates_20261026 as pilot
from scripts.diagnostics import review_verifier_fit_20261031 as review
from scripts.acquisition import restore_verifier_fit_tune_20261031 as sources
from src.data.verifier_relocated_inputs_20261030 import RelocatedCandidateInputs
from src.data.verifier_candidate_inputs_v1 import CandidateInputs
from src.operations.verifier_candidate_archive_v1 import write_json,append_event,backup_file,tree_bytes
from src.operations.full_training_platform import watch_windows,require_ac
from src.training.experiment_config import sha256
BASE=Path('E:/PROWL/readiness/verifier-training-20261031-a01')
DESIGN=BASE/'design-v3.json'
CACHE=Path('E:/PROWL/cache/verifier-views-20261031-a01')
BACKUP=Path('C:/Users/quinn/PROWL-Backups/verifier-views-20261031-a01')

def provider(relocation):
    return RelocatedCandidateInputs(relocation=relocation,partition=pilot.read(pilot.BASE/'partitions.json'),
        partition_sha256=sha256(pilot.BASE/'partitions.json'),expected_partition_sha256=pilot.PARTITION_SHA,
        manifest=pilot.shared.parent.MANIFEST,review=pilot.shared.parent.SOURCE_SETUP/'cohort-review.json',
        train_file=pilot.shared.parent.TRAIN,dev_file=pilot.shared.parent.SOURCE_SETUP/'development.txt')

def read_truth(p,n,role,geometry,*,header_only=False):
    import numpy as np
    if role not in ('verifier_fit','verifier_tune') or p.roles[n]!=role:raise ValueError('Protected supervision')
    meta=p.metadata(n,role)
    # Separate supervision path; the inference provider itself remains label-blind.
    obj=CandidateInputs._object(p,n,'lesion',meta)
    g=geometry['parent_geometry']
    if obj.shape!=tuple(g['source_shape']) or not np.allclose(obj.affine,g['source_affine'],rtol=0,atol=1e-5):raise ValueError('Truth alignment')
    if header_only:return None
    return CandidateInputs._mask(obj).astype(bool)

def resource_check():
    import shutil
    require_ac()
    if min(shutil.disk_usage(d).free for d in ('C:/','E:/'))<100*1024**3:raise ValueError('Free floor')
    if tree_bytes(CACHE)>8*1024**3 or tree_bytes(BACKUP)>8*1024**3:raise ValueError('View cache cap')
    if tree_bytes('C:/Users/quinn/PROWL-Backups')>40*1024**3:raise ValueError('Combined backup cap')

def worker(mode):
    import numpy as np
    from scipy import ndimage
    from src.data.segmenter_native_windows_v1 import orient
    from src.training.candidate_verifier_v1 import candidates,training_labels
    from src.training.verifier_candidate_export_v1 import native_embed
    from src.data.verifier_views_v2_20261031 import make_views
    root=BASE/mode;req=pilot.read(root/'request.json');design=pilot.read(DESIGN)
    for path,pin in req['pins'].items():
        if sha256(path)!=pin:raise ValueError('View producer/input changed')
    relocation=pilot.read(req['relocation_path']);p=provider(relocation)
    records={r['case_id']:r for r in pilot.read(review.MANIFEST)['cases']}
    if sha256(review.OUT/'review.json')!=design['fit_review_sha256']:raise ValueError('Fit label evidence changed')
    fit_evidence={r['case_id']:r for r in pilot.read(review.OUT/'review.json')['cases']}
    rows=[];patient_rows=[];started=time.monotonic()
    if mode=='build':CACHE.mkdir();BACKUP.mkdir()
    dest=(root/'views') if mode=='pilot' else CACHE
    if mode=='pilot':dest.mkdir()
    for n in req['cases']:
        resource_check();r=records[n];role=r['role']
        if role not in ('verifier_fit','verifier_tune') or (mode=='pilot' and role!='verifier_fit'):raise ValueError('View role')
        if sha256(r['prediction_path'])!=r['prediction_sha256']:raise ValueError('Prediction changed')
        case=p.load(n,role=role)
        if any(case[k]!=r['geometry'][k] for k in ('geometry','parent_geometry','region_low','region_high')):raise ValueError('CT/prediction geometry')
        with np.load(r['prediction_path'],allow_pickle=False) as a:codes=a['codes'].copy();prob=a['lesion_probability'].copy()
        labels,parts=candidates(native_embed(codes,r['geometry'])==2)
        if parts!=r['components']:raise ValueError('Candidate membership changed')
        reuse_fit=mode=='build' and role=='verifier_fit'
        truth=read_truth(p,n,role,r['geometry'],header_only=reuse_fit)
        if reuse_fit:
            prior=fit_evidence[n]
            if prior['prediction_sha256']!=r['prediction_sha256']:raise ValueError('Fit label/prediction mismatch')
            stats={k:prior[k] for k in ('candidates','gt_components','annotated_voxels','predicted_voxels')}
            if [{k:c[k] for k in ('component_id','low','high','voxels')} for c in stats['candidates']]!=parts:raise ValueError('Fit component label mapping')
            target_labels={c['component_id']:c['positive'] for c in stats['candidates']}
        else:
            stats=review.summarize(labels,truth,r['geometry']['parent_geometry']['source_affine'],native_embed(prob,r['geometry']))
            target_labels=training_labels(labels,truth)
        sl=tuple(slice(l,h) for l,h in zip(case['region_low'],case['region_high']))
        local_labels=orient(labels,case['parent_geometry'])[sl];local_truth=None if truth is None else orient(truth,case['parent_geometry'])[sl]
        if truth is not None and int(local_truth.sum())!=int(truth.sum()):raise ValueError('Annotated field outside qualified region')
        patient_rows.append(dict(case_id=n,role=role,label_evidence='reused_exact_fit_review' if reuse_fit else 'source_mask',**stats))
        for part in stats['candidates']:
            cid=part['component_id'];views,meta=make_views(case['image'],prob,local_labels,cid,np.asarray(case['geometry']['affine']))
            points=local_labels==cid;pp=prob[points];volume=part['volume_ml'];side=meta['global_view']['spacing_mm'][0]*64
            features=np.asarray([np.log1p(volume)/10,np.log1p(side)/10,pp.mean(),pp.max()],np.float32)
            path=dest/(n+'-'+str(cid)+'.npz')
            with path.open('xb') as f:np.savez_compressed(f,views=views,features=features);f.flush();os.fsync(f.fileno())
            with np.load(path,allow_pickle=False) as stored:
                if not np.array_equal(stored['views'],views) or not np.array_equal(stored['features'],features):raise ValueError('Candidate cache roundtrip')
            if mode=='pilot' and tree_bytes(root)>2*1024**3:raise ValueError('Pilot output cap')
            row=dict(case_id=n,role=role,component_id=cid,positive=target_labels[cid],path=str(path),sha256=sha256(path),view_metadata=meta,
                prediction_sha256=r['prediction_sha256'],source_sha256=p.metadata(n,role)['source_sha256'])
            rows.append(row)
            if mode=='build':backup_file(path,BACKUP/path.name,reserve=lambda _:resource_check())
        if mode=='pilot':
            import matplotlib;matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            fig,ax=plt.subplots(1,3,figsize=(12,4));ax[0].set_title(n+' native CT / truth / prediction')
            focus=pilot.read(BASE/'pilot-focus-v2.json')['components'][n] if mode=='pilot' else None
            if parts and focus not in target_labels:raise ValueError('Pilot focus component missing')
            z=int(np.argmax((local_labels==focus).sum(axis=(0,1)))) if parts else codes.shape[2]//2
            ax[0].imshow(case['image'][:,:,z].T,origin='lower',cmap='gray',vmin=0,vmax=1)
            for mask,color in ((local_truth[:,:,z],'lime'),(codes[:,:,z]==2,'red')):
                if mask.any() and not mask.all():ax[0].contour(mask.T,levels=[.5],colors=[color],linewidths=.6)
            if parts:
                chosen=focus
                with np.load(dest/(n+'-'+str(chosen)+'.npz'),allow_pickle=False) as a:vv=a['views']
                for j,title in enumerate(('complete component view','detail view')):
                    zz=int(np.argmax(vv[j,2].sum(axis=(0,1))));ax[j+1].imshow(vv[j,0,:,:,zz].T,origin='lower',cmap='gray',vmin=0,vmax=1)
                    ax[j+1].contour(vv[j,2,:,:,zz].T,levels=[.5],colors=['red']);ax[j+1].set_title(title)
            else:
                ax[1].text(.1,.5,'Zero candidates: retained in accounting');ax[2].axis('off')
            for axis in ax:axis.set_xticks([]);axis.set_yticks([])
            fig.tight_layout();fig.savefig(root/(n+'.png'),dpi=120);plt.close(fig)
        append_event(root/'progress.jsonl',dict(event='case_complete',case_id=n,patients=len(patient_rows),candidates=len(rows)))
        del case,labels,truth,local_labels,local_truth,prob,codes
    resource_check()
    status='PILOT_COMPLETE_PENDING_VISUAL_REVIEW' if mode=='pilot' else 'QUALIFIED_FIT_TUNE_VIEWS'
    result=dict(status=status,candidates=rows,patient_records=patient_rows,patients=design['patients'],design_sha256=sha256(DESIGN),seconds=time.monotonic()-started)
    write_json(root/'manifest.json',result)
    if mode=='build':backup_file(root/'manifest.json',BACKUP/'manifest.json',reserve=lambda _:resource_check())
    append_event(root/'progress.jsonl',dict(event='completed',patients=len(patient_rows),candidates=len(rows)))

def run(mode):
    root=BASE/mode
    if root.exists():raise ValueError('Stage already started')
    design=pilot.read(DESIGN)
    if design['view_code_sha256']!=sha256(ROOT/'src/data/verifier_views_v2_20261031.py') or design['session_code_sha256']!=sha256(ROOT/'src/training/verifier_session_20261031.py'):raise ValueError('Frozen design implementation changed')
    if mode=='build':
        visual=pilot.read(BASE/'pilot/visual-review.json');res=pilot.read(BASE/'pilot/resources.json')
        if not visual['passed'] or visual['manifest_sha256']!=sha256(BASE/'pilot/manifest.json') or not res['success'] or not res['workers_reaped']:raise ValueError('Real pilot not qualified')
    names=design['pilot_cases'] if mode=='pilot' else design['patients']['verifier_fit']+design['patients']['verifier_tune']
    if sha256(review.MANIFEST)!=review.MANIFEST_SHA:raise ValueError('Archive changed')
    relocation_path=BASE/'pilot-relocation.json' if mode=='pilot' else sources.OUT/'restoration.json'
    p=provider(pilot.read(relocation_path))
    source_metadata=[pilot.shared.parent.SOURCE_SETUP/'cohort-review.json',p.root/'control.json',pilot.shared.parent.MANIFEST,pilot.shared.parent.TRAIN,pilot.shared.parent.SOURCE_SETUP/'development.txt']+[p.root/(n+'.json') for n in names]
    original=Path('E:/PROWL/readiness/verifier-candidate-export-20261027-a01/request.json')
    if sha256(original)!='edd8824e401aad8e5d8aefbf228f876931f3e792caaa457a7b28b32ca38b6a31':raise ValueError('Original source receipt changed')
    inherited={str(Path(k).resolve()).lower():v for k,v in pilot.read(original)['pins'].items()}
    control_path=pilot.RUN/'input-control.json'
    if sha256(control_path)!=inherited.get(str(control_path.resolve()).lower()):raise ValueError('Generator source control changed')
    control=pilot.read(control_path)
    expected={str(source_metadata[i].resolve()).lower():control['bindings'][key] for i,key in ((0,'review'),(2,'manifest'),(3,'train_file'),(4,'dev_file'))}
    expected[str((p.root/'control.json').resolve()).lower()]=control['source_control_sha256']
    expected.update({str((p.root/(n+'.json')).resolve()).lower():p.review['prepared_cache']['members'][n]['metadata_sha256'] for n in names})
    for path in source_metadata:
        if sha256(path)!=expected.get(str(path.resolve()).lower()):raise ValueError('Inherited source metadata identity: '+str(path))
    root.mkdir();files=[Path(__file__),Path(pilot.__file__),Path(review.__file__),Path(sources.__file__),DESIGN,BASE/'pilot-focus-v2.json',relocation_path,review.MANIFEST,review.OUT/'review.json',original,control_path]+source_metadata+list((ROOT/'src').rglob('*.py'))
    write_json(root/'request.json',dict(cases=names,relocation_path=str(relocation_path),pins={str(p):sha256(p) for p in files},seconds=7200 if mode=='build' else 1800,rss_bytes=12*1024**3))
    with (root/'worker.log').open('x') as log:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
        p=subprocess.Popen([sys.executable,__file__,'--worker',mode],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        success=False
        try:watch_windows(p,seconds=7200 if mode=='build' else 1800,rss_bytes=12*1024**3,tick=require_ac);success=True
        finally:write_json(root/'resources.json',dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['pilot','build']);ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if a.worker:worker(a.mode)
    else:run(a.mode)
