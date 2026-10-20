"""Recompute the fixed October20 evidence handoff from hash-bound saved JSON only.

No arrays, weights, new inference, source changes or protected question access.
Original receipts stay in ignored outputs; the portable aggregate can be reviewed.
"""
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'outputs/prowl/model-panorama-handoff-20261020'
HASHES = {
    'ai05-native-6000-vs-8000-20261020.json': 'bd6520f106b509c84fb2997f24cff599be6f15f60b9e65f497ae91900e91ac05',
    'w03-panorama-retained-evidence-20261020.json': '91580c4d3aac0b385a00237a071a2b13af5f935192998603176303e826cd45c4',
}


def read(name):
    raw = (DIRECTORY / name).read_bytes()
    assert len(raw) < 1024**2 and hashlib.sha256(raw).hexdigest() == HASHES[name]
    return json.loads(raw)


def summary(rows):
    ms = [r['metrics'] for r in rows]
    positive = [m for m in ms if m['lesion']['target_voxels'] > 0]
    empty = [m for m in ms if m['lesion']['target_voxels'] == 0]
    recall = [m['lesion']['true_positive']/m['lesion']['target_voxels'] for m in positive]
    error = lambda m, label: abs(m[label]['predicted_voxels']-m[label]['target_voxels'])*m['voxel_mm3']
    fp = [m['lesion']['predicted_voxels']*m['voxel_mm3'] for m in empty]
    avg = lambda xs: mean(xs) if xs else None
    med = lambda xs: median(xs) if xs else None
    return dict(cases=len(ms), positive=len(positive), empty=len(empty),
        positive_lesion_recall_mean=avg(recall), positive_lesion_recall_median=med(recall),
        positive_lesion_absolute_volume_error_mean_mm3=avg([error(m,'lesion') for m in positive]),
        positive_lesion_absolute_volume_error_median_mm3=med([error(m,'lesion') for m in positive]),
        all_lesion_absolute_volume_error_mean_mm3=avg([error(m,'lesion') for m in ms]),
        pancreas_absolute_volume_error_mean_mm3=avg([error(m,'pancreas') for m in ms]),
        empty_false_alarm_count=sum(v>0 for v in fp), empty_FP_volume_total_mm3=sum(fp),
        empty_FP_volume_mean_mm3=avg(fp), positive_dice_mean=avg([m['lesion']['dice'] for m in positive]),
        positive_any_overlap_count=sum(m['lesion']['true_positive']>0 for m in positive))


def same_numbers(actual, expected):
    assert actual.keys() == expected.keys()
    for key, value in actual.items():
        if value is None: assert expected[key] is None
        else: assert math.isclose(value, expected[key], rel_tol=1e-12, abs_tol=1e-9), key


def main():
    model, panorama = [read(name) for name in HASHES]
    results = {}; by_variant = {}
    for variant, report in model['comparison'].items():
        rows = report['rows']; ids = [r['case_id'] for r in rows]
        assert len(ids) == len(set(ids)) == 70
        by_variant[variant] = {r['case_id']:r for r in rows}
        for row in rows:
            assert row['scope'] == 'native_provided_pancreas_region_development'
            assert row['step'] == report['step']
            m = row['metrics']; assert math.isfinite(m['voxel_mm3']) and m['voxel_mm3'] > 0
            for label in ('lesion','pancreas'):
                c=m[label]; t,p,tp=[c[k] for k in ('target_voxels','predicted_voxels','true_positive')]
                assert all(type(n) is int and n >= 0 for n in (t,p,tp)) and tp <= min(t,p)
                if t+p: assert math.isclose(c['dice'],2*tp/(t+p),abs_tol=1e-12)
        results[variant] = summary(rows); same_numbers(results[variant],report['summary'])
        for band, expected in report['size_strata'].items():
            same_numbers(summary([r for r in rows if r['metrics']['size_band']==band]),expected)
        assert {x['id'] for x in report['fixed_subset']} == {
            f'PanTS_{i:08d}' for i in (29,84,927,139,514,698)}
        for x in report['fixed_subset']:
            m=by_variant[variant][x['id']]['metrics']; c=m['lesion']; p=m['pancreas']; v=m['voxel_mm3']
            actual=dict(lesion_recall=c['true_positive']/c['target_voxels'] if c['target_voxels'] else None,
                lesion_absolute_volume_error_mm3=abs(c['predicted_voxels']-c['target_voxels'])*v,
                pancreas_absolute_volume_error_mm3=abs(p['predicted_voxels']-p['target_voxels'])*v,
                lesion_FP_volume_mm3=(c['predicted_voxels']-c['true_positive'])*v,
                lesion_dice=c['dice'], any_overlap_detected=c['true_positive']>0,
                false_alarm_any=c['target_voxels']==0 and c['predicted_voxels']>0)
            same_numbers(actual,{k:x[k] for k in actual})
    a,b=by_variant['baseline'],by_variant['candidate']; assert a.keys()==b.keys()
    for case in a:
        assert a[case]['reconstruction']==b[case]['reconstruction']
        assert a[case]['metrics']['voxel_mm3']==b[case]['metrics']['voxel_mm3']
        for label in ('pancreas','lesion'):
            assert a[case]['metrics'][label]['target_voxels']==b[case]['metrics'][label]['target_voxels']
    a,b=results['baseline'],results['candidate']
    preferred=(b['positive_lesion_recall_mean']>a['positive_lesion_recall_mean']
        and b['empty_FP_volume_total_mm3']<=a['empty_FP_volume_total_mm3']
        and b['positive_lesion_absolute_volume_error_mean_mm3']<=a['positive_lesion_absolute_volume_error_mean_mm3']
        and b['pancreas_absolute_volume_error_mean_mm3']<=a['pancreas_absolute_volume_error_mean_mm3'])
    assert not preferred
    members=panorama['eligibility_members']; ids={r['study_id'] for r in members}
    assert len(members)==len(ids)==345 and len({r['subject_id'] for r in members})==344
    excluded=set(panorama['exclusions']['ids']); assert len(excluded)==274 and not ids & excluded
    q=panorama['qualification']
    assert sum(q['label_headers']['counts'].values())==sum(q['ct_union']['counts'].values())==2238
    assert len(q['technical_holds']['holds'])==59
    assert len(q['union_hold'])==1 and q['union_hold'][0]['study_id'] not in ids
    assert len(q['visual']['reviews'])==5 and not q['visual']['full_cohort_QC_complete']
    assert q['production_binding']['new_cache_integrity_checked']==len(members)
    smoke=panorama['production_smoke']; updates=smoke['producer']['updates']
    assert [r['step'] for r in updates]==list(range(1,6))
    assert len({r['member_id'] for r in updates if r['member_id'].startswith('PanTS_')})==2
    assert len({r['member_id'] for r in updates if r['member_id'].startswith('panorama:')})==2
    assert {r['member_id'] for r in updates if r['member_id'].startswith('panorama:')} <= ids
    assert len(smoke['producer']['evaluations'])==2 and smoke['cold']['exact_restore']
    result=dict(receipt_sha256=HASHES, recomputed=results,
        candidate_decision='reject_preference_recall_worse', preferred=preferred,
        panorama=dict(studies=345,source_subjects=344,excluded_imports=274,
            source_audit_denominator=2238,visual_sample=5,production_smoke_updates=5,
            current_physical_window_qualified=False),
        scope='Saved development metadata arithmetic and internal consistency; no independent array audit or clinical acceptance')
    target=DIRECTORY/'local-reconciliation.json'
    with target.open('x') as stream: json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
