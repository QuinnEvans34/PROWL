"""Bounded CPU audit of existing masks; no CT/model/inference/training access."""
import gc
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.append('/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies')
BASE=Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108')
SOURCE=BASE/'screen-03'
OUT=BASE/'component-audit-02'
BACKUP=Path.home()/'PROWL-Backups/stunet-component-audit-20261108-02'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def safety():
    from src.operations.full_training_platform import require_ac
    require_ac()
    if shutil.disk_usage(Path.home()).free<50_000_000_000 or shutil.disk_usage(BASE).free<100*1024**3:
        raise ValueError('Existing free-space floor')
    if sum(p.stat().st_size for p in (Path.home()/'PROWL-Backups').rglob('*') if p.is_file())>26*1024**3:
        raise ValueError('Existing total backup cap')


def worker():
    import nibabel as nib
    import numpy as np
    from src.data.segmenter_content_v1 import target_content
    from src.inference.lesion_confidence_screen_v2 import unpack,decode
    from src.inference.component_error_audit_20261108 import inspect,summarize
    request=json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items():
        if sha(p)!=h:raise ValueError('Audit pin changed: '+p)
    old=json.loads((SOURCE/'result.json').read_text());old_by={r['case_id']:r for r in old['cases']}
    rows=[]
    for index,case in enumerate(request['cases']):
        source=case['sources']['lesion']; name=case['case_id'];saved=old_by[name]
        if sha(source['path'])!=source['sha256']:raise ValueError('Reference source hash')
        obj=nib.load(source['path'])
        if list(obj.shape)!=case['native_shape'] or not np.allclose(obj.affine,case['native_affine'],atol=1e-5,rtol=0):
            raise ValueError('Reference geometry mismatch')
        lesion,_=target_content(obj.dataobj.get_unscaled(),dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
        if sha(SOURCE/(name+'.npz'))!=saved['artifact']['sha256']:raise ValueError('Saved prediction hash')
        with np.load(SOURCE/(name+'.npz'),allow_pickle=False) as f:code=unpack(f['packed'],[int(n) for n in f['shape']])
        prediction=decode(code,0.);del code
        if hashlib.sha256(prediction.tobytes()).hexdigest()!=saved['mask_sha256']['0.0']:raise ValueError('Raw replay hash')
        row=inspect(prediction,lesion,obj.affine,saved['policies']['0.0']);row['case_id']=name
        if row['policies']['raw']['hit_component_ids']!=saved['policies']['0.0']['hit_component_ids']:
            raise ValueError('Reference component identity drift')
        rows.append(row);write(OUT/(name+'.json'),row)
        del prediction,lesion,obj;gc.collect()
        print(json.dumps(dict(completed=index+1,total=70,case_id=name)),flush=True)
    report=summarize(rows)
    for p,h in request['pins'].items():
        if sha(p)!=h:raise ValueError('Audit pin drift')
    report.update(schema='prowl.stunet.component-audit.20261108.v1',cases=rows,
        source_result_sha256=sha(SOURCE/'result.json'),request_sha256=sha(OUT/'request.json'),
        distance_definition='Minimum world-coordinate voxel-center distance to predicted pancreas; full affine, no reference pancreas filter',
        no_new_inference=True,no_ct_reads=True,no_optimizer_updates=True)
    write(OUT/'result.json',report)


def main():
    if '--worker' in sys.argv:return worker()
    OUT.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False);safety()
    original=json.loads((SOURCE/'request.json').read_text())
    pins={str(p):sha(p) for p in [Path(__file__),ROOT/'src/inference/component_error_audit_20261108.py',
        ROOT/'src/inference/lesion_confidence_screen_v2.py',ROOT/'src/data/segmenter_content_v1.py',SOURCE/'request.json',SOURCE/'result.json']}
    write(OUT/'request.json',dict(scope='New user-authorized CPU saved-prediction/reference audit, no training change',
        cases=original['cases'],pins=pins,rules=['raw','near_predicted_pancreas_10mm','at_least_100mm3','both'],
        reference_use='Scoring and explicitly labeled disjoint-component oracle only; not filter input',
        seconds=1790,rss_bytes=4*1024**3,threads=1,no_ct_or_model_access=True))
    from src.operations.mac_teacher_supervision_v3 import run
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONPATH=str(ROOT)+':/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies')
    ok=run([sys.executable,str(Path(__file__).resolve()),'--worker'],OUT,seconds=1790,rss_bytes=4*1024**3,tick=safety,env=env)
    for p in OUT.glob('*.json'):
        safety();shutil.copyfile(p,BACKUP/p.name)
        if sha(p)!=sha(BACKUP/p.name):raise ValueError('Audit backup mismatch')
    if not ok:raise SystemExit('Audit failed; preserve evidence, no automatic retry')
    print('COMPLETE',OUT)


if __name__=='__main__':main()
