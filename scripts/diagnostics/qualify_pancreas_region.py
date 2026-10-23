"""Region-specific label audit. Reuses admitted identities and CT audit, no CT replay."""
import argparse,json,os,sys,time,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_physical_intake import provider as old_provider,load_labels
from scripts.diagnostics.qualify_native_intake import read_journal
from src.data.segmenter_native_windows_v1 import orient,tiles
from src.data.segmenter_pancreas_region_v1 import POLICY,crop_case,bank
from src.data.segmenter_physical_windows_v1 import sample_window,native_destination
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256
from src.operations.full_training_platform import watch_windows,require_ac
OUT=Path('E:/PROWL/readiness/pancreas-region-20261019-a01')
SOURCE=Path('E:/PROWL/readiness/native-intake-20261018-a02/cohort-complete/cases.jsonl')


def audit():
    import psutil
    from scipy import ndimage
    request=json.loads((OUT/'request.json').read_text())
    for path,h in request['pins'].items():
        if sha256(path)!=h:raise ValueError('Audit source changed')
    p=old_provider();rows=read_journal(SOURCE);began=time.monotonic();results=[]
    with (OUT/'cases.jsonl').open('xb') as f:
        for source in rows:
            if time.monotonic()-began>7200 or psutil.Process().memory_info().rss>10*1024**3:raise ValueError('Audit resource budget')
            case=load_labels(p,source)
            # Original pancreas is separate: target==1 alone would omit overlap with lesion.
            import nibabel as nib
            from src.data.segmenter_content_v1 import target_content
            obj=nib.load(p.rows[source['case_id']]['pancreas_path']);proxy=obj.dataobj
            pancreas,_=target_content(proxy.get_unscaled(),dict(slope=float(proxy.slope),intercept=float(proxy.inter)))
            case['original_pancreas']=pancreas
            roi=crop_case(case);record,cover=bank(roi)
            total=int((case['target']==2).sum());kept=int((roi['target']==2).sum())
            low,high=roi['region_low'],roi['region_high'];sl=tuple(slice(l,h) for l,h in zip(low,high))
            organ=orient(pancreas,case['geometry']);organ_total=int(organ.sum());organ_kept=int(organ[sl].sum())
            # Axis support proof for entire voxel-cell field of the UNION of both annotations.
            support=roi['target']>0;axes=[sorted({o[d] for o in cover}) for d in range(3)]
            for d,(factor,n) in enumerate(zip(record['factors'],record['shape'])):
                indices=np.flatnonzero(support.any(axis=tuple(k for k in range(3) if k!=d)))
                a,b=int(indices[0])*factor,(int(indices[-1])+1)*factor
                exposed=np.zeros(b-a,bool)
                for start in axes[d]:exposed[max(0,start-a):min(b-a,start+144-a)]=True
                if not exposed.all():raise ValueError('Coverage bank gap')
            for origin in cover:
                patch,_=sample_window(roi['target'],record,origin,order=0)
                dst,coords=native_destination(record,origin)
                restored=ndimage.map_coordinates(patch.astype(np.float32),coords,order=1,mode='nearest',prefilter=False)
                if not np.array_equal(restored,roi['target'][dst]):raise ValueError('Window detail roundtrip')
            row=dict(case_id=source['case_id'],role=source['role'],positive=source['positive'],
                lesion_total=total,lesion_kept=kept,pancreas_total=organ_total,pancreas_kept=organ_kept,
                coverage_pass=total==kept and organ_total==organ_kept,cover_windows=len(cover),
                region_low=low,region_high=high,region_fraction=float(np.prod(roi['target'].shape)/np.prod(case['target'].shape)),
                inference_tiles=len(tiles(record['shape'])),window_roundtrip_exact=True,ct_reads=0)
            f.write(canonical(row));f.flush();results.append(row)
            if len(results)%25==0:print(json.dumps(dict(completed=len(results),failed=sum(not r['coverage_pass'] for r in results),seconds=time.monotonic()-began)),flush=True)
    result=dict(completed=len(results)==1403,all_pass=all(r['coverage_pass'] for r in results),
        cases=len(results),failed=[r['case_id'] for r in results if not r['coverage_pass']],seconds=time.monotonic()-began,
        median_region_fraction=float(np.median([r['region_fraction'] for r in results])),ct_reads=0,test_reads=0)
    with (OUT/'result.json').open('xb') as f:f.write(canonical(result))
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if a.worker:audit()
    elif a.run:
        import subprocess
        require_ac()
        if any(shutil.disk_usage(d).free<100*1024**3 for d in ('C:/','E:/')):raise ValueError('Disk floor')
        OUT.mkdir(exist_ok=False)
        files=[Path(__file__),ROOT/'src/data/segmenter_pancreas_region_v1.py',SOURCE,
            ROOT/'src/data/segmenter_physical_windows_v1.py',ROOT/'scripts/diagnostics/qualify_physical_intake.py']
        with (OUT/'request.json').open('xb') as f:f.write(canonical(dict(policy=POLICY,pins={str(p):sha256(p) for p in files},max_seconds=7200)))
        with (OUT/'worker.log').open('x') as log:
            p=subprocess.Popen([sys.executable,__file__,'--worker'],stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
            try:watch_windows(p,seconds=7300,rss_bytes=12*1024**3,tick=require_ac)
            finally:
                with (OUT/'resources.json').open('xb') as f:f.write(canonical(getattr(p,'duration_resources',{})))
    else:ap.error('Choose --run or --worker')
