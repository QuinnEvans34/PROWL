"""One supervised MPS replay of the verified 32k STU-Net inference state."""
import argparse
import gc
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from scripts.diagnostics import evaluate_native_small_lesion_outliner_20261111 as outliner
from scripts.diagnostics import run_stunet_confidence_mac_20261108_v3 as prior
from scripts.diagnostics.audit_stunet_selected_dice_20261110 import admitted_cases
from src.data.segmenter_native_windows_v1 import orient, tiles
from src.data.segmenter_physical_windows_v1 import PhysicalReconstructor, physical_geometry, sample_window
from src.inference.stunet_margin_screen_20261110 import pack
from src.operations.full_training_platform import training_guard
from src.operations.mac_teacher_supervision_v3 import run
from src.training.pants_native_evaluation import native_metrics

GIB = 1024**3
CAP = 14400
RSS = 12 * GIB
MPS = 8 * GIB
MAX_DICE_DRIFT = .01
BASE = Path('/Volumes/PROWL-Data/PROWL/artifacts')
BACKUPS = Path.home()/'PROWL-Backups'
PILOTS = ('PanTS_00006837', 'PanTS_00006880')
read, sha, write = outliner.read, outliner.sha, outliner.write


def packet(directory):
    manifest = read(directory/'manifest.json')
    report = directory/'native-32000.json'
    weights = directory/'model-only.pt'
    if (manifest['step'] != outliner.STEP or manifest['source_checkpoint_sha256'] != outliner.CHECKPOINT_SHA
            or manifest['independent_checkpoint_sha256'] != outliner.CHECKPOINT_SHA
            or manifest['tensor_equality'] is not True or sha(report) != outliner.REPORT_SHA
            or manifest['report_sha256'] != outliner.REPORT_SHA
            or not 0 < weights.stat().st_size <= 300 * 1024**2
            or manifest['model_sha256'] != sha(weights)):
        raise ValueError('32k packet provenance differs')
    original = read(report)
    if original['step'] != outliner.STEP or len(original['cases']) != 70:
        raise ValueError('Original 32k report is incomplete')
    return weights, report


def pack_mask(prediction):
    return pack(prediction)


def parity(mac, cuda):
    for key in ('reference_positive', 'reference_components', 'target_volume_mm3', 'voxel_mm3'):
        if mac[key] != cuda[key]:
            raise ValueError('Reference census or geometry differs from CUDA')
    for key in ('lesion', 'pancreas'):
        if mac[key]['target_voxels'] != cuda[key]['target_voxels']:
            raise ValueError('Reference volume differs from CUDA')
    if mac['lesion']['dice'] is None or cuda['lesion']['dice'] is None:
        if mac['reference_positive'] or cuda['reference_positive']:
            raise ValueError('Incomplete positive-case Dice')
    delta = mac['lesion']['dice'] - cuda['lesion']['dice'] if mac['reference_positive'] else None
    if delta is not None and abs(delta) > MAX_DICE_DRIFT:
        raise ValueError('Mac–Lenovo positive-case Dice drift exceeds 0.01')
    return delta


def safety(directory):
    outliner.safety()
    if prior.tree_bytes(BACKUPS) > 26*GIB or prior.tree_bytes(directory) > 4*GIB:
        raise ValueError('Existing retained backup or attempt limit')


def copy_verified(source, dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as r, dest.open('xb') as w:
        shutil.copyfileobj(r,w)
        w.flush()
        os.fsync(w.fileno())
    if sha(source)!=sha(dest):
        raise ValueError('Independent copy differs')


def setup(directory, transfer):
    weights, report = packet(transfer)
    safety(directory)
    cases,_ = admitted_cases()
    backup = BACKUPS/directory.name
    if directory.parent.resolve()!=BASE.resolve() or directory.exists() or backup.exists():
        raise ValueError('Use a fresh external artifact directory and independent backup')
    predicted_bytes = sum((math.prod(c['native_shape'])+1)//2 for c in cases) + 64*1024**2
    if (predicted_bytes>4*GIB or prior.tree_bytes(BACKUPS)+predicted_bytes>26*GIB
            or shutil.disk_usage(BACKUPS).free-predicted_bytes<50_000_000_000
            or shutil.disk_usage(BASE).free-predicted_bytes<100*GIB
            or BACKUPS.stat().st_dev==BASE.stat().st_dev):
        raise ValueError('Worst-case packed mask reserve fails')
    required = [Path(__file__),Path(outliner.__file__),Path(prior.__file__),Path(prior.ARCH),
                Path(prior.PORTABLE),weights,report,transfer/'manifest.json',outliner.POLICY]
    deadline = time.time()+CAP
    directory.mkdir()
    backup.mkdir()
    req = directory/'request.json'
    write(req,dict(deadline_unix=deadline, max_dice_drift=MAX_DICE_DRIFT, pilots=list(PILOTS),
          weights=str(weights),source_report=str(report),pins={str(p.resolve()):sha(p) for p in required},
          mps_bytes=MPS,rss_bytes=RSS,torch_version=str(torch.__version__),
          scope='same-device Mac 32k baseline; exposed supplied-region development'))
    copy_verified(req,backup/req.name)
    return sha(req)


def bound(directory, expected):
    request = directory/'request.json'
    backup = BACKUPS/directory.name
    if sha(request)!=expected or sha(backup/request.name)!=expected:
        raise ValueError('Frozen request or independent copy differs')
    r = read(request)
    if any(sha(p)!=h for p,h in r['pins'].items()):
        raise ValueError('Replay source pin differs')
    if r['torch_version']!=str(torch.__version__):
        raise ValueError('Frozen Torch runtime differs')
    if time.time()>=r['deadline_unix']:
        raise ValueError('Original cumulative budget exhausted')
    return r,backup


def load_model(weights):
    spec = importlib.util.spec_from_file_location('bound_stunet_32k',prior.PORTABLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.make_model(prior.ARCH,pools=[[2,2,2]]*4+[[1,1,2]])
    state = torch.load(weights,map_location='cpu',weights_only=True)
    if state['step']!=outliner.STEP or state['parent_sha256']!=outliner.CHECKPOINT_SHA:
        raise ValueError('32k model-only checkpoint binding')
    model.load_state_dict(state['model'],strict=True)
    model.eval()
    model.decoder.deep_supervision = False
    return model.to('mps')


def reconstruct(case, model, shape, progress):
    record = physical_geometry(case['geometry'])
    windows = tiles(record['shape'],window=128,stride=64)
    recon = PhysicalReconstructor(record,window=128)
    peak = 0
    with torch.inference_mode():
        for i,origin in enumerate(windows,1):
            image,_ = sample_window(case['image'],record,origin,order=1,window=128)
            x = torch.from_numpy(image[None,None]).to('mps')
            logits = model(x)
            probability = logits.float().softmax(1)[0].cpu().numpy()
            torch.mps.synchronize()
            peak = max(peak,torch.mps.driver_allocated_memory())
            if peak > MPS:
                raise ValueError('MPS memory limit')
            recon.add(origin,probability)
            del logits,probability,x
            torch.mps.synchronize()
            torch.mps.empty_cache()
            if i%10==0:
                progress(i,len(windows))
    local = recon.finish(windows).argmax(0).astype(np.uint8)
    parent = case['parent_geometry']
    codes = np.zeros(parent['shape'],np.uint8)
    region = tuple(slice(l,h) for l,h in zip(case['region_low'],case['region_high']))
    codes[region] = local
    mask = np.ascontiguousarray(orient(codes,parent,inverse=True))
    if mask.shape!=tuple(shape):
        raise ValueError('Native reconstruction shape differs')
    return mask,len(windows),peak


def worker(directory, expected):
    request,backup = bound(directory,expected)
    safety(directory)
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')!='0' or not torch.backends.mps.is_available():
        raise ValueError('MPS required with CPU fallback disabled')
    torch.set_num_threads(2)
    torch.mps.set_per_process_memory_fraction(MPS/torch.mps.recommended_max_memory())
    cases,_ = admitted_cases()
    original = read(request['source_report'])
    controls = {x['case_id']:x for x in original['cases']}
    by_id = {c['case_id']:c for c in cases}
    if len(controls)!=70 or set(controls)!=set(by_id):
        raise ValueError('Original 32k development cohort differs')
    order = list(PILOTS) + [name for name in by_id if name not in PILOTS]
    model = load_model(request['weights'])
    rows,members,deltas = [],[],[]
    started = time.monotonic()
    tiles_done = peak = 0
    for name in order:
        safety(directory)
        row = by_id[name]
        c = prior.load_case(row)
        pred,count,memory = reconstruct(c,model,row['native_shape'],lambda i,n: print(json.dumps(
            dict(case=name,tile=i,tiles=n,complete=len(rows))),flush=True))
        if count!=row['profile']['tiles'] or count!=controls[name]['tiles'] or controls[name]['gaps']!=0:
            raise ValueError('32k native tile census differs')
        metrics = native_metrics(pred,c['original_pancreas'],c['original_lesion'],row['native_affine'])
        delta = parity(metrics,controls[name]['metrics'])
        dest = directory/(name+'.npz')
        with dest.open('xb') as stream:
            np.savez_compressed(stream,packed=pack_mask(pred),shape=np.asarray(pred.shape,dtype=np.int64))
            stream.flush()
            os.fsync(stream.fileno())
        copy_verified(dest,backup/dest.name)
        if not np.array_equal(pred,outliner.unpack_native(backup/dest.name,row['native_shape'])):
            raise ValueError('Independent mask replay differs')
        record = dict(case_id=name,tiles=count,gaps=0,metrics=metrics)
        member = dict(case_id=name,native_shape=row['native_shape'],native_affine=row['native_affine'],
                      source_sha256={k:v['sha256'] for k,v in row['sources'].items()},
                      tiles=count,mask_file=dest.name,mask_sha256=sha(dest))
        write(directory/(name+'.json'),dict(record=record,member=member,cuda_delta=delta))
        copy_verified(directory/(name+'.json'),backup/(name+'.json'))
        rows.append(record);members.append(member);deltas.append(delta)
        tiles_done+=count;peak=max(peak,memory)
        del pred,c
        gc.collect()
        if len(rows)==len(PILOTS):
            remaining_tiles = sum(x['tiles'] for x in controls.values())-tiles_done
            projection = (time.monotonic()-started)*remaining_tiles/tiles_done*1.5
            p = directory/'qualification.json'
            write(p,dict(cases=list(PILOTS),projection_seconds=projection,peak_mps_bytes=peak,
                         remaining_seconds=request['deadline_unix']-time.time()))
            copy_verified(p,backup/p.name)
            if projection > request['deadline_unix']-time.time()-120:
                raise ValueError('Measured reconstruction projection exceeds the budget')
    p = directory/'mac-native-32000.json'
    positive = [r for r in rows if r['metrics']['reference_positive']]
    if len(positive)!=36 or len(rows)!=70:
        raise ValueError('Final 32k denominator')
    dice = sum(r['metrics']['lesion']['dice'] for r in positive)/len(positive)
    write(p,dict(step=outliner.STEP,cases=rows,summary=dict(lesion_dice=dice,positive=36,empty=34)))
    copy_verified(p,backup/p.name)
    original_path = directory/'native-32000.json'
    copy_verified(Path(request['source_report']),original_path)
    copy_verified(original_path,backup/original_path.name)
    manifest = directory/'manifest.json'
    write(manifest,dict(schema='prowl.stunet.mac-native-mask-replay.v1',step=outliner.STEP,
          checkpoint_sha256=outliner.CHECKPOINT_SHA,independent_checkpoint_sha256=outliner.CHECKPOINT_SHA,
          report_sha256=outliner.REPORT_SHA,mac_report_sha256=sha(p),request_sha256=expected,
          cases=members,peak_mps_bytes=peak,maximum_positive_case_dice_drift=max(abs(d) for d in deltas if d is not None)))
    copy_verified(manifest,backup/manifest.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet',type=Path)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--worker')
    args = parser.parse_args()
    if args.worker:
        worker(args.directory,args.worker)
        return
    if len(subprocess.check_output(['ollama','ps'],text=True).strip().splitlines())!=1:
        raise ValueError('Local expert model must release MPS before replay')
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        expected = setup(args.directory,args.packet)
        request,backup = bound(args.directory,expected)
        env = dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',
                   OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
        passed = run(['caffeinate','-is',sys.executable,__file__,str(args.packet),str(args.directory),
                      '--worker',expected],args.directory,seconds=request['deadline_unix']-time.time()-60,
                     rss_bytes=RSS,tick=lambda:safety(args.directory),env=env)
        resources = args.directory/'resources.json'
        copy_verified(resources,backup/resources.name)
        evidence = read(resources)
        if not passed or not evidence['workers_reaped'] or evidence['exit_code']!=0:
            raise SystemExit('Mac reconstruction stopped; preserve evidence')
    manifest = args.directory/'manifest.json'
    bound(args.directory,expected)
    p = args.directory/'closeout.json'
    write(p,dict(status='VERIFIED_COMPLETE',manifest_sha256=sha(manifest),request_sha256=expected,
          resources_sha256=sha(resources),mps_lock_released=True))
    copy_verified(p,backup/p.name)


if __name__=='__main__':
    main()
