"""Hash-bound corrected 24k count audit. No arrays, model, training or tracking writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

from scripts.diagnostics.review_stunet_interim_20261107 import (
    aggregate, close, derived_row, digest, require,
)

ARTIFACT = 'pants_stunet_corrected_continuation_12k_20261108_launch02'
READY = 'd0a291420d0e1ee07e56f1007540797ebb97c9a08ff25cc82111d53f77c4d9f8'
MLFLOW = '13c709ae157949988de1d7f8821a03b7'
METRIC_PRODUCER = '6e02fa0da2db3af02bb76b2caff2e498e5ec9b104bc057b7863907e9ed1eb85a'
STEPS = [14000, 16000, 18000, 20000, 22000, 24000]
MAX_BYTES = 4 * 1024 * 1024
GEOMETRY_SHA = 'c5dcdb2aa77dbe2df2d214932b2d7e27b9dd55351c2aea798f2d676fd047f3cf'


def counterfactual(rows, *, fp_removed=0., fn_recovered=0.):
    """Uniform fractional error oracle; never a deployable prediction policy."""
    require(0 <= fp_removed <= 1 and 0 <= fn_recovered <= 1, 'Oracle fractions outside range')
    values = []
    for r in rows:
        n, p, t = (r[k] for k in ('target_voxels', 'predicted_voxels', 'overlap_voxels'))
        if n:
            new_t = t + fn_recovered * (n - t)
            new_p = new_t + (1 - fp_removed) * (p - t)
            values.append(2 * new_t / (n + new_p))
    require(bool(values), 'No positive cases')
    return mean(values)


def required_fp_fraction(rows, goal=.5):
    if counterfactual(rows) >= goal:
        return 0.
    if counterfactual(rows, fp_removed=1.) < goal:
        return None
    lo, hi = 0., 1.
    for _ in range(60):
        mid = (lo + hi) / 2
        if counterfactual(rows, fp_removed=mid) < goal: lo = mid
        else: hi = mid
    return hi


def describe(rows):
    summary = aggregate(rows)
    positive = [r for r in rows if r['target_voxels']]
    empty = [r for r in rows if not r['target_voxels']]
    tn = sum(r['true_negative_voxels'] for r in rows)
    fp = sum(r['false_positive_voxels'] for r in rows)
    summary.update(
        reference_empty_case_specificity=sum(not r['predicted_voxels'] for r in empty) / len(empty) if empty else None,
        native_voxel_specificity=tn / (tn + fp) if tn + fp else None,
        specificity_scope='Full native voxels in a provided-pancreas-region development evaluation; not clinical specificity',
        positive_cases_with_any_prediction=sum(r['predicted_voxels'] > 0 for r in positive),
        positive_micro_dice=2 * sum(r['overlap_voxels'] for r in positive) /
            sum(r['target_voxels'] + r['predicted_voxels'] for r in positive) if positive else None,
        positive_macro_precision_zero_for_no_prediction=mean(r['precision'] or 0. for r in positive) if positive else None,
        small_case_definition='Total reference lesion volume below 1 mL; not individual component size',
    )
    oracles = dict(perfect_fp_removal=counterfactual(rows, fp_removed=1.),
        perfect_fn_recovery=counterfactual(rows, fn_recovered=1.))
    oracles['uniform_fp_removal_fraction_needed_for_macro_dice_05_with_zero_tp_loss'] = required_fp_fraction(rows)
    oracles['error_budget_grid'] = [dict(fp_removed=fp_cut, fn_recovered=fn_fix,
        macro_dice=counterfactual(rows, fp_removed=fp_cut, fn_recovered=fn_fix))
        for fp_cut in (0., .25, .5, .75, 1.) for fn_fix in (0., .1, .25, .5)]
    ranked = []
    for r in positive:
        one = [r]
        ranked.append(dict(r,
            perfect_fp_removal_dice=counterfactual(one, fp_removed=1.),
            perfect_fn_recovery_dice=counterfactual(one, fn_recovered=1.),
            fp_oracle_gain=counterfactual(one, fp_removed=1.) - r['dice'],
            fn_oracle_gain=counterfactual(one, fn_recovered=1.) - r['dice']))
    return dict(summary=summary, oracle_only=oracles,
        size_bands={band:aggregate([r for r in rows if r['size_band']==band]) for band in ('small','medium','large','empty')},
        worst_dice=sorted(ranked,key=lambda r:(r['dice'],r['case_id']))[:10],
        highest_fp_oracle_gain=sorted(ranked,key=lambda r:(-r['fp_oracle_gain'],r['case_id']))[:10],
        highest_fn_oracle_gain=sorted(ranked,key=lambda r:(-r['fn_oracle_gain'],r['case_id']))[:10],
        largest_empty_alarms=sorted(empty,key=lambda r:(-r['false_positive_mL'],r['case_id']))[:10],
        cases=rows)


def compare(before, after):
    old = {r['case_id']:r for r in before['cases']}
    require(old.keys() == {r['case_id'] for r in after['cases']}, 'Paired membership differs')
    changes = []
    for r in after['cases']:
        a = old[r['case_id']]
        require(r['target_voxels']==a['target_voxels'], 'Paired target changed')
        if r['target_voxels']:
            changes.append(dict(case_id=r['case_id'], dice_before=a['dice'], dice_after=r['dice'],
                dice_delta=r['dice']-a['dice'], recall_delta=r['recall']-a['recall'],
                fp_voxel_delta=r['false_positive_voxels']-a['false_positive_voxels'],
                fn_voxel_delta=r['false_negative_voxels']-a['false_negative_voxels']))
    return dict(better=sum(r['dice_delta']>0 for r in changes), worse=sum(r['dice_delta']<0 for r in changes),
        unchanged=sum(r['dice_delta']==0 for r in changes),
        macro_dice_delta=mean(r['dice_delta'] for r in changes),
        newly_zero_overlap=[r['case_id'] for r in after['cases'] if r['target_voxels'] and r['overlap_voxels']==0 and old[r['case_id']]['overlap_voxels']>0],
        recovered_overlap=[r['case_id'] for r in after['cases'] if r['target_voxels'] and r['overlap_voxels']>0 and old[r['case_id']]['overlap_voxels']==0],
        largest_declines=sorted(changes,key=lambda r:(r['dice_delta'],r['case_id']))[:10],
        largest_gains=sorted(changes,key=lambda r:(-r['dice_delta'],r['case_id']))[:10], changes=changes)


def review(raw, expected_sha):
    require(len(raw)<=MAX_BYTES, 'Metadata exceeds byte limit')
    require(digest(expected_sha) and hashlib.sha256(raw).hexdigest()==expected_sha, 'Export SHA256 mismatch')
    p = json.loads(raw)
    require(p['schema']=='prowl-stunet-saved-native-metadata-v1' and p['artifact_id']==ARTIFACT
        and p['ready_sha256']==READY and p['mlflow_run_id']==MLFLOW, 'Wrong corrected experiment identity')
    require(p['metric_producer_pins_as_recorded']['src\\training\\pants_native_evaluation.py']==METRIC_PRODUCER,
        'Native metric producer differs')
    identities = {r['case_id']:r for r in p['case_identities_from_frozen_inputs']}
    require(len(identities)==len(p['case_identities_from_frozen_inputs'])==70, 'Require 70 unique identities')
    for r in identities.values():
        require(set(r['source_sha256'])=={'ct','pancreas','lesion'} and all(digest(x) for x in r['source_sha256'].values()), 'Missing source binding')
        a = r['native_affine']
        require(len(r['native_shape'])==3 and all(type(x)is int and x>0 for x in r['native_shape'])
            and len(a)==4 and all(len(row)==4 and all(type(x)in(int,float) and math.isfinite(x) for x in row) for row in a)
            and a[3]==[0,0,0,1], 'Invalid native geometry')
    require([r['step'] for r in p['reports']]==STEPS, 'Require all six full corrected validations through 24k')
    result = dict(schema='prowl.stunet.corrected-tuning-audit.v1', source_sha256=expected_sha,
        artifact_id=ARTIFACT, ready_sha256=READY, mlflow_run_id=MLFLOW, observed_at=p['observed_at'],
        scope=p['scope'], new_model_calls=0, new_training_updates=0, new_array_reads=0,
        claims='Descriptive exposed-development audit; no independent-patient inference or threshold deployment',
        series=[])
    previous_refs = None
    for report in p['reports']:
        step=report['step']; name=f'native-{step:05d}.json'
        require(report['report_name']==name and digest(report['report_sha256'])
            and p['source_json_sha256'][name]==report['report_sha256'] and report['independent_report_backup_matches'] is True,
            'Report receipt mismatch')
        cp=report['checkpoint']
        require(cp['name']==f'checkpoint-{step:05d}.pt' and digest(cp['sha256_from_saved_journal'])
            and type(cp['bytes'])is int and cp['bytes']>0, 'Checkpoint binding missing')
        originals=report['cases_as_saved']
        require(len(originals)==70 and {r['case_id'] for r in originals}==identities.keys(), 'Incomplete or duplicate cohort')
        refs={r['case_id']:(r['metrics']['pancreas']['target_voxels'], r['metrics']['lesion']['target_voxels'],r['metrics']['reference_components']) for r in originals}
        require(previous_refs is None or previous_refs==refs, 'References changed across validations')
        previous_refs=refs; rows=[]
        for r in originals:
            identity=identities[r['case_id']]; row=derived_row(r,identity)
            capacity=math.prod(identity['native_shape'])
            tn=capacity-row['target_voxels']-row['false_positive_voxels']
            require(tn>=0, 'Impossible native confusion counts')
            row.update(true_negative_voxels=tn, native_voxels=capacity)
            rows.append(row)
        item=describe(rows)
        s=item['summary']; saved=report['summary_as_saved']
        require(s['positive_cases']==36 and s['empty_cases']==34 and s['reference_components']==45,
            'Changed fixed denominators')
        require(close(saved['lesion_dice'],s['positive_macro_dice']) and saved['positive']==36 and saved['empty']==34
            and saved['detected']==s['detected_positive_cases'] and saved['alarms']==s['empty_alarm_cases'], 'Saved summary mismatch')
        item.update(step=step, report_sha256=report['report_sha256'], checkpoint_sha256_from_peer_journal=cp['sha256_from_saved_journal'])
        result['series'].append(item)
    by_step={r['step']:r for r in result['series']}
    best=max(result['series'],key=lambda r:(r['summary']['positive_macro_dice'],-r['step']))
    result.update(selected_step=best['step'], terminal_step=24000,
        selected_to_terminal=compare(best,by_step[24000]),
        last_interval=compare(by_step[22000],by_step[24000]))
    result['raw_pareto_steps']=[]
    for r in result['series']:
        def dominates(other):
            a,b=other['summary'],r['summary']
            x=(a['positive_macro_dice'],-a['empty_alarm_cases'],-a['false_positive_mL'],a['positive_macro_recall'])
            y=(b['positive_macro_dice'],-b['empty_alarm_cases'],-b['false_positive_mL'],b['positive_macro_recall'])
            return all(u>=v for u,v in zip(x,y)) and any(u>v for u,v in zip(x,y))
        if not any(dominates(other) for other in result['series']):result['raw_pareto_steps'].append(r['step'])
    return result


def review_published(raw, expected_sha, geometry_raw, geometry_sha):
    """Explicit adapter for the peer's original full-report publication envelope.

    Geometry is joined through the unchanged original input-configuration pin,
    not guessed from equal cohort counts. Both original source files stay intact.
    """
    for data,sha in ((raw,expected_sha),(geometry_raw,geometry_sha)):
        require(len(data)<=MAX_BYTES and digest(sha) and hashlib.sha256(data).hexdigest()==sha,
            'Published metadata SHA256/size mismatch')
    require(geometry_sha==GEOMETRY_SHA,'Wrong original geometry export')
    p,g=json.loads(raw),json.loads(geometry_raw)
    require(set(p)=={'scope','reports','completion','bindings','selected','terminal_checkpoint_sha256','inventory','saved_native_arrays'},
        'Unsupported published metadata envelope')
    c=p['completion']; pins=p['bindings']['pins']
    require(c['run_id']=='pants_stunet_corrected_continuation_12k_20261108'
        and c['ready_sha256']==p['bindings']['ready_sha256']==READY and c['status']=='PASS'
        and c['updates']==12000 and c['global_step']==24000 and c['mlflow_status']=='FINISHED'
        and c['stored_losses_exact']==12000 and c['repository_pins_match'] is True,
        'Incomplete corrected closeout')
    require(c['resources']['workers_reaped'] is True and c['resources']['success'] is True
        and c['resources']['exit_code']==0,'Failed worker closeout')
    old_input='E:\\PROWL\\readiness\\stunet-full-input-binding-20261106-a01\\worker\\inputs.json'
    require(pins[old_input]==g['source_json_sha256']['inputs.json'], 'Original development input binding changed')
    require(pins['src\\training\\pants_native_evaluation.py']==METRIC_PRODUCER
        and pins['src\\data\\stunet_inputs_20261106.py']==g['metric_producer_pins_as_recorded']['src\\data\\stunet_inputs_20261106.py'],
        'Inherited native/input producer changed')
    require(pins['C:\\Users\\quinn\\Desktop\\PROWL\\src\\data\\stunet_continuation_inputs_20261108.py']
        =='d501270fc6b486b18effbf2fd0685c704e28c223a52e508c7ab6428faf4cf45f',
        'Corrected inherited-development wrapper changed')
    backups={r['file']:r for r in c['backup_pairs']}
    expected={f'checkpoint-{s:05d}.pt' for s in range(12500,24001,500)}
    expected|={f'native-{s:05d}.json' for s in STEPS}|{'history.jsonl','result.json','selected.json'}
    require(len(c['backup_pairs'])==len(backups)==33 and set(backups)==expected
        and all(digest(r['sha256']) and type(r['bytes'])is int and r['bytes']>0 for r in backups.values()),
        'Incomplete independent backup ledger')
    require(len(p['inventory'])==33 and {r['name']:r['bytes'] for r in p['inventory']}=={n:r['bytes'] for n,r in backups.items()}, 'Execution/backup inventory differs')
    normalized=dict(schema='prowl-stunet-saved-native-metadata-v1',artifact_id=ARTIFACT,
        ready_sha256=READY,mlflow_run_id=MLFLOW,scope=p['scope'],observed_at=c['as_of_utc'],
        metric_producer_pins_as_recorded={'src\\training\\pants_native_evaluation.py':METRIC_PRODUCER},
        case_identities_from_frozen_inputs=g['case_identities_from_frozen_inputs'],source_json_sha256={},reports=[])
    require([r['report']['step'] for r in p['reports']]==STEPS,'Incomplete published curve')
    require(c['reports']==[dict(r['report']['summary'],step=r['report']['step']) for r in p['reports']], 'Completion/report curve differs')
    for wrapper in p['reports']:
        report=wrapper['report'];step=report['step'];name=f'native-{step:05d}.json';cp=f'checkpoint-{step:05d}.pt'
        require(wrapper['path'].replace('\\','/').endswith('/'+name) and wrapper['sha256']==backups[name]['sha256'], 'Published report backup differs')
        normalized['source_json_sha256'][name]=wrapper['sha256']
        normalized['reports'].append(dict(step=step,report_name=name,report_sha256=wrapper['sha256'],
            independent_report_backup_matches=True,cases_as_saved=report['cases'],summary_as_saved=report['summary'],
            checkpoint=dict(name=cp,sha256_from_saved_journal=backups[cp]['sha256'],bytes=backups[cp]['bytes'])))
    normalized_raw=json.dumps(normalized,sort_keys=True,allow_nan=False).encode()
    result=review(normalized_raw,hashlib.sha256(normalized_raw).hexdigest())
    selected=next(r for r in result['series'] if r['step']==result['selected_step'])
    require(c['selected_step']==p['selected']['step']==selected['step']
        and close(p['selected']['lesion_dice'],selected['summary']['positive_macro_dice'])
        and p['selected']['checkpoint']['sha256']==selected['checkpoint_sha256_from_peer_journal']
        and p['terminal_checkpoint_sha256']==backups['checkpoint-24000.pt']['sha256'], 'Selected/terminal checkpoint binding differs')
    result.update(source_sha256=expected_sha,geometry_source_sha256=geometry_sha,
        normalized_adapter_sha256=hashlib.sha256(normalized_raw).hexdigest(),
        geometry_binding='Original inputs.json identity and original input/metric producer pins match; explicit cross-export metadata join',
        closure='Peer saved-JSON backup/process/MLflow attestation; Mac did not reread remote artifact bytes',
        saved_native_arrays=p['saved_native_arrays'],phase_elapsed_seconds=c['seconds'])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--export',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--geometry-export',type=Path);p.add_argument('--geometry-sha256')
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    with args.export.open('rb') as f:raw=f.read(MAX_BYTES+1)
    if args.geometry_export or args.geometry_sha256:
        require(bool(args.geometry_export and args.geometry_sha256),'Both geometry arguments required')
        with args.geometry_export.open('rb') as f:geometry_raw=f.read(MAX_BYTES+1)
        result=review_published(raw,args.sha256,geometry_raw,args.geometry_sha256)
        require(args.geometry_export.read_bytes()==geometry_raw,'Geometry input changed during review')
    else:result=review(raw,args.sha256)
    require(args.export.read_bytes()==raw,'Input changed during review')
    with args.output.open('x') as f:f.write(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
