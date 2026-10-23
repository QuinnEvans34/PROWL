"""Offline completed-run comparator. Never launches/evaluates a model or writes MLflow.

The template is intentionally unbound. Approved matching review and explicit
completed-run evidence must be supplied; small-component omissions block success.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.native_error_review_v1 import (POLICY,compare,final_decision,fingerprint,
    require,select_complete_series,REGION_SCOPE)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text())
def bound(record,pins):
    require(isinstance(record,dict) and isinstance(record.get('path'),str) and isinstance(record.get('sha256'),str),'Explicit pinned file required')
    path=Path(record['path']);require(sha(path)==record['sha256'],'Comparison input hash mismatch')
    pins[str(path.resolve())]=record['sha256'];return path


def fixed_recipe(config):
    keys={'session','initialization','region_policy','training_view_policy','throughput_policy','_experiment'}
    require(keys<=set(config) and set(config)<=keys|{'distillation'},'Unknown/incomplete scientific configuration')
    require(config['_experiment']['run']==dict(checkpoint_every=500,max_updates=24000,validate_every=2000),'Different horizon/cadence')
    return dict({k:config[k] for k in keys-{'_experiment'}},cadence=config['_experiment']['run'])


def completed_arm(arm,expected,pins):
    root=Path(arm['run_directory']);require(root.is_absolute(),'Absolute run directory required')
    require(not (root/'operator-stop.json').exists(),'Stopped run cannot be a completed arm')
    receipt_path=bound(arm['receipt'],pins);require(receipt_path.resolve()==(root/'ready.json').resolve(),'Receipt belongs to another run')
    receipt=read(receipt_path)
    require(receipt['configuration_sha256']==arm['configuration']['sha256'],'Configuration does not match launched receipt')
    result_path=bound(arm['result'],pins);require(result_path.resolve()==(root/'result.json').resolve(),'Result belongs to another run')
    require(read(result_path)['completed_updates']==24000,'Incomplete run')
    resources=read(bound(arm['resources'],pins));require(resources.get('workers_reaped') is True,'Workers not reaped')
    controls=bound(arm['input_control'],pins);require(controls.resolve()==(root/'input-control.json').resolve(),'Control belongs to another run')
    require(sha(controls)==receipt['control_sha256'],'Control does not match launched receipt')
    control=read(controls)
    require(set(control['validation'])==set(expected) and len(control['validation'])==len(expected),'Wrong development cohort')
    require(len(control['train'])==1333 and len(set(control['train']))==1333 and not set(control['train'])&set(expected),'Training/validation role separation')
    journal=root/'execution/history.jsonl';count=0;validations=[];last=None
    with journal.open() as stream:
        for line in stream:
            row=json.loads(line);last=row
            require(row['event']!='failed','Failed journal')
            if row['event']=='update':count+=1;require(row['step']==count,'Noncontiguous update journal')
            if row['event']=='native_completed':validations.append(row['step'])
    require(count==24000 and last and last['event']=='completed' and validations==list(range(2000,24001,2000)),'Normal complete horizon required')
    pins[str(journal)]=sha(journal)
    reports=[];hashes={}
    for step in range(2000,24001,2000):
        path=root/f'execution/native-{step:06d}.json';report=read(path)
        require(report['step']==step and report['scope']==REGION_SCOPE,'Native report identity')
        reports.append(report);hashes[step]=sha(path);pins[str(path)]=hashes[step]
    selected,terminal=select_complete_series(reports,expected)
    for endpoint,chosen in (('selected',selected),('terminal',terminal)):
        path=root/f'execution/native-{endpoint}.json';saved=read(path)
        require(saved['step']==chosen['step'] and saved['cases']==chosen['cases'],'Endpoint selection differs')
        pins[str(path)]=sha(path)
    tracking=read(root/'tracking.json');pins[str(root/'tracking.json')]=sha(root/'tracking.json')
    require(tracking['run_id']==arm['mlflow_run_id'],'Tracking identity differs')
    connection=sqlite3.connect('file:C:/Users/quinn/PROWL-Tracking/mlflow.db?mode=ro',uri=True)
    try:status=connection.execute('SELECT status FROM runs WHERE run_uuid=?',(arm['mlflow_run_id'],)).fetchone()
    finally:connection.close()
    require(status==('FINISHED',),'Tracking not FINISHED')
    return dict(selected=selected,terminal=terminal,hashes=hashes,control=control)


def run(manifest_path,output):
    manifest_path=Path(manifest_path);out=Path(output);require(not out.exists(),'Comparison output exists; no overwrite')
    m=read(manifest_path);require(m.get('status')=='BOUND_FOR_COMPLETED_COMPARISON','Unbound comparison template')
    require(m.get('scope')=='teacher_assisted_exploratory' and m.get('policy')==POLICY,'Evidence scope or policy changed')
    pins={str(manifest_path.resolve()):sha(manifest_path)}
    review_path=bound(m['matching_review'],pins);review=read(review_path)
    require(review.get('approved') is True and review.get('changed_factor')=='auxiliary_teacher_loss_only','Matched recipe review not approved')
    cohort=read(bound(m['cohort'],pins));require(cohort.get('role')=='validation' and len(cohort['case_ids'])==70,'Frozen development cohort required')
    expected=cohort['case_ids'];configurations={};arms={}
    for label in ('control','treatment'):
        configurations[label]=read(bound(m[label]['configuration'],pins))
        require(review[label+'_configuration_sha256']==m[label]['configuration']['sha256'],'Matching review does not bind this configuration')
        arms[label]=completed_arm(m[label],expected,pins)
    require(fixed_recipe(configurations['control'])==fixed_recipe(configurations['treatment']),'Fixed scientific factors differ')
    require(arms['control']['control']==arms['treatment']['control'],'Input/control recipes differ')
    require(not configurations['control'].get('distillation') and configurations['treatment'].get('distillation'),'Declared KD-only intervention required')
    results={}
    for endpoint in ('selected','terminal'):
        evidence={}
        for label in ('control','treatment'):
            item=m[label].get('components',{}).get(endpoint)
            evidence[label]=None if item is None else read(bound(item,pins))
        a,b=arms['control'][endpoint],arms['treatment'][endpoint]
        comparison=compare(a,b,expected,control_components=evidence['control'],treatment_components=evidence['treatment'],
            control_sha256=arms['control']['hashes'][a['step']],treatment_sha256=arms['treatment']['hashes'][b['step']])
        comparison.update(final_decision(comparison),scope='teacher_assisted_exploratory_completed_matched_runs',endpoint=endpoint)
        results[endpoint]=comparison
    # No source mutation or unknown partial-write outcome silently admitted.
    require(all(sha(path)==pin for path,pin in pins.items()),'Comparison input changed during analysis')
    out.mkdir(parents=True,exist_ok=False)
    with (out/'comparison.json').open('x') as stream:
        json.dump(dict(primary=results['selected'],secondary=results['terminal'],source_pins=pins,
            test_reads=0,inference_calls=0,optimizer_updates=0,independent_generalization_claim=False),stream,indent=2,allow_nan=False)
    print(json.dumps({k:{f:v[f] for f in ('hypothesis_decision','practical_decision')} for k,v in results.items()}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.manifest,a.output)
