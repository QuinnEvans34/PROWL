"""Explicitly authorized new CPU-only profile attempt; retain the failed original."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path('E:/PROWL/readiness/region-throughput-20261022-a01/profile')


def main():
    from src.operations.full_training_platform import require_ac, watch_windows, training_guard
    from src.training.experiment_config import sha256
    require_ac()
    if OUT.exists():
        raise ValueError('Profile already started; inspect existing attempt, never overwrite/retry')
    OUT.mkdir(parents=True)
    pins = {str(p): sha256(p) for p in [Path(__file__), ROOT/'scripts/diagnostics/profile_region_input_readonly.py']}
    (OUT/'request.json').write_text(json.dumps(dict(pins=pins,seconds=600,rss_bytes=12*1024**3,
        cuda_visible_devices='-1',authorization='October22 approved throughput setup',scientific=False),indent=2))
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'), (OUT/'profile.log').open('x') as log:
        child = subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_PROFILE_V2='1'))
        try:
            watch_windows(child,seconds=600,rss_bytes=12*1024**3,tick=require_ac)
        finally:
            with (OUT/'profile-resources.json').open('x') as f:
                json.dump(getattr(child,'duration_resources',{}),f,indent=2)


if __name__ == '__main__':
    if sys.argv[1:] == ['--worker']:
        if os.environ.get('PROWL_PROFILE_V2') != '1' or os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
            raise ValueError('Supervisor and explicit CPU isolation required')
        from scripts.diagnostics import profile_region_input_readonly as diagnostic
        diagnostic.OUT = OUT  # Only diagnostic destination changes; production code untouched.
        diagnostic.worker()
    elif not sys.argv[1:]:
        main()
    else:
        raise ValueError('Unsupported arguments')
