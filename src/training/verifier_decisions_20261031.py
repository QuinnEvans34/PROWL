"""Frozen whole-component calibration rule; no development-driven tuning."""
import math
import numpy as np

def metrics(patients,scores,threshold):
    if not math.isfinite(threshold) or not 0<=threshold<=1:raise ValueError('Threshold')
    expected={(r['case_id'],c['component_id']) for r in patients for c in r['candidates']}
    if set(scores)!=expected or any(not math.isfinite(v) or not 0<=v<=1 for v in scores.values()):raise ValueError('Score membership/range')
    positives=[];negative=[];small_hits=small_total=missed=burden=0
    for r in patients:
        kept=[c for c in r['candidates'] if scores[(r['case_id'],c['component_id'])]>=threshold]
        pred=sum(c['voxels'] for c in kept);intersection=sum(c['overlap_voxels'] for c in kept);truth=r['annotated_voxels']
        if truth:
            positives.append(2*intersection/(pred+truth));missed+=not bool(intersection)
        else:negative.append(bool(pred));burden+=pred
        hits={i for c in kept for i in c['gt_hits']}
        for c in r['gt_components']:
            if c['volume_ml']<1:small_total+=1;small_hits+=c['component_id'] in hits
    return dict(positive_dice=float(np.mean(positives)) if positives else None,missed_positive_patients=int(missed),
        negative_alarm_fraction=float(np.mean(negative)) if negative else None,negative_voxels=burden,
        small_hits=small_hits,small_total=small_total,positive_patients=len(positives),negative_patients=len(negative))

def calibrate(patients,scores):
    if not patients or any(r['role']!='verifier_calibration' for r in patients):raise ValueError('Calibration-only role required')
    baseline=metrics(patients,scores,0.)
    if not baseline['positive_patients'] or not baseline['negative_patients'] or not baseline['small_total']:
        return dict(status='NONESTIMABLE_GUARDS_BASELINE_ONLY',threshold=0.,baseline=baseline)
    # Score >= threshold keeps ties. Search also the next representable value to
    # permit rejection of tied candidates, including the largest score below1.
    thresholds={0.,1.}
    for score in scores.values():
        thresholds.add(score)
        if score<1:thresholds.add(float(np.nextafter(score,1.)))
    accepted=[]
    for t in sorted(thresholds):
        m=metrics(patients,scores,t)
        if m['missed_positive_patients']<=baseline['missed_positive_patients'] and m['small_hits']>=baseline['small_hits'] and m['positive_dice']>=baseline['positive_dice']-.01 and m['negative_voxels']<=baseline['negative_voxels']:accepted.append((t,m))
    t,m=accepted[-1]
    return dict(status='CALIBRATION_POLICY_LOCKED_NOT_EFFICACY',threshold=t,baseline=baseline,selected=m,
        absolute_alarm_reduction=baseline['negative_alarm_fraction']-m['negative_alarm_fraction'])
