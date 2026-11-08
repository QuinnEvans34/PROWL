"""Summarize all fixed policies and reject utility gains that lose detections."""
from statistics import mean
import math

KEYS=('0.0','0.4','0.5','0.6')


def summarize(rows):
    if len(rows)!=70 or len({r['case_id'] for r in rows})!=70:
        raise ValueError('Complete unique70-case cohort required')
    policies={}
    for key in KEYS:
        metrics=[r['policies'][key] for r in rows]
        positive=[m for m in metrics if m['reference_positive']]
        empty=[m for m in metrics if not m['reference_positive']]
        if len(positive)!=36 or len(empty)!=34 or sum(m['reference_components'] for m in metrics)!=45:
            raise ValueError('Reference denominators changed')
        for m in metrics:
            n,p,t=(m['lesion'][k] for k in ('target_voxels','predicted_voxels','true_positive'))
            if not all(type(x) is int and x>=0 for x in (n,p,t)) or t>min(n,p):
                raise ValueError('Invalid confusion counts')
            if n and not math.isclose(m['lesion']['dice'],2*t/(n+p),abs_tol=1e-12,rel_tol=0):
                raise ValueError('Dice arithmetic mismatch')
        small=[m for m in positive if m['target_volume_mm3']<1000]
        if len(small)!=5:
            raise ValueError('Small total-volume cohort changed')
        def recall(group):
            return mean(m['lesion']['true_positive']/m['lesion']['target_voxels'] for m in group)
        precision=[m['lesion']['true_positive']/m['lesion']['predicted_voxels'] for m in positive if m['lesion']['predicted_voxels']]
        policies[key]=dict(positive_macro_dice=mean(m['lesion']['dice'] for m in positive),
            positive_macro_recall=recall(positive),small_case_macro_recall=recall(small),
            positive_macro_precision_defined=mean(precision) if precision else None,
            precision_defined_cases=len(precision),pancreas_macro_dice=mean(m['pancreas']['dice'] for m in metrics),
            detected_cases=sum(m['case_detected'] for m in positive),
            detected_components=sum(m['detected_components'] for m in positive),
            empty_alarm_cases=sum(m['false_alarm_any'] for m in empty),
            false_positive_voxels=sum(m['lesion']['predicted_voxels']-m['lesion']['true_positive'] for m in metrics),
            false_positive_mL=sum((m['lesion']['predicted_voxels']-m['lesion']['true_positive'])*m['voxel_mm3']/1000 for m in metrics),
            false_negative_voxels=sum(m['lesion']['target_voxels']-m['lesion']['true_positive'] for m in positive))
    raw=policies['0.0']; guards={}
    for key in KEYS[1:]:
        now=policies[key]; lost_cases=[];lost_components=[]
        for r in rows:
            a,b=(r['policies'][k] for k in ('0.0',key))
            if a['lesion']['target_voxels']!=b['lesion']['target_voxels']:
                raise ValueError('Matched references changed')
            if a['case_detected'] and not b['case_detected']:
                lost_cases.append(r['case_id'])
            for component in sorted(set(a['hit_component_ids'])-set(b['hit_component_ids'])):
                lost_components.append(dict(case_id=r['case_id'],component_id=component))
            if (b['lesion']['true_positive']>a['lesion']['true_positive'] or
                b['lesion']['predicted_voxels']>a['lesion']['predicted_voxels']):
                raise ValueError('Removal-only policy increased lesion counts')
        tp_removed=sum(r['policies']['0.0']['lesion']['true_positive']-r['policies'][key]['lesion']['true_positive'] for r in rows)
        fp_removed=raw['false_positive_voxels']-now['false_positive_voxels']
        checks=dict(dice_gain_at_least_02=now['positive_macro_dice']-raw['positive_macro_dice']>=.02-1e-12,
                    no_lost_cases=not lost_cases,no_lost_components=not lost_components,
                    small_recall_unchanged=now['small_case_macro_recall']>=raw['small_case_macro_recall']-1e-12,
                    overall_recall_within_01=now['positive_macro_recall']>=raw['positive_macro_recall']-.01-1e-12,
                    pancreas_dice_within_01=now['pancreas_macro_dice']>=raw['pancreas_macro_dice']-.01-1e-12,
                    empty_alarms_nonincrease=now['empty_alarm_cases']<=raw['empty_alarm_cases'],
                    fp_volume_nonincrease=now['false_positive_mL']<=raw['false_positive_mL']+1e-12)
        guards[key]=dict(passes=all(checks.values()),checks=checks,lost_cases=lost_cases,lost_components=lost_components,
                         dice_gain=now['positive_macro_dice']-raw['positive_macro_dice'],
                         true_positive_voxels_removed=tp_removed,false_positive_voxels_removed=fp_removed)
    eligible=[k for k in KEYS[1:] if guards[k]['passes']]
    selected=max(eligible,key=lambda k:(policies[k]['positive_macro_dice'],-float(k))) if eligible else '0.0'
    tp=[sum(r['confidence_histogram']['true_positive'][i] for r in rows) for i in range(100)]
    fp=[sum(r['confidence_histogram']['false_positive'][i] for r in rows) for i in range(100)]
    if sum(fp)!=raw['false_positive_voxels'] or sum(tp)!=sum(r['policies']['0.0']['lesion']['true_positive'] for r in rows):
        raise ValueError('Confidence histogram does not reproduce raw counts')
    below=0;u=0
    for a,b in zip(tp,fp):
        u+=a*(below+.5*b);below+=b
    auc=u/(sum(tp)*sum(fp)) if sum(tp) and sum(fp) else None
    return dict(schema='prowl.stunet.confidence-results.v1',policies=policies,guards=guards,
                selected_policy=selected,selection='exposed-development utility screen; no automatic promotion',
                correlation=dict(quantized_auc_correct_vs_incorrect_raw_lesion_winners=auc,
                    interpretation='Voxel-weighted100-bin ranking;0.5 no separation, not patient-level independence/calibration',
                    true_positive_histogram=tp,false_positive_histogram=fp),
                cases=rows)
