"""Explicit case-reuse continuation; same scientific producer, no completed-case reruns."""
import argparse
import gc
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DEPENDENCIES = '/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies'
sys.path.append(DEPENDENCIES)
from scripts.diagnostics.run_stunet_confidence_mac_20261108_v3 import load_case, sha, write, tree_bytes, PORTABLE, ARCH

BASE = Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-margin-mac-20261110')
PARENT_OUT = BASE/'screen-01'
PARENT_BACKUP = Path.home()/'PROWL-Backups/stunet-margin-mac-20261110-01'
PARENT_REQUEST_SHA = '8cff4e3bcb0142ea12bb9c5ee1c1efff4401dbca4755c3fccbe51677e26deb75'
PAUSE_RECEIPT = BASE/'operator-pause-01/receipt.json'
APPROVAL = BASE/'resume-deadline-approval-01.json'
RESUME_ORIGIN = BASE/'resume-preparation-origin-01.json'
OUT = BASE/'screen-02'
BACKUP = Path.home()/'PROWL-Backups/stunet-margin-mac-20261110-02'
CHECKPOINT = BASE/'received/checkpoint-24000.pt'
CHECKPOINT_SHA = '2cb9ff72c66b67f8bcdcb081c5d3f84735a83830f693ad2990fb8139933da92c'
MODEL = BASE/'received/terminal-model-only.pt'
EXPORT = ROOT/'docs/capstone/coordination/LENOVO-STUNET-CORRECTED-COMPLETE-NATIVE-METADATA-20261110.json'
EXPORT_SHA = '6413c8cecc8a0e3c64cdb3f0c3ee9731113a33de7cb0442fc8b4d8614407423e'
OLD_REQUEST = Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108/screen-03/request.json')
PROTOCOL = ROOT/'docs/capstone/operations/STUNET-24K-MARGIN-RESUME-20261110.md'
GIB = 1024**3


def budget():
    origin = json.loads((BASE/'budget-origin.json').read_text())
    pause = json.loads(PAUSE_RECEIPT.read_text())
    resumed = json.loads(RESUME_ORIGIN.read_text())
    approval = json.loads(APPROVAL.read_text())
    if approval.get('approved') is not True or approval.get('cumulative_active_seconds') != origin['seconds']:
        raise ValueError('Explicit pause-aware deadline approval required; no budget reset')
    charged = pause['observed_unix']-origin['unix']
    if not 0 <= charged < origin['seconds'] or resumed['unix'] < pause['observed_unix']:
        raise ValueError('Invalid cumulative pause accounting')
    active_deadline = resumed['unix']+origin['seconds']-charged
    return dict(deadline_unix=min(approval['deadline_unix'], active_deadline),
        prior_charged_seconds=charged, cumulative_seconds=origin['seconds'],
        resume_origin_unix=resumed['unix'], remaining_seconds=min(approval['deadline_unix'],active_deadline)-time.time())


def safety():
    from scripts.diagnostics.probe_stunet_mps_inference_20261108_v2 import safety as platform_safety
    platform_safety()
    if budget()['remaining_seconds'] <= 60:
        raise ValueError('Original cumulative active budget reached; no reset')
    if tree_bytes(Path.home()/'PROWL-Backups') > 26*GIB or tree_bytes(BASE) > 4*GIB:
        raise ValueError('Unchanged total-backup or new-root storage cap')


def partition(parent, pause):
    all_ids = [r['case_id'] for r in parent['cases']]
    reused = pause['reusable_case_ids']
    if (len(all_ids) != 70 or len(set(all_ids)) != 70 or len(set(reused)) != len(reused)
            or not set(reused) < set(all_ids) or pause['status'] != 'USER_PAUSED_VERIFIED'
            or not pause['owned_workers_reaped'] or not pause['gpu_lock_acquired_after_stop']
            or pause['primary_request_sha256'] != PARENT_REQUEST_SHA
            or pause['completed_cases'] != len(reused)
            or set(pause['remaining_case_ids']) != set(all_ids)-set(reused)
            or len(pause['remaining_case_ids']) != len(set(pause['remaining_case_ids']))):
        raise ValueError('Verified unique parent/pause census required')
    order = parent['pilot']+[n for n in all_ids if n not in parent['pilot']]
    return [n for n in order if n in reused], [n for n in order if n not in reused]


def reused_rows(parent, pause):
    reuse, remaining = partition(parent, pause)
    rows = []
    for name in reuse:
        path = PARENT_OUT/(name+'.json')
        if sha(path) != sha(PARENT_BACKUP/path.name):
            raise ValueError('Reusable independent case record differs')
        row = json.loads(path.read_text())
        a = row['artifact']
        if (row['case_id'] != name or row['gaps'] != 0 or not row['independent_policy_replay']
                or set(row['policies']) != set(parent['policies'])
                or sha(a['path']) != a['sha256'] or sha(a['backup']) != a['sha256']):
            raise ValueError('Reusable native-code/policy proof differs')
        rows.append(row)
    if sum(r['tiles'] for r in rows) != pause['completed_tiles']:
        raise ValueError('Reusable tile census differs')
    return rows, remaining


def backup(path):
    path = Path(path)
    dest = BACKUP/('terminal-model-only.pt' if path == MODEL else path.relative_to(OUT))
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = path.stat().st_size
    if tree_bytes(Path.home()/'PROWL-Backups')+size > 26*GIB:
        raise ValueError('Projected total26GiB backup cap')
    if shutil.disk_usage(Path.home()).free-size < 50_000_000_000:
        raise ValueError('Projected internal reserve')
    if path.stat().st_dev == dest.parent.stat().st_dev:
        raise ValueError('Independent backup filesystem required')
    with path.open('rb') as source, dest.open('xb') as target:
        shutil.copyfileobj(source, target, 4*1024**2); target.flush(); os.fsync(target.fileno())
    digest = sha(path)
    if digest != sha(dest):
        raise ValueError('Independent backup hash mismatch')
    return dict(path=str(path), backup=str(dest), bytes=size, sha256=digest)


def prepare():
    import torch
    from src.inference.stunet_margin_screen_20261110 import policies
    safety()
    if OUT.exists() or BACKUP.exists():
        raise FileExistsError('Continuation already prepared; inspect, never automatic retry')
    if sha(PARENT_OUT/'request.json') != PARENT_REQUEST_SHA:
        raise ValueError('Original request binding changed')
    parent = json.loads((PARENT_OUT/'request.json').read_text()); verify(parent)
    pause = json.loads(PAUSE_RECEIPT.read_text())
    if sha(PAUSE_RECEIPT) != sha(PARENT_BACKUP/'operator-pause-01/receipt.json'):
        raise ValueError('Independent pause receipt differs')
    rows, remaining = reused_rows(parent,pause)
    if parent['policies'] != policies():
        raise ValueError('Scientific policy recipe changed')
    if sha(EXPORT) != EXPORT_SHA or sha(CHECKPOINT) != CHECKPOINT_SHA:
        raise ValueError('Completed parent weights/source identity changed')
    model_proof = json.loads((PARENT_OUT/'model-recovery-proof.json').read_text())
    if sha(MODEL) != model_proof['sha256'] or sha(model_proof['backup']) != model_proof['sha256']:
        raise ValueError('Independent model state changed')
    primary = torch.load(MODEL,map_location='cpu',weights_only=True)
    cold = torch.load(model_proof['backup'],map_location='cpu',weights_only=True)
    if (primary['parent_sha256'] != CHECKPOINT_SHA or primary['step'] != 24000
            or set(primary['model']) != set(cold['model'])
            or any(not torch.equal(v,cold['model'][k]) for k,v in primary['model'].items())):
        raise ValueError('Independent inference weights cold replay failed')
    del primary,cold;gc.collect()
    cases = parent['cases']; by_id={c['case_id']:c for c in cases}
    worst = sum((math.prod(by_id[n]['native_shape'])+1)//2 for n in remaining)+64*1024**2
    existing = tree_bytes(Path.home()/'PROWL-Backups')
    if existing+worst > 26*GIB or shutil.disk_usage(Path.home()).free-worst < 50_000_000_000:
        raise ValueError('Remaining native-code worst-case independent backup/reserve fails')
    if tree_bytes(BASE)+worst > 4*GIB or shutil.disk_usage(BASE).free-worst < 100*GIB:
        raise ValueError('Remaining native-code external cap/reserve fails')
    charged = budget()
    # Reuse the measured whole-worker rate, including CPU scoring/backups.
    projected = pause['resources']['seconds']/pause['completed_tiles']*sum(by_id[n]['profile']['tiles'] for n in remaining)*1.5
    available = charged['remaining_seconds']-180
    if projected > available:
        raise ValueError('Conservative remaining-case projection exceeds unspent original active allowance')
    files = [Path(__file__),PROTOCOL,APPROVAL,RESUME_ORIGIN,PAUSE_RECEIPT,
             ROOT/'tests/test_stunet_margin_resume_20261110.py',PARENT_OUT/'request.json',
             PARENT_OUT/'resources.json',PARENT_OUT/'model-recovery-proof.json']
    pins=dict(parent['pins'])
    for path in list((ROOT/'src').rglob('*.py'))+files:
        pins[str(path.resolve())]=sha(path)
    request=dict(parent,schema='prowl.stunet.terminal24k-margin-case-continuation.v1',
        authorization='Nov10 user explicit resume plus separately recorded pause-aware deadline approval',
        parent_request_sha256=PARENT_REQUEST_SHA,parent_mlflow_run_id=pause['mlflow']['run_id'],
        reused_case_ids=[r['case_id'] for r in rows],remaining_case_ids=remaining,
        reused_record_sha256={r['case_id']:sha(PARENT_OUT/(r['case_id']+'.json')) for r in rows},
        deadline_unix=charged['deadline_unix'],seconds=int(available),
        cumulative_prior_charged_seconds=charged['prior_charged_seconds'],
        cumulative_resume_origin_unix=charged['resume_origin_unix'],
        remaining_projected_seconds=projected,worst_case_additional_backup_bytes=worst,
        existing_backup_bytes=existing,projection='1.5x measured parent whole-worker seconds per tile, no pilot reruns',
        pins=pins)
    OUT.mkdir();BACKUP.mkdir()
    write(OUT/'request.json',request);backup(OUT/'request.json')
    for row in rows:
        # Copy only tiny result records; keep original verified native-code pointers.
        path=OUT/(row['case_id']+'.json')
        with (PARENT_OUT/path.name).open('rb') as source,path.open('xb') as target:
            shutil.copyfileobj(source,target);target.flush();os.fsync(target.fileno())
        backup(path)
    write(OUT/'reuse-proof.json',dict(status='REUSE_VERIFIED_NO_MODEL_CALLS',cases=len(rows),
        tiles=pause['completed_tiles'],case_ids=request['reused_case_ids'],
        cold_model_tensor_count=130,independent_model_exact=True,projection_seconds=projected,
        available_seconds=available,original_compute_budget_reset=False))
    backup(OUT/'reuse-proof.json')
    print(json.dumps(dict(status='PREPARED',request_sha256=sha(OUT/'request.json'),
        reused=len(rows),remaining=len(remaining),seconds=available,projection_seconds=projected)),flush=True)


def verify(request):
    for path, expected in request['pins'].items():
        if sha(path) != expected:
            raise ValueError('Producing/input pin changed: '+path)
    if any(importlib.metadata.version(n) != v for n,v in request['environment'].items()):
        raise ValueError('Qualified runtime changed')


def worker():
    import numpy as np
    import torch
    from src.data.segmenter_native_windows_v1 import orient, tiles
    from src.data.segmenter_physical_windows_v1 import physical_geometry, sample_window, PhysicalReconstructor
    from src.inference import stunet_margin_screen_20261110 as screen
    from src.inference.component_proximity_filter_v1 import filter_prediction
    from mlflow import MlflowClient
    request = json.loads((OUT/'request.json').read_text()); verify(request); safety()
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') != '0' or not torch.backends.mps.is_available():
        raise ValueError('Actual MPS with fallback disabled required')
    torch.set_num_threads(2)
    torch.mps.set_per_process_memory_fraction(8*GIB/torch.mps.recommended_max_memory())
    spec = importlib.util.spec_from_file_location('bound_stunet', PORTABLE)
    portable = importlib.util.module_from_spec(spec); spec.loader.exec_module(portable)
    state = torch.load(MODEL, map_location='cpu', weights_only=True)
    if state['parent_sha256'] != CHECKPOINT_SHA or state['step'] != 24000:
        raise ValueError('Model-only parent binding')
    model = portable.make_model(ARCH, pools=[[2,2,2]]*4+[[1,1,2]])
    model.load_state_dict(state['model'], strict=True); del state
    model.eval(); model.decoder.deep_supervision = False; model = model.to('mps')
    expected = {r['case_id']:r['metrics'] for r in json.loads(EXPORT.read_text())['reports'][-1]['cases_as_saved']}
    by_id = {c['case_id']:c for c in request['cases']}
    parent = json.loads((PARENT_OUT/'request.json').read_text())
    rows, order = reused_rows(parent,json.loads(PAUSE_RECEIPT.read_text()))
    if order != request['remaining_case_ids'] or [r['case_id'] for r in rows] != request['reused_case_ids']:
        raise ValueError('Frozen reuse partition changed')
    started=time.monotonic(); tiles_done=sum(r['tiles'] for r in rows); fresh_tiles_done=0; peak_driver=0
    client=MlflowClient(tracking_uri='sqlite:///'+str(BASE/'mlflow.db'))
    experiment=client.create_experiment('PROWL terminal24k margin screen20261110 continuation01',
        artifact_location=(BASE/'mlflow-artifacts').as_uri())
    run_id=client.create_run(experiment,tags={'mlflow.runName':'Terminal24k54policy case-reuse continuation',
        'prowl.kind':'inference_policy','prowl.training_hours':'excluded',
        'prowl.scope':'exposed-development exploratory','prowl.parent_run_id':request['parent_mlflow_run_id'],
        'parent_checkpoint_sha256':CHECKPOINT_SHA}).info.run_id
    for k,v in dict(policies=54,cases=70,reused_cases=len(rows),new_cases=len(order),
                    optimizer_updates=0,checkpoint_sha256=CHECKPOINT_SHA).items():
        client.log_param(run_id,k,str(v))
    write(OUT/'tracking.json',dict(tracking_uri='sqlite:///'+str(BASE/'mlflow.db'),run_id=run_id));backup(OUT/'tracking.json')
    for case_index, name in enumerate(order,start=len(rows)):
        before = time.monotonic(); case = load_case(by_id[name])
        record = physical_geometry(case['geometry']); windows = tiles(record['shape'], window=128, stride=64)
        if len(windows) != by_id[name]['profile']['tiles']:
            raise ValueError('Frozen tiling changed')
        recon = PhysicalReconstructor(record, window=128)
        with torch.inference_mode():
            for index, origin in enumerate(windows):
                image, _ = sample_window(case['image'], record, origin, order=1, window=128)
                x = torch.from_numpy(image[None, None]).to('mps')
                logits = model(x); p = logits.float().softmax(1)[0].cpu().numpy()
                torch.mps.synchronize(); peak_driver = max(peak_driver, torch.mps.driver_allocated_memory())
                if peak_driver > 8*GIB:
                    raise ValueError('MPS8GiB allocation cap')
                recon.add(origin, p); del logits, p, x
                torch.mps.synchronize(); torch.mps.empty_cache(); tiles_done += 1; fresh_tiles_done += 1
                if index % 10 == 0:
                    print(json.dumps(dict(event='tile', case_id=name, tile=index+1,
                        total=len(windows), completed_cases=case_index)), flush=True)
        p = recon.finish(windows); local = screen.encode(p); del p, recon
        parent = case['parent_geometry']; oriented = np.zeros(parent['shape'], np.uint8)
        slices = tuple(slice(l,h) for l,h in zip(case['region_low'], case['region_high']))
        oriented[slices] = local; code = np.ascontiguousarray(orient(oriented, parent, inverse=True))
        del oriented, local
        affine = np.asarray(parent['source_affine'])
        def progress(event):
            print(json.dumps(dict(event, case_id=name)), flush=True)
        results = screen.score_case(code, case['original_pancreas'], case['original_lesion'], affine, progress=progress)
        raw = results['raw']['lesion']; old = expected[name]['lesion']
        if raw['target_voxels'] != old['target_voxels']:
            raise ValueError('Raw reference-count drift')
        difference = None if raw['dice'] is None else raw['dice']-old['dice']
        if difference is not None and abs(difference) > .01:
            raise ValueError('Raw/CUDA per-case Dice sanity bound failed; preserve, no retry')
        standing, context = filter_prediction(screen.decode(code, 0.), affine, maximum_distance_mm=5.)
        replay = screen.apply(code, affine, screen.policies()['bias0_near5_min0'])
        if not np.array_equal(standing, replay):
            raise ValueError('Standing5mm exact mask parity failed')
        parity_hash = hashlib.sha256(standing.tobytes()).hexdigest(); del standing, replay
        path = OUT/(name+'.npz')
        with path.open('xb') as f:
            np.savez_compressed(f, packed=screen.pack(code), shape=np.asarray(code.shape, np.int64))
        proof = backup(path)
        with np.load(proof['backup'], allow_pickle=False) as saved:
            restored = screen.unpack(saved['packed'], [int(x) for x in saved['shape']])
        if not np.array_equal(restored, code):
            raise ValueError('Independent native finite-code replay failed')
        replayed = screen.score_case(restored, case['original_pancreas'], case['original_lesion'], affine)
        if replayed != results:
            raise ValueError('Independent54-policy score replay failed')
        result = dict(case_id=name, tiles=len(windows), gaps=0, policies=results,
            artifact=proof, independent_policy_replay=True, standing5mm_mask_sha256=parity_hash,
            raw_pancreas_context_available=context['context_available'],
            original_cuda_lesion_counts=old, raw_dice_difference_from_cuda=difference,
            seconds=time.monotonic()-before)
        write(OUT/(name+'.json'), result); backup(OUT/(name+'.json')); rows.append(result)
        del code, restored, case, replayed; gc.collect(); torch.mps.empty_cache(); safety()
        print(json.dumps(dict(event='case_complete', case_id=name, completed=len(rows),
                              tiles_done=tiles_done, seconds=result['seconds'])), flush=True)
        if len(rows) == len(request['reused_case_ids'])+2:
            remaining_tiles=sum(by_id[n]['profile']['tiles'] for n in order)-fresh_tiles_done
            projected=(time.monotonic()-started)/fresh_tiles_done*remaining_tiles*1.5
            available=request['deadline_unix']-time.time()-120
            write(OUT/'qualification.json',dict(status='TWO_NEW_CASES_PASS_WITHOUT_RERUNNING_PARENT_CASES',
                projected_remaining_seconds=projected,available_seconds=available,allowed=projected<=available,
                peak_observed_driver_bytes=peak_driver,reused_cases=len(request['reused_case_ids'])))
            backup(OUT/'qualification.json')
            if projected>available:
                raise ValueError('New-case continuation projection exceeds remaining original active budget')
    result = screen.summarize(rows)
    result.update(status='COMPLETE_EXPLORATORY_NOT_DEPLOYED', checkpoint_sha256=CHECKPOINT_SHA,
        request_sha256=sha(OUT/'request.json'), cases=70, positive=36, empty=34, components=45,
        reused_cases=len(request['reused_case_ids']),new_cases=len(request['remaining_case_ids']),
        parent_request_sha256=PARENT_REQUEST_SHA,
        seconds=time.monotonic()-started, peak_observed_driver_bytes=peak_driver,
        best_dice_ignoring_guards=max(result['policies'], key=lambda k:result['policies'][k]['positive_macro_dice']))
    write(OUT/'result.json', result); backup(OUT/'result.json')
    for key, metrics in result['policies'].items():
        for metric, value in metrics.items():
            if value is not None:
                client.log_metric(run_id, key+'/'+metric, float(value))
    stored = client.get_run(run_id).data.metrics
    for key, metrics in result['policies'].items():
        for metric, value in metrics.items():
            if value is not None and stored.get(key+'/'+metric) != float(value):
                raise ValueError('MLflow metric readback mismatch')
    client.log_artifact(run_id, str(OUT/'result.json')); client.log_artifact(run_id, str(OUT/'request.json'))
    verify(request); safety(); client.set_terminated(run_id, status='FINISHED')
    print(json.dumps(dict(event='complete', selected=result['selected_exploratory_policy'])), flush=True)


def launch(expected):
    from src.operations.full_training_platform import training_guard
    from src.operations.mac_teacher_supervision_v3 import run
    request = json.loads((OUT/'request.json').read_text())
    if sha(OUT/'request.json') != expected:
        raise ValueError('Exact frozen request required')
    verify(request); safety()
    # Guard startup and resident local-model inference cannot overlap this study.
    if len(subprocess.check_output(['ollama','ps'], text=True).strip().splitlines()) != 1:
        raise ValueError('Resident Ollama model must be released before exclusive scientific inference')
    if (OUT/'process.json').exists():
        raise FileExistsError('This one-shot attempt was already dispatched')
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        env = dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK='0', OMP_NUM_THREADS='2',
                   PYTHONPATH=str(ROOT)+':'+DEPENDENCIES)
        remaining = min(request['seconds'], int(request['deadline_unix']-time.time()-120))
        ok = run(['caffeinate','-i',sys.executable,str(Path(__file__).resolve()),'--worker'], OUT,
                 seconds=remaining, rss_bytes=12*GIB, tick=safety, env=env)
    backup(OUT/'resources.json')
    if (OUT/'tracking.json').exists():
        from mlflow import MlflowClient
        t = json.loads((OUT/'tracking.json').read_text())
        if not ok:
            MlflowClient(tracking_uri=t['tracking_uri']).set_terminated(t['run_id'], status='FAILED')
        with sqlite3.connect(BASE/'mlflow.db') as source, sqlite3.connect(OUT/'mlflow-snapshot.db') as target:
            source.backup(target)
        backup(OUT/'mlflow-snapshot.db')
    if not ok:
        raise SystemExit('Screen stopped; preserve evidence, no automatic retry')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--worker', action='store_true')
    group.add_argument('--launch-sha256')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.worker:
        worker()
    else:
        launch(args.launch_sha256)
