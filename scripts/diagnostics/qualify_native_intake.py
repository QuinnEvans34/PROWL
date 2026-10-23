"""Bounded, separately versioned intake qualification; never scientific training."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data.segmenter_native_inputs_v1 import NativeInputs
from src.data.segmenter_native_windows_v1 import POLICY, tiles, starts, extract, orient, sample_origin, Reconstructor
from src.training.experiment_config import sha256
from src.data.manifest_records import canonical
from src.operations.full_training_platform import training_guard, watch_windows, require_ac

OUT = Path('E:/PROWL/readiness/native-intake-20261018-a02')
SETUP = Path('E:/PROWL/readiness/pants-augmentation-24k-20261017-a01')
TRAIN = Path('E:/PROWL/readiness/data-setup-20261010-a01/pants-admitted/train.txt')
MANIFEST = Path('E:/PROWL/readiness/data-setup-20261010-a01/pants-manifest.csv')


def provider():
    return NativeInputs(manifest=MANIFEST, review=SETUP/'cohort-review.json', train_file=TRAIN,
                        dev_file=SETUP/'development.txt')


def pins():
    files = list((ROOT/'src').rglob('*.py')) + [Path(__file__), ROOT/'docs/capstone/operations/PANTS-COVERAGE-INTAKE-FIX-20261018.md']
    return {str(p): sha256(p) for p in files}


def verify():
    request = json.loads((OUT/'request.json').read_text())
    amendment = OUT/'parser-amendment.json'
    if amendment.is_file():
        a = json.loads(amendment.read_text())
        if a['parent_request_sha256'] != sha256(OUT/'request.json'): raise ValueError('Amendment parent changed')
        request['pins'][str(Path(__file__))] = a['script_sha256']
    if any(sha256(p) != h for p, h in request['pins'].items()): raise ValueError('Frozen producing pin changed')
    if provider().pin != request['control_sha256']: raise ValueError('Control changed')
    return request


def read_journal(path):
    # Existing canonical() already appends a newline. Retain old evidence bytes.
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def amend_parser():
    request = json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items():
        if Path(p) != Path(__file__) and sha256(p) != h: raise ValueError('Unrelated producing change')
    a = dict(parent_request_sha256=sha256(OUT/'request.json'),script_sha256=sha256(__file__),
             change='Ignore blank journal lines and avoid writing a redundant newline; no numerical/source/sampling changes',
             failure='cohort failed before first case; retained as cohort-failed-parser; no automatic retry',
             reused_pilot_sha256=sha256(OUT/'pilot/cases.jsonl'))
    with (OUT/'parser-amendment.json').open('xb') as f:f.write(canonical(a))


def prepare():
    p = provider()
    names = json.loads(Path('E:/PROWL/readiness/input-fidelity-20261018-a01/selection.json').read_text())['train']
    if len(names) != 12 or not set(names).issubset(p.control['train']): raise ValueError('Pilot selection')
    OUT.mkdir(exist_ok=False)
    (OUT/'request.json').write_bytes(canonical(dict(pins=pins(), policy=POLICY, pilot=names,
        control_sha256=p.pin, control=p.control, scientific_training=False, test_reads=0,
        pilot_seconds=3600, cohort_seconds=21600, worker_rss_bytes=12*1024**3,
        source_identity='prior CT SHA plus unchanged four-field observation; label SHA rechecked')))


def case_check(p, name, role, pilot):
    begin = time.monotonic(); c = p.load(name, role=role)
    shape = c['target'].shape; ts = tiles(shape)
    restored = orient(c['target'] == 2, c['geometry'], inverse=True)
    if not np.array_equal(restored, c['original_lesion']): raise ValueError('Lost/shifted lesion voxels')
    original_union = (c['original_pancreas'] != 0) | (c['original_lesion'] != 0)
    if not np.array_equal(orient(c['target'] > 0, c['geometry'], inverse=True), original_union):
        raise ValueError('Lost/shifted organ voxels')
    # Cartesian tiling covers every cell iff each axis is covered. Independent
    # full-volume one-hot reconstruction below additionally exercises real pilot data.
    for n in shape:
        cover = np.zeros(n, np.uint16)
        for start in starts(n): cover[start:min(start+144, n)] += 1
        if not np.all(cover): raise ValueError('Tiling gap')
    seen = set(); sampled_lesion_voxels = 0
    exposed = np.zeros(shape, dtype=bool)
    for visit in range(18):
        origin, kind = sample_origin(shape, c['centers'], visit=visit, seed=42, case_id=name, coverage=c['coverage'])
        exposed[tuple(slice(o,min(o+144,n)) for o,n in zip(origin,shape))] = True
        if kind.startswith('anchor_'):
            index = int(kind.split('_')[1]); seen.add(index)
            center = c['centers'][index]
            if not all(o <= q < o+144 for o, q in zip(origin, center)): raise ValueError('Anchor outside window')
        patch, _ = extract(c['target'], origin)
        sampled_lesion_voxels += int((patch == 2).sum())
    if seen != set(range(len(c['centers']))): raise ValueError('Unexposed component in minimum schedule')
    support = c['target'] == 2 if c['positive'] else c['target'] > 0
    if not np.all(exposed[support]): raise ValueError('Incomplete annotated field exposure in minimum schedule')
    training_coverage = float(exposed[support].mean())
    del exposed, support
    oracle_exact = None
    if pilot:
        recon = Reconstructor(shape)
        for origin in ts:
            patch, _ = extract(c['target'], origin)
            pred = np.stack([patch == k for k in range(3)]).astype(np.float32)
            recon.add(origin, pred)
        oracle_exact = bool(np.array_equal(recon.finish(ts).argmax(0), c['target']))
        if not oracle_exact: raise ValueError('Oracle reconstruction failure')
        del recon
        render(c, p, name)
    old = c['old_transform']['native_box']; lo, hi = old
    total = int(c['original_lesion'].sum())
    retained = int(c['original_lesion'][tuple(slice(a,b) for a,b in zip(lo,hi))].sum())
    a = np.array(c['geometry']['affine'])
    r = dict(case_id=name, role=role, positive=c['positive'], source_shape=c['geometry']['source_shape'],
        native_shape=list(shape), spacing_mm=np.linalg.norm(a[:3,:3], axis=0).tolist(),
        window_edge_lengths_mm=(np.linalg.norm(a[:3,:3], axis=0)*144).tolist(),
        lesion_voxels=total, old_coverage=retained/total if total else None,
        new_field_coverage=1., roundtrip_dice=1. if total else None, roundtrip_recall=1. if total else None,
        exact_target_roundtrip=True, boundary_voxels_unchanged=True, components=len(c['centers']) if total else 0,
        component_anchors_exposed_18_visits=len(seen), all_anchors_exposed=True,
        annotated_field_exposure_18_visits=training_coverage, guaranteed_cover_windows=len(c['coverage']),
        sampled_lesion_voxels_with_repetition=sampled_lesion_voxels,
        full_field_tile_count=len(ts), oracle_reconstruction_exact=oracle_exact,
        source_sha256=c['source_sha256'], metadata_sha256=c['metadata_sha256'],
        geometry=c['geometry'], elapsed_seconds=time.monotonic()-begin,
        estimated_inference_accumulator_bytes=int(np.prod(shape))*16)
    return r


def render(c, p, name):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    image, target = c['image'], c['target']; positive = target == 2
    center = np.asarray(c['centers'][0]); origin, _ = sample_origin(target.shape, c['centers'], visit=0, seed=42, case_id=name, coverage=c['coverage'])
    fig, axes = plt.subplots(1, 3, figsize=(15,5))
    spacing = np.linalg.norm(np.array(c['geometry']['affine'])[:3,:3], axis=0)
    for axis, ax in enumerate(axes):
        other = [i for i in range(3) if i != axis]; sl = [slice(None)]*3; sl[axis] = int(center[axis])
        ax.imshow(image[tuple(sl)].T, origin='lower', cmap='gray', vmin=0, vmax=1, aspect=spacing[other[1]]/spacing[other[0]])
        for code, color in ((1, 'cyan'), (2, 'red')):
            mask = target[tuple(sl)] == code
            if mask.any() and not mask.all(): ax.contour(mask.T, levels=[.5], colors=[color], linewidths=.6)
        ax.add_patch(Rectangle((origin[other[0]],origin[other[1]]),144,144,fill=False,edgecolor='yellow',lw=1))
        ax.set_title(f'Native axis {axis}, index {center[axis]}'); ax.set_axis_off()
    fig.suptitle(name+' | cyan pancreas, red lesion, yellow first training window\nFull native field; acquired spacing/obliquity retained; not radiologist adjudication', fontsize=11)
    fig.tight_layout(); fig.savefig(OUT/'pilot'/(name+'.png'),dpi=110); plt.close(fig)


def worker(stage):
    request = verify(); p = provider(); directory = OUT/stage
    names = [(n,'train') for n in request['pilot']] if stage == 'pilot' else (
        [(n,'train') for n in p.control['train']] + [(n,'validation') for n in p.control['validation']])
    pilot_records = {}
    if stage == 'cohort':
        pilot_records = {r['case_id']: r for r in read_journal(OUT/'pilot/cases.jsonl')}
    begin = time.monotonic(); completed = []
    for name, role in names:
        r = dict(pilot_records[name], reused_pilot=True) if name in pilot_records else case_check(p,name,role,stage=='pilot')
        with (directory/'cases.jsonl').open('ab') as f:
            f.write(canonical(r)); f.flush(); os.fsync(f.fileno())
        completed.append(r)
        print(json.dumps(dict(completed=len(completed), total=len(names), case=name, seconds=time.monotonic()-begin)),flush=True)
    verify()
    (directory/'results.json').write_bytes(canonical(dict(completed=True, cases=len(completed),
        train=sum(r['role']=='train' for r in completed), development=sum(r['role']=='validation' for r in completed),
        seconds=time.monotonic()-begin, all_target_roundtrips_exact=True, all_field_coverage=1.,
        all_component_anchors_exposed=True, test_reads=0, scientific_updates=0,
        total_inference_tiles=sum(r['full_field_tile_count'] for r in completed))))


def run(stage):
    request = verify()
    if stage == 'cohort':
        if not (OUT/'pilot/visual-review.json').is_file(): raise ValueError('Human/agent visual review not recorded')
        if not json.loads((OUT/'pilot/results.json').read_text())['completed']: raise ValueError('Pilot incomplete')
    directory = OUT/stage; directory.mkdir(exist_ok=False)
    def tick():
        require_ac()
        if any(shutil.disk_usage(d).free < 100*1024**3 for d in ('C:/','E:/')): raise ValueError('Storage floor')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        tick()
        with (directory/'worker.log').open('x') as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker',stage],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            try:
                watch_windows(process, seconds=request[stage+'_seconds'], rss_bytes=request['worker_rss_bytes'],tick=tick)
            finally:
                (directory/'resources.json').write_bytes(canonical(getattr(process,'duration_resources',{})))
    print(stage+' complete; worker reaped',flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--prepare',action='store_true'); ap.add_argument('--amend-parser',action='store_true'); ap.add_argument('--run',choices=['pilot','cohort']); ap.add_argument('--worker',choices=['pilot','cohort']); args = ap.parse_args()
    if args.amend_parser: amend_parser()
    elif args.prepare: prepare()
    elif args.run: run(args.run)
    elif args.worker: worker(args.worker)
