"""Post-run audit and fixed native comparison; no training, retries or test reads."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.experiment_config import sha256
from src.data.source_inventory_records import require
from scripts.diagnostics.compare_panorama_positive import compare

SETUP=Path('E:/PROWL/readiness/panorama-positive-run-20261012-a01')
RUN=Path('E:/PROWL/artifacts/pants_plus_expert_panorama_dicefocal_24k_20261012')
PARENT=Path('E:/PROWL/artifacts/pants_course_reference_dicefocal_24k_20261011')
OUT=Path('E:/PROWL/readiness/panorama-positive-review-20261013-a01')
BACKUP=Path('C:/Users/quinn/PROWL-Backups')/RUN.name


def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def save(p,r):
    with Path(p).open('x') as f:json.dump(r,f,indent=2,allow_nan=False)


def tensor_summary(rows):
    p=[r['metrics'] for r in rows if r['metrics']['lesion']['target_voxels']]
    e=[r['metrics'] for r in rows if not r['metrics']['lesion']['target_voxels']]
    return dict(positive_cases=len(p),empty_cases=len(e),lesion_dice=sum(r['lesion']['dice'] for r in p)/len(p),
        detected=sum(r['lesion']['true_positive']>0 for r in p),alarms=sum(r['lesion']['predicted_voxels']>0 for r in e),
        pancreas_dice=sum(r['metrics']['pancreas']['dice'] for r in rows)/len(rows))


def audit():
    receipt=SETUP/'ready.json'
    require(sha256(receipt)=='604d19b280e90dcf1ca3c3409bfb13a6820592dd192308a410fad38653651233','Receipt changed')
    ready=read(receipt);changed=[p for p,h in ready['file_sha256'].items() if sha256(p)!=h]
    require(not changed,'Frozen producing files changed: '+str(changed))
    history=lines(RUN/'execution/history.jsonl');updates=[r for r in history if r['event']=='update']
    require([r['step'] for r in updates]==list(range(1,24001)) and history[-1]['event']=='completed','Incomplete/noncontiguous training')
    selected=[r for r in history if r['event']=='validation']
    require([r['step'] for r in selected]==list(range(2000,24001,2000)),'Selection cadence differs')
    best=max(selected,key=lambda r:r['lesion_positive_macro_dice'])
    control=history[0]['identity']['control'];dev=set(control['validation'])
    require(len(dev)==70 and not dev.intersection(control['excluded_development']),'Excluded development used')
    checkpoints={}
    for name in ('initial.pt','best.pt','last.pt','step-008000.pt','step-024000.pt'):
        path=RUN/'execution'/name;pin=sha256(path)
        require(sha256(BACKUP/name)==pin,'Independent checkpoint mismatch: '+name)
        checkpoints[name]=pin
    require(sha256(RUN/'execution/history.jsonl')==sha256(BACKUP/'history.jsonl'),'Final journal backup mismatch')
    groups={}
    for label,path in [('parent',PARENT),('mixed',RUN)]:
        buckets=defaultdict(list)
        for r in lines(path/'execution/history.jsonl'):
            if r['event']=='validation_case' and r['case_id'] in dev:buckets[r['step']].append(r)
        require(all(len(v)==70 and len({r['case_id'] for r in v})==70 for v in buckets.values()),'Missing/duplicate case metrics')
        groups[label]={str(k):tensor_summary(v) for k,v in buckets.items()}
    exposure=Counter(r['member_id'] for r in updates)
    source=Counter()
    classes=Counter();bins=defaultdict(list)
    for n,count in exposure.items():
        s='PANORAMA' if n.startswith('panorama:') else 'PanTS';source[s]+=count
        classes[control['target_states'][n]]+=count;bins[s].append(count)
    OUT.mkdir(exist_ok=False)
    result=dict(completed=True,updates=24000,best_step=best['step'],best_tensor_dice=best['lesion_positive_macro_dice'],
        final_tensor_dice=selected[-1]['lesion_positive_macro_dice'],last_update_elapsed_seconds=updates[-1]['elapsed_seconds'],
        checkpoints=checkpoints,all_frozen_pins_match=True,independent_backups_match=True,
        original_run=str(RUN),history_sha256=sha256(RUN/'execution/history.jsonl'),matched_tensor_curves=groups,
        training_exposures=dict(source=source,target=classes,per_source_ranges={k:[min(v),max(v)] for k,v in bins.items()}),
        test_reads=0,optimizer_updates_during_review=0,receipt_sha256=sha256(receipt))
    save(OUT/'audit.json',result)
    print(json.dumps(result,indent=2),flush=True)


def native_summary(rows):
    pos=[r['metrics'] for r in rows if r['metrics']['reference_positive']]
    empty=[r['metrics'] for r in rows if not r['metrics']['reference_positive']]
    return dict(lesion_dice=sum(r['lesion']['dice'] for r in pos)/len(pos),detected=sum(r['case_detected'] for r in pos),
        positive=len(pos),alarms=sum(r['false_alarm_any'] for r in empty),empty=len(empty),
        pancreas_dice=sum(r['metrics']['pancreas']['dice'] for r in rows)/len(rows),
        components_detected=sum(r['detected_components'] for r in pos),components_total=sum(r['reference_components'] for r in pos),
        empty_predicted_volume_mm3=sum(r['predicted_volume_mm3'] for r in empty),
        empty_alerts_50mm3=sum(r['case_alert_50mm3'] for r in empty))


def finish():
    from scripts.diagnostics.compare_panorama_positive import compare
    parent=read(SETUP/'parent-reduced-comparison.json');best=read(OUT/'native-best/report.json');final=read(OUT/'native-final/report.json')
    audit_result=read(OUT/'audit.json')
    for label,r in [('best',best),('final',final)]:
        require(r['complete_development_cohort'] and len(r['cases'])==70 and {c['case_id'] for c in r['cases']}==set(parent['development']), 'Native cohort mismatch')
        require(r['step']==(audit_result['best_step'] if label=='best' else 24000),'Wrong checkpoint')
        require(read(OUT/('native-'+label)/'resources.json')['workers_reaped'],'Evaluator remains active')
    primary=compare(parent['reports']['best']['cases'],best['cases'])
    secondary=compare(parent['reports']['024000']['cases'],final['cases'])
    a={r['case_id']:r['metrics'] for r in parent['reports']['best']['cases']};b={r['case_id']:r['metrics'] for r in best['cases']}
    pairs=[]
    for n in a:
        pairs.append(dict(case_id=n,size_band=a[n]['size_band'],reference_positive=a[n]['reference_positive'],
            control_dice=a[n]['lesion']['dice'],mixed_dice=b[n]['lesion']['dice'],
            dice_delta=b[n]['lesion']['dice']-a[n]['lesion']['dice'] if a[n]['reference_positive'] else None,
            control_detected=a[n]['case_detected'],mixed_detected=b[n]['case_detected'],
            control_alarm=a[n]['false_alarm_any'],mixed_alarm=b[n]['false_alarm_any']))
    positive=[r for r in pairs if r['reference_positive']]
    result=dict(primary=primary,mandatory_final_secondary=secondary,
        summaries={'parent_best':native_summary(parent['reports']['best']['cases']),'mixed_best':native_summary(best['cases']),
            'parent_final':native_summary(parent['reports']['024000']['cases']),'mixed_final':native_summary(final['cases'])},
        positive_cases_improved=sum(r['dice_delta']>0 for r in positive),positive_cases_worsened=sum(r['dice_delta']<0 for r in positive),
        complementarity=dict(both_detected=sum(r['control_detected'] and r['mixed_detected'] for r in positive),
            parent_only=sum(r['control_detected'] and not r['mixed_detected'] for r in positive),
            mixed_only=sum(not r['control_detected'] and r['mixed_detected'] for r in positive),
            both_missed=sum(not r['control_detected'] and not r['mixed_detected'] for r in positive)),
        size_bands={band:dict(n=len(rs),control_dice=sum(r['control_dice'] for r in rs)/len(rs),mixed_dice=sum(r['mixed_dice'] for r in rs)/len(rs),
            control_detected=sum(r['control_detected'] for r in rs),mixed_detected=sum(r['mixed_detected'] for r in rs))
            for band in ('small','medium','large') if (rs:=[r for r in positive if r['size_band']==band])},
        case_pairs=pairs,scope='exploratory_reused_development_not_independent_benchmark',
        evidence_sha256={str(p):sha256(p) for p in [SETUP/'parent-reduced-comparison.json',OUT/'native-best/report.json',OUT/'native-final/report.json',OUT/'audit.json']})
    save(OUT/'results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('case_pairs','evidence_sha256')},indent=2),flush=True)


def queue():
    reviewed=read(OUT/'audit.json')
    with (OUT/'evaluation-queue.jsonl').open('x') as journal:
        def event(**r):
            r['utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());journal.write(json.dumps(r)+'\n');journal.flush();print(json.dumps(r),flush=True)
        try:
            for label,name in [('best','best.pt'),('final','step-024000.pt')]:
                event(stage=label,status='started')
                subprocess.run([sys.executable,str(ROOT/'scripts/diagnostics/evaluate_pants_native.py'),
                    '--experiment',str(SETUP/'experiment.yaml'),'--checkpoint',str(RUN/'execution'/name),
                    '--sha256',reviewed['checkpoints'][name],'--output',str(OUT/('native-'+label))],cwd=ROOT,check=True)
                event(stage=label,status='completed')
            finish();event(stage='review',status='completed')
        except BaseException as exc:event(stage='review',status='failed',error=str(exc));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['audit','queue','finish']);a=parser.parse_args()
    globals()[a.stage]()
