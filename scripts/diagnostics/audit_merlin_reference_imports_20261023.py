"""Bounded CPU-only upstream import audit; no model construction or image reads."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.prepare_merlin_reference_20261023 import BASE,OUT,write


def worker():
    if os.environ.get('PROWL_MERLIN_IMPORT_AUDIT')!='1': raise ValueError('Supervisor required')
    sys.path[:0]=[str(BASE/'cli-dependencies'),
        'E:/PROWL/teachers/medformer-pants-b854c824/dependencies',
        str(BASE/'source/rsuper_train')]
    import torch
    torch.set_num_threads(1)
    import predict_abdomenatlas
    from model.dim3 import MedFormer
    import timm,einops,huggingface_hub
    if torch.cuda.is_initialized(): raise ValueError('CUDA initialized during CPU import audit')
    write(OUT/'import-audit-01/result.json',dict(success=True,model_constructed=False,
        model_forward=False,ct_reads=0,cuda_initialized=False,
        upstream_prediction_module=predict_abdomenatlas.__file__,
        constructor_module=MedFormer.__module__,torch=torch.__version__,
        timm=timm.__version__,einops=einops.__version__,huggingface_hub=huggingface_hub.__version__,
        qualification='Import compatibility only, not exact upstream environment or numerical parity'))


def run():
    from src.operations.full_training_platform import watch_windows
    folder=OUT/'import-audit-01';folder.mkdir(exist_ok=False)
    files=[Path(__file__)]+list((BASE/'cli-dependencies').rglob('*.py'))
    write(folder/'request.json',dict(seconds=180,rss_bytes=4*1024**3,CPU_only=True,
          pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
             PYTHONDONTWRITEBYTECODE='1',PROWL_MERLIN_IMPORT_AUDIT='1')
    with (folder/'worker.log').open('x') as log:
        p=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,env=env,
                           stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        success=False
        try:
            watch_windows(p,seconds=180,rss_bytes=4*1024**3);success=True
        finally:
            write(folder/'resources.json',dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode))


if __name__=='__main__':
    if sys.argv[1:]==['--worker']:worker()
    elif not sys.argv[1:]:run()
    else:raise ValueError('Unsupported arguments')
