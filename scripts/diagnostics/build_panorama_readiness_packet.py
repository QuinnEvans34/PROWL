"""Generate QC and duplicate-calibration evidence, then stop for review. No training."""
import argparse
from collections import Counter,defaultdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.audit_panorama_setup import sha,observation


def save(path,value):
    with path.open('x') as f:f.write(json.dumps(value,indent=2,allow_nan=False)+'\n')


def select_qc(rows,audit,scanners):
    clean=[r for r in rows if r['disposition']!='excluded_declared_import']
    selected={};reasons=defaultdict(list)
    def add(r,why):selected[r['study_id']]=r;reasons[r['study_id']].append(why)
    for prefix in ('expert_pdac','optional_machine','not_generic'):
        eligible=[r for r in clean if r['disposition'].startswith(prefix)
                  and audit[r['study_id']]['status']=='ct_content_pass_not_admitted']
        if len(eligible)<10:raise ValueError('Insufficient QC stratum')
        for r in eligible[:10]:add(r,prefix)
    for r in clean:
        if r['disposition']=='quarantined_manual_non_pdac':add(r,'manual_non_PDAC_anomaly')
        if audit[r['study_id']]['status']=='union_crop_technical_hold':add(r,'resampling_loss')
    families=defaultdict(list)
    for r in rows:families[r['subject_id']].append(r)
    for subject,members in families.items():
        if len(members)>1:
            eligible=[r for r in members if r in clean]
            if eligible:
                eligible.sort(key=lambda r:(audit[r['study_id']]['status']!='ct_content_pass_not_admitted',r['study_id']))
                add(eligible[0],'repeat_family:'+subject)
    for scanner in sorted(set(scanners.get(r['study_id'],'unknown') for r in clean)):
        eligible=[r for r in clean if scanners.get(r['study_id'],'unknown')==scanner
                  and audit[r['study_id']]['status']=='ct_content_pass_not_admitted']
        if eligible:add(eligible[0],'scanner:'+scanner)
    return [dict(row=selected[k],reasons=reasons[k]) for k in sorted(selected)]


def render_qc(selection,audit,out):
    import nibabel as nib
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.data.segmenter_geometry_v2 import recipe,canonical_geometry
    from src.data.panorama_setup import map_labels
    records=[]
    for item in selection:
        r=item['row'];name=r['publisher_study_id'];prior=audit[r['study_id']]
        if prior['status']=='retained_prior_hold_or_exclusion':
            records.append(dict(study_id=r['study_id'],status='held_not_rendered',reasons=item['reasons']))
            continue
        paths=[Path(r[k]['path']) for k in ('ct','label')];before=[observation(p) for p in paths]
        for k,p in zip(('ct','label'),paths):
            if sha(p)!=r[k]['expected_sha256']:raise ValueError('QC source hash changed')
        ct,mask=[nib.load(p) for p in paths]
        canonical_geometry(list(ct.shape),ct.affine,recipe())
        if ct.shape!=mask.shape or not np.allclose(ct.affine,mask.affine,atol=1e-5,rtol=0):
            raise ValueError('QC source grid changed')
        image=ct.get_fdata(dtype=np.float32);raw=mask.dataobj.get_unscaled()
        mapped=map_labels(raw,diagnosis='PDAC' if r['pdac']=='positive' else 'non-PDAC')
        supports=[mapped['pancreas'],mapped['lesion'] if mapped['lesion'].any() else mapped['pancreas']]
        centers=[]
        for support in supports:
            centers.append([int(np.median(np.flatnonzero(support.any(axis=tuple(k for k in range(3) if k!=axis))))) for axis in range(3)])
        fig,axes=plt.subplots(2,3,figsize=(12,8),facecolor='black')
        for j,center in enumerate(centers):
            for axis in range(3):
                ax=axes[j,axis];sl=[slice(None)]*3;sl[axis]=center[axis];sl=tuple(sl)
                ax.imshow(image[sl].T,origin='lower',cmap='gray',vmin=-100,vmax=250)
                for code,color in [(4,'lime'),(1,'red')]:
                    field=(raw[sl].T==code)
                    if field.any():ax.contour(field,levels=[.5],colors=[color],linewidths=.6)
                ax.set_title(f'axis {axis}, index {center[axis]}',color='white',fontsize=9);ax.axis('off')
        fig.suptitle(name+' | green: machine pancreas; red: lesion | native array axes, not radiological orientation',color='white',fontsize=9)
        fig.tight_layout();path=out/(name+'.png');fig.savefig(path,dpi=120,facecolor='black');plt.close(fig)
        if before!=[observation(p) for p in paths]:raise ValueError('QC source changed during render')
        record=dict(study_id=r['study_id'],subject_id=r['subject_id'],reasons=item['reasons'],
            status='awaiting_visual_review',overlay=str(path),overlay_sha256=sha(path),
            ct_sha256=r['ct']['expected_sha256'],label_sha256=r['label']['expected_sha256'],
            prior_status=prior['status'],source_annotation_method=r['lesion_method'],
            boundary_contact=bool(np.any(mapped['crop_support'][[0,-1],:,:]) or np.any(mapped['crop_support'][:,[0,-1],:]) or np.any(mapped['crop_support'][:,:,[0,-1]])),
            pancreas_voxels=int(mapped['pancreas'].sum()),lesion_voxels=int(mapped['lesion'].sum()),
            training_ready=False)
        records.append(record)
        save(out/(name+'.json'),record)
        print(json.dumps(dict(stage='qc',completed=len(records),total=len(selection))),flush=True)
    save(out/'index.json',records)


def calibration(bank_rows,out):
    import nibabel as nib
    import numpy as np
    from src.data.ct_fingerprint_v1 import CONFIG,canonical,decoded_hash,fingerprint,variants,candidates
    save(out/'frozen-config.json',dict(config=CONFIG,bank=bank_rows,parents=[0,1,10,11],
        controls='20 planted variants; other subjects are distractors, not adjudicated nonmatches'))
    vectors=[];observations=[]
    for row in bank_rows:
        path=Path(row['path']);before=observation(path)
        actual=sha(path)
        if actual!=row['expected_sha256']:raise ValueError('Calibration source hash changed')
        image=canonical(nib.load(path));vectors.append(fingerprint(image))
        observations.append(dict(study_id=row['study_id'],ct_sha256=actual,decoded_sha256=decoded_hash(image),
            shape=list(image.shape),affine=image.affine.tolist()))
        if observation(path)!=before:raise ValueError('Calibration source changed')
    bank=np.stack(vectors);np.save(out/'bank.npy',bank,allow_pickle=False)
    results=[]
    for index in (0,1,10,11):
        row=bank_rows[index];image=canonical(nib.load(row['path']))
        for label,variant in variants(image):
            if label=='header_copy':
                # Real gzip/header round trip, not just an in-memory identity copy.
                variant.header['descrip']=b'PROWL planted duplicate control'
                path=out/f'planted-{index}.nii.gz';nib.save(variant,path);variant=nib.load(path)
            vector=fingerprint(canonical(variant));matches=candidates(vector,bank)
            results.append(dict(parent=row['study_id'],variant=label,recovered=index in [i for i,d in matches],
                candidates=[dict(study_id=bank_rows[i]['study_id'],distance=d) for i,d in matches]))
        print(json.dumps(dict(stage='calibration',variants=len(results))),flush=True)
    recovered=sum(r['recovered'] for r in results)
    save(out/'result.json',dict(config=CONFIG,observations=observations,planted=results,
        recovered=recovered,total=len(results),recall_gate_passed=recovered>=19,
        qualified_for_full_scan=False,training_ready=False,
        next='Review both-source distractors/negative controls and candidate burden before approving frozen scan parameters'))


def worker(base,out):
    from src.training.experiment_config import ids
    rows=[json.loads(s) for s in (base/'panorama-candidates.jsonl').read_text().splitlines()]
    audit={r['study_id']:r for r in [json.loads(s) for s in (base/'panorama-ct-union-a01/cases.jsonl').read_text().splitlines()]}
    # Read the retained metadata export, not clinical labels for protected PanTS.
    metadata=json.loads((ROOT/'outputs/prowl/readiness-reset-20261010/panorama-workbook-values.json').read_text())
    values=metadata['values'];scanners={'panorama:study:'+str(r[1]):str(r[5] or 'unknown') for r in values[1:]}
    selection=select_qc(rows,audit,scanners);save(out/'qc-selection.json',selection)
    handoff=Path('E:/PROWL/transfer/PanTS-8h-20261008')
    inventory=[]
    for role,file in [('train','train.txt'),('development','val.txt'),('test','test.txt')]:
        for name in ids(handoff/'splits/original'/file):
            if not name.startswith('PanTS_') or not name[6:].isdigit():raise ValueError('Unsafe case ID')
            path=Path('D:/PanTS/data')/('ImageTe' if role=='test' else 'ImageTr')/name/'ct.nii.gz'
            inventory.append(dict(study_id=name,role=role,path=str(path),present=path.is_file()))
    save(out/'protected-CT-inventory.json',inventory)
    missing=[r for r in inventory if not r['present']]
    save(out/'coverage.json',dict(counts=dict(Counter(r['role'] for r in inventory)),missing=missing,
        protected_CT_payloads_opened=False,no_test_labels=True,no_models=True))
    render_qc(selection,audit,out/'quality')
    source=json.loads((handoff/'metadata/source-file-hashes.json').read_text())
    hashes={r['case_id']:r['sha256'] for r in source if r['kind']=='ct'}
    train=[r for r in inventory if r['role']=='train' and r['study_id'] in hashes and r['present']][:10]
    pano=[r for r in rows if audit[r['study_id']]['status']=='ct_content_pass_not_admitted'][:10]
    bank=[dict(study_id=r['study_id'],path=r['path'],expected_sha256=hashes[r['study_id']],source='pants') for r in train]
    bank += [dict(study_id=r['study_id'],path=r['ct']['path'],expected_sha256=r['ct']['expected_sha256'],source='panorama') for r in pano]
    if len(bank)!=20:raise ValueError('Calibration bank incomplete')
    calibration(bank,out/'calibration')
    save(out/'summary.json',dict(completed=True,status='review_required',training_ready=False,
        quality_selected=len(selection),missing_protected_CTs=len(missing),models=0,optimizer_updates=0,
        next=['visual_dispositions','calibration_negative_control_review','full_duplicate_scan','cohort','mixed_provider_and_smoke']))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
    if a.worker:return worker(a.base,a.output)
    from src.operations.full_training_platform import training_guard,watch_windows,require_ac
    from scripts.train_full_segmenter import tree_bytes
    prior=a.base/'panorama-ct-union-a01'
    if not json.loads((prior/'summary.json').read_text())['completed'] or not json.loads((prior/'resources.json').read_text())['workers_reaped']:
        raise ValueError('Prior content preparation incomplete')
    for path,pin in json.loads((prior/'request.json').read_text())['pins'].items():
        if sha(path)!=pin:raise ValueError('Prior producing evidence changed')
    if a.output.exists():raise FileExistsError(a.output)
    controls=[Path(__file__),ROOT/'src/data/ct_fingerprint_v1.py',a.base/'panorama-candidates.jsonl',
              prior/'cases.jsonl',ROOT/'outputs/prowl/readiness-reset-20261010/panorama-workbook-values.json']
    pins={str(p):sha(p) for p in controls};device=a.output.parent.stat().st_dev;last=[0.]
    def tick():
        if time.monotonic()-last[0]<10:return
        require_ac()
        if a.output.stat().st_dev!=device or shutil.disk_usage(a.output).free<100*1024**3 or tree_bytes(a.output)>4*1024**3:
            raise RuntimeError('Readiness packet storage boundary')
        if any(sha(path)!=pin for path,pin in pins.items()):raise RuntimeError('Producing input/code changed')
        last[0]=time.monotonic()
    with training_guard(ROOT/'outputs/prowl/.panorama-readiness-packet.lock'):
        a.output.mkdir();(a.output/'quality').mkdir();(a.output/'calibration').mkdir();tick()
        save(a.output/'request.json',dict(pins=pins,seconds=14400,rss_bytes=12*1024**3,no_training=True))
        with (a.output/'worker.log').open('x') as log:
            child=subprocess.Popen([sys.executable,__file__,'--base',str(a.base),'--output',str(a.output),'--worker'],
                cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2'))
            try:watch_windows(child,seconds=14400,rss_bytes=12*1024**3,tick=tick)
            finally:save(a.output/'resources.json',getattr(child,'duration_resources',{}))
        print((a.output/'summary.json').read_text(),flush=True)


if __name__=='__main__':main()
