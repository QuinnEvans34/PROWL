"""Pin one explicitly selected exposed development case; does not run inference.

Private output includes local source paths. Keep it outside tracked configuration.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.inference.on_demand import sha, canonical
from src.inference.assisted_prediction import recipe_sha


def build_config(case_id, ct, pancreas, checkpoint, checkpoint_sha256, device):
    import re
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',case_id) or device not in ('cpu','mps','cuda'):
        raise ValueError('Invalid case/device')
    if sha(checkpoint)!=checkpoint_sha256:raise ValueError('Selected checkpoint hash differs')
    root=Path(__file__).resolve().parents[1]
    def ref(p):
        p=Path(p).resolve(strict=True)
        return dict(path=str(p),sha256=sha(p))
    code=[root/p for p in ('scripts/predict_assisted_on_demand.py','scripts/run_on_demand_worker.py',
                           'src/inference/on_demand.py','src/inference/assisted_prediction.py','src/inference/assisted_windows.py')]
    return dict(schema='on-demand-worker-v1',python=sys.executable,device=device,
                worker=ref(code[0]),code=[ref(p) for p in code],checkpoint=ref(checkpoint),
                recipe_sha256=recipe_sha(),timeout_seconds=600,rss_limit_mib=8192,
                cases=[dict(case_id=case_id,role='exposed_development',ct=ref(ct),pancreas=ref(pancreas))])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case-id',required=True)
    p.add_argument('--ct',type=Path,required=True)
    p.add_argument('--pancreas',type=Path,required=True)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--checkpoint-sha256',required=True)
    p.add_argument('--device',choices=['cpu','mps','cuda'],required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--exposed-development',action='store_true',required=True)
    a=p.parse_args()
    config=build_config(a.case_id,a.ct,a.pancreas,a.checkpoint,a.checkpoint_sha256,a.device)
    with a.output.open('xb') as f:f.write(canonical(config))
    print('Pinned private configuration created. No model loaded or inference started.')
