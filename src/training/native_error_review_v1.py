"""Report-only native error analysis and prospective paired comparison.

No image IO, model execution, MLflow writes or training imports. Counts describe
voxel error, not spatial boundary diagnosis. Missing evidence never becomes a pass.
"""
import hashlib
import json
import math
import re
import numpy as np

SCOPES={'native_provided_pancreas_region_development','native_development_provided_pancreas','native_provided_pancreas_development'}
REGION_SCOPE='native_provided_pancreas_region_development'
POLICY=dict(version='native-error-review-1',seed=20261023,replicates=10000,
    interval='paired_patient_percentile_95',dice_gain=.02,detection_delta_min=-.03,
    alarm_delta_max=.03,pancreas_delta_min=-.02,empty_voxel_delta_max=0,
    macro_recall_delta_min=-.03,small_component_recall_delta_min=-.03,
    small_component_mm3_lt=1000,component_matching='native_GT_26connectivity_any_predicted_lesion_overlap',
    small_case='total_patient_annotated_volume_lt_1000mm3_NOT_individual_component_size')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def require(condition,message):
    if not condition:raise ValueError(message)


def integer(value):return type(value) is int and value>=0
def close(a,b):return math.isfinite(float(a)) and math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10)
def mean(values):return None if not values else float(np.mean(values))
def size_band(mm3):return 'empty' if mm3==0 else 'small' if mm3<1000 else 'medium' if mm3<=10000 else 'large'


def validate_report(report,expected_ids,*,positive_cases=36):
    require(report.get('scope') in SCOPES,'Native development scope required')
    require(type(report.get('step')) is int and report['step']>0,'Positive report step')
    rows=report['cases'];expected=list(expected_ids);names=[r['case_id'] for r in rows]
    require(len(set(expected))==len(expected) and len(set(names))==len(names) and set(names)==set(expected),'Duplicate/missing/cohort cases')
    for row in rows:
        # The completed October17 producer used a different top-level spelling
        # from its case records. Admit that exact historical pair only; do not
        # normalize it into the newer region scope for a matched comparison.
        row_scope='native_development_provided_pancreas' if report['scope']=='native_provided_pancreas_development' else report['scope']
        require(row.get('scope')==row_scope and row.get('step')==report['step'],'Case scope/step mismatch')
        m=row['metrics'];volume=m['voxel_mm3']
        require(type(volume) in (int,float) and math.isfinite(volume) and volume>0,'Voxel volume')
        for label in ('lesion','pancreas'):
            x=m[label];n,p,tp=(x[k] for k in ('target_voxels','predicted_voxels','true_positive'))
            require(all(integer(v) for v in (n,p,tp)) and tp<=min(n,p),'Impossible native confusion counts')
            require(x['dice'] is None if n+p==0 else x['dice'] is not None and close(x['dice'],2*tp/(n+p)),'Dice/count disagreement')
        x=m['lesion'];n,p,tp=(x[k] for k in ('target_voxels','predicted_voxels','true_positive'))
        require(close(m['target_volume_mm3'],n*volume) and close(m['predicted_volume_mm3'],p*volume),'Native volume/count disagreement')
        require(m['size_band']==size_band(n*volume),'Size band/reference mismatch')
        for key,truth in dict(reference_positive=n>0,case_detected=tp>0,false_alarm_any=n==0 and p>0,case_alert_50mm3=p*volume>=50).items():
            require(type(m[key]) is bool and m[key]==truth,'Boolean metric/count disagreement: '+key)
        require(all(integer(m[k]) for k in ('reference_components','detected_components','predicted_components')),'Component counts')
        require(m['detected_components']<=m['reference_components'] and (m['reference_components']>0)==(n>0)
            and (m['predicted_components']>0)==(p>0) and (m['detected_components']>0)==(tp>0),'Component semantics')
        if report['scope']==REGION_SCOPE:
            rec=row.get('reconstruction',{})
            require(rec.get('gap_voxels')==0 and rec.get('lesion_guided_region') is False and rec.get('assistance')=='provided_pancreas_mask','Unqualified reconstruction scope')
    positive=[r for r in rows if r['metrics']['reference_positive']]
    require(len(positive)==positive_cases and len(positive)<len(rows),'Positive/negative cohort counts')
    if 'lesion_positive_macro_dice' in report:
        require(close(report['lesion_positive_macro_dice'],mean([r['metrics']['lesion']['dice'] for r in positive])),'Report macro Dice mismatch')
    return {r['case_id']:r for r in rows}


def case_error(row):
    m=row['metrics'];x=m['lesion'];n,p,tp=(x[k] for k in ('target_voxels','predicted_voxels','true_positive'))
    fn,fp=n-tp,p-tp
    if not n:kind='negative_false_positive' if p else 'negative_clean'
    elif not tp:kind='complete_miss_with_off_target_prediction' if p else 'complete_miss_no_prediction'
    elif fn==fp==0:kind='exact_voxel_match'
    elif fn>fp:kind='missed_voxel_dominant'
    elif fp>fn:kind='extra_voxel_dominant'
    else:kind='balanced_mixed_error'
    return dict(case_id=row['case_id'],size_band=m['size_band'],dice=x['dice'],target_voxels=n,predicted_voxels=p,
        true_positive=tp,false_negative=fn,false_positive=fp,target_mL=n*m['voxel_mm3']/1000,
        predicted_mL=p*m['voxel_mm3']/1000,false_positive_mL=fp*m['voxel_mm3']/1000,
        voxel_recall=None if not n else tp/n,voxel_precision=None if not p else tp/p,
        predicted_to_target_volume=None if not n else p/n,error_pattern=kind,
        flags=dict(any_missing_annotation=n>0 and fn>0,more_than_half_annotation_missed=n>0 and fn/n>.5,
            any_extra_prediction=fp>0,more_than_half_prediction_extra=p>0 and fp/p>.5,
            net_oversized=n>0 and p>n,at_least_double_target_volume=n>0 and p>=2*n),
        case_detected=m['case_detected'],components_detected=m['detected_components'],components=m['reference_components'])


def group_summary(errors):
    n=len(errors);positive=[r for r in errors if r['target_voxels']>0];negative=[r for r in errors if r['target_voxels']==0]
    patterns={key:sum(r['error_pattern']==key for r in errors) for key in sorted({r['error_pattern'] for r in errors})}
    precision=[r['voxel_precision'] for r in positive if r['voxel_precision'] is not None]
    return dict(cases=n,positive_cases=len(positive),negative_cases=len(negative),
        positive_macro_dice=mean([r['dice'] for r in positive]),positive_macro_recall=mean([r['voxel_recall'] for r in positive]),
        positive_macro_precision=mean(precision),precision_defined_positive_cases=len(precision),
        detected=sum(r['case_detected'] for r in positive),complete_misses=sum(not r['case_detected'] for r in positive),
        negative_alarms=sum(r['predicted_voxels']>0 for r in negative),negative_predicted_voxels=sum(r['predicted_voxels'] for r in negative),
        negative_predicted_mL=sum(r['predicted_mL'] for r in negative),
        total_false_negative_voxels=sum(r['false_negative'] for r in errors),total_false_positive_voxels=sum(r['false_positive'] for r in errors),
        patterns=patterns,flags={k:sum(r['flags'][k] for r in positive) for k in
            ('any_missing_annotation','more_than_half_annotation_missed','any_extra_prediction','more_than_half_prediction_extra','net_oversized','at_least_double_target_volume')})


def summarize(report,expected_ids,*,positive_cases=36):
    rows=validate_report(report,expected_ids,positive_cases=positive_cases)
    errors=[case_error(rows[n]) for n in sorted(rows)]
    result=group_summary(errors)
    result.update(step=report['step'],scope=report['scope'],cases_detail=errors,
        pancreas_macro_dice=mean([r['metrics']['pancreas']['dice'] for r in rows.values() if r['metrics']['pancreas']['dice'] is not None]),
        pancreas_defined_cases=sum(r['metrics']['pancreas']['dice'] is not None for r in rows.values()),
        negative_alerts_50mm3=sum(r['metrics']['case_alert_50mm3'] for r in rows.values() if not r['metrics']['reference_positive']),
        bands={b:group_summary([r for r in errors if r['size_band']==b]) for b in ('small','medium','large','empty')})
    return result


def paired_stat(values,*,seed=20261023,replicates=10000,total=False):
    require(type(replicates) is int and 100<=replicates<=100000,'Bootstrap replicate bounds')
    v=np.asarray(values,dtype=float);require(v.ndim==1 and np.isfinite(v).all(),'Finite paired differences')
    if not len(v):return dict(estimate=None,ci95=None,n=0,status='not_estimable')
    rng=np.random.default_rng(seed);draws=v[rng.integers(len(v),size=(replicates,len(v)))]
    draws=draws.sum(1) if total else draws.mean(1)
    return dict(estimate=float(v.sum() if total else v.mean()),ci95=np.quantile(draws,[.025,.975]).tolist(),n=len(v),status='estimable')


def check_pair(a,b):
    require(set(a)==set(b),'Unmatched patient cohort')
    for name in a:
        x,y=a[name]['metrics'],b[name]['metrics']
        for key in ('reference_positive','reference_components','size_band','target_volume_mm3','voxel_mm3'):
            require(x[key]==y[key],'Mismatched target semantics: '+key)
        for label in ('lesion','pancreas'):
            require(x[label]['target_voxels']==y[label]['target_voxels'],'Mismatched native targets')


def component_table(sidecar,report,report_sha256):
    """All GT components, not only small or detected; report bytes bind predictions."""
    require(isinstance(report_sha256,str) and re.fullmatch('[0-9a-f]{64}',report_sha256),'Explicit report hash required')
    require(sidecar.get('version')=='native-components-1' and sidecar.get('report_sha256')==report_sha256,'Component/report binding')
    require(sidecar.get('matching')==POLICY['component_matching'],'Component matching policy')
    rows={r['case_id']:r for r in report['cases']};cases=sidecar['cases'];names=[r['case_id'] for r in cases]
    require(len(names)==len(set(names)) and set(names)==set(rows),'Component case completeness')
    result={}
    for case in cases:
        m=rows[case['case_id']]['metrics'];items=case['components']
        require(all(isinstance(case.get(k),str) and re.fullmatch('[0-9a-f]{64}',case[k]) for k in ('target_sha256','geometry_sha256')),'Component source hashes')
        ids=[r['component_id'] for r in items]
        require(ids==list(range(1,len(items)+1)) and len(items)==m['reference_components'],'Component identities/counts')
        for r in items:
            require(integer(r['voxels']) and r['voxels']>0 and type(r['detected']) is bool and close(r['volume_mm3'],r['voxels']*m['voxel_mm3']),'Component volumes/hits')
        require(sum(r['voxels'] for r in items)==m['lesion']['target_voxels'] and sum(r['detected'] for r in items)==m['detected_components'],'Component totals inconsistent')
        result[case['case_id']]=case
    return result


def small_components(control,treatment,a,b,*,control_sha256,treatment_sha256,seed=20261023,replicates=10000):
    if a is None or b is None:return dict(status='missing_component_sidecars',estimate=None,ci95=None)
    x=component_table(a,control,control_sha256);y=component_table(b,treatment,treatment_sha256)
    pos=sorted(r['case_id'] for r in control['cases'] if r['metrics']['reference_positive'])
    counts=[];differences=[];ca=cb=0
    for name in x:
        require(x[name]['target_sha256']==y[name]['target_sha256'] and x[name]['geometry_sha256']==y[name]['geometry_sha256'],'Component source mismatch')
        old,new=x[name]['components'],y[name]['components']
        require([(r['component_id'],r['voxels'],r['volume_mm3']) for r in old]==[(r['component_id'],r['voxels'],r['volume_mm3']) for r in new],'Component target mismatch')
    for name in pos:
        old=[r for r in x[name]['components'] if r['volume_mm3']<1000]
        new=[r for r in y[name]['components'] if r['volume_mm3']<1000]
        na,nb=sum(r['detected'] for r in old),sum(r['detected'] for r in new)
        counts.append(len(old));differences.append(nb-na);ca+=na;cb+=nb
    n=sum(counts)
    if not n:return dict(status='no_small_components',estimate=None,ci95=None,components=0)
    indices=np.random.default_rng(seed).integers(len(pos),size=(replicates,len(pos)))
    denominators=np.asarray(counts)[indices].sum(1);numerators=np.asarray(differences)[indices].sum(1);valid=denominators>0
    require(valid.any(),'Small-component bootstrap empty')
    draws=numerators[valid]/denominators[valid]
    return dict(status='estimable',estimate=(cb-ca)/n,ci95=np.quantile(draws,[.025,.975]).tolist(),components=n,
        control_detected=ca,treatment_detected=cb,control_recall=ca/n,treatment_recall=cb/n,
        bootstrap_unit='paired_positive_patient_cluster_ratio_of_component_totals',zero_denominator_draws=int((~valid).sum()))


def compare(control,treatment,expected_ids,*,positive_cases=36,control_components=None,treatment_components=None,
            control_sha256=None,treatment_sha256=None,seed=20261023,replicates=10000):
    a=validate_report(control,expected_ids,positive_cases=positive_cases);b=validate_report(treatment,expected_ids,positive_cases=positive_cases)
    require(control['scope']==treatment['scope'],'Different inference scopes; descriptive summaries only')
    check_pair(a,b);names=sorted(a);pos=[n for n in names if a[n]['metrics']['reference_positive']];neg=[n for n in names if n not in pos]
    ae={n:case_error(a[n]) for n in names};be={n:case_error(b[n]) for n in names}
    def stat(ns,field,total=False):return paired_stat([be[n][field]-ae[n][field] for n in ns],seed=seed,replicates=replicates,total=total)
    pancreas=[n for n in names if a[n]['metrics']['pancreas']['dice'] is not None and b[n]['metrics']['pancreas']['dice'] is not None]
    stats=dict(dice=stat(pos,'dice'),macro_recall=stat(pos,'voxel_recall'),
        detection=paired_stat([int(be[n]['case_detected'])-int(ae[n]['case_detected']) for n in pos],seed=seed,replicates=replicates),
        alarm=paired_stat([int(b[n]['metrics']['false_alarm_any'])-int(a[n]['metrics']['false_alarm_any']) for n in neg],seed=seed,replicates=replicates),
        pancreas=paired_stat([b[n]['metrics']['pancreas']['dice']-a[n]['metrics']['pancreas']['dice'] for n in pancreas],seed=seed,replicates=replicates),
        empty_voxels=stat(neg,'predicted_voxels',True),empty_mL=stat(neg,'predicted_mL',True))
    stats['small_component_recall']=small_components(control,treatment,control_components,treatment_components,
        control_sha256=control_sha256,treatment_sha256=treatment_sha256,seed=seed,replicates=replicates)
    def guard(key,bound,minimum=True,available=True):
        v=stats[key]['estimate']
        return dict(delta=v,bound=bound,comparison='>=' if minimum else '<=',
            passed=None if v is None or not available else bool(v>=bound if minimum else v<=bound))
    guards=dict(detection=guard('detection',-.03),alarm=guard('alarm',.03,False),
        pancreas=guard('pancreas',-.02,available=len(pancreas)==len(names)),empty_voxels=guard('empty_voxels',0,False),
        macro_recall=guard('macro_recall',-.03),small_component_recall=guard('small_component_recall',-.03))
    pairs=[dict(case_id=n,size_band=ae[n]['size_band'],control=ae[n],treatment=be[n],
        dice_delta=None if n in neg else be[n]['dice']-ae[n]['dice'],
        recall_delta=None if n in neg else be[n]['voxel_recall']-ae[n]['voxel_recall']) for n in names]
    return dict(policy=POLICY,seed=seed,replicates=replicates,control_step=control['step'],treatment_step=treatment['step'],
        metrics=stats,guards=guards,size_bands={band:stat([n for n in pos if ae[n]['size_band']==band],'dice') for band in ('small','medium','large')},
        paired_cases=pairs,improved=sum(be[n]['dice']>ae[n]['dice'] for n in pos),worsened=sum(be[n]['dice']<ae[n]['dice'] for n in pos),
        unchanged=sum(be[n]['dice']==ae[n]['dice'] for n in pos),hypothesis_decision=None,practical_decision=None,
        scope='diagnostic_only_until_completed_series_and_matched_recipe_contract_verified',
        limitations=['conditional_on_checkpoints_not_selection_adjusted','single_seed_not_training_replicates','reused_development_not_independent_test'])


def select_complete_series(reports,expected_ids,*,positive_cases=36):
    require(len(reports)==12 and sorted(r['step'] for r in reports)==list(range(2000,24001,2000)),'Full twelve-validation horizon required')
    first=None;scores=[]
    for report in sorted(reports,key=lambda r:r['step']):
        require(report['scope']==reports[0]['scope'],'Mixed inference scopes in series')
        index=validate_report(report,expected_ids,positive_cases=positive_cases)
        if first is None:first=index
        else:check_pair(first,index)
        scores.append((mean([r['metrics']['lesion']['dice'] for r in index.values() if r['metrics']['reference_positive']]),report))
    return max(scores,key=lambda pair:pair[0])[1],max(reports,key=lambda r:r['step'])


def final_decision(comparison):
    """Pure policy calculation; CLI only calls after full series/contract admission."""
    dice=comparison['metrics']['dice'];values=[g['passed'] for g in comparison['guards'].values()]
    null='reject_H0' if dice['ci95'][0]>0 else 'fail_to_reject_H0'
    if False in values or dice['ci95'][1]<.02:practical='reject'
    elif None in values:practical='not_evaluable_missing_required_guard'
    elif dice['estimate']>=.02 and dice['ci95'][0]>0:practical='accept'
    else:practical='inconclusive'
    return dict(hypothesis_decision=null,practical_decision=practical,
        guardrail_claim='point_estimate_guards_not_statistical_noninferiority')
