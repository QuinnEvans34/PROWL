"""Completed-run retrospective using saved native reports only; no inference."""
import json
import sqlite3
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.review_region_results_timing import read,events,summary,timing,compare as validate_compare
from src.training.experiment_config import sha256

RUN=Path('E:/PROWL/artifacts/pants_varied_focus_24k_20261022')
CONTROL=Path('E:/PROWL/artifacts/pants_pancreas_region_24k_20261019')
HISTORICAL=Path('E:/PROWL/artifacts/pants_only_augmented_views_24k_win_20261017')
OUT=Path('E:/PROWL/readiness/varied-focus-review-20261025-a01')
SETUP=Path('E:/PROWL/readiness/varied-deterministic-20261022-a02')


def compare(a,b):
    # Reuse prior native-target/identity admission, but NOT its old seed/guards.
    result=validate_compare(a,b)
    aa={r['case_id']:r['metrics'] for r in a};bb={r['case_id']:r['metrics'] for r in b}
    names=sorted(n for n in aa if aa[n]['reference_positive'])
    delta=np.array([bb[n]['lesion']['dice']-aa[n]['lesion']['dice'] for n in names])
    rng=np.random.default_rng(20261022)
    ci=np.quantile(delta[rng.integers(len(names),size=(10000,len(names)))].mean(1),[.025,.975]).tolist()
    ca,cb=result['control'],result['treatment']
    guards=dict(detection=(cb['detected']-ca['detected'])/ca['positive']>=-.03,
        empty_alarm=(cb['alarms']-ca['alarms'])/ca['empty']<=.03,
        pancreas=cb['pancreas']-ca['pancreas']>=-.02,
        empty_voxel_burden=cb['empty_voxels']<=ca['empty_voxels'],
        positive_macro_recall=cb['positive_macro_recall']-ca['positive_macro_recall']>=-.03)
    accepted=float(delta.mean())>=.02 and ci[0]>0 and all(guards.values())
    rejected=not all(guards.values()) or ci[1]<.02
    result.update(ci95=ci,seed=20261022,guards=guards,
        null='reject' if ci[0]>0 else 'fail_to_reject',
        practical='accept' if accepted else 'reject' if rejected else 'inconclusive')
    for band,row in result['size_bands'].items():
        ns=[n for n in names if aa[n]['size_band']==band]
        for key,source in [('control',aa),('treatment',bb)]:
            row[key+'_recall']=float(np.mean([source[n]['lesion']['true_positive']/source[n]['lesion']['target_voxels'] for n in ns]))
    return result


def main():
    if OUT.exists():raise ValueError('Review already started; inspect rather than overwrite')
    from scripts.diagnostics.prepare_distillation import normal_parent_gate
    names=(RUN/'splits/development_ids.txt').read_text().split()
    completion=normal_parent_gate(names) # final70,12validations,backups,MLflow,reaping
    pins=read(SETUP/'ready.json')['pins']
    for path,pin in pins.items():
        if sha256(path)!=pin:raise ValueError('Producing pin changed: '+path)
    binding=read(SETUP/'parent-comparison.json')['pins']
    inputs=[];comparisons={}
    for endpoint,key in [('selected','primary'),('terminal','secondary')]:
        a=CONTROL/f'execution/native-{endpoint}.json';b=RUN/f'execution/native-{endpoint}.json'
        if str(a) not in binding and str(a).replace('/','\\') not in binding:raise ValueError('Parent binding absent')
        pin=binding.get(str(a),binding.get(str(a).replace('/','\\')))
        if sha256(a)!=pin:raise ValueError('Frozen parent report changed')
        comparisons[key]=compare(read(a)['cases'],read(b)['cases']);inputs += [a,b]
    history=events(RUN/'execution/history.jsonl');parent_history=events(CONTROL/'execution/history.jsonl')
    curve=[]
    for step in range(2000,24001,2000):
        path=RUN/f'execution/native-{step:06d}.json';inputs.append(path)
        curve.append(dict(step=step,**summary(read(path)['cases'])))
    counts={}
    for row in history:
        if row['event']!='update':continue
        view=row['input_view']['window'];kind=view['kind']
        v=counts.setdefault(kind,dict(updates=0,positive_updates=0,positive_without_lesion=0))
        v['updates']+=1
        if view.get('positive_case'):
            v['positive_updates']+=1
            v['positive_without_lesion']+=row['input_view']['augmentation']['class_counts'][2]==0
    times={name:timing(rows) for name,rows in [('current',history),('parent',parent_history)]}
    for value in times.values():value.pop('case_mean_seconds')
    historical=read(HISTORICAL/'execution/native-selected.json');inputs.append(HISTORICAL/'execution/native-selected.json')
    connection=sqlite3.connect('file:C:/Users/quinn/PROWL-Tracking/mlflow.db?mode=ro',uri=True)
    try:
        stored_losses=connection.execute("SELECT COUNT(*) FROM metrics WHERE run_uuid=? AND key='train/loss'",('a84c0a6ae0cb424ca182350425adc7aa',)).fetchone()[0]
    finally:connection.close()
    result=dict(completion=completion,**comparisons,curve=curve,timing=times,sampling=counts,
        historical_native_record=summary(historical['cases']),historical_step=historical['step'],
        all_producing_pins_verified=len(pins),normal_completion_backups_mlflow_verified=True,
        stored_mlflow_loss_points=stored_losses,
        scope='Exploratory selected-checkpoint paired development comparison; provided pancreas assistance; no independent test claim',
        evidence_sha256={str(p):sha256(p) for p in inputs+[RUN/'execution/history.jsonl',CONTROL/'execution/history.jsonl',SETUP/'ready.json',Path(__file__)]},
        review_ct_reads=0,review_inference_calls=0,review_optimizer_updates=0)
    OUT.mkdir()
    with (OUT/'results.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in result.items() if k not in ('evidence_sha256','curve')},indent=2))


if __name__=='__main__':main()
