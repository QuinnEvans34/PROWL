"""One bounded inference-only 128-cube MPS capacity check; no clinical data."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.append("/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies")
OUT = Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108/inference-capacity-02')
ARCH = Path('/Volumes/PROWL-Data/PROWL/teachers/stunet-audit-20261106-source/nnUNet-2.2/nnunetv2/training/nnUNetTrainer/STUNetTrainer.py')
WEIGHTS = Path('/Volumes/PROWL-Data/PROWL/teachers/stunet-b-base-20261106/base_ep4k.model')
PORTABLE = ROOT/'outputs/prowl/testing/stunet-continuation-review-20261108-02/src/training/stunet_transfer_20261106.py'


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(4*1024**2), b''):
            h.update(b)
    return h.hexdigest()


def safety():
    from src.operations.full_training_platform import require_ac
    require_ac()
    if shutil.disk_usage(Path.home()).free < 50_000_000_000:
        raise ValueError('Existing Mac 50 GB reserve')
    if shutil.disk_usage('/Volumes/PROWL-Data').free < 100*1024**3:
        raise ValueError('External100GiB reserve')
    report = subprocess.check_output(['memory_pressure', '-Q'], text=True)
    if int(re.search(r'free percentage:\s*(\d+)', report)[1]) < 10:
        raise ValueError('Memory pressure floor')


def worker():
    import torch
    torch.set_num_threads(2)
    request = json.loads((OUT/'request.json').read_text())
    for path, expected in request['pins'].items():
        if sha(path) != expected:
            raise ValueError('Capacity input changed')
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') != '0' or not torch.backends.mps.is_available():
        raise ValueError('MPS without CPU fallback required')
    torch.mps.set_per_process_memory_fraction(6*1024**3/torch.mps.recommended_max_memory())
    spec = importlib.util.spec_from_file_location('bound_stunet', PORTABLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    start = time.monotonic()
    model, proof = module.load_transfer(ARCH, WEIGHTS, pools=[[2,2,2]]*4+[[1,1,2]])
    model.eval(); model.decoder.deep_supervision = False
    model = model.to('mps')
    with torch.inference_mode():
        image = torch.zeros((1,1,128,128,128), device='mps')
        torch.mps.synchronize(); before = time.monotonic()
        logits = model(image)
        probabilities = logits.float().softmax(1)
        torch.mps.synchronize()
        if logits.shape != (1,3,128,128,128) or not torch.isfinite(probabilities).all():
            raise ValueError('Inference output integrity')
        driver = torch.mps.driver_allocated_memory()
        if driver > 6*1024**3:
            raise ValueError('MPS6GiB cap')
    result = dict(status='SYNTHETIC_INFERENCE_ONLY_PASS', seconds=time.monotonic()-start,
                  inference_seconds=time.monotonic()-before, driver_bytes=driver,
                  live_tensor_bytes=torch.mps.current_allocated_memory(), source_load=proof,
                  clinical_reads=0, optimizer_updates=0, trained_checkpoint_used=False,
                  qualification='capacity only; no native-data or full-screen readiness claim')
    with (OUT/'result.json').open('x') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        return worker()
    from src.operations.full_training_platform import training_guard
    from src.operations.mac_teacher_supervision_v3 import run
    safety(); OUT.mkdir(parents=True, exist_ok=False)
    pins = {str(p):sha(p) for p in (Path(__file__), ARCH, WEIGHTS, PORTABLE)}
    request = dict(pins=pins, seconds=300, rss_bytes=12*1024**3, mps_bytes=6*1024**3,
                   scientific_updates=0, backward=False, user_authorization='Nov8 Mac12k confidence experiment')
    with (OUT/'request.json').open('x') as f:
        json.dump(request, f, indent=2)
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        env = dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK='0', OMP_NUM_THREADS='2')
        ok = run(['caffeinate','-i',sys.executable,str(Path(__file__).resolve()),'--worker'],
                 OUT, seconds=300, rss_bytes=12*1024**3, tick=safety, env=env)
    if not ok:
        raise SystemExit('Inference capacity failed; preserved, no automatic retry')


if __name__ == '__main__':
    main()
