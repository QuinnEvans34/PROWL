"""Post-run analysis of saved metrics only; no inference, data replay or training."""
import json
from pathlib import Path
import sys
from collections import defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.backfill_full_runs_mlflow import summarize
from src.training.experiment_config import sha256
from src.data.source_inventory_records import require
RUN=Path('E:/PROWL/artifacts/pants_only_ema_72k_20261013')
SETUP=Path('E:/PROWL/readiness/pants-ema-72k-20261013-a01')
OUT=Path('E:/PROWL/readiness/pants-ema-review-20261016-a01')

def compare(left,right,minimum):
    a={r['case_id']:r['metrics'] for r in left};b={r['case_id']:r['metrics'] for r in right}
    require(len(a)==len(left)==len(b)==len(right) and a.keys()==b.keys(),'Duplicate or mismatched cases')
    for n in a:
        for key in ('reference_positive','reference_components','target_volume_mm3','size_band'):
            require(a[n][key]==b[n][key],'Reference changed')
        for organ in ('lesion','pancreas'):require(a[n][organ]['target_voxels']==b[n][organ]['target_voxels'],'Reference voxels changed')
    pos=sorted(n for n in a if a[n]['reference_positive']);empty=sorted(set(a)-set(pos))
    require(pos and empty,'Both groups required')
    vectors=dict(dice=[b[n]['lesion']['dice']-a[n]['lesion']['dice'] for n in pos],
        detection=[int(b[n]['case_detected'])-int(a[n]['case_detected']) for n in pos],
        false_alarm=[int(b[n]['false_alarm_any'])-int(a[n]['false_alarm_any']) for n in empty],
        pancreas=[b[n]['pancreas']['dice']-a[n]['pancreas']['dice'] for n in sorted(a)])
    rng=np.random.default_rng(20261013);stats={}
    for key,values in vectors.items():
        v=np.asarray(values);require(np.isfinite(v).all(),'Nonfinite metric')
        draws=v[rng.integers(len(v),size=(10000,len(v)))].mean(axis=1)
        stats[key]=dict(difference=float(v.mean()),ci95=np.quantile(draws,[.025,.975]).tolist())
    guards=dict(detection=stats['detection']['difference']>=-.03,false_alarm=stats['false_alarm']['difference']<=.03,
        pancreas=stats['pancreas']['difference']>=-.02)
    accepted=all(guards.values()) and stats['dice']['difference']>=minimum and stats['dice']['ci95'][0]>0
    rejected=not all(guards.values()) or stats['dice']['ci95'][1]<minimum
    return dict(decision='accepted' if accepted else 'rejected' if rejected else 'inconclusive',
        null_hypothesis='rejected' if stats['dice']['ci95'][0]>0 else 'not_rejected',metrics=stats,guardrails=guards,
        practical_minimum=minimum,seed=20261013,resamples=10000,positive_cases=len(pos),empty_cases=len(empty),
        positive_improved=sum(v>0 for v in vectors['dice']),positive_worsened=sum(v<0 for v in vectors['dice']))

def main():
    history=RUN/'execution/history.jsonl';events=[json.loads(s) for s in history.read_text().splitlines()]
    require(events[-1]['event']=='completed' and events[-1]['step']==72000,'Not complete')
    updates=[r for r in events if r['event']=='update'];require([r['step'] for r in updates]==list(range(1,72001)),'Missing updates')
    resource=json.loads((SETUP/'training-resources.json').read_text());require(resource['workers_reaped'],'Unreaped worker')
    receipt=json.loads((SETUP/'ready.json').read_text());require(sha256(SETUP/'ready.json')=='8e20da25466bf1fe27205fdbb89633dbe02680a552c61d828cebdf390fb3fee6','Receipt changed')
    mismatch=[p for p,h in receipt['file_sha256'].items() if sha256(p)!=h];require(not mismatch,'Frozen evidence changed: '+str(mismatch))
    backup=Path('C:/Users/quinn/PROWL-Backups/pants_only_ema_72k_20261013');checkpoints={}
    for path in (RUN/'execution').glob('*.pt'):
        pin=sha256(path);require(pin==sha256(backup/path.name),'Independent checkpoint differs');checkpoints[path.name]=pin
    require(sha256(history)==sha256(backup/'history.jsonl'),'Independent journal differs')
    control=json.loads((RUN/'input-control.json').read_text());names=set(control['validation']);require(len(names)==70,'Wrong cohort')
    groups=defaultdict(list);completed=[]
    for row in events:
        if row['event']=='native_case':groups[(row['step'],row['variant'])].append(row)
        if row['event']=='native_completed':completed.append((row['step'],row['variant']))
    keys={(s,v) for s in (24000,36000,48000,60000,72000) for v in ('raw','ema')}
    require(set(groups)==keys and set(completed)==keys and len(completed)==10,'Missing/duplicate native evaluations')
    summaries={}
    for (step,variant),rows in sorted(groups.items()):
        require(len(rows)==70 and {r['case_id'] for r in rows}==names,'Native cohort mismatch')
        stats=summarize(rows,native=True);bands={}
        for band in ('small','medium','large'):
            selected=[r['metrics'] for r in rows if r['metrics']['reference_positive'] and r['metrics']['size_band']==band]
            if selected:bands[band]=dict(n=len(selected),dice=float(np.mean([m['lesion']['dice'] for m in selected])),detected=sum(m['case_detected'] for m in selected))
        summaries[f'{step}/{variant}']=dict(**stats,size_bands=bands)
    validation=[r for r in events if r['event']=='validation']
    best={v:max((r for r in validation if r['variant']==v),key=lambda r:r['lesion_positive_macro_dice']) for v in ('raw','ema')}
    loss={str(s):float(np.mean([r['loss'] for r in updates[s-2000:s]])) for s in (24000,36000,48000,60000,72000)}
    result=dict(history_sha256=sha256(history),frozen_pins_verified=len(receipt['file_sha256']),checkpoint_sha256=checkpoints,
        resources=resource,elapsed_seconds=events[-1]['elapsed_seconds'],end_utc_ms=events[-1]['utc_ms'],native=summaries,
        duration=compare(groups[24000,'raw'],groups[72000,'raw'],.02),ema=compare(groups[72000,'raw'],groups[72000,'ema'],.01),
        tensor_best=best,mean_training_loss_last_2000_updates=loss,
        inference_calls=0,test_reads=0,scope='Exploratory reused development; provided ROI; single seed; SuPreM membership unverified',
        bootstrap_unit='Paired PanTS case ID, treated as patient unit under frozen cohort; repeated-patient independence not separately verified')
    OUT.mkdir(exist_ok=False)
    (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
