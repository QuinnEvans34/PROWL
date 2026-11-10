"""Finish six frozen voxel-clipping settings, reusing two backed-up pilots."""
import argparse
import fcntl
import gc
import json
import os
from pathlib import Path
import plistlib
import shutil
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DEPENDENCIES = '/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies'
sys.path.append(DEPENDENCIES)
from scripts.diagnostics.resume_stunet_margin_mac_20261110 import (
    OUT as PRIMARY, BACKUP, BASE, backup, sha, write, tree_bytes,
)
from scripts.diagnostics.probe_stunet_mps_inference_20261108_v2 import safety as platform_safety

OUT = PRIMARY/'voxel-clip-02'
OLD = PRIMARY/'voxel-clip-01'
REQUEST = OUT/'request.json'
PARENT_PROOF = ROOT/'docs/capstone/evaluation/STUNET-24K-MARGIN-RESUMED-CLOSEOUT-20261110.json'
REPORT = ROOT/'docs/capstone/evaluation/STUNET-24K-SPATIAL-CLIP-RESUMED-RESULTS-20261110.md'
EVIDENCE = ROOT/'docs/capstone/evaluation/STUNET-24K-SPATIAL-CLIP-RESUMED-CLOSEOUT-20261110.json'
APPROVAL = ROOT/'docs/capstone/operations/STUNET-24K-VOXEL-CLIP-RESUME-APPROVAL-20261110.json'
LABEL = 'com.prowl.stunet-voxel-clip-20261110-03'
GIB = 1024**3
RESERVE = 64*1024**2
CLOSEOUT_SECONDS = 180


def read(path):
    return json.loads(Path(path).read_text())


def timing():
    approval = read(APPROVAL)
    origin = read(BASE/'budget-origin.json')
    previous_deadline = read(OLD/'request.json')['deadline_unix']
    if (approval['cumulative_active_seconds'] != origin['seconds'] or
            not approval['hold_verified_unix'] < approval['resume_origin_unix'] <= time.time()):
        raise ValueError('Cumulative active-work accounting changed')
    deadline = min(approval['wall_deadline_unix'],
                   approval['resume_origin_unix'] + previous_deadline - approval['hold_verified_unix'])
    spent = read(OLD/'resources.json')['seconds']
    worker_seconds = min(approval['cpu_cap_seconds']-spent,
                         deadline-time.time()-CLOSEOUT_SECONDS)
    return deadline, worker_seconds


def safety():
    platform_safety()
    if not os.path.ismount('/Volumes/PROWL-Data'):
        raise ValueError('External drive is not mounted')
    if time.time() >= timing()[0]:
        raise ValueError('Approved cumulative deadline reached')
    if tree_bytes(Path.home()/'PROWL-Backups') > 26*GIB or tree_bytes(BASE) > 4*GIB:
        raise ValueError('Unchanged storage cap reached')


def verify_pins(pins):
    for path, expected in pins.items():
        if sha(path) != expected:
            raise ValueError('Producing or input pin changed: '+path)


def verify_request():
    request = read(REQUEST)
    verify_pins(request['pins'])
    if sha(PRIMARY/'request.json') != request['primary_request_sha256']:
        raise ValueError('Primary request changed')
    return request


def reusable_cases(request):
    p = read(PRIMARY/'request.json')
    rows = {r['case_id']:r for r in p['cases']}
    if len(rows) != 70 or len(p['cases']) != 70 or set(request['reused']) != set(p['pilot']) or len(p['pilot']) != 2:
        raise ValueError('Unexpected cohort or pilot census')
    if {f.stem for f in OLD.glob('PanTS_*.json')} != set(p['pilot']):
        raise ValueError('Unexpected saved CPU case census')
    result = {}
    for name, digest in request['reused'].items():
        case = OLD/(name+'.json')
        cold = BACKUP/OLD.name/case.name
        if case.stat().st_dev == cold.stat().st_dev or sha(case) != digest or sha(cold) != digest:
            raise ValueError('Pilot record or independent backup changed')
        row, primary = read(cold), read(PRIMARY/case.name)
        artifact = primary['artifact']
        if (row['case_id'] != name or len(row['policies']) != 7 or len(row['contexts']) != 6 or
                row['policies']['raw'] != primary['policies']['raw'] or
                row['code_backup_sha256'] != artifact['sha256'] or sha(artifact['backup']) != artifact['sha256']):
            raise ValueError('Pilot record does not match fixed primary inputs')
        for k in ('pancreas','lesion'):
            source = rows[name]['sources'][k]
            if sha(source['path']) != source['sha256']:
                raise ValueError('Pilot reference changed')
        result[name] = row
    return result


def prepare():
    safety()
    if OUT.exists() or (BACKUP/OUT.name).exists() or EVIDENCE.exists() or REPORT.exists():
        raise ValueError('Existing attempt or report; never overwrite or retry')
    old = read(OLD/'request.json')
    original = read(PRIMARY/'request.json')
    if any(original['pins'][f] != h for f,h in old['pins'].items() if f in original['pins']):
        raise ValueError('Parent/secondary pins disagree')
    binding = read(OLD/'parent-binding.json')
    resources = read(OLD/'resources.json')
    if (not resources['workers_reaped'] or resources['success'] or
            read(PARENT_PROOF)['status'] != 'VERIFIED_COMPLETE' or
            sha(PARENT_PROOF) != binding['primary_closeout_sha256'] or
            sha(PRIMARY/'result.json') != binding['primary_result_sha256'] or
            sha(PRIMARY/'request.json') != old['primary_request_sha256']):
        raise ValueError('Verified primary and stopped previous attempt required')
    tracking = read(OLD/'tracking.json')
    with sqlite3.connect((BASE/'mlflow.db').as_uri()+'?mode=ro', uri=True) as conn:
        if conn.execute('SELECT status FROM runs WHERE run_uuid=?',(tracking['run_id'],)).fetchone() != ('FAILED',):
            raise ValueError('Old CPU tracking is not closed')
    if (tree_bytes(Path.home()/'PROWL-Backups')+RESERVE > 26*GIB or tree_bytes(BASE)+RESERVE > 4*GIB or
            shutil.disk_usage(Path.home()).free-RESERVE < 50_000_000_000 or
            shutil.disk_usage(BASE).free-RESERVE < 100*GIB):
        raise ValueError('Projected metadata exceeds existing reserves')
    pins = original['pins'] | old['pins']
    verify_pins(pins)
    for file in (Path(__file__),APPROVAL,PARENT_PROOF,PRIMARY/'request.json',PRIMARY/'result.json',
                 OLD/'request.json',OLD/'parent-binding.json',OLD/'resources.json',OLD/'qualification.json',
                 OLD/'tracking.json',OLD/'failure.json',BASE/'budget-origin.json'):
        pins[str(file)] = sha(file)
    for row in original['cases']:
        file = PRIMARY/(row['case_id']+'.json')
        pins[str(file)] = sha(file)
    request = dict(schema='terminal24k-secondary-voxel-clip-pilot-reuse-v1', pins=pins,
        primary_request_sha256=old['primary_request_sha256'], previous_run_id=tracking['run_id'],
        reused={name:sha(OLD/(name+'.json')) for name in original['pilot']},
        projected_remaining_seconds=read(OLD/'qualification.json')['projected_remaining_seconds'],
        rss_bytes=4*GIB, publish_report=True)
    reusable_cases(request)
    deadline, available = timing()
    if request['projected_remaining_seconds'] > available:
        raise ValueError('Remaining cases no longer fit the approved time allowance')
    request['deadline_unix'] = deadline
    OUT.mkdir()
    write(REQUEST, request); backup(REQUEST)
    write(OUT/'parent-binding.json', binding); backup(OUT/'parent-binding.json')
    job = Path.home()/'Library/Application Support/PROWL/owned-jobs'/LABEL
    job.mkdir(parents=True)
    plist = job/'job.plist'
    with plist.open('xb') as f:
        plistlib.dump(dict(Label=LABEL, RunAtLoad=True, KeepAlive=False, ExitTimeOut=15,
            ProcessType='Background', WorkingDirectory=str(Path.home()),
            StandardOutPath=str(job/'launchd.stdout.log'), StandardErrorPath=str(job/'launchd.stderr.log'),
            ProgramArguments=[sys.executable,str(Path(__file__).resolve()),'--launch-sha256',sha(REQUEST)],
            EnvironmentVariables=dict(HOME=str(Path.home()), PYTHONPATH=f'{ROOT}:{DEPENDENCIES}',
                PATH='/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
                PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')),f)
    print(json.dumps(dict(plist=str(plist), request_sha256=sha(REQUEST), deadline_unix=deadline,
                          available_seconds=available, projected_remaining_seconds=request['projected_remaining_seconds'])))


def worker():
    import nibabel as nib
    import numpy as np
    from scipy import ndimage
    from mlflow import MlflowClient
    from src.data.segmenter_content_v1 import target_content
    from src.inference.stunet_margin_screen_20261110 import unpack
    from src.inference.stunet_voxel_clip_20261110 import clip_prediction, summarize
    from src.training.pants_native_evaluation import native_metrics
    request = verify_request()
    binding = json.loads((OUT/'parent-binding.json').read_text())
    if sha(PRIMARY/'result.json') != binding['primary_result_sha256'] or sha(PARENT_PROOF) != binding['primary_closeout_sha256']:
        raise ValueError('Verified primary changed')
    cohort = json.loads((PRIMARY/'request.json').read_text())['cases']
    by_id = {r['case_id']:r for r in cohort}
    pilot = json.loads((PRIMARY/'request.json').read_text())['pilot']
    order = pilot + [r['case_id'] for r in cohort if r['case_id'] not in pilot]
    reused = reusable_cases(request)
    client = MlflowClient(tracking_uri='sqlite:///'+str(BASE/'mlflow.db'))
    experiment = client.create_experiment('PROWL terminal24k attached-voxel-clip20261110 pilot reuse',
                                          artifact_location=(BASE/'mlflow-artifacts').as_uri())
    run_id = client.create_run(experiment, tags={'mlflow.runName':'Six CPU anatomy-support decisions (68 remaining)',
        'prowl.previous_run_id':request['previous_run_id'],
        'prowl.kind':'inference_policy','prowl.training_hours':'excluded',
        'prowl.scope':'exposed-development secondary; combined60settings'}).info.run_id
    write(OUT/'tracking.json', dict(tracking_uri='sqlite:///'+str(BASE/'mlflow.db'), run_id=run_id))
    backup(OUT/'tracking.json')
    for k,v in dict(optimizer_updates=0, model_calls=0, ct_voxel_reads=0, cases=70,
                    primary_request_sha256=request['primary_request_sha256'], combined_settings=60,
                    reused_cases=len(reused), new_cases=70-len(reused)).items():
        client.log_param(run_id, k, str(v))
    rows = []; started = time.monotonic()
    for name in order:
        safety()
        if name in reused:
            result = reused[name]
            write(OUT/(name+'.json'), result); backup(OUT/(name+'.json'))
            if sha(OUT/(name+'.json')) != request['reused'][name]:
                raise ValueError('Copied pilot record differs')
            rows.append(result)
            print(json.dumps(dict(event='cpu_case_reused', case_id=name, completed=len(rows))), flush=True)
            continue
        before = time.monotonic(); row = by_id[name]
        affine = np.asarray(row['native_affine'])
        masks = {}
        for kind in ('pancreas','lesion'):
            source = row['sources'][kind]
            if sha(source['path']) != source['sha256']:
                raise ValueError('Admitted reference identity changed')
            obj = nib.load(source['path'])
            if list(obj.shape) != row['native_shape'] or not np.allclose(obj.affine, affine, rtol=0, atol=1e-5):
                raise ValueError('Native reference geometry changed')
            masks[kind],_ = target_content(obj.dataobj.get_unscaled(),
                dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
        primary = json.loads((PRIMARY/(name+'.json')).read_text())
        artifact = primary['artifact']
        if sha(artifact['backup']) != artifact['sha256']:
            raise ValueError('Independent finite-code backup identity changed')
        with np.load(artifact['backup'], allow_pickle=False) as saved:
            code = unpack(saved['packed'], [int(x) for x in saved['shape']])
        if list(code.shape) != row['native_shape']:
            raise ValueError('Native code geometry changed')
        reference,_ = ndimage.label(masks['lesion'], structure=np.ones((3,3,3)))
        metrics = dict(raw=primary['policies']['raw']); contexts = {}
        for bias in (0., .5):
            for radius in (5., 10., 20.):
                key = f'clip_bias{bias:g}_near{radius:g}'
                pred, context = clip_prediction(code, affine, bias=bias, radius_mm=radius)
                m = native_metrics(pred, masks['pancreas'], masks['lesion'], affine)
                m['hit_component_ids'] = [int(x) for x in np.unique(reference[pred == 2]) if x]
                if m['lesion']['target_voxels'] != metrics['raw']['lesion']['target_voxels']:
                    raise ValueError('Reference/raw mismatch')
                metrics[key] = m; contexts[key] = context
                del pred
        result = dict(case_id=name, policies=metrics, contexts=contexts, code_backup_sha256=artifact['sha256'],
                      seconds=time.monotonic()-before)
        write(OUT/(name+'.json'), result); backup(OUT/(name+'.json')); rows.append(result)
        del code, masks, reference; gc.collect(); safety()
        print(json.dumps(dict(event='cpu_case_complete', case_id=name, completed=len(rows),seconds=result['seconds'])), flush=True)
    final = summarize(rows)
    parent = json.loads((PRIMARY/'result.json').read_text())
    for key,value in final['policies']['raw'].items():
        if value != parent['policies']['raw'][key]:
            raise ValueError('Secondary summary raw/primary mismatch')
    combined = dict(parent['policies'], **{k:v for k,v in final['policies'].items() if k != 'raw'})
    guards = dict(parent['guards'], **final['guards'])
    qualified = [k for k,g in guards.items() if g['passes']]
    selected = sorted(qualified, key=lambda k:(-combined[k]['positive_macro_dice'], k))[0] if qualified else 'raw'
    best = sorted(combined, key=lambda k:(-combined[k]['positive_macro_dice'], k))[0]
    final.update(status='COMPLETE_CPU_EXPLORATORY', combined_settings=len(combined),
        combined_best_ignoring_guards=best, combined_selected_exploratory_policy=selected,
        combined_selected_metrics=combined[selected], combined_best_metrics=combined[best],
        combined_best_guard_pass=guards.get(best,{}).get('passes'),
        primary_result_sha256=binding['primary_result_sha256'], seconds=time.monotonic()-started,
        model_calls=0, ct_voxel_reads=0, optimizer_updates=0, reused_cases=2, new_cases=68)
    if len(combined) != 60:
        raise ValueError('Combined prospective search census changed')
    for key, metrics in final['policies'].items():
        for k,v in metrics.items():
            client.log_metric(run_id, key+'/'+k, float(v))
    stored = client.get_run(run_id).data.metrics
    for key, metrics in final['policies'].items():
        for k,v in metrics.items():
            if stored.get(key+'/'+k) != float(v):
                raise ValueError('CPU MLflow metric readback')
    verify_request(); write(OUT/'result.json', final); backup(OUT/'result.json')
    client.log_artifact(run_id, str(OUT/'result.json')); client.set_terminated(run_id, status='FINISHED')


def finish_report():
    import sqlite3
    from mlflow import MlflowClient
    from src.inference.stunet_voxel_clip_20261110 import summarize
    safety()
    request = verify_request()
    resources = json.loads((OUT/'resources.json').read_text())
    if not resources['success'] or not resources['workers_reaped'] or resources['exit_code'] != 0:
        raise ValueError('CPU study failed safely; no automatic retry')
    final = json.loads((OUT/'result.json').read_text())
    cases = json.loads((PRIMARY/'request.json').read_text())['cases']
    pilot = json.loads((PRIMARY/'request.json').read_text())['pilot']
    order = pilot+[r['case_id'] for r in cases if r['case_id'] not in pilot]
    rows = [json.loads((OUT/(name+'.json')).read_text()) for name in order]
    check = summarize(rows)
    if any(final[k] != v for k,v in check.items()):
        raise ValueError('CPU independent reduction mismatch')
    if {p.stem for p in OUT.glob('PanTS_*.json')} != set(order):
        raise ValueError('Unexpected CPU case records')
    for p in OUT.glob('PanTS_*.json'):
        target = BACKUP/OUT.name/p.name
        if sha(p) != sha(target):
            raise ValueError('CPU case backup mismatch')
    t = json.loads((OUT/'tracking.json').read_text())
    if MlflowClient(tracking_uri=t['tracking_uri']).get_run(t['run_id']).info.status != 'FINISHED':
        raise ValueError('CPU MLflow not FINISHED')
    with sqlite3.connect((BASE/'mlflow.db').as_uri()+'?mode=ro', uri=True) as source, sqlite3.connect(OUT/'mlflow-snapshot.db') as target:
        source.backup(target)
        if target.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Tracking database snapshot failed integrity check')
    backup(OUT/'mlflow-snapshot.db'); backup(OUT/'resources.json')
    proof = dict(status='VERIFIED_COMPLETE_CPU_ONLY', resources=resources, cases=70,
        policies=6, combined_settings=60, independent_case_backups_match=True,
        summary_rebuilt_from_case_records=True, producing_pins_match=True,
        mlflow=t, mlflow_status='FINISHED', result_sha256=sha(OUT/'result.json'),
        reused_cases=2, new_cases=68, request_sha256=sha(REQUEST), previous_run_id=request['previous_run_id'],
        policy_deployed=False, model_calls=0, optimizer_updates=0, ct_voxel_reads=0)
    text = ['# Terminal24k: secondary attached-voxel clipping results', '',
        'Six additional prospectively frozen CPU policies, reusing the primary study’s exact native codes. '
        'Combined search:60 settings; all70 exposed development cases retained (two pilots reused, 68 newly scored). No additional model pass, CT voxel read or training update.', '',
        '| Secondary policy | Dice | Recall | Small recall | Case/component hits | Empty alarms | FP mL | Guards |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for key,m in sorted(final['policies'].items()):
        text.append(f"| {key} | {m['positive_macro_dice']:.6f} | {m['positive_macro_recall']:.6f} | "
            f"{m['small_case_macro_recall']:.6f} | {m['detected_cases']}/36; {m['detected_components']}/45 | "
            f"{m['empty_alarm_cases']}/34 | {m['false_positive_mL']:.3f} | {final['guards'].get(key,{}).get('passes','control')} |")
    m = final['combined_selected_metrics']
    parent = json.loads((PRIMARY/'result.json').read_text())
    text += ['', f"Best guard-qualified setting across all60: **{final['combined_selected_exploratory_policy']}**, "
        f"Dice **{m['positive_macro_dice']:.6f}**; gain versus raw {m['positive_macro_dice']-parent['policies']['raw']['positive_macro_dice']:+.6f}, "
        f"versus standing5mm {m['positive_macro_dice']-parent['policies']['bias0_near5_min0']['positive_macro_dice']:+.6f}.", '',
        f"Highest Dice ignoring guards: **{final['combined_best_ignoring_guards']}**, "
        f"{final['combined_best_metrics']['positive_macro_dice']:.6f}; guard pass: {final['combined_best_guard_pass']}.", '',
        'Selection remains optimistic on already exposed development cases. Failed recall/detection/pancreas safeguards '
        'cannot be traded for a higher headline score. No policy deployed and no independent/leakage-free claim.', '',
        '[Primary54-policy result](STUNET-24K-MARGIN-RESUMED-RESULTS-20261110.md). '
        '[Prospective addendum](../operations/STUNET-24K-VOXEL-CLIP-ADDENDUM-20261110.md).', '']
    safety()
    with EVIDENCE.open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
    with REPORT.open('x') as f:f.write('\n'.join(text))
    if request['publish_report']:
        if subprocess.check_output(['git','branch','--show-current'], cwd=ROOT, text=True).strip() != 'main':
            raise ValueError('Report prepared; publishing requires unchanged main branch')
        paths = [str(p.relative_to(ROOT)) for p in (REPORT,EVIDENCE)]
        subprocess.run(['git','add','--']+paths,cwd=ROOT,check=True,timeout=60)
        subprocess.run(['git','commit','--only','-m','Report guarded anatomy clipping across sixty fixed settings','--']+paths,cwd=ROOT,check=True,timeout=60)
        subprocess.run(['git','push','origin','main'],cwd=ROOT,check=True,timeout=60)
    print(json.dumps(dict(status=proof['status'], selected=final['combined_selected_exploratory_policy'])),flush=True)



def launch(expected):
    if sha(REQUEST) != expected:
        raise ValueError('Launch request digest mismatch')
    with (OUT/'dispatch.lock').open('x') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        request = verify_request()
        safety()
        deadline, seconds = timing()
        if deadline != request['deadline_unix'] or seconds < request['projected_remaining_seconds']:
            raise ValueError('Conservative projection no longer fits approved budget')
        from src.operations.mac_teacher_supervision_v3 import run
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        ok = run([sys.executable,str(Path(__file__).resolve()),'--cpu-worker',expected], OUT,
                 seconds=seconds,rss_bytes=request['rss_bytes'],tick=safety,env=env)
        if not ok:
            if (OUT/'tracking.json').exists():
                from mlflow import MlflowClient
                t = read(OUT/'tracking.json')
                MlflowClient(tracking_uri=t['tracking_uri']).set_terminated(t['run_id'],status='FAILED')
            backup(OUT/'resources.json')
            raise ValueError('CPU continuation stopped; preserve evidence, no retry')
        finish_report()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--launch-sha256')
    mode.add_argument('--cpu-worker')
    args = parser.parse_args()
    try:
        if args.prepare:
            prepare()
        elif args.cpu_worker:
            if sha(REQUEST) != args.cpu_worker:
                raise ValueError('Worker request digest mismatch')
            worker()
        else:
            launch(args.launch_sha256)
    except Exception as error:
        if OUT.exists() and not args.prepare:
            path = OUT/('worker-failure.json' if args.cpu_worker else 'failure.json')
            if not path.exists():
                write(path, dict(status='SECONDARY_STOPPED_NO_RETRY', reason=repr(error)))
        raise
