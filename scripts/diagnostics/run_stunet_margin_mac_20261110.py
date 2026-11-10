"""One owned terminal24k MPS pass, 54 fixed CPU policies, no retry or training."""
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
OUT = BASE/'screen-01'
BACKUP = Path.home()/'PROWL-Backups/stunet-margin-mac-20261110-01'
CHECKPOINT = BASE/'received/checkpoint-24000.pt'
CHECKPOINT_SHA = '2cb9ff72c66b67f8bcdcb081c5d3f84735a83830f693ad2990fb8139933da92c'
MODEL = BASE/'received/terminal-model-only.pt'
EXPORT = ROOT/'docs/capstone/coordination/LENOVO-STUNET-CORRECTED-COMPLETE-NATIVE-METADATA-20261110.json'
EXPORT_SHA = '6413c8cecc8a0e3c64cdb3f0c3ee9731113a33de7cb0442fc8b4d8614407423e'
OLD_REQUEST = Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108/screen-03/request.json')
PROTOCOL = ROOT/'docs/capstone/operations/STUNET-24K-MARGIN-SCREEN-20261110.md'
GIB = 1024**3


def safety():
    from scripts.diagnostics.probe_stunet_mps_inference_20261108_v2 import safety as platform_safety
    platform_safety()
    if time.time() >= json.loads((BASE/'budget-origin.json').read_text())['deadline_unix']-60:
        raise ValueError('Original new-experiment cumulative deadline reached; no reset')
    if tree_bytes(Path.home()/'PROWL-Backups') > 26*GIB or tree_bytes(BASE) > 4*GIB:
        raise ValueError('Unchanged total-backup or new-root storage cap')


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
    if OUT.exists() or BACKUP.exists() or MODEL.exists():
        raise FileExistsError('An attempt/model already exists; never automatic retry')
    if sha(EXPORT) != EXPORT_SHA or CHECKPOINT.stat().st_size != 698166891 or sha(CHECKPOINT) != CHECKPOINT_SHA:
        raise ValueError('Frozen terminal/source identity mismatch')
    # Only CPU deserialization with restricted loader; optimizer state is never used.
    state = torch.load(CHECKPOINT, map_location='cpu', weights_only=True)
    if state['version'] != 'stunet-continuation-session-1' or state['step'] != 24000 or sum(state['exposure'].values()) != 24000:
        raise ValueError('Terminal scientific checkpoint envelope mismatch')
    model = dict(version='stunet-margin-model-only-v1', parent_sha256=CHECKPOINT_SHA,
                 step=24000, model=state['model'])
    with MODEL.open('xb') as f:
        torch.save(model, f); f.flush(); os.fsync(f.fileno())
    del model, state; gc.collect()
    old = json.loads(OLD_REQUEST.read_text())
    cases = old['cases']
    exported = json.loads(EXPORT.read_text())
    members = {r['case_id']:r for r in exported['case_identities_from_frozen_inputs']}
    if len(cases) != 70 or set(members) != {r['case_id'] for r in cases}:
        raise ValueError('Original cohort census mismatch')
    for case in cases:
        if members[case['case_id']] != {k:v for k,v in case.items() if k != 'sources'}:
            raise ValueError('Corrected source/profile identity changed')
        if any(not Path(v['path']).is_file() for v in case['sources'].values()):
            raise ValueError('Admitted development source missing')
    worst_codes = sum((math.prod(c['native_shape'])+1)//2 for c in cases)
    reserve = 64*1024**2
    existing = tree_bytes(Path.home()/'PROWL-Backups')
    needed = worst_codes+MODEL.stat().st_size+reserve
    if existing+needed > 26*GIB or shutil.disk_usage(Path.home()).free-needed < 50_000_000_000:
        raise ValueError('Worst-case independent packed/model backup projection fails')
    external_needed = worst_codes+reserve  # MODEL already exists inside BASE.
    if tree_bytes(BASE)+external_needed > 4*GIB or shutil.disk_usage(BASE).free-external_needed < 100*GIB:
        raise ValueError('Worst-case external root/reserve projection fails')
    qualification = BASE.parent/'stunet-confidence-mac-20261108/cache-release-qualification-02'
    q = json.loads((qualification/'result.json').read_text())
    resource = json.loads((qualification/'resources.json').read_text())
    if q['status'] != 'PASS_EXACT_OUTPUTS_CACHE_RELEASE' or not resource['success'] or not resource['workers_reaped']:
        raise ValueError('Historical allocation-lifecycle proof missing')
    origin = json.loads((BASE/'budget-origin.json').read_text())
    remaining = int(origin['deadline_unix']-time.time()-120)
    if remaining < 1800:
        raise ValueError('Insufficient unspent new-experiment budget')
    files = [Path(__file__), EXPORT, OLD_REQUEST, PORTABLE, ARCH, PROTOCOL, MODEL,
             BASE/'budget-origin.json', qualification/'result.json', qualification/'resources.json',
             ROOT/'tests/test_stunet_margin_screen_20261110.py',
             ROOT/'scripts/diagnostics/run_stunet_confidence_mac_20261108_v3.py',
             ROOT/'scripts/diagnostics/probe_stunet_mps_inference_20261108_v2.py']
    files += list((ROOT/'src').rglob('*.py'))
    request = dict(schema='prowl.stunet.terminal24k-margin-screen.v1',
        authorization='Nov10 explicit autonomous tuning experiment; new bounded study, not Nov8 retry',
        scope='exposed provided-pancreas-region development; no independent/leakage-free claim',
        checkpoint=dict(path=str(CHECKPOINT), sha256=CHECKPOINT_SHA, bytes=698166891),
        model_only=dict(path=str(MODEL), sha256=sha(MODEL), bytes=MODEL.stat().st_size),
        cases=cases, pilot=old['pilot'], policies=policies(), seconds=remaining,
        deadline_unix=origin['deadline_unix'], cumulative_origin_unix=origin['unix'],
        cumulative_seconds=14400, rss_bytes=12*GIB, mps_bytes=8*GIB,
        total_backup_bytes=26*GIB, new_root_bytes=4*GIB, existing_backup_bytes=existing,
        worst_case_additional_backup_bytes=needed, raw_cuda_dice_sanity_difference=.01,
        environment={n:importlib.metadata.version(n) for n in ('torch','numpy','scipy','nibabel')},
        pins={str(p.resolve()):sha(p) for p in files})
    OUT.mkdir(); BACKUP.mkdir()
    write(OUT/'request.json', request)
    # Independent minimal inference recovery state; full optimizer parent stays preserved.
    proof = backup(MODEL)
    primary = torch.load(MODEL, map_location='cpu', weights_only=True)
    reopened = torch.load(proof['backup'], map_location='cpu', weights_only=True)
    if (set(primary['model']) != set(reopened['model']) or
            any(not torch.equal(v, reopened['model'][k]) for k,v in primary['model'].items())):
        raise ValueError('Independent weights cold-reopen mismatch')
    write(OUT/'model-recovery-proof.json', dict(**proof, tensor_count=len(primary['model']),
        independently_reopened_exact=True, full_source_checkpoint_sha256=CHECKPOINT_SHA))
    backup(OUT/'model-recovery-proof.json'); backup(OUT/'request.json')
    print(json.dumps(dict(event='prepared', request_sha256=sha(OUT/'request.json'),
                          worst_case_backup_bytes=needed, remaining_seconds=remaining)), flush=True)


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
    order = request['pilot']+[c['case_id'] for c in request['cases'] if c['case_id'] not in request['pilot']]
    rows = []; started = time.monotonic(); tiles_done = 0; peak_driver = 0; client = None; run_id = None
    for case_index, name in enumerate(order):
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
                torch.mps.synchronize(); torch.mps.empty_cache(); tiles_done += 1
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
        if len(rows) == 2:
            elapsed = time.monotonic()-started
            remaining_tiles = sum(c['profile']['tiles'] for c in request['cases'])-tiles_done
            projected_remaining = elapsed/tiles_done*remaining_tiles*1.5
            available = request['deadline_unix']-time.time()-120
            write(OUT/'qualification.json', dict(status='TWO_NATIVE_CASES_PASS', cases=request['pilot'],
                peak_observed_driver_bytes=peak_driver, projected_remaining_seconds=projected_remaining,
                available_seconds=available, full_cohort_allowed=projected_remaining <= available,
                spatial_equivalence_to_cuda='not established; new matched MPS control'))
            backup(OUT/'qualification.json')
            if projected_remaining > available:
                raise ValueError('Conservative full-cohort projection exceeds remaining cumulative deadline')
            client = MlflowClient(tracking_uri='sqlite:///'+str(BASE/'mlflow.db'))
            experiment = client.create_experiment('PROWL terminal24k margin screen20261110',
                                                   artifact_location=(BASE/'mlflow-artifacts').as_uri())
            run_id = client.create_run(experiment, tags={'mlflow.runName':'Terminal24k54policy screen',
                'prowl.kind':'inference_policy', 'prowl.training_hours':'excluded',
                'prowl.scope':'exposed-development exploratory', 'parent_checkpoint_sha256':CHECKPOINT_SHA}).info.run_id
            for k,v in dict(policies=54, cases=70, window=128, stride=64, optimizer_updates=0,
                            parent_checkpoint_sha256=CHECKPOINT_SHA).items():
                client.log_param(run_id, k, str(v))
            write(OUT/'tracking.json', dict(tracking_uri='sqlite:///'+str(BASE/'mlflow.db'), run_id=run_id))
            backup(OUT/'tracking.json')
    result = screen.summarize(rows)
    result.update(status='COMPLETE_EXPLORATORY_NOT_DEPLOYED', checkpoint_sha256=CHECKPOINT_SHA,
        request_sha256=sha(OUT/'request.json'), cases=70, positive=36, empty=34, components=45,
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
