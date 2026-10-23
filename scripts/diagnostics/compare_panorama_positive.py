"""Paired native development review for the prospectively amended PANORAMA addition."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.source_inventory_records import require
from src.training.experiment_config import sha256


def compare(control,treatment):
    a={r['case_id']:r['metrics'] for r in control};b={r['case_id']:r['metrics'] for r in treatment}
    require(len(a)==len(control)==len(b)==len(treatment) and a.keys()==b.keys(), 'Comparison cohorts differ or duplicate')
    for n in a:
        require(a[n]['target_volume_mm3']==b[n]['target_volume_mm3'] and
            a[n]['reference_components']==b[n]['reference_components'] and
            a[n]['reference_positive']==b[n]['reference_positive'], 'Reference definition changed')
    pos=sorted(n for n in a if a[n]['reference_positive']);empty=sorted(n for n in a if not a[n]['reference_positive'])
    require(pos and empty,'Both reference groups required')
    vectors=dict(dice=np.array([b[n]['lesion']['dice']-a[n]['lesion']['dice'] for n in pos]),
        detection=np.array([int(b[n]['case_detected'])-int(a[n]['case_detected']) for n in pos]),
        false_alarm=np.array([int(b[n]['false_alarm_any'])-int(a[n]['false_alarm_any']) for n in empty]),
        pancreas=np.array([b[n]['pancreas']['dice']-a[n]['pancreas']['dice'] for n in sorted(a)]))
    require(all(np.isfinite(v).all() for v in vectors.values()), 'Nonfinite comparison')
    rng=np.random.default_rng(20261012);stats={}
    for key,v in vectors.items():
        draws=v[rng.integers(len(v),size=(10000,len(v)))].mean(axis=1)
        stats[key]=dict(difference=float(v.mean()),ci95=np.quantile(draws,[.025,.975]).tolist())
    guardrails=stats['detection']['difference']>=-.03 and stats['false_alarm']['difference']<=.03 and stats['pancreas']['difference']>=-.02
    accepted=stats['dice']['difference']>=.02 and stats['dice']['ci95'][0]>0 and guardrails
    rejected=not guardrails or stats['dice']['ci95'][1]<.02
    return dict(status='accepted' if accepted else 'rejected' if rejected else 'inconclusive',
        null_evidence='paired_interval_excludes_nonpositive_gain' if stats['dice']['ci95'][0]>0 else 'null_not_rejected_by_interval',
        positive_cases=len(pos),reference_empty_cases=len(empty),metrics=stats,
        interpretation='Exploratory development intervention; point guardrails, not statistical noninferiority or clean generalization',
        seed=20261012,bootstrap_resamples=10000)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','best','final','history','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();parent=json.loads(args.parent.read_text());best=json.loads(args.best.read_text());final=json.loads(args.final.read_text())
    events=[json.loads(s) for s in args.history.read_text().splitlines()]
    require(events[-1]['event']=='completed' and events[-1]['step']==24000,'Complete treatment horizon required')
    validations=[r for r in events if r['event']=='validation']
    require([r['step'] for r in validations]==list(range(2000,24001,2000)),'Selection opportunity mismatch')
    selected=max(validations,key=lambda r:r['lesion_positive_macro_dice'])['step']
    require(best['step']==selected and final['step']==24000,'Checkpoint selection mismatch')
    for r in (best,final):
        require(r['complete_development_cohort'] and r['test_reads']==r['optimizer_updates']==0 and
            len(r['cases'])==70 and {c['case_id'] for c in r['cases']}==set(parent['development']), 'Wrong native cohort')
    result=dict(primary=compare(parent['reports']['best']['cases'],best['cases']),
        mandatory_secondary_not_alternate_acceptance=compare(parent['reports']['024000']['cases'],final['cases']),
        input_sha256={str(f):sha256(f) for f in (args.parent,args.best,args.final,args.history)})
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps(result['primary'],indent=2))


if __name__=='__main__':main()
