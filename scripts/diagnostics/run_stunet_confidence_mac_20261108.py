"""Bounded, single-pass Mac confidence screen on the completed STU-Net12k.

Zero optimizer updates. New raw and three policies share each reconstructed
probability field. Original CUDA metric parity is reported, not called spatial
equivalence. No model promotion or independent-test inference is performed.
"""
import argparse
import csv
import gc
import hashlib
import importlib.util
import importlib.metadata
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
DEPENDENCIES = '/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies'
sys.path.append(DEPENDENCIES)
BASE = Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108')
OUT = BASE/'screen-01'
BACKUP = Path.home()/'PROWL-Backups/stunet-confidence-mac-20261108-01'
CHECKPOINT = BASE/'received/checkpoint-12000.pt'
CHECKPOINT_SHA = 'ed000e1ce25829c29f1efea7bf7a5f3684cddf43b0dbcdc5d9f47e8afc8bfa55'
CHECKPOINT_BYTES = 698140651
EXPORT = ROOT/'docs/capstone/coordination/LENOVO-STUNET-COMPLETE-NATIVE-METADATA-20261108.json'
EXPORT_SHA = 'c5dcdb2aa77dbe2df2d214932b2d7e27b9dd55351c2aea798f2d676fd047f3cf'
MANIFEST = Path('/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/rsuper-training-sources-01/manifest.csv')
PORTABLE = ROOT/'outputs/prowl/testing/stunet-continuation-review-20261108-02/src/training/stunet_transfer_20261106.py'
ARCH = Path('/Volumes/PROWL-Data/PROWL/teachers/stunet-audit-20261106-source/nnUNet-2.2/nnunetv2/training/nnUNetTrainer/STUNetTrainer.py')
THRESHOLDS = (0., .4, .5, .6)
SECONDS = 13980  # Upper bound, further reduced by actual preparation/transfer elapsed time.


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())


def tree_bytes(root):
    return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())


def safety():
    from scripts.diagnostics.probe_stunet_mps_inference_20261108_v2 import safety as platform_safety
    platform_safety()
    if tree_bytes(Path.home()/'PROWL-Backups') > 26*1024**3:
        raise ValueError('Existing Mac26GiB total backup cap')
    if OUT.exists() and tree_bytes(OUT) > 4*1024**3:
        raise ValueError('Screen4GiB primary artifact cap')


def backup(path):
    path = Path(path)
    dest = BACKUP/path.relative_to(OUT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise FileExistsError(dest)
    size = path.stat().st_size
    if tree_bytes(Path.home()/'PROWL-Backups')+size > 26*1024**3:
        raise ValueError('Backup projected total cap')
    if tree_bytes(BACKUP)+size > 4*1024**3:
        raise ValueError('New backup4GiB cap')
    if shutil.disk_usage(Path.home()).free-size < 50_000_000_000:
        raise ValueError('Backup projected internal reserve')
    if OUT.stat().st_dev == BACKUP.stat().st_dev:
        raise ValueError('Independent backup filesystem required')
    with path.open('rb') as source, dest.open('xb') as target:
        shutil.copyfileobj(source, target, 4*1024**2)
        target.flush(); os.fsync(target.fileno())
    if sha(path) != sha(dest):
        raise ValueError('Backup identity mismatch')
    return dict(path=str(path), backup=str(dest), bytes=size, sha256=sha(path))


def prepare():
    safety()
    if CHECKPOINT.stat().st_size != CHECKPOINT_BYTES or sha(CHECKPOINT) != CHECKPOINT_SHA:
        raise ValueError('Completed12k checkpoint identity')
    if sha(EXPORT) != EXPORT_SHA:
        raise ValueError('Native source export changed')
    export = json.loads(EXPORT.read_text())
    members = export['case_identities_from_frozen_inputs']
    assert len(members) == len({r['case_id'] for r in members}) == 70
    with MANIFEST.open() as f:
        paths = {r['case_id']:r for r in csv.DictReader(f)}
    cases = []
    for member in members:
        row = paths[member['case_id']]
        if row['protected_role'] != 'development':
            raise ValueError('Development role required')
        sources = {kind:dict(path=row[kind+'_path'], sha256=member['source_sha256'][kind])
                   for kind in ('ct','pancreas','lesion')}
        for v in sources.values():
            if not Path(v['path']).is_file():
                raise ValueError('Missing admitted source')
        cases.append(dict(member, sources=sources))
    pilot = [max((r for r in cases if r['profile']['positive'] == positive),
                 key=lambda r:(math.prod(r['profile']['region_shape']),r['case_id']))['case_id']
             for positive in (True, False)]
    worst = sum((math.prod(r['native_shape'])+1)//2 for r in cases)+CHECKPOINT_BYTES+32*1024**2
    existing = tree_bytes(Path.home()/'PROWL-Backups')
    if existing+worst > 26*1024**3 or shutil.disk_usage(Path.home()).free-worst < 50_000_000_000:
        raise ValueError('Worst-case compact backup projection does not fit')
    if shutil.disk_usage(BASE).free-worst < 100*1024**3:
        raise ValueError('External projected reserve')
    files = [Path(__file__), EXPORT, PORTABLE, ARCH, MANIFEST]
    files += list((ROOT/'src').rglob('*.py'))
    files += [ROOT/'scripts/diagnostics'/n for n in
              ('probe_stunet_mps_inference_20261108_v2.py','qualify_distillation_mac.py',
               'summarize_stunet_confidence_20261108.py')]
    origin=(BASE/'inference-capacity-01/request.json').stat().st_mtime
    remaining=min(SECONDS,int(14400-(time.time()-origin)-120))
    if remaining<=0:
        raise ValueError('Original cumulative four-hour experiment budget exhausted')
    request = dict(schema='prowl.stunet.mac-confidence-screen.v1',
        user_authorization='2026-11-08 explicit Mac12k confidence experiment',
        scope='exposed provided-pancreas development; descriptive, no independent-patient claim',
        checkpoint=dict(path=str(CHECKPOINT),sha256=CHECKPOINT_SHA,bytes=CHECKPOINT_BYTES),
        cases=cases, pilot=pilot, thresholds=THRESHOLDS, seconds=remaining,
        cumulative_budget_origin_unix=origin,cumulative_budget_seconds=14400,cleanup_reserve_seconds=120,
        rss_bytes=12*1024**3, mps_bytes=6*1024**3, total_backup_bytes=26*1024**3,
        internal_reserve_bytes=50_000_000_000, external_reserve_bytes=100*1024**3,
        worst_case_new_backup_bytes=worst, existing_backup_bytes=existing,
        raw_dice_sanity_max_absolute_difference=.01,
        parity_policy='Same-Mac fresh raw control; CUDA counts/differences reported, not spatial equivalence',
        environment={name:importlib.metadata.version(name) for name in ('torch','numpy','scipy','nibabel')},
        pins={str(p.resolve()):sha(p) for p in files})
    OUT.mkdir(parents=True, exist_ok=False); BACKUP.mkdir(exist_ok=False)
    write(OUT/'request.json', request)
    return request


def load_case(row):
    import nibabel as nib
    import numpy as np
    from src.data.segmenter_native_windows_v1 import geometry, orient
    from src.data.segmenter_pancreas_region_v1 import crop_case
    from src.data.segmenter_fast_varied_v1 import normalize_region
    from src.data.segmenter_content_v1 import target_content
    for source in row['sources'].values():
        if sha(source['path']) != source['sha256']:
            raise ValueError('Source identity mismatch: '+row['case_id'])
    objects = {k:nib.load(v['path']) for k,v in row['sources'].items()}
    ct = objects['ct']
    if ct.shape != tuple(row['native_shape']) or not np.allclose(ct.affine,row['native_affine'],atol=1e-5,rtol=0):
        raise ValueError('Original native geometry mismatch')
    if math.prod(ct.shape) > 256000000:
        raise ValueError('Existing source voxel cap')
    parent = geometry(ct.shape, ct.affine)
    masks = {}
    for kind in ('pancreas','lesion'):
        obj = objects[kind]
        if obj.shape != ct.shape or not np.allclose(obj.affine,ct.affine,atol=1e-5,rtol=0):
            raise ValueError('Mask alignment')
        masks[kind],_ = target_content(obj.dataobj.get_unscaled(),
            dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
    if not masks['pancreas'].any():
        raise ValueError('Empty supplied pancreas')
    target = orient(masks['pancreas'],parent).astype(np.uint8)
    target[orient(masks['lesion'],parent)!=0] = 2
    case = crop_case(dict(name=row['case_id'],target=target,geometry=parent,
        positive=bool(masks['lesion'].any()),original_pancreas=masks['pancreas']))
    if int((case['target']==2).sum()) != int(masks['lesion'].sum()) or np.count_nonzero(case['target']) != np.count_nonzero(target):
        raise ValueError('Annotation field clipped')
    case['image'] = normalize_region(ct.get_fdata(dtype=np.float32,caching='unchanged'),
                                    parent,case['region_low'],case['region_high'])
    if list(case['image'].shape) != row['profile']['region_shape']:
        raise ValueError('Region geometry mismatch')
    case.update(original_pancreas=masks['pancreas'],original_lesion=masks['lesion'])
    return case


def worker():
    import numpy as np
    import torch
    from scipy import ndimage
    from src.data.segmenter_native_windows_v1 import orient, tiles
    from src.data.segmenter_physical_windows_v1 import physical_geometry, sample_window, PhysicalReconstructor
    from src.inference.lesion_confidence_screen_v2 import encode,decode,pack,unpack,confidence_histogram
    from src.training.pants_native_evaluation import native_metrics
    from scripts.diagnostics.summarize_stunet_confidence_20261108 import summarize
    request = json.loads((OUT/'request.json').read_text())
    if any(importlib.metadata.version(name)!=version for name,version in request['environment'].items()):
        raise ValueError('Qualified runtime package identity changed')
    for path, expected in request['pins'].items():
        if sha(path) != expected:
            raise ValueError('Producing source/input changed')
    if sha(CHECKPOINT) != CHECKPOINT_SHA:
        raise ValueError('Checkpoint changed')
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') != '0' or not torch.backends.mps.is_available():
        raise ValueError('MPS with fallback disabled required')
    torch.set_num_threads(2)
    torch.mps.set_per_process_memory_fraction(6*1024**3/torch.mps.recommended_max_memory())
    spec = importlib.util.spec_from_file_location('bound_stunet', PORTABLE)
    portable = importlib.util.module_from_spec(spec); spec.loader.exec_module(portable)
    state = torch.load(CHECKPOINT,map_location='cpu',weights_only=True)
    if state['version'] != 'stunet-session-1' or state['step'] != 12000 or sum(state['exposure'].values()) != 12000:
        raise ValueError('Completed scientific checkpoint envelope')
    model = portable.make_model(ARCH,pools=[[2,2,2]]*4+[[1,1,2]])
    model.load_state_dict(state['model'],strict=True)
    del state
    model.eval(); model.decoder.deep_supervision = False; model = model.to('mps')
    shutil.copyfile(CHECKPOINT,OUT/'checkpoint-12000.pt')
    backup(OUT/'checkpoint-12000.pt'); backup(OUT/'request.json')
    export = json.loads(EXPORT.read_text())
    expected = {r['case_id']:r['metrics'] for r in export['reports'][-1]['cases_as_saved']}
    by_id = {r['case_id']:r for r in request['cases']}
    order = request['pilot']+[r['case_id'] for r in request['cases'] if r['case_id'] not in request['pilot']]
    rows = []; started = time.monotonic(); tiles_done = 0; peak_driver = 0
    client=None;run_id=None
    for case_index, name in enumerate(order):
        before = time.monotonic(); row = by_id[name]; case = load_case(row)
        record = physical_geometry(case['geometry']); windows = tiles(record['shape'],window=128,stride=64)
        if len(windows) != row['profile']['tiles']:
            raise ValueError('Tiling changed')
        recon = PhysicalReconstructor(record,window=128)
        with torch.inference_mode():
            for index, origin in enumerate(windows):
                image,_ = sample_window(case['image'],record,origin,order=1,window=128)
                x = torch.from_numpy(image[None,None]).to('mps')
                logits = model(x)
                probabilities = logits.float().softmax(1)[0].cpu().numpy()
                torch.mps.synchronize(); peak_driver=max(peak_driver,torch.mps.driver_allocated_memory())
                if peak_driver > 6*1024**3:
                    raise ValueError('MPS allocation cap')
                recon.add(origin,probabilities); del logits,probabilities,x
                tiles_done += 1
                if index%10 == 0:
                    print(json.dumps(dict(event='tile',case_id=name,tile=index+1,total=len(windows),completed_cases=case_index)),flush=True)
        probabilities = recon.finish(windows)
        local_code = encode(probabilities)
        truth = (case['target']==2).astype(np.uint8)
        histogram = confidence_histogram(probabilities,truth)
        del probabilities,recon,truth
        parent = case['parent_geometry']; codes=np.zeros(parent['shape'],np.uint8)
        slices=tuple(slice(l,h) for l,h in zip(case['region_low'],case['region_high']))
        codes[slices]=local_code; code=np.ascontiguousarray(orient(codes,parent,inverse=True))
        del codes,local_code
        components,_=ndimage.label(case['original_lesion'],structure=np.ones((3,3,3)))
        results={}; hashes={}
        for threshold in THRESHOLDS:
            prediction=decode(code,threshold)
            metrics=native_metrics(prediction,case['original_pancreas'],case['original_lesion'],np.asarray(parent['source_affine']))
            metrics['hit_component_ids']=[int(x) for x in np.unique(components[prediction==2]) if x]
            key=str(threshold); results[key]=metrics
            hashes[key]=hashlib.sha256(prediction.tobytes()).hexdigest()
            del prediction
        raw=results['0.0']['lesion']; old=expected[name]['lesion']
        if raw['target_voxels']!=old['target_voxels']:
            raise ValueError('Reference count drift')
        difference=None if raw['dice'] is None or old['dice'] is None else raw['dice']-old['dice']
        if difference is not None and abs(difference)>.01:
            raise ValueError('Raw Dice sanity drift beyond prospectively fixed .01; not a numerical equivalence tolerance')
        path=OUT/(name+'.npz')
        with path.open('xb') as f:
            np.savez_compressed(f,packed=pack(code),shape=np.asarray(code.shape,np.int64))
        proof=backup(path)
        with np.load(proof['backup'],allow_pickle=False) as f:
            restored=unpack(f['packed'],[int(n) for n in f['shape']])
        if not np.array_equal(restored,code):
            raise ValueError('Independent mask replay failed')
        for threshold in THRESHOLDS:
            if hashlib.sha256(decode(restored,threshold).tobytes()).hexdigest()!=hashes[str(threshold)]:
                raise ValueError('Reopened policy hash mismatch')
        result=dict(case_id=name,tiles=len(windows),gaps=0,policies=results,mask_sha256=hashes,
                    confidence_histogram=histogram,artifact=proof,seconds=time.monotonic()-before,
                    original_cuda_lesion_counts=old,raw_dice_difference_from_cuda=difference)
        write(OUT/(name+'.json'),result); backup(OUT/(name+'.json')); rows.append(result)
        del case,code,restored,components
        gc.collect();torch.mps.empty_cache();safety()
        print(json.dumps(dict(event='case_complete',case_id=name,completed=len(rows),seconds=result['seconds'])),flush=True)
        if len(rows)==2:
            projected=(time.monotonic()-started)/tiles_done*sum(r['profile']['tiles'] for r in request['cases'])*1.5
            write(OUT/'qualification.json',dict(status='TWO_NATIVE_CASES_PASS',cases=request['pilot'],
                peak_observed_driver_bytes=peak_driver,projected_total_seconds=projected,
                limit_seconds=request['seconds'],spatial_equivalence_to_original_cuda='not established; fresh same-device control'))
            backup(OUT/'qualification.json')
            if projected>request['seconds']-(time.monotonic()-started):
                raise ValueError('Conservative full-cohort projection exceeds remaining total cap')
            from mlflow import MlflowClient
            uri='sqlite:///'+str(BASE/'mlflow.db')
            client=MlflowClient(tracking_uri=uri)
            experiment=client.create_experiment('PROWL STU-Net confidence screen20261108',
                                               artifact_location=(BASE/'mlflow-artifacts').as_uri())
            run_id=client.create_run(experiment,tags={'mlflow.runName':'CAP-EXP-020 Mac12k fixed thresholds',
                'prowl.kind':'inference_policy','prowl.training_hours':'excluded',
                'prowl.scope':'exposed-development exploratory','parent_checkpoint_sha256':CHECKPOINT_SHA}).info.run_id
            for key,value in dict(thresholds='raw,.40,.50,.60',window=128,stride=64,cases=70,
                                  optimizer_updates=0,checkpoint_sha256=CHECKPOINT_SHA).items():
                client.log_param(run_id,key,str(value))
            write(OUT/'tracking.json',dict(tracking_uri=uri,run_id=run_id,experiment_id=experiment))
            backup(OUT/'tracking.json')
    result=summarize(rows)
    result.update(status='COMPLETE_DESCRIPTIVE_ONLY',request_sha256=sha(OUT/'request.json'),
                  checkpoint_sha256=CHECKPOINT_SHA,seconds=time.monotonic()-started,
                  peak_observed_driver_bytes=peak_driver,optimizer_updates=0)
    write(OUT/'result.json',result);backup(OUT/'result.json')
    for key,metrics in result['policies'].items():
        for name,value in metrics.items():
            if value is not None:
                client.log_metric(run_id,'policy_'+key.replace('.','')+'/'+name,float(value))
    client.log_artifact(run_id,str(OUT/'result.json'))
    client.log_artifact(run_id,str(OUT/'request.json'))
    client.set_terminated(run_id,status='FINISHED')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    if args.worker:
        return worker()
    from src.operations.full_training_platform import training_guard
    from src.operations.mac_teacher_supervision_v3 import run
    request=prepare()
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='2',PYTHONPATH=str(ROOT)+':'+DEPENDENCIES)
        ok=run(['caffeinate','-i',sys.executable,str(Path(__file__).resolve()),'--worker'],OUT,
               seconds=request['seconds'],rss_bytes=12*1024**3,tick=safety,env=env)
    backup(OUT/'resources.json')
    if (OUT/'tracking.json').exists():
        from mlflow import MlflowClient
        tracking=json.loads((OUT/'tracking.json').read_text())
        if not ok:
            MlflowClient(tracking_uri=tracking['tracking_uri']).set_terminated(tracking['run_id'],status='FAILED')
        import sqlite3
        with sqlite3.connect(BASE/'mlflow.db') as source,sqlite3.connect(OUT/'mlflow-snapshot.db') as target:
            source.backup(target)
        backup(OUT/'mlflow-snapshot.db')
    if not ok:
        raise SystemExit('Screen stopped; preserve evidence, no automatic retry')


if __name__=='__main__':
    main()
