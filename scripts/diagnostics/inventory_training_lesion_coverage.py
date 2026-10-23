"""Training-positive label-only crop inventory; no CT/model/cache mutations."""
import csv,json,sys,time,shutil
from pathlib import Path
import numpy as np
import nibabel as nib
import psutil
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.segmenter_content_v1 import target_content
from src.data.segmenter_geometry_v2 import validate_record
from src.training.experiment_config import sha256
SETUP=Path('E:/PROWL/readiness/pants-augmentation-24k-20261017-a01')
OUT=Path('E:/PROWL/readiness/training-coverage-inventory-20261018-a01')


def coverage(mask,box):
    lo,hi=box;total=int(mask.sum());inside=int(mask[tuple(slice(l,h) for l,h in zip(lo,hi))].sum())
    assert total>0
    low=[];high=[]
    for axis in range(3):
        support=np.flatnonzero(mask.any(axis=tuple(a for a in range(3) if a!=axis)))
        low.append(int(support[0]));high.append(int(support[-1])+1)
    return dict(total_voxels=total,inside_voxels=inside,outside_voxels=total-inside,
        coverage=inside/total,lesion_box=[low,high])


def main():
    started=time.monotonic();process=psutil.Process();peak=0
    def tick():
        nonlocal peak
        peak=max(peak,process.memory_info().rss)
        assert time.monotonic()-started<1800 and peak<8*1024**3,'Diagnostic limit'
        assert all(shutil.disk_usage(d).free>=100*1024**3 for d in ('C:/','E:/')),'Free space floor'
    review=json.loads((SETUP/'cohort-review.json').read_text());root=Path(review['prepared_cache']['root'])
    train=Path('E:/PROWL/readiness/data-setup-20261010-a01/pants-admitted/train.txt').read_text().split()
    dev=(SETUP/'development.txt').read_text().split()
    names=[n for n in train if review['target_states'][n]=='positive']
    assert len(train)==1333 and len(names)==671 and not set(train)&set(dev)
    with Path('E:/PROWL/readiness/data-setup-20261010-a01/pants-manifest.csv').open(newline='') as f:rows={r['case_id']:r for r in csv.DictReader(f)}
    tick();OUT.mkdir(exist_ok=False)
    pins=dict(script=sha256(__file__),cohort_review=sha256(SETUP/'cohort-review.json'))
    (OUT/'request.json').write_text(json.dumps(dict(train_positive_cases=names,source_pins=pins,ct_reads=0,test_reads=0,maximum_seconds=1800),indent=2))
    records=[]
    try:
        for index,n in enumerate(names):
            tick();metadata=root/(n+'.json');meta=json.loads(metadata.read_text());t=meta['transform']
            assert sha256(metadata)==review['prepared_cache']['members'][n]['metadata_sha256']
            validate_record(t,meta['transform_sha256'])
            path=Path(rows[n]['lesion_path']);assert sha256(path)==meta['source_sha256']['lesion']
            obj=nib.load(path);assert obj.shape==tuple(t['source_shape']) and np.allclose(obj.affine,t['source_affine'],rtol=0,atol=1e-5)
            p=obj.dataobj;mask,decode=target_content(p.get_unscaled(),dict(slope=float(p.slope),intercept=float(p.inter)))
            r=coverage(mask,t['native_box']);assert r['total_voxels']==sum(c['native_voxels'] for c in meta['fidelity']['components'])
            plane_mm=1/np.linalg.norm(np.linalg.inv(np.array(t['source_affine'])[:3,:3]),axis=1)
            needed=np.maximum(np.maximum(np.array(t['native_box'][0])-r['lesion_box'][0],np.array(r['lesion_box'][1])-t['native_box'][1]),0)
            r.update(case_id=n,extra_margin_beyond_old_box_mm=float(max(needed*plane_mm)),
                source_lesion_sha256=meta['source_sha256']['lesion'],source_file=path.name,
                cache_metadata_sha256=sha256(metadata),effective_spacing_mm=t['effective_spacing_mm'][0])
            with (OUT/'cases.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
            records.append(r);del mask
            if (index+1)%25==0:print(json.dumps(dict(completed=index+1,total=671,clipped=sum(x['outside_voxels']>0 for x in records),seconds=time.monotonic()-started)),flush=True)
        summary=dict(completed=True,n=len(records),fully_covered=sum(r['outside_voxels']==0 for r in records),
            clipped=[r for r in records if r['outside_voxels']>0],minimum_coverage=min(r['coverage'] for r in records),
            elapsed_seconds=time.monotonic()-started,peak_rss=peak,ct_reads=0,development_reads=0,test_reads=0,
            code_sha256=pins['script'],scope='All admitted positive training masks, coverage only not clinical annotation adjudication')
        (OUT/'results.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='clipped'}),flush=True)
    except BaseException as exc:
        (OUT/'failure.json').write_text(json.dumps(dict(completed_cases=len(records),error=str(exc))));raise


if __name__=='__main__':main()
