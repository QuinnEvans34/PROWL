"""Versioned, stateless augmentation of verified PanTS optimizer batches only.

The historical Session, cache, geometry and evaluator remain unmodified. Spatial
operations are exact permutations; only CT values within geometric support receive
intensity augmentation. The ordinary model RNG and case sampler are not consumed.
"""
from copy import deepcopy
import hashlib
import json

import numpy as np

from src.data import segmenter_full_batch_v1 as boundary
from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require
from src.training.experiment_config import sha256
from src.training.segmenter_full_session_v1 import Session

POLICY = 'pants_cached_view_augmentation_v1'


def augmentation_identity():
    # Policy constants below are versioned code; NumPy also governs noise sampling.
    return dict(policy=POLICY, numpy_version=np.__version__, rng='PCG64_SHA256_first8_little_endian')


def support_mask(shape, transform):
    low, size = transform['pad_low'], transform['normalized_shape']
    require(len(shape) == len(low) == len(size) == 3 and
            all(type(v) is int for v in list(low) + list(size)) and
            all(0 <= a and 0 < n and a+n <= s for a, n, s in zip(low, size, shape)),
            'Invalid cached geometric support')
    support = np.zeros(shape, dtype=bool)
    support[tuple(slice(a, a+n) for a, n in zip(low, size))] = True
    return support


def augment(image, target, transform, *, seed, update, case_id):
    require(type(seed) is int and 0 <= seed < 2**32 and type(update) is int and update > 0
            and isinstance(case_id, str) and case_id, 'Invalid augmentation address')
    require(image.dtype == np.float32 and image.shape == (1, *target.shape) and
            target.ndim == 3 and target.shape[0] == target.shape[1] and
            np.issubdtype(target.dtype, np.integer) and np.isin(target, [0, 1, 2]).all()
            and np.isfinite(image).all() and image.min() >= 0 and image.max() <= 1,
            'Invalid augmentation tensors')
    support = support_mask(target.shape, transform)
    require(not np.any(image[0, ~support]) and not np.any(target[~support]),
            'Cached padding must be zero')
    address = f'{POLICY}:{seed}:{update}:{case_id}'
    rng_seed = int.from_bytes(hashlib.sha256(address.encode('utf-8')).digest()[:8], 'little')
    rng = np.random.Generator(np.random.PCG64(rng_seed))
    x, y = image[0].copy(), target.copy()
    flips = []
    for axis in range(3):
        take = bool(rng.random() < .2); flips.append(take)
        if take:
            x, y, support = (np.flip(a, axis=axis) for a in (x, y, support))
    k = int(rng.integers(1, 4)) if rng.random() < .2 else 0
    if k:
        x, y, support = (np.rot90(a, k=k, axes=(0, 1)) for a in (x, y, support))
    scale = float(rng.uniform(.9, 1.1)) if rng.random() < .15 else None
    shift = float(rng.uniform(-.1, .1)) if rng.random() < .15 else None
    noise = bool(rng.random() < .2)
    # Include valid zero-HU-window voxels; intensity is not a support mask.
    values = x[support].copy()
    if scale is not None: values *= scale
    if shift is not None: values += shift
    if noise: values += rng.normal(0., .01, size=values.shape).astype(np.float32)
    x = np.zeros(target.shape, dtype=np.float32)
    x[support] = np.clip(values, 0., 1.)
    y = np.ascontiguousarray(y)
    trace = dict(policy=POLICY, seed=rng_seed, one_based_update=update, flips=flips,
                 rotation_k=k, rotation_axes=[0, 1], intensity_scale=scale,
                 intensity_shift=shift, gaussian_noise=noise, noise_standard_deviation=.01,
                 valid_voxels=int(support.sum()), support_sha256=boundary.array_hash(support),
                 class_counts=np.bincount(y.reshape(-1), minlength=3).tolist())
    return x[None], y, trace


class OptimizerViews:
    """One-update adapter. Evaluation never receives this provider."""
    def __init__(self, provider, *, seed, update):
        self.provider, self.seed, self.update = provider, seed, update
        self.trace = None

    def __getattr__(self, key): return getattr(self.provider, key)

    def get(self, name, *, role, operation):
        require(role == 'train' and operation == 'optimizer', 'Augmentation is optimizer-only')
        require(self.trace is None, 'Only one augmented batch per update')
        batch = self.provider.get(name, role=role, operation=operation)
        x, y = batch.checked(self.provider.pin, operation, name)
        metadata = self.provider.root / (name + '.json')
        require(sha256(metadata) == self.provider.members[name]['metadata_sha256'],
                'Augmentation metadata changed')
        transform = json.loads(metadata.read_text())['transform']
        ax, ay, trace = augment(x, y, transform, seed=self.seed, update=self.update, case_id=name)
        result = boundary.Batch(boundary._TOKEN, study_id=name, role=role, operation=operation,
                                image=ax, target=ay, control_sha256=self.provider.pin)
        self.trace = dict(trace, source_batch_sha256=batch.hashes(), transformed_batch_sha256=result.hashes())
        return result


class AugmentedSession:
    def __init__(self, raw):
        self.raw = raw
        self.identity = dict(version='segmenter-augmented-session-1', raw=deepcopy(raw.identity),
                             augmentation=augmentation_identity())
        self.identity_pin = digest(canonical(self.identity))

    def __getattr__(self, key): return getattr(self.raw, key)

    def _check(self):
        require(digest(canonical(self.identity)) == self.identity_pin and
                self.identity['augmentation'] == augmentation_identity(), 'Augmentation identity changed')

    def update(self, provider):
        self._check()
        adapter = OptimizerViews(provider, seed=self.config['seed'], update=self.step+1)
        result = self.raw.update(adapter)
        require(adapter.trace is not None, 'Missing augmentation evidence')
        return dict(result, augmentation=adapter.trace)

    def state(self):
        self._check()
        return dict(version=1, identity=deepcopy(self.identity), identity_sha256=self.identity_pin,
                    raw=self.raw.state())

    @classmethod
    def restore(cls, state, identity):
        require(state['version'] == 1 and state['identity'] == identity and
                state['identity_sha256'] == digest(canonical(identity)) and
                identity['augmentation'] == augmentation_identity(), 'Augmentation checkpoint identity mismatch')
        result = cls(Session.restore(state['raw'], identity['raw']))
        require(result.identity == identity, 'Augmentation implementation identity mismatch')
        return result
