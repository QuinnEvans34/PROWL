"""Continuation-bound CPU secondary screen; same six settings, no extra inference."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.append('/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies')
from scripts.diagnostics.resume_stunet_margin_mac_20261110 import OUT as PRIMARY, BASE, backup, safety, sha, write

OUT = PRIMARY/'voxel-clip-01'
REQUEST = OUT/'request.json'
PARENT_PROOF = ROOT/'docs/capstone/evaluation/STUNET-24K-MARGIN-RESUMED-CLOSEOUT-20261110.json'
REPORT = ROOT/'docs/capstone/evaluation/STUNET-24K-SPATIAL-CLIP-RESUMED-RESULTS-20261110.md'
EVIDENCE = ROOT/'docs/capstone/evaluation/STUNET-24K-SPATIAL-CLIP-RESUMED-CLOSEOUT-20261110.json'


def verify_request():
    r = json.loads(REQUEST.read_text())
    for p,h in r['pins'].items():
        if sha(p) != h:
            raise ValueError('Secondary producing pin changed')
    if sha(PRIMARY/'request.json') != r['primary_request_sha256']:
        raise ValueError('Primary scope binding changed')
    return r


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
    client = MlflowClient(tracking_uri='sqlite:///'+str(BASE/'mlflow.db'))
    experiment = client.create_experiment('PROWL terminal24k attached-voxel-clip20261110 resumed',
                                          artifact_location=(BASE/'mlflow-artifacts').as_uri())
    run_id = client.create_run(experiment, tags={'mlflow.runName':'Six CPU anatomy-support decisions',
        'prowl.kind':'inference_policy','prowl.training_hours':'excluded',
        'prowl.scope':'exposed-development secondary; combined60settings'}).info.run_id
    write(OUT/'tracking.json', dict(tracking_uri='sqlite:///'+str(BASE/'mlflow.db'), run_id=run_id))
    backup(OUT/'tracking.json')
    for k,v in dict(optimizer_updates=0, model_calls=0, ct_voxel_reads=0, cases=70,
                    primary_request_sha256=request['primary_request_sha256'], combined_settings=60).items():
        client.log_param(run_id, k, str(v))
    rows = []; started = time.monotonic(); processed_voxels = 0
    for name in order:
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
        processed_voxels += code.size
        del code, masks, reference; gc.collect(); safety()
        print(json.dumps(dict(event='cpu_case_complete', case_id=name, completed=len(rows),seconds=result['seconds'])), flush=True)
        if len(rows) == 2:
            total = sum(int(np.prod(r['native_shape'])) for r in cohort)
            projected = (time.monotonic()-started)/processed_voxels*(total-processed_voxels)*1.5
            available = min(binding['worker_deadline_unix'], request['deadline_unix']-120)-time.time()
            write(OUT/'qualification.json', dict(projected_remaining_seconds=projected,
                available_seconds=available, allowed=projected <= available))
            backup(OUT/'qualification.json')
            if projected > available:
                raise ValueError('Secondary CPU projection exceeds original remaining budget')
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
        model_calls=0, ct_voxel_reads=0, optimizer_updates=0)
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
    for p in OUT.glob('PanTS_*.json'):
        target = Path.home()/'PROWL-Backups/stunet-margin-mac-20261110-02/voxel-clip-01'/p.name
        if sha(p) != sha(target):
            raise ValueError('CPU case backup mismatch')
    t = json.loads((OUT/'tracking.json').read_text())
    if MlflowClient(tracking_uri=t['tracking_uri']).get_run(t['run_id']).info.status != 'FINISHED':
        raise ValueError('CPU MLflow not FINISHED')
    with sqlite3.connect(BASE/'mlflow.db') as source, sqlite3.connect(OUT/'mlflow-snapshot.db') as target:
        source.backup(target)
    backup(OUT/'mlflow-snapshot.db'); backup(OUT/'resources.json')
    proof = dict(status='VERIFIED_COMPLETE_CPU_ONLY', resources=resources, cases=70,
        policies=6, combined_settings=60, independent_case_backups_match=True,
        summary_rebuilt_from_case_records=True, producing_pins_match=True,
        mlflow=t, mlflow_status='FINISHED', result_sha256=sha(OUT/'result.json'),
        policy_deployed=False, model_calls=0, optimizer_updates=0, ct_voxel_reads=0)
    text = ['# Terminal24k: secondary attached-voxel clipping results', '',
        'Six additional prospectively frozen CPU policies, reusing the primary study’s exact native codes. '
        'Combined search:60 settings; all70 exposed development cases retained. No additional model pass, CT voxel read or training update.', '',
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


def main():
    request = verify_request()
    while not PARENT_PROOF.exists():
        safety()
        resource = PRIMARY/'resources.json'
        if resource.exists() and not json.loads(resource.read_text())['success']:
            raise ValueError('Primary failed; no secondary or retry')
        time.sleep(2)
    if json.loads(PARENT_PROOF.read_text())['status'] != 'VERIFIED_COMPLETE':
        raise ValueError('Primary closeout did not pass')
    safety()
    available = int(request['deadline_unix']-time.time()-120)
    if available < 300:
        raise ValueError('Original budget insufficient for secondary CPU qualification')
    seconds = min(1200, available)
    write(OUT/'parent-binding.json', dict(primary_result_sha256=sha(PRIMARY/'result.json'),
        primary_closeout_sha256=sha(PARENT_PROOF), worker_deadline_unix=time.time()+seconds))
    backup(OUT/'parent-binding.json'); backup(REQUEST)
    from src.operations.mac_teacher_supervision_v3 import run
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    ok = run([sys.executable,str(Path(__file__).resolve()),'--cpu-worker'],OUT,
             seconds=seconds,rss_bytes=4*1024**3,tick=safety,env=env)
    if not ok:
        if (OUT/'tracking.json').exists():
            from mlflow import MlflowClient
            t=json.loads((OUT/'tracking.json').read_text())
            MlflowClient(tracking_uri=t['tracking_uri']).set_terminated(t['run_id'],status='FAILED')
        backup(OUT/'resources.json')
        raise ValueError('CPU screen stopped; preserve evidence, no retry')
    finish_report()


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cpu-worker',action='store_true');a=p.parse_args()
    try:
        worker() if a.cpu_worker else main()
    except Exception as exc:
        # Supervisor and worker have distinct additive failure receipts.
        path=OUT/('worker-failure.json' if a.cpu_worker else 'failure.json')
        write(path,dict(status='SECONDARY_STOPPED_NO_RETRY',reason=repr(exc)))
        raise
