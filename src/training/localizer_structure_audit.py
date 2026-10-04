"""Prediction-only structural diagnostics. Never a selected ROI/cleanup policy."""
import itertools
import math
import numpy as np
from scipy import ndimage
from src.data.source_inventory_records import require

MAX_VOXELS = 96_000_000
MAX_COMPONENTS = 100_000


def analyze(prediction, affine, *, margin_mm=10.0, heartbeat=lambda: None):
    p = np.asarray(prediction)
    a = np.asarray(affine, dtype=float)
    require(p.ndim == 3 and p.dtype == np.uint8 and
            0 < math.prod(p.shape) <= MAX_VOXELS, 'Invalid bounded uint8 prediction')
    require(a.shape == (4, 4) and np.isfinite(a).all() and
            np.allclose(a[3], [0, 0, 0, 1], rtol=0, atol=1e-8), 'Invalid affine')
    spacing = np.linalg.norm(a[:3, :3], axis=0)
    require((spacing > 0).all() and np.allclose(a[:3, :3].T @ a[:3, :3],
            np.diag(spacing**2), rtol=1e-4, atol=1e-4), 'Orthogonal axes required')
    require(math.isfinite(margin_mm) and 0 <= margin_mm <= 100, 'Invalid margin')
    foreground = 0
    for z in range(0, p.shape[2], 16):
        slab = p[:, :, z:z+16]
        require(np.isin(slab, [0, 1]).all(), 'Nonbinary prediction')
        foreground += int(np.count_nonzero(slab))
        heartbeat()
    pad = np.ceil(margin_mm / spacing).astype(int)
    labels = np.empty(p.shape, dtype=np.int32)
    count = ndimage.label(p, structure=np.ones((3, 3, 3), dtype=np.uint8), output=labels)
    heartbeat()
    require(count <= MAX_COMPONENTS, 'Component analytical budget exceeded; retain failed case')
    counts = np.zeros(count + 1, dtype=np.int64)
    for z in range(0, p.shape[2], 16):
        counts += np.bincount(labels[:, :, z:z+16].ravel(), minlength=count+1)
        heartbeat()
    slices = ndimage.find_objects(labels, max_label=count) if count else []
    del labels
    heartbeat()
    voxel_ml = abs(float(np.linalg.det(a[:3, :3]))) / 1000

    def box(lo, hi):
        lo = np.maximum(0, np.asarray(lo) - pad)
        hi = np.minimum(p.shape, np.asarray(hi) + pad)
        return dict(bounds=[lo.tolist(), hi.tolist()],
                    scan_fraction=math.prod((hi-lo).tolist())/math.prod(p.shape))

    components = []
    for label_id, (n, sl) in enumerate(zip(counts[1:], slices), 1):
        require(n > 0 and sl is not None, 'Missing component')
        lo = [s.start for s in sl]; hi = [s.stop for s in sl]
        corners = np.asarray([(*x, 1) for x in itertools.product(*zip(lo, hi))]) @ a.T
        components.append(dict(label=label_id, voxels=int(n), volume_ml=int(n)*voxel_ml,
            bounds=[lo, hi], extent_mm=((np.asarray(hi)-lo)*spacing).tolist(),
            world_box_ras_mm=[corners[:, :3].min(0).tolist(), corners[:, :3].max(0).tolist()],
            margin_box=box(lo, hi)))
    components.sort(key=lambda c: (-c['voxels'], c['label']))
    require(sum(c['voxels'] for c in components) == foreground, 'Component count disagreement')
    union = largest = None; controllers = []
    if components:
        lo = np.min([c['bounds'][0] for c in components], axis=0)
        hi = np.max([c['bounds'][1] for c in components], axis=0)
        union = box(lo, hi)
        largest = components[0]['margin_box']
        for axis in range(3):
            controllers.append(dict(axis=axis,
                low=[c['label'] for c in components if c['bounds'][0][axis] == lo[axis]],
                high=[c['label'] for c in components if c['bounds'][1][axis] == hi[axis]]))
    return dict(schema_version='localizer-structure-audit-1', connectivity=26,
        component_count=count, foreground_voxels=foreground, volume_ml=foreground*voxel_ml,
        spacing_mm=spacing.tolist(), margin_mm=margin_mm, components=components,
        union_margin_box=union, union_face_controllers=controllers,
        largest_margin_box=largest, largest_fraction=components[0]['voxels']/foreground if foreground else None,
        hypothetical_box_fraction_reduction=(1-largest['scan_fraction']/union['scan_fraction']) if foreground else None,
        component_reference_overlap='not_measured', policy_state='diagnostic_only_not_selected')


def recall_bounds(result, retained_metrics):
    """Pigeonhole bounds from old aggregate TP; no reference arrays or inferred overlap."""
    v = result['foreground_voxels']; m = retained_metrics
    n, tp = m['reference_voxels'], m['true_positive']
    require(m['predicted_voxels'] == v and type(n) is int and n > 0 and
            type(tp) is int and 0 <= tp <= min(n, v), 'Invalid retained counts')
    biggest = result['components'][0]['voxels'] if v else 0
    return dict(lower=max(0, tp-(v-biggest))/n, upper=min(tp, biggest)/n,
                interpretation='count-only bound, not measured component recall')
