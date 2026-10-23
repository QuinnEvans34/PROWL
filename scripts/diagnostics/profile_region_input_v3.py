"""User-approved corrected CPU profile; failed v1/v2 evidence is immutable."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
OUT=Path('E:/PROWL/readiness/region-throughput-20261022-a01/profile-v3')
INPUT=Path('E:/PROWL/readiness/pancreas-region-review-20261022-a01/results.json')


def preflight():
    value=json.loads(INPUT.read_text())
    if len(value['timing']['current']['case_mean_seconds'])!=1333:
        raise ValueError('Missing original timing report')
    if OUT.exists():raise ValueError('Attempt already started; no retry')


def main():
    from src.operations.full_training_platform import require_ac,watch_windows,training_guard
    from src.training.experiment_config import sha256
    require_ac();preflight();OUT.mkdir()
    # The unchanged measurement helper reads OUT/results.json. Bind an exact
    # input copy there before starting it, independently of its output files.
    shutil.copyfile(INPUT,OUT/'results.json')
    if sha256(INPUT)!=sha256(OUT/'results.json'):raise ValueError('Profile input copy mismatch')
    paths=[Path(__file__),ROOT/'scripts/diagnostics/profile_region_input_readonly.py',INPUT,OUT/'results.json']
    with (OUT/'request.json').open('x') as f:
        json.dump(dict(pins={str(p):sha256(p) for p in paths},seconds=600,rss_bytes=12*1024**3,
            cuda_visible_devices='-1',scientific=False,
            authorization='User explicitly approved one corrected bounded profile after v2 path failure'),f,indent=2)
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'),(OUT/'profile.log').open('x') as log:
        process=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_PROFILE_V3='1'))
        try:watch_windows(process,seconds=600,rss_bytes=12*1024**3,tick=require_ac)
        finally:
            with (OUT/'profile-resources.json').open('x') as f:json.dump(getattr(process,'duration_resources',{}),f,indent=2)


if __name__=='__main__':
    if sys.argv[1:]==['--worker']:
        if os.environ.get('PROWL_PROFILE_V3')!='1' or os.environ.get('CUDA_VISIBLE_DEVICES')!='-1':
            raise ValueError('Explicit CPU supervisor required')
        from scripts.diagnostics import profile_region_input_readonly as diagnostic
        diagnostic.OUT=OUT;diagnostic.worker()
    elif sys.argv[1:]==['--check']:preflight();print('Input report and new destination checks passed')
    elif not sys.argv[1:]:main()
    else:raise ValueError('Unsupported arguments')
