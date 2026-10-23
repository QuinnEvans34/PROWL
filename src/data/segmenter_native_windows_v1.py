"""Lossless native-grid window geometry. No labels enter inference tile selection.

Closest-RAS permutation/flip preserves obliquity and acquired spacing; it is NOT
isotropic resampling or deobliquing. All boxes use half-open voxel indices.
"""
from itertools import product
import hashlib
import numpy as np
import nibabel as nib

POLICY = dict(version='native-windows-2', window=144, stride=72,
              orientation='closest_RAS_lossless_not_deoblique',
              spacing='acquired_native', hu_window=[-100, 250],
              inference='full_CT_edge_anchored_positive_triangular_blend',
              training='cycle_complete_lesion_cover_then_component_jitter_every_fourth_uniform_CT',
              empty_training='cycle_complete_pancreas_cover_then_pancreas_jitter_every_fourth_uniform_CT')


def geometry(shape, affine):
    a = np.asarray(affine, dtype=float)
    if len(shape) != 3 or any(int(n) != n or n < 1 for n in shape):
        raise ValueError('Nonempty 3D source required')
    if a.shape != (4, 4) or not np.isfinite(a).all() or abs(np.linalg.det(a[:3, :3])) < 1e-10:
        raise ValueError('Invalid affine')
    original = nib.orientations.io_orientation(a)
    ras = nib.orientations.axcodes2ornt(('R', 'A', 'S'))
    forward = nib.orientations.ornt_transform(original, ras)
    inverse = nib.orientations.ornt_transform(ras, original)
    canonical_shape = np.asarray(shape)[np.argsort(forward[:, 0].astype(int))]
    return dict(source_shape=list(map(int, shape)), source_affine=a.tolist(),
                shape=canonical_shape.tolist(), forward=forward.tolist(), inverse=inverse.tolist(),
                affine=(a @ nib.orientations.inv_ornt_aff(forward, shape)).tolist())


def orient(array, record, *, inverse=False):
    expected = record['shape' if inverse else 'source_shape']
    if array.shape != tuple(expected):
        raise ValueError('Array/geometry mismatch')
    return nib.orientations.apply_orientation(array, np.asarray(record['inverse' if inverse else 'forward']))


def starts(length, window=144, stride=72):
    if length < 1 or window < 1 or not 1 <= stride <= window:
        raise ValueError('Invalid tiling')
    last = max(0, length-window)
    return sorted(set(list(range(0, last+1, stride)) + [last]))


def tiles(shape, window=144, stride=72):
    return list(product(*(starts(n, window, stride) for n in shape)))


def extract(array, origin, window=144):
    if len(origin) != 3 or any(type(int(o)) is not int or o != int(o) or o < 0 or o > max(0, n-window)
                              for o, n in zip(origin, array.shape)):
        raise ValueError('Invalid window origin')
    slices = tuple(slice(int(o), min(int(o)+window, n)) for o, n in zip(origin, array.shape))
    view = array[slices]
    out = np.zeros((window,)*3, dtype=array.dtype)
    out[tuple(slice(0, n) for n in view.shape)] = view
    return out, dict(pad_low=[0]*3, normalized_shape=list(view.shape))


def coverage_origins(mask, window=144):
    """Cover the ENTIRE annotated bounding field, not only component centers."""
    if not mask.any(): raise ValueError('Empty coverage support')
    axes = []
    for axis, n in enumerate(mask.shape):
        support = np.flatnonzero(mask.any(axis=tuple(i for i in range(3) if i != axis)))
        low, high = int(support[0]), int(support[-1])+1
        if high-low <= window:
            axes.append([int(np.clip((low+high-window)//2, 0, max(0, n-window)))])
        else:
            axes.append(sorted(set([min(low+s, n-window) for s in starts(high-low, window, window)])))
    return list(product(*axes))


def sample_origin(shape, centers, *, visit, seed, case_id, window=144, coverage=()):
    """Round-robin component anchors, with every fourth visit sampling all CT.

    Anchors are actual component voxels, never an outside-mask centroid.
    This guarantees component exposure, not whole-lesion containment per patch.
    """
    if visit < 0 or not centers:
        raise ValueError('Nonnegative visit and anatomical anchors required')
    key = f'{POLICY["version"]}:{seed}:{case_id}:{visit}'.encode()
    rng = np.random.Generator(np.random.PCG64(int.from_bytes(hashlib.sha256(key).digest()[:8], 'little')))
    if visit % 4 == 3:
        return tuple(int(rng.integers(max(0, n-window)+1)) for n in shape), 'uniform_CT'
    ordinal = (visit-visit//4) % (len(coverage)+len(centers))
    if ordinal < len(coverage): return tuple(coverage[ordinal]), f'coverage_{ordinal}'
    index = ordinal-len(coverage)
    center = centers[index]
    # Jitter while keeping the selected component voxel inside the patch.
    origin = tuple(int(np.clip(c-int(rng.integers(window//4, 3*window//4)), 0, max(0, n-window)))
                   for c, n in zip(center, shape))
    return origin, f'anchor_{index}'


def blend_weight(window=144):
    w = 1-np.abs((np.arange(window, dtype=np.float32)+.5)*2/window-1)
    return np.maximum(w[:, None, None]*w[None, :, None]*w[None, None, :], 1e-3)


class Reconstructor:
    def __init__(self, shape, classes=3, window=144):
        self.shape, self.window = tuple(shape), window
        self.total = np.zeros((classes, *shape), dtype=np.float32)
        self.weight = np.zeros(shape, dtype=np.float32)
        self.kernel = blend_weight(window)
        self.seen = set()

    def add(self, origin, probabilities):
        origin = tuple(origin)
        if origin in self.seen or probabilities.shape != (self.total.shape[0], self.window, self.window, self.window):
            raise ValueError('Duplicate tile or wrong prediction shape')
        if any(o < 0 or o > max(0, n-self.window) for o, n in zip(origin, self.shape)):
            raise ValueError('Out-of-bounds prediction')
        if not np.isfinite(probabilities).all() or probabilities.min() < 0 or probabilities.max() > 1:
            raise ValueError('Invalid probabilities')
        dst = tuple(slice(o, min(o+self.window, n)) for o, n in zip(origin, self.shape))
        src = tuple(slice(0, s.stop-s.start) for s in dst)
        w = self.kernel[src]
        self.total[(slice(None), *dst)] += probabilities[(slice(None), *src)]*w
        self.weight[dst] += w
        self.seen.add(origin)

    def finish(self, expected_tiles):
        if self.seen != set(map(tuple, expected_tiles)) or not np.all(self.weight > 0):
            raise ValueError('Missing tiles or reconstruction gaps')
        self.total /= self.weight[None]
        return self.total
