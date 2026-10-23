"""Fixed report snapshot and CPU-only error review; no CT/mask or GPU access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.native_error_review_v1 import POLICY,summarize,compare,require

BASE=Path('E:/PROWL/readiness/distillation-error-review-20261023-a01')
RUN=Path('E:/PROWL/artifacts/pants_varied_focus_24k_20261022')
PARENT=Path('E:/PROWL/artifacts/pants_pancreas_region_24k_20261019')
HISTORICAL=Path('E:/PROWL/artifacts/pants_only_augmented_views_24k_win_20261017')
PREP=Path('E:/PROWL/readiness/distillation-preparation-20261023-a01/preparation.json')
STEPS=list(range(2000,10001,2000))  # Intentionally fixed at the last complete validation when review began.


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False)


def report_text(data):
    lines=['# Existing native-error patterns before distillation','',
        'Snapshot: current complete validations through **10,000 updates**. No interim hypothesis verdict. Twelve-thousand validation was incomplete when the scope was fixed.','',
        '| Checkpoint | Positive Dice | Recall | Precision* | Detected | Empty alarms | Empty mL |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for title,key in [('Varied views at 10k','current_10k'),('Same-region parent at 10k','parent_10k'),
        ('Varied views best so far','current_best_so_far'),('Parent selected 22k','parent_selected'),('Historical augmented selected 18k','historical_selected')]:
        s=data['summaries'][key]
        lines.append(f"| {title} | {s['positive_macro_dice']:.6f} | {s['positive_macro_recall']:.4f} | {s['positive_macro_precision']:.4f} | {s['detected']}/36 | {s['negative_alarms']}/34 | {s['negative_predicted_mL']:.3f} |")
    lines+=['','*Precision averages only positive patients with nonempty predictions; exact denominators are in JSON. Recall and Dice include every positive patient and all misses.',
        '', 'The historical pipeline differs in representation and checkpoint-selection method. Its score is a reference, not a matched KD control.',
        '', '## Current 10k size groups','', '| Total annotated patient volume | Cases | Dice | Recall | Precision | Missed cases | >50% annotation missed | >50% prediction extra | ≥2× target volume |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for b in ('small','medium','large'):
        s=data['summaries']['current_10k']['bands'][b];f=s['flags']
        lines.append(f"| {b} | {s['cases']} | {s['positive_macro_dice']:.4f} | {s['positive_macro_recall']:.4f} | {s['positive_macro_precision']:.4f} | {s['complete_misses']} | {f['more_than_half_annotation_missed']} | {f['more_than_half_prediction_extra']} | {f['at_least_double_target_volume']} |")
    lines+=['','Small <1 mL; medium 1–10 mL inclusive; large >10 mL. These are total patient lesion volumes, not individual lesion-component sizes. Flags overlap.',
        '', '## Exclusive positive-case error patterns','', '| Pattern | Current 10k | Parent 10k | Parent selected | Historical selected |',
        '| --- | ---: | ---: | ---: | ---: |']
    keys=['current_10k','parent_10k','parent_selected','historical_selected']
    patterns=sorted(set(k for key in keys for k in data['summaries'][key]['patterns'] if not k.startswith('negative_')))
    for pattern in patterns:lines.append('| '+pattern+' | '+' | '.join(str(data['summaries'][key]['patterns'].get(pattern,0)) for key in keys)+' |')
    lines+=['', 'Missed-voxel versus extra-voxel dominance compares FN with FP. It does not localize boundary error; a complete miss can coexist with predictions elsewhere.',
        '', '## Same-step paired diagnostic (parent 10k → current 10k)','']
    for key,stat in data['same_step_diagnostic']['metrics'].items():
        if stat.get('estimate') is not None:lines.append(f"- {key}: {stat['estimate']:+.6f}; paired 95% interval {stat['ci95']}; n={stat.get('n','component-specific')}.")
    lines+=['','No final H0/adoption decision: the successor has not completed its planned horizon. These are exploratory checkpoint-conditional intervals, not sequential tests or clinical noninferiority.',
        '', '## Current completed curve','', '| Updates | Dice | Recall | Detected | Empty alarms | Empty mL |','| ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in data['current_curve']:lines.append(f"| {s['step']} | {s['positive_macro_dice']:.6f} | {s['positive_macro_recall']:.4f} | {s['detected']}/36 | {s['negative_alarms']}/34 | {s['negative_predicted_mL']:.3f} |")
    lines+=['','## Evidence limits','',
        '- No CT, mask, prediction-volume, test-set, model-weight or GPU reads/execution in this analysis.',
        '- Aggregate reports cannot locate contour shifts, distinguish false components from splits, or establish calibrated confidence.',
        '- Component-level <1 mL recall cannot be recovered from current per-patient totals. The new comparator requires bound component sidecars; missing evidence blocks a practical acceptance.',
        '- All patient-level records and paired deltas are retained in analysis.json; no zero-Dice case is omitted.',
        '- Counts describe annotated-negative cases, not a clinical declaration of a healthy pancreas.']
    return '\n'.join(lines)+'\n'


def worker(attempt):
    out=BASE/('analysis' if attempt=='01' else 'analysis-'+attempt);snapshot=out/'snapshots';snapshot.mkdir();pins={}
    def capture(path,name):
        raw=Path(path).read_bytes();pin=hashlib.sha256(raw).hexdigest()
        with (snapshot/name).open('xb') as stream:stream.write(raw)
        pins[str(path)]=pin;return json.loads(raw)
    control=capture(RUN/'input-control.json','input-control.json');ids=control['validation']
    require(len(ids)==70 and not set(ids)&set(control['train']),'Development role separation')
    prep=capture(PREP,'teacher-preparation.json')
    current={s:capture(RUN/f'execution/native-{s:06d}.json',f'current-{s:06d}.json') for s in STEPS}
    parent={s:capture(PARENT/f'execution/native-{s:06d}.json',f'parent-{s:06d}.json') for s in range(2000,24001,2000)}
    historical=capture(HISTORICAL/'execution/native-selected.json','historical-selected.json')
    curve=[summarize(current[s],ids) for s in STEPS];parent_curve=[summarize(parent[s],ids) for s in sorted(parent)]
    best_current=max(curve,key=lambda s:s['positive_macro_dice']);best_parent=max(parent_curve,key=lambda s:s['positive_macro_dice'])
    summaries=dict(current_10k=curve[-1],parent_10k=next(s for s in parent_curve if s['step']==10000),
        current_best_so_far=best_current,parent_selected=best_parent,historical_selected=summarize(historical,ids))
    same=compare(parent[10000],current[10000],ids)
    data=dict(scope='read_only_interim_error_review',captured_utc=datetime.now(timezone.utc).isoformat(),
        current_horizon_reviewed=10000,source_pins=pins,summaries=summaries,current_curve=curve,parent_curve=parent_curve,
        same_step_diagnostic=same,test_reads=0,CT_reads=0,mask_reads=0,inference_calls=0,optimizer_updates=0)
    write(out/'analysis.json',data)
    with (out/'report.md').open('x',encoding='utf-8') as stream:stream.write(report_text(data))
    write(out/'cohort.json',dict(role='validation',case_ids=ids,positive_cases=36,source_control_sha256=pins[str(RUN/'input-control.json')]))
    checklist=[]
    by_name={r['case_id']:r for r in prep['pilot']}
    for name in prep['pilot_order']:
        row=by_name[name]
        checklist.append(dict(case_id=name,role='train',selection_reasons=row['reasons'],positive=row['positive'],
            preparation_sha256=pins[str(PREP)],reviewed=False,figure_sha256=None,reviewer=None,
            alignment=None,field_coverage=None,boundary_detail=None,all_components_reviewed=None,
            high_probability_contradictions=None,low_probability_true_lesions=None,
            eligible_KD_positive_voxels=None,teacher_usefulness=None,resource_checks=None,findings=[],decision='pending'))
    write(out/'pilot-review-template.json',dict(status='PENDING_NOT_VISUALLY_REVIEWED',accepted=False,
        cases=checklist,limits=prep['limits'],current_pilot_not_run=True,new_CT_reads=0))
    arm=dict(run_directory=None,receipt=None,configuration=None,input_control=None,result=None,resources=None,mlflow_run_id=None,
        components=dict(selected=None,terminal=None))
    write(out/'comparison-template.json',dict(status='UNBOUND_NOT_READY',scope='teacher_assisted_exploratory',policy=POLICY,
        cohort=dict(path=str(out/'cohort.json'),sha256=sha(out/'cohort.json')),matching_review=None,
        control=arm,treatment=arm,notes='Bind after current-run review; no launch authority. Missing component sidecars cannot be passed using small-patient averages.'))
    require(all(sha(path)==pin for path,pin in pins.items()),'Source report changed during snapshot')
    write(out/'result.json',dict(success=True,report_snapshots=len(current)+len(parent)+1,pilot_cases=len(checklist),
        current_steps=STEPS,source_pins_unchanged=True,new_CT_reads=0,scientific_updates=0))
    print(json.dumps(dict(summaries={k:{f:v[f] for f in ('step','positive_macro_dice','positive_macro_recall','positive_macro_precision','detected','negative_alarms','negative_predicted_mL','patterns','flags')} for k,v in summaries.items()},same_step={k:v for k,v in same['metrics'].items()})))


def supervise(stage,attempt):
    from src.operations.full_training_platform import watch_windows
    BASE.mkdir(exist_ok=True);out=BASE/(('tests-'+attempt) if stage=='tests' else ('analysis' if attempt=='01' else 'analysis-'+attempt));out.mkdir(exist_ok=False)
    paths=[Path(__file__),ROOT/'src/training/native_error_review_v1.py',ROOT/'scripts/diagnostics/compare_native_distillation.py',
        ROOT/'tests/test_native_error_review_v1.py']
    write(out/'request.json',dict(scope='CPU report-only, no clinical inference',seconds=180,rss_bytes=2*1024**3,pins={str(p):sha(p) for p in paths}))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PROWL_REPORT_REVIEW='1')
    command=[sys.executable,__file__,'--worker','--attempt',attempt] if stage=='analysis' else [sys.executable,'-m','pytest','-q','-p','no:cacheprovider',str(paths[-1]),'--junitxml',str(out/'tests.xml')]
    success=False;error=None
    with (out/'worker.log').open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        try:watch_windows(process,seconds=180,rss_bytes=2*1024**3);success=True
        except Exception as exc:error=repr(exc)
        finally:
            report=dict(getattr(process,'duration_resources',{}),success=success,error=error,exit_code=process.returncode)
            write(out/'resources.json',report);print(json.dumps(report))
    if not success:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--tests',action='store_true');group.add_argument('--run',action='store_true');group.add_argument('--worker',action='store_true')
    parser.add_argument('--attempt',default='01')
    args=parser.parse_args()
    require(len(args.attempt)==2 and args.attempt.isascii() and args.attempt.isdecimal(),'Two-digit explicit attempt required')
    if args.worker:
        require(os.environ.get('PROWL_REPORT_REVIEW')=='1','Supervisor required');worker(args.attempt)
    else:supervise('tests' if args.tests else 'analysis',args.attempt)
