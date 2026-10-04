"""Predeclared development coverage stop; never filters cases or selects a model."""
import math
from src.data.source_inventory_records import require

REAL_POLICY=dict(schema_version='twomm-coverage-guard-1',start_step=300,
    mean_recall_floor=.95,minimum_recall_floor=.65,box_coverage_threshold=.995,
    box_pass_fraction_floor=.95,maximum_mean_recall_drop=.03)


def validate_policy(p):
    require(set(p)==set(REAL_POLICY) and p['schema_version']==REAL_POLICY['schema_version'] and
        type(p['start_step']) is int and 0<=p['start_step']<=1200,'Invalid coverage policy')
    for k in set(p)-{'schema_version','start_step'}:
        require(type(p[k]) in (float,int) and math.isfinite(p[k]) and 0<=p[k]<=1,
            'Invalid coverage threshold')


def review(rows,policy,step,previous):
    validate_policy(policy)
    require(type(step) is int and step>=0 and rows and len({r['study_id'] for r in rows})==len(rows) and
        all(r['role']=='evaluator' and r['step']==step for r in rows),'Coverage membership/stage differs')
    recalls=[];boxes=0
    for r in rows:
        m=r['metrics'];n=m['reference_voxels'];tp=m['true_positive']
        require(type(n) is int and n>0 and type(tp) is int and 0<=tp<=n and m['recall']==tp/n,
            'Coverage recall arithmetic differs')
        recalls.append(m['recall']);coverage=m['box_reference_coverage']
        require(coverage is None or (type(coverage) in (float,int) and math.isfinite(coverage) and 0<=coverage<=1),
            'Invalid box coverage')
        boxes+=coverage is not None and coverage>=policy['box_coverage_threshold']
    mean=sum(recalls)/len(recalls);minimum=min(recalls);reasons=[]
    active=step>=policy['start_step']
    prior=[r['mean_recall'] for r in previous if r['state']=='pass']
    if active:
        if mean<policy['mean_recall_floor']:reasons.append('mean_recall_below_floor')
        if minimum<policy['minimum_recall_floor']:reasons.append('minimum_recall_below_floor')
        if boxes<len(rows)*policy['box_pass_fraction_floor']:reasons.append('box_coverage_below_floor')
        if prior and max(prior)-mean>policy['maximum_mean_recall_drop']:
            reasons.append('mean_recall_drop_from_best_checkpoint')
    return dict(schema_version='twomm-coverage-review-1',step=step,
        state='stop' if reasons else 'pass' if active else 'warmup',reasons=reasons,
        cases=len(rows),mean_recall=mean,minimum_recall=minimum,box_coverage_passes=int(boxes),
        best_prior_mean_recall=max(prior) if prior else None)
