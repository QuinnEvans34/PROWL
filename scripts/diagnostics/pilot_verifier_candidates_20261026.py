"""One bounded six-fit-case export pilot; no scientific training or full533 dispatch."""
import argparse,json,os,sys,time,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.experiment_config import sha256
from scripts.diagnostics import setup_fast_varied as shared
from src.operations.full_training_platform import require_ac,watch_windows,training_guard
BASE=Path('E:/PROWL/readiness/verifier-generator-20261023-a01')
OUT=Path('E:/PROWL/readiness/verifier-candidate-pilot-20261026-a01')
RUN=Path('E:/PROWL/artifacts/pants_reserved_verifier_generator_24k_20261025')
REVIEW=Path('E:/PROWL/readiness/verifier-generator-review-20261026-a01/results.json')
PARTITION_SHA='e70e110078d59d35b4171a9711bd2e0ea1ffa9f25aaf405e0d010f31e030fd35'
CHECKPOINT_SHA='0da3ac2b31eceeab82f040af6c95bded6bf3b500fe6cac00449584e2404f49b8'
read=shared.read;write=shared.write

def provider():
    from src.data.verifier_candidate_inputs_v1 import CandidateInputs
    return CandidateInputs(partition=read(BASE/'partitions.json'),partition_sha256=sha256(BASE/'partitions.json'),
        expected_partition_sha256=PARTITION_SHA,manifest=shared.parent.MANIFEST,
        review=shared.parent.SOURCE_SETUP/'cohort-review.json',train_file=shared.parent.TRAIN,
        dev_file=shared.parent.SOURCE_SETUP/'development.txt')

def prepare():
    import numpy as np
    from src.data.segmenter_native_windows_v1 import tiles
    if OUT.exists():raise ValueError('Pilot directory exists; no overwrite')
    if sha256(BASE/'partitions.json')!=PARTITION_SHA or sha256(RUN/'execution/terminal.pt')!=CHECKPOINT_SHA:raise ValueError('Parent identity')
    review=read(REVIEW)
    if review['status']!='CLOSEOUT_PASS_NOT_VERIFIER_EFFICACY':raise ValueError('Parent closeout')
    rows=[]
    for n in read(BASE/'partitions.json')['roles']['verifier_fit']:
        m=read(shared.CACHE/(n+'.json'))
        volume=m['lesion_voxels']*abs(np.linalg.det(np.array(m['geometry']['affine'])[:3,:3]))/1000
        rows.append((n,m,volume))
    selected=['PanTS_00002720']
    if selected[0] not in {r[0] for r in rows}:raise ValueError('Required difficult case no longer fit')
    groups=[sorted([r for r in rows if r[2]==0],key=lambda r:r[0]),
        sorted([r for r in rows if r[2]==0],key=lambda r:-np.prod(r[1]['geometry']['shape'])),
        sorted([r for r in rows if 0<r[2]<1],key=lambda r:r[2]),
        sorted([r for r in rows if 1<=r[2]<=10],key=lambda r:r[0]),
        sorted([r for r in rows if r[2]>10],key=lambda r:-len(tiles(r[1]['record']['shape'])))]
    for group in groups:
        n=next(r[0] for r in group if r[0] not in selected);selected.append(n)
    estimates={n:dict(tiles=len(tiles(m['record']['shape'])),region_voxels=int(np.prod(m['geometry']['shape'])),volume_ml=v) for n,m,v in rows if n in selected}
    raw=sum(e['region_voxels']*5 for e in estimates.values())
    if raw>int(1.8*1024**3):raise ValueError('Pilot uncompressed artifact estimate exceeds budget')
    files=list((ROOT/'src').rglob('*.py'))+[Path(__file__),BASE/'partitions.json',REVIEW,RUN/'execution/terminal.pt',RUN/'input-control.json',RUN/'configuration.json',RUN/'ready.json',RUN/'execution/history.jsonl',ROOT/'tests/test_verifier_candidate_preparation_v1.py']
    files.extend(shared.CACHE/(n+'.json') for n in selected)
    OUT.mkdir()
    write(OUT/'request.json',dict(cases=selected,estimates=estimates,estimated_raw_bytes=raw,
        pins={str(p):sha256(p) for p in files},seconds=3600,rss_bytes=12*1024**3,gpu_bytes=6*1024**3,
        output_bytes=2*1024**3,scientific_training=False,optimizer_updates=0,full533_authorized=False))
    print(json.dumps(dict(cases=selected,estimates=estimates,raw_bytes=raw)))

def check():
    r=read(OUT/'request.json')
    for p,h in r['pins'].items():
        if sha256(p)!=h:raise ValueError('Pilot pin changed: '+p)
    return r

def worker():
    import numpy as np,torch
    from scipy import ndimage
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from src.training.segmenter_physical_windows_session_v1 import predict_native
    from src.training.verifier_candidate_export_v1 import predict,native_embed
    from src.training.candidate_verifier_v1 import candidates,training_labels,retain_candidates
    from src.training.verifier_candidate_provenance_v1 import validate_records
    from src.data.segmenter_native_windows_v1 import orient
    r=check();torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(r['gpu_bytes']/torch.cuda.get_device_properties(0).total_memory)
    state=torch.load(RUN/'execution/terminal.pt',map_location='cpu',weights_only=True)
    identity=json.loads((RUN/'execution/history.jsonl').open().readline())['identity']
    s=FastVariedSession.restore(state['session'],identity)
    if s.step!=24000 or state['best_score'] is not None:raise ValueError('Wrong fixed terminal')
    s.raw.model.requires_grad_(False);p=provider();records=[];start=time.monotonic()
    def tick(done=0,total=0):
        require_ac()
        if time.monotonic()-start>r['seconds'] or torch.cuda.max_memory_reserved()>r['gpu_bytes']:raise ValueError('Worker resource cap')
        if sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file())>r['output_bytes']:raise ValueError('Output cap')
    for n in r['cases']:
        began=time.monotonic();case=p.load(n,role='verifier_fit');meta=read(shared.CACHE/(n+'.json'))
        for k in ('geometry','parent_geometry','region_low','region_high'):
            if case[k]!=meta[k]:raise ValueError('Existing geometry differs: '+k)
        codes,prob,info=predict(s.raw,case['image'],case['geometry'],progress=tick)
        with torch.no_grad():baseline,oldinfo=predict_native(s.raw,case['image'],case['geometry'],progress=tick)
        if not np.array_equal(codes,baseline) or info!=oldinfo:raise ValueError('Baseline equivalence failed')
        archive=OUT/(n+'.npz')
        with archive.open('xb') as f:np.savez_compressed(f,codes=codes,lesion_probability=prob)
        with np.load(archive,allow_pickle=False) as a:
            if not np.array_equal(a['codes'],codes) or not np.array_equal(a['lesion_probability'],prob):raise ValueError('Archive roundtrip')
        # Labels read only after predictions have been computed and persisted.
        truth=p.fit_truth(n,role='verifier_fit',parent_geometry=case['parent_geometry'])
        native=native_embed(codes,case);labels,parts=candidates(native==2)
        targets=training_labels(labels,truth)
        if not np.array_equal(retain_candidates(labels,{i:0 for i in targets},0),native==2):raise ValueError('Baseline gate identity')
        gt,gt_count=ndimage.label(truth,np.ones((3,3,3)));hit=set(np.unique(gt[native==2]))-{0}
        truth_roi=orient(truth,case['parent_geometry'])[tuple(slice(l,h) for l,h in zip(case['region_low'],case['region_high']))]
        support=truth_roi if truth_roi.any() else codes==2
        center=[int(np.argmax(support.sum(axis=tuple(k for k in range(3) if k!=axis)))) if support.any() else codes.shape[axis]//2 for axis in range(3)]
        fig,axes=plt.subplots(1,3,figsize=(12,4))
        for axis,ax in enumerate(axes):
            ct=np.take(case['image'],center[axis],axis=axis).T;tr=np.take(truth_roi,center[axis],axis=axis).T;pr=np.take(codes==2,center[axis],axis=axis).T
            ax.imshow(ct,cmap='gray',vmin=0,vmax=1,origin='lower')
            if tr.any():ax.contour(tr,levels=[.5],colors=['lime'],linewidths=.7)
            if pr.any():ax.contour(pr,levels=[.5],colors=['red'],linewidths=.7)
            ax.set_title('Axis '+str(axis));ax.axis('off')
        fig.suptitle(n+' fit-only pilot: green annotation / red prediction');fig.tight_layout()
        figure=OUT/(n+'.png');fig.savefig(figure,dpi=100);plt.close(fig)
        row=dict(case_id=n,role='verifier_fit',checkpoint_sha256=CHECKPOINT_SHA,
            generator_receipt_sha256=sha256(RUN/'ready.json'),prediction_sha256=sha256(archive),
            ct_sha256=case['source_sha256']['ct'],pancreas_sha256=case['source_sha256']['pancreas'],
            gap_voxels=info['gap_voxels'],candidate_count=len(parts),true_candidates=sum(targets.values()),
            false_candidates=len(parts)-sum(targets.values()),gt_components=gt_count,detected_gt_components=len(hit),
            prediction_voxels=int((native==2).sum()),annotation_voxels=int(truth.sum()),
            annotation_outside_region=int(truth.sum()-truth_roi.sum()),baseline_exact=True,archive_exact=True,
            seconds=time.monotonic()-began,artifact_bytes=archive.stat().st_size,tiles=info['tiles'],
            figure=figure.name,figure_sha256=sha256(figure),geometry={k:case[k] for k in ('geometry','parent_geometry','region_low','region_high')},
            components=[dict(part,positive=targets[part['component_id']]) for part in parts])
        if row['annotation_outside_region']:raise ValueError('Coverage loss: investigate, no exclusions')
        write(OUT/(n+'.json'),row);records.append(row);tick();print(json.dumps({k:row[k] for k in ('case_id','seconds','tiles','candidate_count','false_candidates')}),flush=True)
        del case,codes,prob,baseline,truth,native,labels,gt,truth_roi,support
    validate_records(records,read(BASE/'partitions.json'),checkpoint_sha256=CHECKPOINT_SHA,
        receipt_sha256=sha256(RUN/'ready.json'),actual_generator_ids=list(s.raw.exposure),required_ids=r['cases'])
    write(OUT/'result.json',dict(passed=True,cases=records,seconds=time.monotonic()-start,
        peak_gpu_reserved=torch.cuda.max_memory_reserved(),visual_review_pending=True,optimizer_updates=0))

def run(pin):
    if sha256(OUT/'request.json')!=pin:raise ValueError('Request identity')
    if (OUT/'worker.log').exists() or (OUT/'resources.json').exists():raise ValueError('Pilot already started; no retry')
    r=check();shared.resources()
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        with (OUT/'worker.log').open('x') as log:
            env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_CANDIDATE_PILOT='1');env.pop('CUDA_VISIBLE_DEVICES',None)
            process=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            success=False
            try:watch_windows(process,seconds=r['seconds'],rss_bytes=r['rss_bytes'],tick=require_ac);success=True
            finally:write(OUT/'resources.json',dict(getattr(process,'duration_resources',{}),success=success,exit_code=process.returncode))

if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--run-sha256');g.add_argument('--worker',action='store_true');a=ap.parse_args()
    if a.prepare:prepare()
    elif a.run_sha256:run(a.run_sha256)
    elif os.environ.get('PROWL_CANDIDATE_PILOT')=='1':worker()
    else:raise ValueError('Supervisor required')
