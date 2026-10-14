"""Construct only the missing expert-PDAC production cache under the approved amendment.

No duplicate search, PanTS preprocessing, test payloads, or model work. Prior audit artifacts
are reused and remain immutable. Each consumed source and derived tensor is identity-bound.
"""
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.training.experiment_config import sha256, load_experiment, ids, resolve
from scripts.diagnostics.audit_panorama_setup import sha, observation
from scripts.diagnostics.plan_panorama_positive_cohort import plan
from src.data.source_inventory_records import require

BASE = Path('E:/PROWL/readiness/data-setup-20261010-a01')
OUT = Path('E:/PROWL/readiness/panorama-positive-run-20261012-a01')
CACHE = Path('E:/PROWL/cache/panorama-positive-20261012-a01')
PARENT = Path('E:/PROWL/readiness/pants-course-reference-20261011-a01/experiment.yaml')
NARROW = Path('E:/PROWL/readiness/panorama-narrow-readiness-20261011-a01')
EXCLUDED = ['PanTS_00000922', 'PanTS_00005105', 'PanTS_00005370', 'PanTS_00007299', 'PanTS_00007523']


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def ledger(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def reduced_parent(dev):
    """Reuse saved case metrics only; no inference or protected source reads."""
    run = Path('E:/PROWL/artifacts/pants_course_reference_dicefocal_24k_20261011')
    history = run/'execution/history.jsonl'
    groups = defaultdict(list)
    for row in ledger(history):
        if row['event'] == 'validation_case' and row['case_id'] in dev:
            groups[row['step']].append(row)
    require(sorted(groups) == list(range(2000, 24001, 2000)), 'Parent selection history incomplete')
    scores = []
    for step, rows in sorted(groups.items()):
        require(len(rows) == len(dev) and {r['case_id'] for r in rows} == set(dev), 'Parent case ledger differs')
        values = [r['metrics']['lesion']['dice'] for r in rows if r['metrics']['lesion']['target_voxels']]
        require(len(values) == 36, 'Expected 36 retained positives')
        scores.append(dict(step=step, positive_macro_dice=sum(values)/len(values)))
    best = max(scores, key=lambda r: r['positive_macro_dice'])['step']
    require(best == 14000, 'Reduced-cohort parent selection changed: reconcile retained checkpoint before launch')
    reports = {}
    for label in ('best', '024000'):
        source = Path('E:/PROWL/readiness/pants-course-retrospective-20261012')/('native-'+label)/'report.json'
        report = read(source)
        records = [r for r in report['cases'] if r['case_id'] in dev]
        require(len(records) == 70 and {r['case_id'] for r in records} == set(dev), 'Native comparison membership differs')
        positive = [r['metrics'] for r in records if r['metrics']['reference_positive']]
        empty = [r['metrics'] for r in records if not r['metrics']['reference_positive']]
        reports[label] = dict(source_report=str(source), source_sha256=sha256(source), cases=records,
            checkpoint_sha256=report['checkpoint_sha256'], step=report['step'],
            summary=dict(positive_cases=len(positive), reference_empty_cases=len(empty),
                lesion_dice=sum(r['lesion']['dice'] for r in positive)/len(positive),
                detected_cases=sum(r['case_detected'] for r in positive),
                empty_alarm_cases=sum(r['false_alarm_any'] for r in empty),
                pancreas_dice=sum(r['metrics']['pancreas']['dice'] for r in records)/len(records)))
    return dict(excluded=EXCLUDED, development=dev, selection_scores=scores,
        selected_step=best, parent_history_sha256=sha256(history), reports=reports,
        source_payload_reads=0, inference_calls=0)


def design():
    cfg = load_experiment(PARENT)
    dev = ids(resolve(cfg['_experiment']['cohort']['development_ids']))
    actual = sorted(r['study_id'] for r in read(NARROW/'provenance.json')['ambiguous_records'] if r['admitted_development'])
    require(actual == EXCLUDED and set(EXCLUDED) <= set(dev), 'Exclusion evidence changed')
    dev = [n for n in dev if n not in EXCLUDED]
    candidates = ledger(BASE/'panorama-candidates.jsonl')
    audits = ledger(BASE/'panorama-ct-union-a01/cases.jsonl')
    roster = plan(candidates, audits)
    require((roster['studies'], roster['subjects']) == (345, 344), 'Prospective roster changed')
    require(read(BASE/'panorama-ct-union-a01/summary.json')['completed'], 'Prior audit incomplete')
    require(read(BASE/'panorama-ct-union-a01/resources.json')['workers_reaped'], 'Prior audit active')
    exclusions = read(NARROW/'exclusions.json')
    require(exclusions['counts'] == {'MSD_dataset': 194, 'NIH_dataset': 80}, 'Declared exclusions differ')
    wanted = {r['study_id'] for r in roster['candidates']}
    require(not wanted.intersection(exclusions['ids']), 'Declared import included')
    rows = sorted((r for r in candidates if r['study_id'] in wanted), key=lambda r:r['study_id'])
    parent = reduced_parent(dev)
    OUT.mkdir(parents=True, exist_ok=False)
    save(OUT/'parent-reduced-comparison.json', parent)
    (OUT/'development.txt').write_text('\n'.join(dev)+'\n')
    save(OUT/'selection.json', dict(rows=rows, excluded_development=EXCLUDED,
        retained_repeated_studies=True, prior_candidate_count=345, source_subjects=344,
        policy='exploratory_declared_exclusions_plus_five_dev_holds_20261012',
        prior_evidence_sha256={str(p):sha256(p) for p in [BASE/'panorama-candidates.jsonl',
            BASE/'panorama-ct-union-a01/cases.jsonl', NARROW/'provenance.json', NARROW/'visual-review.json',
            NARROW/'exclusions.json', ROOT/'docs/capstone/operations/PANORAMA-EXPLORATORY-ADMISSION-20261012.md']},
        geometry=cfg['full_segmenter']['geometry'], training_ready=False))
    print(json.dumps(dict(development=70, positive=36, empty=34, candidates=345,
        parent_best=parent['reports']['best']['summary'], parent_final=parent['reports']['024000']['summary'])), flush=True)


def worker():
    import nibabel as nib
    import numpy as np
    from src.data.panorama_geometry import preprocess
    selected = read(OUT/'selection.json')
    audit = {r['study_id']:r for r in ledger(BASE/'panorama-ct-union-a01/cases.jsonl')}
    started = time.monotonic()
    members = {}
    with (OUT/'cache-cases.jsonl').open('x') as stream:
        for row in selected['rows']:
            name = row['study_id']; paths = {k:Path(row[k]['path']) for k in ('ct', 'label')}
            before = {k:list(observation(p)) for k,p in paths.items()}
            require(all(sha(p) == row[k]['expected_sha256'] for k,p in paths.items()), 'Consumed source changed: '+name)
            ct, mask = nib.load(paths['ct']), nib.load(paths['label'])
            require(ct.shape == mask.shape and np.allclose(ct.affine, mask.affine, rtol=0, atol=1e-5), 'Changed source grids')
            require(float(mask.dataobj.slope) == 1 and float(mask.dataobj.inter) == 0, 'Changed source label scaling')
            result = preprocess(ct.get_fdata(dtype=np.float32), mask.dataobj.get_unscaled(), ct.affine,
                selected['geometry'], source_identity=dict(study_id=name, ct_sha256=row['ct']['expected_sha256']), diagnosis='PDAC')
            require(result['mechanical_survival_pass'] and not result['lost_component_ids'], 'Component loss: '+name)
            require(result['geometry_sha256'] == audit[name]['geometry_sha256'], 'Previously audited geometry changed: '+name)
            require(before == {k:list(observation(p)) for k,p in paths.items()}, 'Source changed during construction')
            path = CACHE/(row['publisher_study_id']+'.npz')
            with path.open('xb') as f:
                np.savez_compressed(f, image=result['image'][None].astype(np.float32), target=result['target'].astype(np.uint8))
                f.flush(); os.fsync(f.fileno())
            with np.load(path, allow_pickle=False) as data:
                require(np.array_equal(data['image'], result['image'][None].astype(np.float32)) and
                    np.array_equal(data['target'], result['target']), 'Cache readback mismatch')
            meta = dict(study_id=name, subject_id=row['subject_id'], source=row, observations=before,
                cache=str(path), cache_sha256=sha256(path), geometry=result['geometry'],
                geometry_sha256=result['geometry_sha256'], mechanical_survival_pass=True,
                tensor_lesion_voxels=int((result['target']==2).sum()), tensor_pancreas_voxels=int((result['target']==1).sum()),
                mapping='panorama_union_1_to_lesion_4_to_pancreas', scientific_admission='pending_production_binding')
            metadata = path.with_suffix('.json'); save(metadata, meta)
            members[name] = dict(metadata=str(metadata), metadata_sha256=sha256(metadata),
                cache=str(path), cache_sha256=meta['cache_sha256'], subject_id=row['subject_id'])
            progress = dict(study_id=name, count=len(members), seconds=time.monotonic()-started, status='cache_readback_pass')
            stream.write(json.dumps(progress)+'\n'); stream.flush(); os.fsync(stream.fileno())
            print(json.dumps(progress), flush=True)
            del ct, mask, result
    save(OUT/'cache-complete.json', dict(completed=True, members=members, cases=len(members),
        seconds=time.monotonic()-started, selection_sha256=sha256(OUT/'selection.json'),
        duplicate_search=False, pants_cache_rebuilt=False, training_started=False))


def prepare():
    from src.operations.full_training_platform import training_guard, watch_windows, require_ac
    from scripts.train_full_segmenter import tree_bytes
    selected = read(OUT/'selection.json')
    files = [Path(__file__), ROOT/'scripts/diagnostics/audit_panorama_setup.py',
        ROOT/'src/data/panorama_geometry.py', ROOT/'src/data/panorama_setup.py',
        ROOT/'src/data/segmenter_geometry_v2.py', ROOT/'src/data/segmenter_geometry_v1.py', OUT/'selection.json']
    pins = {str(p):sha256(p) for p in files}
    pins.update(selected['prior_evidence_sha256'])
    require(all(sha256(p)==h for p,h in pins.items()), 'Preparation evidence changed')
    last=[0.]
    def tick():
        if time.monotonic()-last[0]<30:return
        require_ac()
        require(all(shutil.disk_usage(p).free >= 100*1024**3 for p in ('C:/', 'E:/')), 'Storage floor')
        require(tree_bytes('E:/PROWL/cache') <= 32*1024**3, 'Aggregate cache cap')
        require(tree_bytes(OUT) <= 4*1024**3, 'Evidence cap')
        require(all(sha256(p)==h for p,h in pins.items()), 'Pinned preparation input changed')
        last[0]=time.monotonic()
    with training_guard(ROOT/'outputs/prowl/.panorama-setup-audit.lock'):
        CACHE.mkdir(parents=True, exist_ok=False);tick()
        save(OUT/'cache-request.json', dict(pins=pins, seconds=14400, rss_bytes=12*1024**3,
            selected_studies=345, purpose='missing_production_tensors_only_no_duplicate_scan_no_models'))
        with (OUT/'cache-worker.log').open('x') as log:
            p=subprocess.Popen([sys.executable,__file__,'prepare','--worker'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2'))
            try:
                watch_windows(p,seconds=14400,rss_bytes=12*1024**3,tick=tick)
                require(all(sha256(p)==h for p,h in pins.items()), 'Producing pins changed')
            finally:save(OUT/'cache-resources.json',getattr(p,'duration_resources',{}))
        print(json.dumps({k:v for k,v in read(OUT/'cache-complete.json').items() if k!='members'}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['design','prepare'])
    parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    if args.stage=='design':design()
    elif args.worker:worker()
    else:prepare()
