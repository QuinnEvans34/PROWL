"""Isolated acquisition and inert CPU conversion; never inference or training."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.diagnostics.acquire_distillation_teacher import fetch, write

BASE = Path('E:/PROWL/teachers/rsuper-merlin-eab1a7e9-reference')
OUT = Path('E:/PROWL/readiness/merlin-upstream-reference-20261023-a01')
REV = 'eab1a7e9f421740bf8f3f834d1f69d17cbe3a8aa'
CODE = '45fea075a805797e78e002e9880330f4241afb1a'
WEIGHT = 'merlin_pancreas_pants_release/fold_0_latest.pth'
SHA = '38535f10430265e431ca3ffa7fe3ff15efed5bccb65ba909b6e3ce18af11e459'
SIZE = 606931502


def acquire():
    if BASE.exists() or OUT.exists():
        raise ValueError('Acquisition already started; inspect, never retry automatically')
    if any(shutil.disk_usage(d).free < 101*1024**3 for d in ('C:/','E:/')):
        raise ValueError('Free-space floor')
    BASE.mkdir(); OUT.mkdir()
    write(OUT/'request.json', dict(model_revision=REV, code_revision=CODE,
        checkpoint_sha256=SHA, checkpoint_bytes=SIZE, source_cap_bytes=8*1024**2,
        no_inference=True, no_automatic_dispatch=True, license='Unresolved; do not inherit baseline MIT',
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    start=time.monotonic(); files=[]
    try:
        tree_url=f'https://api.github.com/repos/MrGiovanni/R-Super/git/trees/{CODE}?recursive=1'
        with urllib.request.urlopen(urllib.request.Request(tree_url,headers={'User-Agent':'PROWL'}),timeout=30) as response:
            tree=json.load(response)
        if tree.get('truncated'): raise ValueError('Truncated source tree')
        rows=[r for r in tree['tree'] if r['type']=='blob' and (r['path']=='LICENSE' or
            r['path'].startswith('rsuper_train/') and Path(r['path']).suffix in ('.py','.yaml','.yml','.txt'))]
        if sum(r['size'] for r in rows)>8*1024**2: raise ValueError('Source budget')
        write(BASE/'source-tree.json',dict(revision=CODE,files=rows))
        def one(row):
            name=row['path']
            return fetch(f'https://raw.githubusercontent.com/MrGiovanni/R-Super/{CODE}/{name}',
                         BASE/'source'/name,maximum=row['size'],git_blob=row['sha'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for result in pool.map(one,rows): files.append(result)
        for name in ('README.md','labels_pants.yaml','merlin_pancreas_pants_release/config.txt'):
            files.append(fetch(f'https://huggingface.co/AbdomenAtlas/R-SuperPanTSMerlin/resolve/{REV}/{name}',
                               BASE/'release'/name,maximum=128*1024))
        files.append(fetch(f'https://huggingface.co/AbdomenAtlas/R-SuperPanTSMerlin/resolve/{REV}/{WEIGHT}',
                           BASE/'release'/WEIGHT,maximum=SIZE,sha256=SHA))
        # Copy the already admitted isolated dependency; never alter the live venv.
        original=Path('E:/PROWL/teachers/medformer-pants-b854c824/dependencies')
        shutil.copytree(original,BASE/'dependencies',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        dependencies={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (BASE/'dependencies').rglob('*') if p.is_file()}
        write(BASE/'acquisition.json',dict(success=True,hf_revision=REV,code_revision=CODE,
            files=files,dependencies=dependencies,seconds=time.monotonic()-start,
            model_execution=False,ct_reads=0,source_unmodified=True,license='No inherited model license'))
    except BaseException as exc:
        write(OUT/'acquisition-failure.json',dict(error=repr(exc),completed=files,retry=False))
        raise


def convert_worker():
    from scripts.diagnostics import convert_distillation_teacher as old
    old.BASE=BASE; old.CHECKPOINT=BASE/'release'/WEIGHT; old.SHA=SHA
    old.OUT=OUT/'conversion-01'
    old.worker()  # Existing restricted weights_only/inert-record conversion only.


def convert():
    from src.operations.full_training_platform import watch_windows
    if not json.loads((BASE/'acquisition.json').read_text())['success']:
        raise ValueError('Acquisition incomplete')
    destination=OUT/'conversion-01'; destination.mkdir(exist_ok=False)
    pins=[Path(__file__),ROOT/'scripts/diagnostics/convert_distillation_teacher.py',
          ROOT/'src/training/teacher_checkpoint_v1.py',BASE/'acquisition.json']
    write(destination/'request.json',dict(seconds=180,rss_bytes=4*1024**3,
        pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in pins},
        source_sha256=SHA,scientific=False,CPU_only=True))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
             PYTHONDONTWRITEBYTECODE='1',PROWL_TEACHER_CONVERT='1')
    with (destination/'worker.log').open('x') as log:
        p=subprocess.Popen([sys.executable,__file__,'--convert-worker'],cwd=ROOT,env=env,
                           stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        success=False
        try:
            watch_windows(p,seconds=180,rss_bytes=4*1024**3); success=True
        finally:
            write(destination/'resources.json',dict(getattr(p,'duration_resources',{}),
                  success=success,exit_code=p.returncode))


if __name__=='__main__':
    if sys.argv[1:]==['--acquire']: acquire()
    elif sys.argv[1:]==['--convert']: convert()
    elif sys.argv[1:]==['--convert-worker']: convert_worker()
    else: raise ValueError('Select one explicit preparation stage')
