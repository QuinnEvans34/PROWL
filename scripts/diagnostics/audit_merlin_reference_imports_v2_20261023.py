"""One authorized corrected CPU import audit; preserves import-audit-01."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.prepare_merlin_reference_20261023 import BASE,OUT,write
DEST=OUT/'import-audit-02'
DEPENDENCIES=[BASE/'batchgenerators-dependencies-01',BASE/'cli-dependencies',BASE/'dependencies']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def worker():
    if os.environ.get('PROWL_MERLIN_IMPORT_AUDIT_V2')!='1' or os.environ.get('CUDA_VISIBLE_DEVICES')!='':
        raise ValueError('CPU supervisor required')
    request=json.loads((DEST/'request.json').read_text())
    for path,pin in request['pins'].items():
        if sha(path)!=pin:raise ValueError('Import audit pin changed: '+path)
    sys.path[:0]=[str(p) for p in DEPENDENCIES]+[str(BASE/'source/rsuper_train')]
    import torch
    torch.set_num_threads(1)
    import predict_abdomenatlas
    from model.dim3 import MedFormer
    from batchgenerators.augmentations.utils import pad_nd_image
    import batchgenerators,timm,einops,huggingface_hub
    if torch.cuda.is_initialized():raise ValueError('CUDA initialized during CPU import audit')
    write(DEST/'result.json',dict(success=True,model_constructed=False,model_forward=False,
        ct_reads=0,cuda_initialized=False,upstream_prediction_module=predict_abdomenatlas.__file__,
        constructor_module=MedFormer.__module__,torch=torch.__version__,
        timm=timm.__version__,einops=einops.__version__,huggingface_hub=huggingface_hub.__version__,
        batchgenerators=importlib.metadata.version('batchgenerators'),
        batchgenerators_path=batchgenerators.__file__,padding_function=pad_nd_image.__module__,
        qualification='Import compatibility only; not model loading, CUDA readiness or numerical parity'))


def run():
    from src.operations.full_training_platform import watch_windows
    if DEST.exists():raise ValueError('Corrected audit already started; no retry')
    prior=OUT/'import-audit-01'
    resource=json.loads((prior/'resources.json').read_text())
    if resource['success'] or not resource['workers_reaped']:raise ValueError('Expected preserved/reaped failure')
    old=json.loads((prior/'request.json').read_text())
    for path,pin in old['pins'].items():
        if sha(path)!=pin:raise ValueError('Historical import audit pin changed')
    files=[Path(__file__),prior/'request.json',prior/'resources.json',prior/'worker.log',
           BASE/'acquisition.json',ROOT/'src/operations/full_training_platform.py',
           ROOT/'scripts/diagnostics/prepare_merlin_reference_20261023.py']
    for folder in DEPENDENCIES+[BASE/'source']:
        files += [p for p in folder.rglob('*') if p.is_file() and (p.suffix=='.py' or p.name in ('METADATA','RECORD'))]
    DEST.mkdir(exist_ok=False)
    write(DEST/'request.json',dict(seconds=180,rss_bytes=4*1024**3,CPU_only=True,
        correction='Isolated batchgenerators0.25.1; user-authorized single corrected audit',
        pins={str(p):sha(p) for p in files},automatic_retry=False))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
        PYTHONDONTWRITEBYTECODE='1',PROWL_MERLIN_IMPORT_AUDIT_V2='1',MLFLOW_DISABLE_AGENT_HINT='1')
    with (DEST/'worker.log').open('x') as log:
        p=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,env=env,
            stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        success=False
        try:
            watch_windows(p,seconds=180,rss_bytes=4*1024**3);success=True
        finally:
            write(DEST/'resources.json',dict(getattr(p,'duration_resources',{}),success=success,exit_code=p.returncode))


if __name__=='__main__':
    if sys.argv[1:]==['--worker']:worker()
    elif not sys.argv[1:]:run()
    else:raise ValueError('Unsupported arguments')
