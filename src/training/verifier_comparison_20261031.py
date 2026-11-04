"""Matched final comparison after model and calibration lock; no tuning API."""
import numpy as np
from src.training.verifier_decisions_20261031 import metrics

def compare(patients,scores,threshold,*,seed=20261023,replicates=10000):
    if not patients or any(r['role']!='development' for r in patients) or len({r['case_id'] for r in patients})!=len(patients):raise ValueError('Unique development records required')
    baseline=metrics(patients,scores,0.);selected=metrics(patients,scores,threshold)
    negative=[r for r in patients if not r['annotated_voxels']]
    missing=not negative or not baseline['positive_patients'] or not baseline['small_total']
    differences=np.array([float(bool(r['candidates']))-float(any(scores[(r['case_id'],c['component_id'])]>=threshold for c in r['candidates'])) for r in negative])
    if not len(differences):return dict(status='INCONCLUSIVE',hypothesis='NOT_ESTIMABLE',reason='No negative patients',baseline=baseline,selected=selected)
    rng=np.random.default_rng(seed);means=differences[rng.integers(0,len(differences),size=(replicates,len(differences)))].mean(1)
    interval=np.percentile(means,[2.5,97.5]).tolist();delta=float(differences.mean())
    guards=dict(no_additional_missed_patient=selected['missed_positive_patients']<=baseline['missed_positive_patients'],
        small_component_detection_preserved=selected['small_hits']>=baseline['small_hits'] if baseline['small_total'] else None,
        positive_dice_preserved=selected['positive_dice']>=baseline['positive_dice']-.01 if baseline['positive_patients'] else None,
        negative_voxel_burden_not_increased=selected['negative_voxels']<=baseline['negative_voxels'])
    reject=interval[0]>0
    if missing:status='INCONCLUSIVE'
    elif all(guards.values()) and reject and delta>=.10:status='PRACTICAL_SUPPORT'
    elif not all(guards.values()) or interval[1]<.10:status='PRACTICAL_REJECTION'
    else:status='INCONCLUSIVE'
    return dict(status=status,hypothesis='REJECT_H0' if reject else 'FAIL_TO_REJECT_H0',alarm_reduction=delta,alarm_reduction_ci95=interval,
        guards=guards,baseline=baseline,selected=selected,bootstrap_seed=seed,bootstrap_replicates=replicates,
        scope='Exploratory reused development cohort; not clinical safety or statistical noninferiority')
