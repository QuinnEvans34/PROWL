"""Reopen independent backups and reproduce all630 saved candidate mask hashes."""
import gc
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
DEPS='/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies'
sys.path[:0]=[str(ROOT),DEPS]
BASE=Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108')
SCREEN=BASE/'postprocess-screen-01'
BACKUP=Path.home()/'PROWL-Backups/stunet-postprocess-screen-20261108-01'
RAW_BACKUP=Path.home()/'PROWL-Backups/stunet-confidence-mac-20261108-03'
OUT=BASE/'postprocess-verification-01'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def worker():
    import numpy as np
    from src.inference.saved_postprocess_screen_v1 import predictions,POLICIES
    from src.inference.lesion_confidence_screen_v2 import unpack
    from scripts.diagnostics.screen_saved_postprocessing_20261108 import summarize
    r=json.loads((BACKUP/'result.json').read_text());request=json.loads((BACKUP/'request.json').read_text())
    resources=json.loads((BACKUP/'resources.json').read_text());assert resources['success'] and resources['exit_code']==0 and resources['workers_reaped']
    assert resources['peak_owned_rss_bytes']<=request['rss_bytes'] and resources['seconds']<=request['seconds']
    assert SCREEN.stat().st_dev!=BACKUP.stat().st_dev
    assert sha(SCREEN/'request.json')==r['request_sha256']
    for p,h in request['pins'].items():assert sha(p)==h,p
    files=list(SCREEN.glob('*.json'))
    for p in files:assert sha(p)==sha(BACKUP/p.name),p
    rows=[json.loads((BACKUP/(x['case_id']+'.json')).read_text()) for x in r['cases']]
    derived=summarize(rows,POLICIES)
    for k,v in derived.items():assert r[k]==v,k
    source=json.loads((RAW_BACKUP/'result.json').read_text());original={x['case_id']:x for x in source['cases']}
    components=json.loads((BASE/'component-audit-02/result.json').read_text());by={x['case_id']:x for x in components['cases']}
    checks=0
    for row in request['cases']:
        name=row['case_id'];path=RAW_BACKUP/(name+'.npz')
        assert sha(path)==original[name]['artifact']['sha256']
        expected=json.loads((BACKUP/(name+'.json')).read_text())
        with np.load(path,allow_pickle=False) as f:code=unpack(f['packed'],[int(x) for x in f['shape']])
        for policy,prediction in predictions(code,row['native_affine'],by[name]['components']):
            assert hashlib.sha256(prediction.tobytes()).hexdigest()==expected['mask_sha256'][policy]
            checks+=1;del prediction
        del code;gc.collect()
        print(json.dumps(dict(cases_verified=checks//9,total=70)),flush=True)
    assert checks==630
    report=dict(status='PASS',source_pins_verified=len(request['pins']),report_backup_pairs_verified=len(files),
        policy_mask_hashes_reproduced_from_independent_raw_backups=checks,summary_reproduced_exactly=True,
        result_sha256=sha(SCREEN/'result.json'),request_sha256=sha(SCREEN/'request.json'),
        primary_resources=resources,clinical_arrays_read=False,model_forwards=0,optimizer_updates=0,
        development_screen_leader=r['development_screen_leader'])
    with (OUT/'result.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')


def main():
    if '--worker' in sys.argv:return worker()
    from src.operations.mac_teacher_supervision_v3 import run
    from scripts.diagnostics.screen_saved_postprocessing_20261108 import safety
    OUT.mkdir(exist_ok=False);safety()
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONPATH=str(ROOT)+':'+DEPS)
    ok=run([sys.executable,str(Path(__file__).resolve()),'--worker'],OUT,seconds=600,rss_bytes=8*1024**3,tick=safety,env=env)
    for path in OUT.glob('*.json'):
        dest=BACKUP/('verification-'+path.name);shutil.copyfile(path,dest);assert sha(path)==sha(dest)
    if not ok:raise SystemExit('Verification failed; preserve evidence, do not retry')
    print('VERIFIED',OUT)


if __name__=='__main__':main()
