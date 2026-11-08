"""Bounded real-input allocation-lifecycle qualification; zero optimizer updates."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
sys.path.append('/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies')
from scripts.diagnostics import run_stunet_confidence_mac_20261108 as original
OUT=original.BASE/'cache-release-qualification-02'


def worker():
    import numpy as np
    import torch
    from src.data.segmenter_physical_windows_v1 import sample_window,physical_geometry
    from src.data.segmenter_native_windows_v1 import tiles
    request=json.loads((OUT/'request.json').read_text())
    for path,pin in request['pins'].items():
        if original.sha(path)!=pin:raise ValueError('Qualification source changed')
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')!='0':raise ValueError('Fallback forbidden')
    torch.set_num_threads(2)
    torch.mps.set_per_process_memory_fraction(8*1024**3/torch.mps.recommended_max_memory())
    s=importlib.util.spec_from_file_location('bound_stunet',original.PORTABLE)
    module=importlib.util.module_from_spec(s);s.loader.exec_module(module)
    state=torch.load(original.CHECKPOINT,map_location='cpu',weights_only=True)
    assert state['step']==12000
    model=module.make_model(original.ARCH,pools=[[2,2,2]]*4+[[1,1,2]])
    model.load_state_dict(state['model'],strict=True);del state
    model.eval();model.decoder.deep_supervision=False;model=model.to('mps')
    row=next(r for r in json.loads((original.OUT/'request.json').read_text())['cases'] if r['case_id']=='PanTS_00006837')
    case=original.load_case(row);record=physical_geometry(case['geometry']);origins=tiles(record['shape'],window=128,stride=64)
    samples=[];reference=None;start=time.monotonic()
    with torch.inference_mode():
        # Baseline then8same-input replays;8other native windows exercise reuse.
        for i,origin in enumerate([origins[0]]*9+origins[1:9]):
            image,_=sample_window(case['image'],record,origin,order=1,window=128)
            x=torch.from_numpy(image[None,None]).to('mps');y=model(x)
            p=y.float().softmax(1)[0].cpu().numpy();torch.mps.synchronize()
            peak=torch.mps.driver_allocated_memory()
            if not np.isfinite(p).all() or peak>8*1024**3:raise ValueError('Output/memory gate')
            if i==0:reference=p.copy()
            elif i<9 and not np.array_equal(p,reference):raise ValueError('Repeated exact probability equality failed')
            del x,y,p
            torch.mps.synchronize();before=torch.mps.driver_allocated_memory();torch.mps.empty_cache()
            samples.append(dict(index=i,driver_during_output=peak,driver_before_release=before,
                driver_after_release=torch.mps.driver_allocated_memory(),live_after_release=torch.mps.current_allocated_memory()))
    original.write(OUT/'result.json',dict(status='PASS_EXACT_OUTPUTS_CACHE_RELEASE',case_id=row['case_id'],
        source_sha256=row['source_sha256'],checkpoint_sha256=original.CHECKPOINT_SHA,
        repeats_exact=8,other_windows=8,samples=samples,seconds=time.monotonic()-start,
        optimizer_updates=0,scientific_native_results=0,
        interpretation='Unused allocation release only; no precision/model/geometry/policy change'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');a=p.parse_args()
    if a.worker:return worker()
    from src.operations.full_training_platform import training_guard
    from src.operations.mac_teacher_supervision_v3 import run
    approval=json.loads((original.BASE/'user-mps8-approval.json').read_text())
    if approval.get('mps_bytes')!=8*1024**3 or approval.get('approved') is not True:
        raise ValueError('Explicit8GiB qualification approval required')
    original.safety();OUT.mkdir(exist_ok=False)
    pins={str(p):original.sha(p) for p in [Path(__file__),Path(original.__file__),original.CHECKPOINT,original.ARCH,original.PORTABLE]}
    original.write(OUT/'request.json',dict(pins=pins,seconds=300,rss_bytes=12*1024**3,mps_bytes=8*1024**3,
        reason='New8GiB inference allocation qualification only after explicit approval; preserve both6GiB failures',
        unchanged_science=True,continued_original_cumulative_budget=True))
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        ok=run(['caffeinate','-i',sys.executable,str(Path(__file__).resolve()),'--worker'],OUT,
               seconds=300,rss_bytes=12*1024**3,tick=original.safety,
               env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='2'))
    if not ok:raise SystemExit('Allocation-lifecycle qualification failed; stop, no retry')


if __name__=='__main__':main()
