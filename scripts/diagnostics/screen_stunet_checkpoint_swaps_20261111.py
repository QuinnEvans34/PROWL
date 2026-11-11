"""Replay fixed 12k candidate swaps against the saved 24k core mask on CPU."""
import argparse
import gc
import json
from pathlib import Path
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

from scripts.diagnostics.audit_stunet_selected_dice_20261110 import admitted_cases, read, sha
from scripts.diagnostics.probe_stunet_mps_inference_20261108_v2 import safety
from scripts.diagnostics.screen_stunet_lesion_core_20261110 import core_support, score
from src.data.segmenter_content_v1 import target_content
from src.inference.lesion_confidence_screen_v2 import unpack as unpack_12k
from src.inference.standard_segmentation_postprocess_v1 import MAXIMUM_DISTANCE_MM
from src.inference.stunet_margin_screen_20261110 import STRUCTURE, unpack as unpack_24k

ARTIFACTS = Path('/Volumes/PROWL-Data/PROWL/artifacts')
OLDER = ARTIFACTS / 'stunet-confidence-mac-20261108/screen-03'
OLDER_BACKUP = Path.home() / 'PROWL-Backups/stunet-confidence-mac-20261108-03'
CORE = Path('/tmp/prowl-core-screen-20261110.ImvTkV/result.json')
CORE_PROOF = ROOT / 'docs/capstone/evaluation/STUNET-24K-CONFIDENT-CORE-RESULTS-20261110.json'
CONFIG = ROOT / 'configs/inference/segmentation-postprocessing-v1.json'
RULES = {f'{level}_{ratio}to1': (level, ratio) for level in ('.50', '.60') for ratio in (1, 2)}


def archive(artifact, unpack, shape):
    local, backup = (Path(artifact[key]) for key in ('path', 'backup'))
    if local.stat().st_dev == backup.stat().st_dev or any(sha(p) != artifact['sha256'] for p in (local, backup)):
        raise ValueError('Archive or independent copy changed')
    with np.load(backup, allow_pickle=False) as saved:
        if saved['shape'].tolist() != shape:
            raise ValueError('Prediction geometry changed')
        return unpack(saved['packed'], shape)


def older_candidate(old, current, baseline, basis, level):
    """Find at most one small, disconnected, pancreas-adjacent 12k lesion."""
    predicted_pancreas = (current < 6) & ((current & 1) == 1)
    locations = np.argwhere((old >= level) & ~predicted_pancreas)
    if not len(locations):
        return np.empty(0, dtype=np.intp)
    low, high = locations.min(0), locations.max(0) + 1
    roi = tuple(slice(l, h) for l, h in zip(low, high))
    labels, count = ndimage.label((old[roi] >= level) & ~predicted_pancreas[roi], structure=STRUCTURE)
    del locations
    raw_pancreas = np.argwhere(predicted_pancreas)
    if not len(raw_pancreas):
        return np.empty(0, dtype=np.intp)
    tree = cKDTree(raw_pancreas @ basis.T)
    occupied = cKDTree(np.column_stack(np.unravel_index(baseline, old.shape)))
    voxel_mm3 = abs(float(np.linalg.det(basis)))
    candidates = []
    for component, box in enumerate(ndimage.find_objects(labels, max_label=count), 1):
        points = np.argwhere(labels[box] == component)
        if not 10 <= len(points) * voxel_mm3 < 1000:
            continue
        points += low + np.array([s.start for s in box])
        if (occupied.query(points, p=np.inf, workers=1)[0] <= 1).any():
            continue
        if tree.query(points @ basis.T, workers=1)[0].min() > MAXIMUM_DISTANCE_MM:
            continue
        indices = np.ravel_multi_index(points.T, old.shape)
        values = old.reshape(-1)[indices]
        candidates.append((float(np.mean(values >= 8)), len(indices), -int(indices[0]), indices))
    return max(candidates, key=lambda x: x[:3])[3] if candidates else np.empty(0, dtype=np.intp)


def replay(case, current_receipt, old_receipt, expected):
    safety()
    shape, affine = case['native_shape'], np.asarray(case['native_affine'])
    current = archive(current_receipt['artifact'], unpack_24k, shape)
    old = archive(old_receipt['artifact'], unpack_12k, shape)
    index, tiers, distances, shells = core_support(current, affine, trim_levels=[2, 3], grow_radii=[1.5])
    keep = (tiers > 3) | (distances <= 4)
    base = np.concatenate((index[keep], shells[1.5]))
    if len(np.unique(base)) != len(base):
        raise ValueError('Overlapping incumbent voxels')
    # Lowest saved tier first, then farthest from the 24k core. Protect old raw
    # support, the incumbent core, and the incumbent's existing growth shell.
    weak = keep & (tiers <= 3) & (old.reshape(-1)[index] < 2)
    order = np.lexsort((index[weak], -distances[weak], tiers[weak]))
    eligible_drop = index[weak][order]
    additions = {level: older_candidate(old, current, base, affine[:3, :3], tier)
                 for level, tier in (('.50', 6), ('.60', 8))} if len(base) else {}
    candidate_sets = {}
    for rule, (level, ratio) in RULES.items():
        added = additions.get(level, np.empty(0, dtype=np.intp))
        if not len(added) or len(eligible_drop) < ratio * len(added):
            candidate_sets[rule] = (base, 0, 0)
            continue
        removed = eligible_drop[:ratio * len(added)]
        candidate_sets[rule] = (np.concatenate((base[~np.isin(base, removed)], added)), len(added), len(removed))
    del current, old
    source = case['sources']['lesion']
    if sha(source['path']) != source['sha256']:
        raise ValueError('Reference hash changed')
    image = nib.load(source['path'])
    if list(image.shape) != shape or not np.allclose(image.affine, affine, atol=1e-5, rtol=0):
        raise ValueError('Reference geometry changed')
    truth, _ = target_content(image.dataobj.get_unscaled(),
        dict(slope=float(image.dataobj.slope), intercept=float(image.dataobj.inter)))
    labels, count = ndimage.label(truth, structure=STRUCTURE)
    labels = labels.reshape(-1)
    voxel_mm3 = abs(float(np.linalg.det(affine[:3, :3])))
    sizes = np.bincount(labels[labels > 0], minlength=count + 1)
    small = [int(i) for i in np.flatnonzero(sizes * voxel_mm3 < 1000) if i]
    baseline = score(base, labels)
    reference_count = int(sizes.sum())
    if (baseline != {k: expected['core'][k] for k in ('p', 't', 'hits')}
            or (reference_count, count) != (expected['n'], expected['reference_count'])):
        raise ValueError('Selected 24k core replay differs')
    results = {name: dict(score(indices, labels), added=added, removed=removed)
               for name, (indices, added, removed) in candidate_sets.items()}
    return dict(case_id=case['case_id'], n=reference_count, components=count, small=small,
                voxel_mm3=voxel_mm3, baseline=baseline, rules=results)


def summarize(rows):
    positive = [r for r in rows if r['n']]
    empty = [r for r in rows if not r['n']]
    if (len(rows), len({r['case_id'] for r in rows}), len(positive), len(empty),
            sum(r['components'] for r in rows), sum(len(r['small']) for r in rows)) != (70, 70, 36, 34, 45, 12):
        raise ValueError('Benchmark census')
    def metrics(get):
        def fp(cohort):
            return sum((get(r)['p'] - get(r)['t']) * r['voxel_mm3'] / 1000 for r in cohort)
        return dict(dice=mean(2 * get(r)['t'] / (r['n'] + get(r)['p']) for r in positive),
                    recall=mean(get(r)['t'] / r['n'] for r in positive),
                    small_case_recall=mean(get(r)['t'] / r['n'] for r in positive if r['n']*r['voxel_mm3']<1000),
                    positive_fp_ml=fp(positive), empty_fp_ml=fp(empty),
                    empty_alarms=sum(get(r)['p'] > 0 for r in empty),
                    small_hits=sum(len(set(r['small']) & set(get(r)['hits'])) for r in positive),
                    total_tp=sum(get(r)['t'] for r in positive),
                    components_hit=sum(len(get(r)['hits']) for r in positive))
    baseline = metrics(lambda r: r['baseline'])
    results = {}
    for rule in RULES:
        result = metrics(lambda r: r['rules'][rule])
        result['scans_changed'] = sum(bool(r['rules'][rule]['added']) for r in rows)
        result['lost_components'] = sum(len(set(r['baseline']['hits']) - set(r['rules'][rule]['hits'])) for r in positive)
        result['added_voxels'] = sum(r['rules'][rule]['added'] for r in rows)
        result['removed_voxels'] = sum(r['rules'][rule]['removed'] for r in rows)
        result['passes'] = (result['dice'] > baseline['dice'] and result['small_hits'] > baseline['small_hits']
                            and not result['lost_components'] and all(result[k] >= baseline[k]
                                for k in ('recall', 'small_case_recall', 'total_tp'))
                            and all(result[k] <= baseline[k] for k in ('positive_fp_ml', 'empty_fp_ml', 'empty_alarms')))
        results[rule] = result
    return baseline, results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    cases, receipts = admitted_cases()
    for name in ('request.json', 'result.json'):
        if sha(OLDER / name) != sha(OLDER_BACKUP / name):
            raise ValueError('12k request/result does not match independent copy')
    core = read(CORE)
    if sha(CORE) != read(CORE_PROOF)['full_local_result_sha256']:
        raise ValueError('24k core summary changed')
    core_cases = {r['case_id']: dict(r, core=r['arms'][core['selected']]) for r in core['rows']}
    old_cases = {r['case_id']: r for r in read(OLDER / 'request.json')['cases']}
    if set(old_cases) != set(receipts) or set(core_cases) != set(receipts):
        raise ValueError('Checkpoint cohort mismatch')
    rows = []
    for case in cases:
        name = case['case_id']
        old_case = old_cases[name]
        if any(old_case[key] != case[key] for key in ('native_shape', 'native_affine', 'sources')):
            raise ValueError('Source identities or native geometry differ')
        older_receipt = OLDER / (name + '.json')
        if sha(older_receipt) != sha(OLDER_BACKUP / older_receipt.name):
            raise ValueError('12k case receipt mismatch')
        rows.append(replay(case, receipts[name], read(older_receipt), core_cases[name]))
        print(f'Replayed {len(rows)}/70', flush=True)
        gc.collect()
    baseline, results = summarize(rows)
    with args.output.open('x') as stream:
        json.dump(dict(baseline=baseline, rules=results, rows=rows, core_sha256=sha(CORE),
                       old_request_sha256=sha(OLDER/'request.json'), policy_sha256=sha(CONFIG)),
                  stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
