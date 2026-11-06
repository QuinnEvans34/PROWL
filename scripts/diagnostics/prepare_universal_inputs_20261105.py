"""One bounded header-only admission of four dev and twelve predeclared train cases."""
import csv
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path('E:/PROWL/readiness/universal-swin-20261105-a01')
DEV = ['PanTS_'+n.zfill(8) for n in ['2028','1347','2514','8743']]
TRAIN = ['PanTS_'+n.zfill(8) for n in ['4029','1477','2585','1197','4497','7093',
                                      '3142','1362','7256','6264','147','8795']]


def main():
    import nibabel as nib
    import numpy as np
    start = time.monotonic()
    OUT.mkdir(exist_ok=False)
    plan = {'development':DEV, 'training_header_candidates':TRAIN,
            'selection':'first four explicit-mm positive dev in frozen order; first six positive/six empty restored verifier-fit cases in historical train order',
            'maximum_header_cases':16,'voxel_reads':0,'gpu':False}
    (OUT/'input-plan.json').write_text(json.dumps(plan,indent=2))
    previous = json.loads(Path('E:/PROWL/artifacts/week05-autonomous70-20261103-a03/request.json').read_text())
    olddev = {c['case_id']:c for c in previous['cases']}
    source = Path('E:/PROWL/sources/pants/verifier-fit-tune-ct-20261031')
    restoration = json.loads((source/'restoration.json').read_text())
    with Path('E:/PROWL/readiness/data-setup-20261010-a01/pants-manifest.csv').open(newline='') as f:
        rows = {r['case_id']:r for r in csv.DictReader(f)}
    cache = Path('E:/PROWL/cache/pants-setup-20261010/cfab5906fce0fe759599990ec3b1a5955eddb77d1b7b60eeb93e171e7b990bf4')
    records=[]
    for name in DEV+TRAIN:
        if time.monotonic()-start > 300: raise RuntimeError('Header admission time cap')
        role = 'development' if name in DEV else 'train'
        if rows[name]['protected_role'] != role: raise ValueError('Role mismatch')
        meta = json.loads((cache/(name+'.json')).read_text())
        if role=='development': files=olddev[name]['files']
        else:
            restored=restoration['cases'][name]
            if restored['role']!='verifier_fit' or restored['sha256']!=meta['source_sha256']['ct']:
                raise ValueError('Restoration/fit identity mismatch')
            files={'ct':restored['path'], 'pancreas':rows[name]['pancreas_path'], 'lesion':rows[name]['lesion_path']}
        headers={}; failures=[]
        for kind,path in files.items():
            p=Path(path); image=nib.load(p)  # Header only; never touches dataobj.
            a=np.asarray(image.affine); shape=list(image.shape)
            headers[kind]={'shape':shape,'affine':a.tolist(),'units':image.header.get_xyzt_units()[0],
                           'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
            if headers[kind]['units']!='mm': failures.append(kind+': spatial units not mm')
            if shape!=meta['transform']['source_shape'] or not np.allclose(a,meta['transform']['source_affine'],atol=1e-5,rtol=0):
                failures.append(kind+': geometry mismatch')
            if not np.isfinite(a).all() or abs(np.linalg.det(a[:3,:3]))<1e-12: failures.append(kind+': invalid affine')
        records.append({'case_id':name,'role':role,'narrow_prior_role':'verifier_fit' if role=='train' else 'exposed_development',
                        'target_state':rows[name]['target_state'],'files':files,'source_sha256':meta['source_sha256'],
                        'headers':headers,'admitted':not failures,'failures':failures})
    eligible=[r['case_id'] for r in records if r['role']=='train' and r['admitted']]
    result={'status':'CPU_HEADER_ADMISSION_ONLY','plan':plan,'cases':records,'eligible_train':eligible,
            'training_admission':'ELIGIBLE_PENDING_CONVERSION' if len(eligible)>=4 else 'NOT_ADMITTED_FEWER_THAN_FOUR',
            'development_admitted':all(r['admitted'] for r in records if r['role']=='development'),
            'seconds':time.monotonic()-start,'header_only':True,'new_voxel_reads':0,'gpu':False}
    (OUT/'input-admission.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','plan')}))


if __name__=='__main__': main()
