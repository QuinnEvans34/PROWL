"""Read-only CPU import/file audit for the two isolated execution runtimes."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser();p.add_argument('--kind',choices=['worker','supervisor'],required=True);p.add_argument('--output',required=True);a=p.parse_args()
    start=time.monotonic();output=Path(a.output)
    if output.exists():raise FileExistsError('Audit already exists')
    import psutil
    from src.inference.universal_model_loading_20261105 import digest
    if a.kind=='worker':
        sys.path.insert(0,'E:/PROWL/teachers/medformer-pants-b854c824/dependencies')
        import torch
        import nibabel
        from monai.transforms import Orientation,Spacing
        from monai.inferers import sliding_window_inference
        from src.inference import universal_native_20261105,saved_prediction_scoring,four_case_metrics_20261102
        from src.inference.universal_model_loading_20261105 import load_cpu
        torch.set_num_threads(1);torch.set_num_interop_threads(1)
        root=Path('E:/PROWL/teachers/clip-universal-76f0304-20261105')
        model,loaded=load_cpu(root/'source',root/'checkpoint.pth',json.loads((root/'source-receipt.json').read_text()))
        packages=['torch','monai','numpy','scipy','nibabel','einops','psutil']
    else:
        from mlflow.tracking import MlflowClient
        from scripts.diagnostics.backfill_full_runs_mlflow import URI
        from src.operations.full_training_platform import training_guard,watch_windows,require_ac
        packages=['mlflow','numpy','psutil'];loaded=None
    files={str(Path(sys.executable).resolve())}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f and Path(f).is_file():files.add(str(Path(f).resolve()))
    for mapping in psutil.Process().memory_maps():
        path=Path(mapping.path)
        if path.is_file() and 'site-packages' in str(path).lower():files.add(str(path.resolve()))
    pins={path:digest(path) for path in sorted(files)}
    report={'kind':a.kind,'python':platform.python_version(),'executable':sys.executable,
            'packages':{name:importlib.metadata.version(name) for name in packages},
            'loaded':loaded,'imported_and_mapped_file_pins':pins,'seconds':time.monotonic()-start,
            'gpu_forwards':0,'data_reads':0}
    with output.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({'kind':a.kind,'files':len(pins),'seconds':report['seconds'],'loaded':loaded}))


if __name__=='__main__':main()
