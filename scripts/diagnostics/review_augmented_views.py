"""Audit saved augmentation results only; no inference, training or CT reads."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.training.experiment_config import sha256
from scripts.diagnostics.review_panorama_positive_run import native_summary

RUN = Path('E:/PROWL/artifacts/pants_only_augmented_views_24k_win_20261017')
SETUP = Path('E:/PROWL/readiness/pants-augmentation-24k-20261017-a01')
CONTROL = Path('E:/PROWL/readiness/panorama-positive-run-20261012-a01/parent-reduced-comparison.json')
OUT = Path('E:/PROWL/readiness/pants-augmentation-review-20261018-a01')


def read(path):
    return json.loads(path.read_text())


def compare(left, right):
    a = {r['case_id']: r['metrics'] for r in left}
    b = {r['case_id']: r['metrics'] for r in right}
    assert len(a) == len(left) == len(b) == len(right) and a.keys() == b.keys()
    for n in a:
        for key in ('reference_positive', 'reference_components', 'target_volume_mm3', 'size_band'):
            assert a[n][key] == b[n][key], (n, key)
        for organ in ('lesion', 'pancreas'):
            assert a[n][organ]['target_voxels'] == b[n][organ]['target_voxels']
    pos = sorted(n for n in a if a[n]['reference_positive'])
    empty = sorted(set(a)-set(pos))
    assert pos and empty
    vectors = dict(dice=[b[n]['lesion']['dice']-a[n]['lesion']['dice'] for n in pos],
        detection=[int(b[n]['case_detected'])-int(a[n]['case_detected']) for n in pos],
        false_alarm=[int(b[n]['false_alarm_any'])-int(a[n]['false_alarm_any']) for n in empty],
        pancreas=[b[n]['pancreas']['dice']-a[n]['pancreas']['dice'] for n in sorted(a)])
    rng = np.random.default_rng(20261017)
    stats = {}
    for key, values in vectors.items():
        v = np.asarray(values)
        assert np.isfinite(v).all()
        draws = v[rng.integers(len(v), size=(10000, len(v)))].mean(axis=1)
        stats[key] = dict(difference=float(v.mean()), ci95=np.quantile(draws, [.025, .975]).tolist())
    burden = {k: sum(m[n]['lesion']['predicted_voxels'] for n in empty) for k, m in [('control', a), ('treatment', b)]}
    guards = dict(detection=stats['detection']['difference'] >= -.03,
        false_alarm=stats['false_alarm']['difference'] <= .03,
        pancreas=stats['pancreas']['difference'] >= -.02,
        empty_voxel_burden=burden['treatment'] <= burden['control'])
    accepted = all(guards.values()) and stats['dice']['difference'] >= .02 and stats['dice']['ci95'][0] > 0
    rejected = not all(guards.values()) or stats['dice']['ci95'][1] < .02
    return dict(decision='accepted' if accepted else 'rejected' if rejected else 'inconclusive',
        null_hypothesis='rejected' if stats['dice']['ci95'][0] > 0 else 'not_rejected',
        metrics=stats, guardrails=guards, empty_predicted_voxels=burden,
        seed=20261017, resamples=10000, positive_cases=len(pos), empty_cases=len(empty),
        improved=sum(x > 0 for x in vectors['dice']), worsened=sum(x < 0 for x in vectors['dice']),
        size_bands={band: dict(n=len(names), control_dice=float(np.mean([a[n]['lesion']['dice'] for n in names])),
            treatment_dice=float(np.mean([b[n]['lesion']['dice'] for n in names])))
            for band in ('small', 'medium', 'large') if (names := [n for n in pos if a[n]['size_band'] == band])})


def main():
    hpath = RUN/'execution/history.jsonl'
    events = [json.loads(line) for line in hpath.read_text().splitlines()]
    assert events[-1]['event'] == 'completed', 'Native endpoint work not finished'
    resources = read(SETUP/'training-resources.json')
    assert resources['workers_reaped']
    receipt = SETUP/'ready.json'
    assert sha256(receipt) == '139dd1a6ad52569c2567a713c37599c882de92e93c4a91fd46966ce3688db246'
    pins = read(receipt)['file_sha256']
    assert all(sha256(p) == expected for p, expected in pins.items()), 'Producing pin changed'
    assert sha256(CONTROL) == 'e0d2fa007873bb49aaa78d440bda07054216cd958c21db689a9f30e2fde321d5'
    parent = read(CONTROL)
    updates = [r for r in events if r['event'] == 'update']
    assert [r['step'] for r in updates] == list(range(1, 24001))
    vals = [r for r in events if r['event'] == 'validation']
    assert [r['step'] for r in vals] == list(range(2000, 24001, 2000))
    best = max(vals, key=lambda r: r['lesion_positive_macro_dice'])
    for val in vals:
        cases = [r for r in events if r['event'] == 'validation_case' and r['step'] == val['step']]
        assert len(cases) == 70 and {r['case_id'] for r in cases} == set(parent['development'])
        scores = [r['metrics']['lesion']['dice'] for r in cases if r['metrics']['lesion']['target_voxels']]
        assert len(scores) == 36 and abs(sum(scores)/36-val['lesion_positive_macro_dice']) < 1e-12
    reports = {e: read(RUN/f'execution/native-{e}.json') for e in ('selected', 'terminal')}
    for e, r in reports.items():
        assert r['step'] == (best['step'] if e == 'selected' else 24000)
        assert len(r['cases']) == 70 and {c['case_id'] for c in r['cases']} == set(parent['development'])
        assert r['checkpoint_sha256'] == sha256(RUN/'execution'/('best.pt' if e == 'selected' else 'last.pt'))
    backup = Path('C:/Users/quinn/PROWL-Backups')/RUN.name
    paths = [hpath, *sorted((RUN/'execution').glob('*.pt')), *sorted((RUN/'execution').glob('native-*.json'))]
    hashes = {str(p): sha256(p) for p in paths}
    assert all(sha256(backup/p.name) == hashes[str(p)] for p in paths), 'Backup mismatch'
    result = dict(primary=compare(parent['reports']['best']['cases'], reports['selected']['cases']),
        mandatory_secondary=compare(parent['reports']['024000']['cases'], reports['terminal']['cases']),
        summaries={k: native_summary(rows) for k, rows in dict(control_selected=parent['reports']['best']['cases'],
            augmented_selected=reports['selected']['cases'], control_final=parent['reports']['024000']['cases'],
            augmented_final=reports['terminal']['cases']).items()},
        selected_step=best['step'], tensor_curve=vals, resources=resources,
        training_seconds=events[-1]['training_seconds'], total_seconds=events[-1]['elapsed_seconds'],
        verified_producing_pins=len(pins), independent_backups_match=True, evidence_sha256=hashes,
        control_sha256=sha256(CONTROL), review_code_sha256=sha256(__file__),
        bootstrap_unit='Sorted paired PanTS case IDs, treated as patients under frozen cohort',
        scope='Exploratory reused development; single seed; provided pancreas ROI; not external validation',
        review_optimizer_updates=0, review_inference_calls=0, review_test_reads=0)
    OUT.mkdir(exist_ok=False)
    with (OUT/'results.json').open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in result.items() if k not in ('evidence_sha256', 'tensor_curve')}, indent=2))


if __name__ == '__main__':
    main()
