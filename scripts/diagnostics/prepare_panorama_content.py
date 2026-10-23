"""Supervised CT integrity/union-ROI diagnostics; never admits or trains a cohort."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.diagnostics.audit_panorama_setup import sha, observation


def inspect_case(row, prior):
    import nibabel as nib
    import numpy as np
    from src.data.segmenter_geometry_v2 import recipe, canonical_geometry
    from src.data.panorama_geometry import preprocess
    result=dict(study_id=row['study_id'],disposition=row['disposition'],training_ready=False)
    if prior['status']!='technical_pass_not_admitted':
        return dict(result,status='retained_prior_hold_or_exclusion',prior_status=prior['status'],
                    reason=prior.get('reason'),payloads_opened=False)
    paths=[Path(row[k]['path']) for k in ('ct','label')]
    before=[observation(p) for p in paths]
    for i,kind in enumerate(('ct','label')):
        if before[i][2]!=row[kind]['bytes'] or sha(paths[i])!=row[kind]['expected_sha256']:
            raise ValueError('Source SHA256/size changed: '+row['study_id']+' '+kind)
    ct,mask=[nib.load(p) for p in paths]
    geometry=recipe()
    canonical_geometry(list(ct.shape),ct.affine,geometry)
    if ct.shape!=mask.shape or not np.allclose(ct.affine,mask.affine,rtol=0,atol=1e-5):
        raise ValueError('Previously accepted grid changed')
    image=ct.get_fdata(dtype=np.float32)
    if not np.isfinite(image).all():raise ValueError('Nonfinite CT content')
    result.update(ct_sha256=row['ct']['expected_sha256'],label_sha256=row['label']['expected_sha256'],
        ct_shape=list(ct.shape),hu_min=float(image.min()),hu_max=float(image.max()),
        status='ct_content_pass_not_admitted')
    if row['pdac']=='positive':
        if float(mask.dataobj.slope)!=1 or float(mask.dataobj.inter)!=0:
            raise ValueError('Label scaling changed')
        derived=preprocess(image,mask.dataobj.get_unscaled(),ct.affine,geometry,
            source_identity=dict(study_id=row['study_id'],ct_sha256=row['ct']['expected_sha256']),diagnosis='PDAC')
        result.update(geometry=derived['geometry'],geometry_sha256=derived['geometry_sha256'],
            mechanical_survival_pass=derived['mechanical_survival_pass'],
            lost_component_ids=derived['lost_component_ids'],
            tensor_pancreas_voxels=int(np.count_nonzero(derived['target']==1)),
            tensor_lesion_voxels=int(np.count_nonzero(derived['target']==2)))
        if not derived['mechanical_survival_pass']:result['status']='union_crop_technical_hold'
    else:
        result['target_policy']='unknown_generic_lesion_no_three_class_training_target'
    if before!=[observation(p) for p in paths]:raise ValueError('Source changed during inspection')
    return result


def worker(catalog,audit,output):
    request=json.loads((audit/'request.json').read_text())
    if sha(catalog)!=request['catalog_sha256']:
        raise ValueError('Catalog differs from completed header audit')
    rows=[json.loads(s) for s in catalog.read_text().splitlines()]
    prior_rows=[json.loads(s) for s in (audit/'cases.jsonl').read_text().splitlines()]
    prior={r['study_id']:r for r in prior_rows}
    summary=json.loads((audit/'summary.json').read_text())
    resources=json.loads((audit/'resources.json').read_text())
    if not summary['completed'] or not resources['workers_reaped']:
        raise ValueError('Completed reaped prior audit required')
    if len(prior)!=len(prior_rows) or len(rows)!=len(prior) or {r['study_id'] for r in rows}!=set(prior):
        raise ValueError('Catalog/prior audit identity mismatch')
    counts=Counter();started=time.monotonic()
    with (output/'cases.jsonl').open('x') as stream:
        for row in rows:
            result=inspect_case(row,prior[row['study_id']])
            result['elapsed_seconds']=time.monotonic()-started
            stream.write(json.dumps(result,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
            counts[result['status']]+=1
            if sum(counts.values())%25==0:print(json.dumps(dict(checked=sum(counts.values()),counts=counts)),flush=True)
    (output/'summary.json').write_text(json.dumps(dict(completed=True,counts=counts,
        seconds=time.monotonic()-started,training_ready=False,optimizer_updates=0,
        remaining=['duplicate_calibration_and_adjudication','machine_pancreas_visual_review','cohort_admission']),indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('catalog','audit','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--worker',action='store_true');a=p.parse_args()
    if a.worker:return worker(a.catalog,a.audit,a.output)
    from src.operations.full_training_platform import training_guard,watch_windows,require_ac
    if a.output.exists():raise FileExistsError(a.output)
    controls=[a.catalog]+[a.audit/n for n in ('summary.json','resources.json','cases.jsonl')]
    pins={str(path):sha(path) for path in controls}
    source_paths=[ROOT/p for p in ('scripts/diagnostics/prepare_panorama_content.py',
        'scripts/diagnostics/audit_panorama_setup.py','src/data/panorama_geometry.py',
        'src/data/panorama_setup.py','src/data/segmenter_geometry_v2.py','src/data/segmenter_geometry_v1.py')]
    pins.update({str(path):sha(path) for path in source_paths})
    device=a.output.parent.stat().st_dev
    def tick():
        require_ac()
        if a.output.stat().st_dev!=device or shutil.disk_usage(a.output).free<100*1024**3:
            raise RuntimeError('Output volume/space boundary')
    with training_guard(ROOT/'outputs/prowl/.panorama-setup-audit.lock'):
        a.output.mkdir();tick()
        (a.output/'request.json').write_text(json.dumps(dict(pins=pins,seconds=14400,
            rss_bytes=12*1024**3,purpose='CT_content_union_geometry_only_no_training_no_test_reads'),indent=2)+'\n')
        with (a.output/'worker.log').open('x') as log:
            child=subprocess.Popen([sys.executable,__file__,'--catalog',str(a.catalog),
                '--audit',str(a.audit),'--output',str(a.output),'--worker'],cwd=ROOT,
                stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2'))
            try:
                watch_windows(child,seconds=14400,rss_bytes=12*1024**3,tick=tick)
                if any(sha(Path(path))!=pin for path,pin in pins.items()):raise RuntimeError('Pinned inputs/code changed')
            finally:
                (a.output/'resources.json').write_text(json.dumps(getattr(child,'duration_resources',{}),indent=2)+'\n')
        print((a.output/'summary.json').read_text(),flush=True)


if __name__=='__main__':main()
