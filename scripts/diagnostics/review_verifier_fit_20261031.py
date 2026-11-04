"""Fit-only candidate design evidence. No model fitting or calibration access."""
import json,os,sys,time,subprocess,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import pilot_verifier_candidates_20261026 as pilot
from src.operations.verifier_candidate_archive_v1 import write_json,append_event
from src.operations.full_training_platform import watch_windows,require_ac
from src.training.experiment_config import sha256
OUT=Path('E:/PROWL/readiness/verifier-fit-design-20261031-a01')
MANIFEST=Path('E:/PROWL/artifacts/verifier-candidates-20261030-a01/manifest.json')
MANIFEST_SHA='b5c989a158598e2aa3e3c6ecdaed5f0bf4b91803d0574b3250c5def473827aed'

def summarize(labels,truth,affine,probability):
    import numpy as np
    from scipy import ndimage
    if labels.shape!=truth.shape or probability.shape!=truth.shape:raise ValueError('Alignment')
    gt,ngt=ndimage.label(truth,np.ones((3,3,3),np.uint8));voxel_ml=abs(np.linalg.det(np.asarray(affine)[:3,:3]))/1000
    parts=[]
    for i,box in enumerate(ndimage.find_objects(labels),1):
        mask=labels[box]==i;overlap=gt[box][mask];hits=sorted(int(k) for k in np.unique(overlap) if k)
        pp=probability[box][mask];low=[s.start for s in box];high=[s.stop for s in box]
        parts.append(dict(component_id=i,low=low,high=high,voxels=int(mask.sum()),volume_ml=float(mask.sum()*voxel_ml),
            extent_mm=((np.array(high)-low)*np.linalg.norm(np.asarray(affine)[:3,:3],axis=0)).tolist(),
            positive=bool(hits),gt_hits=hits,overlap_voxels=int((overlap>0).sum()),probability_mean=float(pp.mean())))
    sizes=np.bincount(gt.ravel(),minlength=ngt+1)[1:];hit=set(k for p in parts for k in p['gt_hits'])
    return dict(candidates=parts,gt_components=[dict(component_id=i+1,volume_ml=float(v*voxel_ml),detected=i+1 in hit) for i,v in enumerate(sizes)],
        annotated_voxels=int(truth.sum()),predicted_voxels=int((labels>0).sum()))

def worker():
    import numpy as np
    from src.training.candidate_verifier_v1 import candidates
    from src.training.verifier_candidate_export_v1 import native_embed
    req=pilot.read(OUT/'request.json')
    for p,h in req['pins'].items():
        if sha256(p)!=h:raise ValueError('Pinned review input changed')
    provider=pilot.provider();rows=[];began=time.monotonic()
    archive=pilot.read(MANIFEST);byid={r['case_id']:r for r in archive['cases']}
    for n in req['cases']:
        row=byid[n]
        if row['role']!='verifier_fit':raise ValueError('Only fitting patients')
        path=Path(row['prediction_path'])
        if sha256(path)!=row['prediction_sha256']:raise ValueError('Prediction changed')
        truth=provider.fit_truth(n,role='verifier_fit',parent_geometry=row['geometry']['parent_geometry'])
        with np.load(path,allow_pickle=False) as a:
            pred=native_embed(a['codes'],row['geometry']);prob=native_embed(a['lesion_probability'],row['geometry'])
        labels,parts=candidates(pred==2)
        if parts!=row['components']:raise ValueError('Native component identity changed')
        result=summarize(labels,truth,row['geometry']['parent_geometry']['source_affine'],prob)
        rows.append(dict(case_id=n,role='verifier_fit',prediction_sha256=row['prediction_sha256'],**result))
        append_event(OUT/'progress.jsonl',dict(event='fit_case_reviewed',case_id=n,completed=len(rows),candidates=len(parts)))
        del truth,pred,prob,labels
        require_ac()
    flat=[c for r in rows for c in r['candidates']]
    stats=dict(patients=len(rows),zero_candidate_patients=sum(not r['candidates'] for r in rows),candidates=len(flat),
        positive_candidates=sum(c['positive'] for c in flat),negative_candidates=sum(not c['positive'] for c in flat),
        maximum_extent_mm=np.max([c['extent_mm'] for c in flat],axis=0).tolist(),
        extent_percentiles_mm=np.percentile([c['extent_mm'] for c in flat],[50,90,95,99],axis=0).tolist())
    write_json(OUT/'review.json',dict(status='FIT_ONLY_DESIGN_EVIDENCE',cases=rows,summary=stats,seconds=time.monotonic()-began,
        optimizer_updates=0,tune_label_reads=0,calibration_label_reads=0,development_reads=0))
    append_event(OUT/'progress.jsonl',dict(event='completed',**stats))

def run():
    if OUT.exists():raise ValueError('Design review already started')
    if sha256(MANIFEST)!=MANIFEST_SHA:raise ValueError('Completed manifest changed')
    part=pilot.read(pilot.BASE/'partitions.json')
    if sha256(pilot.BASE/'partitions.json')!=pilot.PARTITION_SHA:raise ValueError('Partition changed')
    OUT.mkdir();write_json(OUT/'request.json',dict(cases=part['roles']['verifier_fit'],seconds=3600,rss_bytes=12*1024**3,
        pins={str(p):sha256(p) for p in [Path(__file__),MANIFEST,pilot.BASE/'partitions.json',ROOT/'tests/test_verifier_fit_design_20261031.py']},scientific_training=False))
    with (OUT/'worker.log').open('x') as log:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
        p=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        success=False
        try:watch_windows(p,seconds=3600,rss_bytes=12*1024**3,tick=require_ac);success=True
        finally:write_json(OUT/'resources.json',dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if a.worker:worker()
    else:run()
