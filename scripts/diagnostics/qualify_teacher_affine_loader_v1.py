"""Bounded CPU qualification of the two-case affine path and ordinary-case equality."""
import csv,json,sys,time,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
import SimpleITK as sitk
import torch
from scripts.diagnostics.qualify_distillation_mac import BASE,write
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from src.data.teacher_affine_loader_v1 import load,EXCEPTIONS,POLICY
from src.data.segmenter_teacher_geometry_v2 import preprocess,plan


def main():
    out=Path(sys.argv[1]);out.mkdir(exist_ok=False);began=time.monotonic()
    torch.set_num_threads(2);sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(2)
    rows={r['case_id']:r for r in csv.DictReader((BASE/'rsuper-training-sources-01/manifest.csv').open())}
    names=['PanTS_00003067','PanTS_00004348','PanTS_00002331','PanTS_00007555'];cases=[];sources=[]
    for name in names:
        p=Path(rows[name]['ct_path']);mp=BASE/f'metadata-received-01/native-region/members/{name}.json';meta=json.loads(mp.read_text())
        if sha(p)!=meta['source_sha256']['ct']:raise ValueError('Source content changed')
        image,expected,record=load(p,meta,name)
        values,actual,processing=preprocess(image,max_voxels=256000000)
        assert expected['shape']==actual['shape'] and np.allclose(expected['affine'],actual['affine'],atol=1e-4,rtol=0)
        plan(actual['shape'],max_voxels=256000000,max_tiles=10000)
        exact=None
        if name not in EXCEPTIONS:
            old=sitk.ReadImage(str(p));ov,og,op=preprocess(old,max_voxels=256000000)
            exact=bool(np.array_equal(values,ov) and actual==og and processing==op)
            assert exact;del old,ov
        case=dict(case_id=name,success=True,ordinary_exact=exact,grid=actual,loader=record,source_sha256=sha(p),metadata_sha256=sha(mp),finite=bool(np.isfinite(values).all()))
        assert case['finite'];cases.append(case);write(out/(name+'.json'),case);sources.extend([p,mp]);print(name,'PASS',flush=True)
        del image,values
        if time.monotonic()-began>600:raise ValueError('CPU qualification time budget')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>12*1024**3:raise ValueError('CPU qualification memory budget')
    prior=BASE/'teacher-header-audit-20261028-02/result.json';audit=json.loads(prior.read_text())
    assert audit['total']==1333 and {r['case_id'] for r in audit['failures']}==EXCEPTIONS
    files=sources+[Path(__file__),ROOT/'src/data/teacher_affine_loader_v1.py',ROOT/'tests/test_teacher_affine_loader_v1.py',prior]
    pins=dict(audit['pins']);pins.update({str(p.resolve()):sha(p) for p in files})
    result=dict(success=True,complete_cohort_geometry=True,total=1333,unchanged_header_pass=1331,qualified_exceptions=sorted(EXCEPTIONS),policy=POLICY,cases=cases,pins=pins,seconds=time.monotonic()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,inference=False,student_training=False)
    write(out/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['pins','cases']}),flush=True)
if __name__=='__main__':main()
