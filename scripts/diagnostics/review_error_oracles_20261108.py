"""Hash-bound, count-only error counterfactuals; no images, models or tracking."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

STU_SHA = 'c5dcdb2aa77dbe2df2d214932b2d7e27b9dd55351c2aea798f2d676fd047f3cf'
KD_SHA = '2679c09ebefc2361cb81122ead80530c48fcbeb99b333d2e526d1723a2e0033b'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def positive_case(case_id, target, prediction, overlap, saved_dice):
    require(all(type(x) is int and x >= 0 for x in (target, prediction, overlap)),
            'Nonnegative integer counts required')
    require(target > 0 and overlap <= min(target, prediction), 'Invalid positive counts')
    require(isinstance(saved_dice, (int, float)) and math.isfinite(saved_dice), 'Invalid Dice')
    dice = 2 * overlap / (target + prediction)
    require(math.isclose(dice, saved_dice, abs_tol=1e-12, rel_tol=0), 'Saved Dice mismatch')
    fp, fn = prediction - overlap, target - overlap
    # Remove FP only: new prediction = TP. Recover FN only: new prediction = GT + FP.
    no_fp = 2 * overlap / (target + overlap)
    no_fn = 2 * target / (2 * target + fp)
    return dict(case_id=case_id, target_voxels=target, predicted_voxels=prediction,
                true_positive=overlap, false_positive=fp, false_negative=fn,
                dice=dice, perfect_fp_removal_dice=no_fp, perfect_fn_recovery_dice=no_fn,
                fp_removal_gain=no_fp-dice, fn_recovery_gain=no_fn-dice,
                both_errors_fixed_dice=1.0)


def summarize(rows, saved_macro):
    ids = [r['case_id'] for r in rows]
    require(len(ids) == len(set(ids)) == 70, 'Require 70 unique cases')
    positives, empty = [], []
    for r in rows:
        n, p, tp = (r[k] for k in ('target_voxels', 'predicted_voxels', 'true_positive'))
        require(all(type(x) is int and x >= 0 for x in (n, p, tp)), 'Invalid count type/value')
        require(tp <= min(n, p), 'Impossible overlap')
        if n:
            row = positive_case(r['case_id'], n, p, tp, r['dice'])
            require(r['size_band'] in ('small', 'medium', 'large'), 'Unknown positive size band')
            row['size_band'] = r['size_band']
            positives.append(row)
        else:
            # Do not invent an empty/empty Dice convention or add negatives to the headline.
            require(tp == 0, 'Empty reference overlap')
            empty.append(dict(case_id=r['case_id'], false_positive_voxels=p))
    require(len(positives) == 36 and len(empty) == 34, 'Changed class denominators')

    def aggregate(group):
        return dict(cases=len(group), **{
            k: mean(x[k] for x in group) for k in
            ('dice', 'perfect_fp_removal_dice', 'perfect_fn_recovery_dice',
             'fp_removal_gain', 'fn_recovery_gain')})

    summary = aggregate(positives)
    require(math.isclose(summary['dice'], saved_macro, abs_tol=1e-12, rel_tol=0),
            'Saved macro does not reproduce')
    summary.update(empty_alarm_cases=sum(r['false_positive_voxels'] > 0 for r in empty),
                   empty_false_positive_voxels=sum(r['false_positive_voxels'] for r in empty),
                   positive_false_positive_voxels=sum(r['false_positive'] for r in positives),
                   positive_false_negative_voxels=sum(r['false_negative'] for r in positives),
                   removing_only_empty_case_alarms_positive_macro_dice=summary['dice'],
                   complete_misses_unfixed_by_fp_removal=[r['case_id'] for r in positives
                                                        if r['true_positive'] == 0])
    return dict(summary=summary, size_bands={band: aggregate([r for r in positives if r['size_band'] == band])
                                            for band in ('small', 'medium', 'large')},
                largest_fp_penalties=sorted(positives, key=lambda r: r['fp_removal_gain'], reverse=True)[:5],
                positive_cases=positives, empty_cases=empty)


def bound_json(raw, expected):
    require(hashlib.sha256(raw).hexdigest() == expected, 'Source hash mismatch')
    return json.loads(raw)


def analyze(stu_raw, kd_raw):
    stu, kd = bound_json(stu_raw, STU_SHA), bound_json(kd_raw, KD_SHA)
    require([r['step'] for r in stu['reports']] == list(range(2000, 12001, 2000)),
            'Incomplete STU validation series')
    require(kd['status'] == 'CLOSED_DESCRIPTIVE_ONLY', 'KD source not closed')
    result = dict(schema='prowl.error-oracles.20261108.v1',
                  inputs_sha256=dict(stunet_native_export=STU_SHA, completed_kd_report=KD_SHA),
                  scope='exposed provided-pancreas development; within-run descriptive arithmetic',
                  limitations=[
                      'Ground-truth oracles, not deployable filters or measured threshold results.',
                      'Perfect FP removal preserves TP and FN; it cannot recover missed lesions.',
                      'FP-only and FN-only gains are nonlinear, overlap, and must not be added.',
                      'Headline is macro Dice on 36 positives, excluding 34 empty cases.',
                      'Small bands are total case lesion volume, not individual component size.',
                      'No independent-patient inference or cross-model superiority claim.',
                      'No new CT/mask, model, checkpoint or protected-test reads; no MLflow writes.',
                  ], stunet_series=[], kd_endpoints={})
    for report in stu['reports']:
        rows = [dict(case_id=r['case_id'], size_band=r['metrics']['size_band'],
                     **r['metrics']['lesion']) for r in report['cases_as_saved']]
        out = summarize(rows, report['summary_as_saved']['lesion_dice'])
        out.update(step=report['step'], report_sha256=report['report_sha256'])
        result['stunet_series'].append(out)
    for endpoint in ('selected', 'terminal'):
        result['kd_endpoints'][endpoint] = {}
        for arm in ('control', 'treatment'):
            saved = kd['endpoints'][endpoint][arm]
            out = summarize(saved['cases_detail'], saved['positive_macro_dice'])
            out.update(step=saved['step'])
            result['kd_endpoints'][endpoint][arm] = out
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stunet', type=Path, required=True)
    parser.add_argument('--kd', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.stunet.read_bytes(), args.kd.read_bytes())
    with args.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(output=str(args.output), stunet_reports=len(result['stunet_series']),
                          kd_endpoint_arms=4)))


if __name__ == '__main__':
    main()
