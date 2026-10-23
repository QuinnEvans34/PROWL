"""Final CPU-only engineering regression with complete local source/test pins."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.manifest_records import canonical
from src.operations.full_training_platform import watch_windows
BASE=Path('E:/PROWL/readiness/distillation-engineering-20261023-a01')


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def write(path,value):
    with path.open('xb') as stream:stream.write(canonical(value))


def run(attempt):
    if len(attempt)!=2 or not attempt.isascii() or not attempt.isdecimal():raise ValueError('Two digit attempt')
    root=BASE/('verification-'+attempt);root.mkdir(exist_ok=False)
    tests=[ROOT/'tests/test_segmenter_distillation_v1.py',ROOT/'tests/test_segmenter_teacher_targets_v1.py']
    tests+=sorted((ROOT/'tests').glob('test_distillation_*v1.py'))
    files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))+tests
    pins={str(p):sha(p) for p in files}
    write(root/'request.json',dict(scope='synthetic CPU only; no patient reads or scientific training',pins=pins,seconds=240,rss_bytes=4*1024**3))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
        PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    cmd=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider',*[str(p) for p in tests],'--junitxml',str(root/'tests.xml')]
    success=False;error=None
    with (root/'worker.log').open('x') as log:
        process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            watch_windows(process,seconds=240,rss_bytes=4*1024**3)
            suites=ET.parse(root/'tests.xml').getroot().findall('testsuite')
            counts={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
            if not counts['tests'] or any(counts[k] for k in ('failures','errors','skipped')):raise ValueError('Incomplete tests')
            if any(sha(Path(path))!=pin for path,pin in pins.items()):raise ValueError('Source changed during verification')
            write(root/'result.json',dict(success=True,**counts,source_pins_unchanged=True,scientific_updates=0,real_teacher_quality_qualified=False))
            success=True
        except Exception as exc:error=repr(exc)
        finally:
            value=dict(getattr(process,'duration_resources',{}),success=success,exit_code=process.returncode,error=error)
            write(root/'resources.json',value);print(json.dumps(value))
    if not success:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',default='01');args=parser.parse_args();run(args.attempt)
