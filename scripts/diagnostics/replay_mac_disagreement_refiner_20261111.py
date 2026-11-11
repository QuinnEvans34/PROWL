"""Score a frozen CT refiner at saved cross-checkpoint disagreement prompts."""
import argparse
import gc
import json
import os
from pathlib import Path
from statistics import mean
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import torch

from scripts.diagnostics import screen_stunet_checkpoint_swaps_20261111 as saved
from scripts.diagnostics import run_mac_local_refiner_disk_20261110 as refiner_run
from scripts.diagnostics.audit_stunet_selected_dice_20261110 import SELECTED as MARGIN_INCUMBENT
from src.data.segmenter_native_windows_v1 import geometry
from src.operations.mac_teacher_supervision_v3 import run
from src.training.stunet_local_refiner_v1 import Refiner, channels, crop_record, slices, valid_support

GIB = 1024**3
MAX_PROMPTS = 4
SIZE = 64
SECONDS = 780  # Charge 120 s for the three preserved attempts.
THRESHOLDS = (.50, .70)
CHECKPOINT = Path('fit/checkpoint-2400.pt')
PROOF = ROOT / 'docs/capstone/operations/LOCAL-REFINER-MAC-CLOSEOUT-20261111.json'


def safety():
    refiner_run.safety()
    if time.time() >= refiner_run.pilot.DEADLINE:
        raise ValueError('Departure cutoff')


def verified_checkpoint(cases):
    proof = saved.read(PROOF)
    root, backup = refiner_run.OUT, refiner_run.BACKUP
    for relative in (CHECKPOINT, Path('closeout.json'), Path('ready.json')):
        if saved.sha(root / relative) != saved.sha(backup / relative):
            raise ValueError('Independent refiner artifact differs')
    if saved.sha(root / 'closeout.json') != proof['verified_closeout_sha256']:
        raise ValueError('Refiner closeout identity')
    _, parent = refiner_run.verify(proof['request_sha256'])
    train = parent['train']
    if len(train) != 108 or {r['case_id'] for r in train} & {r['case_id'] for r in cases}:
        raise ValueError('Training and development identities overlap')
    if {r['sources']['ct']['sha256'] for r in train} & {r['sources']['ct']['sha256'] for r in cases}:
        raise ValueError('Training and development images overlap')
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    checkpoint = torch.load(backup / CHECKPOINT, map_location='cpu', weights_only=True)
    if checkpoint['step'] != 2400 or not checkpoint['optimizer']['state']:
        raise ValueError('Final checkpoint state')
    model = Refiner().cpu().eval()
    model.load_state_dict(checkpoint['model'])
    return model, saved.sha(backup / CHECKPOINT)


def prompts(old, current, baseline, voxel_mm3):
    """Old lesion winners at 0.50 that overlap current raw predicted pancreas."""
    positions = np.argwhere(old >= 6)
    if not len(positions):
        return [], 0
    low, high = positions.min(0), positions.max(0) + 1
    region = slices(low, high)
    labels, count = ndimage.label(old[region] >= 6, structure=saved.STRUCTURE)
    candidates = []
    for label, box in enumerate(ndimage.find_objects(labels, max_label=count), 1):
        points = np.argwhere(labels[box] == label)
        if not 10 <= len(points) * voxel_mm3 < 1000:
            continue
        points += low + [s.start for s in box]
        indices = np.ravel_multi_index(points.T, old.shape)
        if np.isin(indices, baseline).any():
            continue
        here = current.reshape(-1)[indices]
        disagree = (here < 6) & ((here & 1) == 1)
        if not disagree.any():
            continue
        # The hint is an actual disagreement voxel closest to the candidate center.
        nearest = np.square(points[disagree] - points.mean(axis=0)).sum(axis=1).argmin()
        center = points[disagree][nearest]
        fraction_high = float(np.mean(old.reshape(-1)[indices] >= 8))
        candidates.append((fraction_high, int(disagree.sum()), len(indices), indices, center))
    candidates.sort(key=lambda x: (x[0], x[1], x[2], -int(x[3][0])), reverse=True)
    return candidates[:MAX_PROMPTS], len(candidates)


def ct_crop(image, g, window, to_source):
    low, high = np.asarray(window['source_low']), np.asarray(window['source_high'])
    corners = nib.affines.apply_affine(to_source, [low, high - 1]).astype(int)
    slab = np.asarray(image.dataobj[slices(corners.min(0), corners.max(0) + 1)], dtype=np.float32)
    oriented = nib.orientations.apply_orientation(slab, np.asarray(g['forward']))
    support = valid_support(window)
    output = np.zeros((SIZE,) * 3, dtype=np.float32)
    output[slices(window['dest_low'], window['dest_high'])] = oriented
    if not np.isfinite(output[support]).all():
        raise ValueError('Nonfinite CT window')
    return channels(output, support), support


def component_at_seed(probability, support, patch_seed, window, to_source, shape, baseline, threshold, voxel_mm3):
    labels, _ = ndimage.label((probability >= threshold) & support, structure=saved.STRUCTURE)
    inside = ((patch_seed >= 0) & (patch_seed < SIZE)).all(axis=1)
    if not inside.any():
        return np.empty(0, dtype=np.intp)
    locations = tuple(patch_seed[inside].T)
    counts = np.bincount(labels[locations])
    counts[0] = 0
    if not counts.any():
        return np.empty(0, dtype=np.intp)
    points = np.argwhere(labels == counts.argmax())
    if not 10 <= len(points) * voxel_mm3 < 1000:
        return np.empty(0, dtype=np.intp)
    points = nib.affines.apply_affine(to_source, points + window['origin']).astype(int)
    indices = np.ravel_multi_index(points.T, shape)
    if np.isin(indices, baseline).any():
        return np.empty(0, dtype=np.intp)
    return indices


def proposals(case, model, old, current, baseline, voxel_mm3):
    candidates, eligible = prompts(old, current, baseline, voxel_mm3)
    refinements = {t: [] for t in THRESHOLDS}
    if not candidates:
        return [], refinements, eligible
    src = case['sources']['ct']
    if saved.sha(src['path']) != src['sha256']:
        raise ValueError('CT identity changed')
    image = nib.load(src['path'])
    shape = case['native_shape']
    affine = np.asarray(case['native_affine'])
    if list(image.shape) != shape or not np.allclose(image.affine, affine, atol=1e-5, rtol=0):
        raise ValueError('Native CT geometry changed')
    g = geometry(shape, affine)
    to_source = nib.orientations.inv_ornt_aff(np.asarray(g['forward']), shape)
    to_ras = np.linalg.inv(to_source)
    seeds = []
    for _, _, _, seed, center in candidates:
        ras_center = nib.affines.apply_affine(to_ras, center).astype(int)
        window = crop_record(g['shape'], g['affine'], ras_center, SIZE)
        x, support = ct_crop(image, g, window, to_source)
        with torch.no_grad():
            probability = model(torch.from_numpy(x)[None])[0, 0].sigmoid().numpy()
        if not np.isfinite(probability).all():
            raise ValueError('Nonfinite refiner output')
        seed_points = np.column_stack(np.unravel_index(seed, shape))
        patch_seed = nib.affines.apply_affine(to_ras, seed_points).astype(int) - window['origin']
        seeds.append(seed)
        for threshold in THRESHOLDS:
            refined = component_at_seed(probability, support, patch_seed, window, to_source,
                                        shape, baseline, threshold, voxel_mm3)
            refinements[threshold].append(refined)
    return seeds, refinements, eligible


def within_pancreas_distance(indices, pancreas, shape, basis):
    """Use the post-edit predicted pancreas and a native-world 5 mm rule."""
    remaining = pancreas[~np.isin(pancreas, indices)]
    if not len(remaining):
        return False
    coords = lambda x: np.column_stack(np.unravel_index(x, shape)) @ basis.T
    return cKDTree(coords(remaining)).query(coords(indices), workers=1)[0].min() <= 5


def arms(seeds, refined, weak, pancreas, shape, basis):
    empty = np.empty(0, dtype=np.intp)
    # Each arm takes at most the first eligible candidate in the same frozen order.
    output = {'baseline': (empty, empty)}
    for label, candidates in [('seed', seeds), *((f'refine{int(t*100)}', refined[t]) for t in THRESHOLDS)]:
        raw = next((x for x in candidates if len(x)), empty)
        output[label + '_raw'] = (raw, empty)
        near = [x for x in candidates if len(x) and within_pancreas_distance(x, pancreas, shape, basis)]
        output[label + '_near5'] = (near[0] if near else empty, empty)
        affordable = next((x for x in near if len(weak) >= 2 * len(x)), empty)
        if label != 'seed':
            output[label + '_near5_swap'] = (affordable, weak[:2 * len(affordable)])
    return output


def open_reference(binding, shape, affine):
    if saved.sha(binding['path']) != binding['sha256']:
        raise ValueError('Reference identity changed')
    image = nib.load(binding['path'])
    if list(image.shape) != shape or not np.allclose(image.affine, affine, atol=1e-5, rtol=0):
        raise ValueError('Reference geometry changed')
    return saved.target_content(image.dataobj.get_unscaled(),
                                dict(slope=float(image.dataobj.slope), intercept=float(image.dataobj.inter)))[0]


def replay(case, current_receipt, old_receipt, expected, model):
    safety()
    shape, affine = case['native_shape'], np.asarray(case['native_affine'])
    basis = affine[:3, :3]
    voxel_mm3 = abs(float(np.linalg.det(basis)))
    current = saved.archive(current_receipt['artifact'], saved.unpack_24k, shape)
    old = saved.archive(old_receipt['artifact'], saved.unpack_12k, shape)
    index, tiers, distances, shells = saved.core_support(current, affine, trim_levels=[2, 3], grow_radii=[1.5])
    keep = (tiers > 3) | (distances <= 4)
    base = np.concatenate((index[keep], shells[1.5]))
    # Weak lesion voxels never include the incumbent core, raw pancreas, or old lesion support.
    weak = keep & (tiers <= 3) & (old.reshape(-1)[index] < 2) & ((current.reshape(-1)[index] & 1) == 0)
    order = np.lexsort((index[weak], -distances[weak], tiers[weak]))
    pancreas = np.flatnonzero((current < 4) & ((current & 1) == 1))
    seeds, refined, eligible = proposals(case, model, old, current, base, voxel_mm3)
    policies = arms(seeds, refined, index[weak][order], pancreas, shape, basis)
    del current, old

    truth = open_reference(case['sources']['lesion'], shape, affine)
    labels, count = ndimage.label(truth, structure=saved.STRUCTURE)
    labels = labels.reshape(-1)
    sizes = np.bincount(labels[labels > 0], minlength=count + 1)
    small = [int(i) for i in np.flatnonzero(sizes * voxel_mm3 < 1000) if i]
    base_score = saved.score(base, labels)
    n = int(sizes.sum())
    if (n, count) != (expected['n'], expected['reference_count']) or base_score != {
        k: expected['core'][k] for k in ('p', 't', 'hits')
    }:
        raise ValueError('Baseline lesion replay differs')
    del truth
    pancreas_truth = open_reference(case['sources']['pancreas'], shape, affine).reshape(-1)
    # Match the canonical multiclass reference: lesion takes precedence.
    pancreas_truth[labels != 0] = 0
    pan_n = int(np.count_nonzero(pancreas_truth))
    pan_t = int(np.count_nonzero(pancreas_truth[pancreas]))
    known = current_receipt['policies'][MARGIN_INCUMBENT]['pancreas']
    if (pan_n, len(pancreas), pan_t) != tuple(known[k] for k in ('target_voxels', 'predicted_voxels', 'true_positive')):
        raise ValueError('Baseline pancreas replay differs')

    results = {}
    for label, (add, remove) in policies.items():
        lesion = np.concatenate((base[~np.isin(base, remove)], add))
        pan_loss = add[np.isin(add, pancreas)]
        pan_dice = 2 * (pan_t - int(np.count_nonzero(pancreas_truth[pan_loss]))) / (pan_n + len(pancreas) - len(pan_loss))
        added_truth = saved.score(add, labels)
        results[label] = dict(saved.score(lesion, labels), added=len(add), removed=len(remove),
                              added_false_component=bool(len(add) and not added_truth['t']),
                              pancreas_relabelled=len(pan_loss), pancreas_dice=pan_dice)
    return dict(case_id=case['case_id'], n=n, components=count, small=small, voxel_mm3=voxel_mm3,
                eligible_prompts=eligible, evaluated_prompts=len(seeds),
                seed_hits=saved.score(np.unique(np.concatenate(seeds)), labels)['hits'] if seeds else [],
                refined_hits={str(t): saved.score(np.unique(np.concatenate(items)), labels)['hits'] if items else []
                              for t, items in refined.items()},
                arms=results)


def summarize(rows):
    positives = [r for r in rows if r['n']]
    empty = [r for r in rows if not r['n']]
    if (len(rows), len({r['case_id'] for r in rows}), len(positives), len(empty),
            sum(r['components'] for r in rows), sum(len(r['small']) for r in rows)) != (70, 70, 36, 34, 45, 12):
        raise ValueError('Development census')
    def metrics(key):
        def fp(cohort):
            return sum((r['arms'][key]['p'] - r['arms'][key]['t']) * r['voxel_mm3'] / 1000 for r in cohort)
        return dict(dice=mean(2*r['arms'][key]['t']/(r['n']+r['arms'][key]['p']) for r in positives),
                    recall=mean(r['arms'][key]['t']/r['n'] for r in positives),
                    small_case_recall=mean(r['arms'][key]['t']/r['n'] for r in positives if r['n']*r['voxel_mm3']<1000),
                    small_hits=sum(len(set(r['arms'][key]['hits']) & set(r['small'])) for r in positives),
                    components_hit=sum(len(r['arms'][key]['hits']) for r in positives),
                    positive_fp_ml=fp(positives), empty_fp_ml=fp(empty),
                    empty_alarms=sum(r['arms'][key]['p'] > 0 for r in empty),
                    pancreas_dice=mean(r['arms'][key]['pancreas_dice'] for r in rows),
                    added_false_components=sum(r['arms'][key]['added_false_component'] for r in rows),
                    scans_with_additions=sum(bool(r['arms'][key]['added']) for r in rows),
                    scans_with_more_fp=sum(
                        r['arms'][key]['p'] - r['arms'][key]['t'] >
                        r['arms']['baseline']['p'] - r['arms']['baseline']['t'] for r in rows),
                    lost_components=sum(len(set(r['arms']['baseline']['hits']) - set(r['arms'][key]['hits'])) for r in positives))
    baseline = metrics('baseline')
    results = {}
    for key in rows[0]['arms']:
        if key == 'baseline':
            continue
        m = metrics(key)
        m['passes'] = ('_near5' in key and m['dice'] > baseline['dice'] and m['small_hits'] > baseline['small_hits']
                       and m['recall'] >= baseline['recall'] and m['small_case_recall'] >= baseline['small_case_recall']
                       and m['pancreas_dice'] >= baseline['pancreas_dice']
                       and not (m['lost_components'] or m['added_false_components'] or m['scans_with_more_fp'])
                       and all(m[k] <= baseline[k] for k in ('positive_fp_ml', 'empty_fp_ml', 'empty_alarms')))
        results[key] = m
    def new_small(r, hits):
        return sorted(set(hits) & set(r['small']) - set(r['arms']['baseline']['hits']))
    return dict(baseline=baseline, rules=results, eligible_prompts=sum(r['eligible_prompts'] for r in rows),
                evaluated_prompts=sum(r['evaluated_prompts'] for r in rows),
                new_small_seed_hits=sum(len(new_small(r, r['seed_hits'])) for r in rows),
                new_small_refiner_hits={str(t): sum(len(new_small(r, r['refined_hits'][str(t)])) for r in rows)
                                        for t in THRESHOLDS}, rows=rows)


def worker(directory):
    cases, receipts = saved.admitted_cases()
    model, checkpoint_sha = verified_checkpoint(cases)
    for file in ('request.json', 'result.json'):
        if saved.sha(saved.OLDER/file) != saved.sha(saved.OLDER_BACKUP/file):
            raise ValueError('12k evidence differs')
    core = saved.read(saved.CORE)
    if saved.sha(saved.CORE) != saved.read(saved.CORE_PROOF)['full_local_result_sha256']:
        raise ValueError('24k incumbent changed')
    prior = {r['case_id']: dict(r, core=r['arms'][core['selected']]) for r in core['rows']}
    old_cases = {r['case_id']: r for r in saved.read(saved.OLDER/'request.json')['cases']}
    if set(old_cases) != set(prior) or set(prior) != set(receipts):
        raise ValueError('Cohort membership differs')
    rows = []
    with (directory/'cases.jsonl').open('x') as journal:
        for case in cases:
            key = case['case_id']
            if any(case[k] != old_cases[key][k] for k in ('native_shape', 'native_affine', 'sources')):
                raise ValueError('Checkpoint source mismatch')
            file = key + '.json'
            if saved.sha(saved.OLDER/file) != saved.sha(saved.OLDER_BACKUP/file):
                raise ValueError('Independent 12k receipt differs')
            row = replay(case, receipts[key], saved.read(saved.OLDER/file), prior[key], model)
            journal.write(json.dumps(row, allow_nan=False) + '\n')
            journal.flush()
            rows.append(row)
            print(json.dumps(dict(scans=len(rows), prompts=row['evaluated_prompts'])), flush=True)
            gc.collect()
        os.fsync(journal.fileno())
    result = summarize(rows)
    payload = json.dumps(dict(result, checkpoint_sha256=checkpoint_sha, policy_sha256=saved.sha(saved.CONFIG),
                              source_sha256=saved.sha(__file__), scope='exposed development, frozen CPU refiner only'),
                         indent=2, allow_nan=False)
    with (directory/'result.json').open('x') as stream:
        stream.write(payload + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        worker(args.directory)
        return
    safety()
    args.directory.mkdir()
    limit = min(SECONDS, refiner_run.pilot.DEADLINE - time.time() - 60)
    if limit < 240:
        raise ValueError('Insufficient time for supervised replay')
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
               PYTHONDONTWRITEBYTECODE='1')
    if not run([sys.executable, __file__, str(args.directory), '--worker'], args.directory,
               seconds=limit, rss_bytes=4*GIB, tick=safety, env=env):
        raise SystemExit('Replay stopped. Preserve the attempt.')


if __name__ == '__main__':
    main()
