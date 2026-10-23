"""Coverage-reserved, reproducibly varied TRAINING views; inference is unchanged."""
from copy import deepcopy
import hashlib
import numpy as np
from scipy import ndimage
from src.data.manifest_records import canonical, digest
from src.data.segmenter_pancreas_region_v1 import RegionInputs, bank, window_origin
from src.data.segmenter_physical_windows_v1 import sample_window

POLICY = dict(version='coverage-reserved-component-jitter-1', window=144,
    global_mix='three_focused_one_context', coverage_slots='floor(j*N/B),j=0..B-1',
    coverage='unchanged_union_pancreas_lesion_bank_once_per_full_schedule',
    positive_focus='26_connected_lesion_components_round_robin',
    empty_focus='26_connected_pancreas_components_round_robin',
    jitter='uniform_valid_origin_retaining_component_box_if_fits_else_anchor',
    context='identical_provided_pancreas_region_v1_rng', inference='unchanged_region_v1')


def planned_visits(names, max_steps=24000, seed=42):
    """Replay the existing patient permutation, without allocating any CT/GPU."""
    import torch
    from src.training.segmenter_full_session_v1 import POLICY as ORDER
    names = list(names)
    if not names or len(set(names)) != len(names): raise ValueError('Training membership')
    focused = dict.fromkeys(names, 0); exposure = dict.fromkeys(names, 0)
    for step in range(max_steps):
        epoch, cursor = divmod(step, len(names))
        if cursor == 0:
            key = int.from_bytes(hashlib.sha256(f'{seed}:{epoch}:{ORDER}'.encode()).digest()[:8], 'little')
            order = torch.randperm(len(names), generator=torch.Generator().manual_seed(key)).tolist()
        name = names[order[cursor]]; exposure[name] += 1
        if step % 4 != 3: focused[name] += 1
    return focused, exposure


def coverage_slots(total, required):
    if type(total) != int or type(required) != int or not 0 < required <= total:
        raise ValueError('Insufficient scheduled focus visits for complete coverage')
    return tuple(j * total // required for j in range(required))


def components(target, record):
    """Small metadata only; no dense fine-resolution label cache."""
    positive = bool((target == 2).any())
    support = target == 2 if positive else target > 0
    labels, count = ndimage.label(support, structure=np.ones((3, 3, 3)))
    if count == 0: raise ValueError('Empty focused supervision')
    factors = np.asarray(record['factors'], dtype=np.int64)
    result = []
    for index, box in enumerate(ndimage.find_objects(labels), 1):
        points = np.argwhere(labels[box] == index)
        anchor = points[np.argmin(((points - points.mean(0)) ** 2).sum(1))]
        low = np.array([s.start for s in box]); high = np.array([s.stop for s in box])
        # An integer subvoxel inside a known labeled native voxel, even for even factors.
        point = (anchor + low) * factors + (factors - 1) // 2
        result.append(dict(low=(low * factors).tolist(), high=(high * factors).tolist(),
                           anchor=point.tolist(), voxels=int(len(points))))
    return result, positive


def choose(record, cover, parts, *, step, focused_visit, total, seed, name):
    if type(step) != int or step < 0 or type(focused_visit) != int or focused_visit < 0:
        raise ValueError('Invalid sampling counters')
    slots = coverage_slots(total, len(cover))
    if step % 4 == 3:
        origin, kind = window_origin(record, cover, step=step, focused_visit=focused_visit, seed=seed, name=name)
        return origin, dict(kind=kind)
    if focused_visit >= total: raise ValueError('Focus plan exhausted')
    if focused_visit in slots:
        index = slots.index(focused_visit)
        return tuple(cover[index]), dict(kind='reserved_cover', coverage_index=index)
    if not parts: raise ValueError('Missing component metadata')
    jitter_visit = focused_visit - sum(v < focused_visit for v in slots)
    key = digest(canonical(dict(seed=seed, name=name, policy=POLICY['version'])))
    order = np.random.Generator(np.random.PCG64(int(key[:16], 16))).permutation(len(parts))
    index = int(order[jitter_visit % len(parts)]); part = parts[index]
    key = digest(canonical(dict(seed=seed, name=name, step=step, focused_visit=focused_visit,
                                policy=POLICY['version'])))
    rng = np.random.Generator(np.random.PCG64(int(key[:16], 16)))
    fits = all(h-l <= 144 for l,h in zip(part['low'], part['high']))
    low = part['low'] if fits else part['anchor']
    high = part['high'] if fits else [a+1 for a in part['anchor']]
    origin = []
    for n,l,h in zip(record['shape'], low, high):
        a, b = max(0, h-144), min(l, max(0, n-144))
        if a > b: raise ValueError('No valid component-retaining origin')
        origin.append(int(rng.integers(a, b+1)))
    return tuple(origin), dict(kind='component_jitter', component_index=index,
        jitter_visit=jitter_visit, whole_component_fits=fits, anchor=part['anchor'])


class VariedInputs(RegionInputs):
    def __init__(self, *, planned_counts, **kwargs):
        super().__init__(**kwargs)
        if set(planned_counts) != set(self.control['train']): raise ValueError('Plan membership')
        self.planned_counts = deepcopy(planned_counts); self.component_cache = {}
        self.control.update(version=POLICY['version'], training_view_policy=deepcopy(POLICY),
                            planned_focused_counts=deepcopy(planned_counts))
        self.pin = digest(canonical(self.control))

    def training_window(self, name, *, step, focused_visit, seed):
        case = self.load(name, role='train', operation='optimizer')
        return self.from_case(case, step=step, focused_visit=focused_visit, seed=seed)

    def from_case(self, case, *, step, focused_visit, seed):
        name = case['name']; self.check_role(name, 'train', 'optimizer')
        record, cover = bank(case)
        # load() rechecks source observations/hashes on every visit; cached parts are metadata only.
        key = digest(canonical(dict(source=case['source_sha256'], low=case['region_low'],
                                    high=case['region_high'], record=record)))
        cached = self.component_cache.get(name)
        if cached is None or cached[0] != key:
            cached = (key, *components(case['target'], record)); self.component_cache[name] = cached
        parts, positive = cached[1:]
        origin, trace = choose(record, cover, parts, step=step, focused_visit=focused_visit,
                               total=self.planned_counts[name], seed=seed, name=name)
        image, transform = sample_window(case['image'], record, origin, order=1)
        target, _ = sample_window(case['target'], record, origin, order=0)
        if trace['kind'] == 'component_jitter':
            anchor = tuple(a-o for a,o in zip(trace['anchor'], origin))
            if any(not 0 <= a < 144 for a in anchor) or target[anchor] != (2 if positive else 1):
                raise ValueError('Focused anchor lost during actual sampling')
        return image[None], target, transform, dict(trace, origin=list(origin),
            focused_visit=focused_visit, planned_focused_visits=self.planned_counts[name],
            coverage_windows=len(cover), positive_case=positive, lesion_voxels=int((target==2).sum()),
            region_low=case['region_low'], region_high=case['region_high'])
