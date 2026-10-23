import itertools
import numpy as np
import pytest
from src.data.segmenter_native_windows_v1 import geometry, orient, starts, tiles, extract, sample_origin, Reconstructor, coverage_origins


def test_all_axis_orders_flips_and_oblique_roundtrip():
    x = np.arange(5*7*9).reshape(5, 7, 9)
    for order in itertools.permutations(range(3)):
        for signs in itertools.product((-1, 1), repeat=3):
            a = np.eye(4); a[:3, :3] = np.eye(3)[:, order] @ np.diag(np.array(signs)*[.7, 1.2, 3.])
            a[0, 1] += .05; a[:3, 3] = [15, -4, 19]
            r = geometry(x.shape, a); y = orient(x, r)
            assert y.shape == tuple(r['shape'])
            np.testing.assert_array_equal(orient(y, r, inverse=True), x)
            # Physical positions are invariant, including flipped boundary voxels.
            for q in itertools.product(*[(0, n-1) for n in y.shape]):
                p = np.argwhere(x == y[q])[0]
                np.testing.assert_allclose(a @ [*p, 1], np.array(r['affine']) @ [*q, 1], atol=1e-10)


@pytest.mark.parametrize('shape', [(3, 5, 7), (8, 8, 8), (9, 17, 23), (24, 16, 9)])
def test_tiles_reconstruct_every_voxel_and_padding(shape):
    x = np.random.default_rng(2).uniform(size=shape).astype(np.float32)
    out = Reconstructor(shape, classes=2, window=8); ts = tiles(shape, 8, 4)
    for p in ts:
        patch, _ = extract(x, p, 8)
        out.add(p, np.stack((patch, 1-patch)))
    got = out.finish(ts)
    np.testing.assert_allclose(got[0], x, atol=2e-7)
    np.testing.assert_allclose(got.sum(0), 1, atol=2e-7)
    assert np.all(out.weight > 0)


def test_missing_duplicate_and_invalid_tiles_fail():
    r = Reconstructor((9, 8, 8), window=8)
    p = np.full((3, 8, 8, 8), 1/3, np.float32)
    r.add((0, 0, 0), p)
    with pytest.raises(ValueError): r.add((0, 0, 0), p)
    with pytest.raises(ValueError): r.finish(tiles((9, 8, 8), 8, 4))
    with pytest.raises(ValueError): starts(10, 8, 9)


def test_sampling_reproducible_component_exposure_and_boundaries():
    centers = [[0, 0, 0], [299, 199, 149], [100, 50, 50]]
    seen = set()
    for visit in range(16):
        args = dict(visit=visit, seed=42, case_id='train')
        p, kind = sample_origin((300, 200, 150), centers, **args)
        assert (p, kind) == sample_origin((300, 200, 150), centers, **args)
        if kind.startswith('anchor'):
            i = int(kind.split('_')[1]); seen.add(i)
            assert all(o <= c < o+144 for o, c in zip(p, centers[i]))
    assert seen == {0, 1, 2}


def test_protected_roles_rejected_before_io():
    from src.data.segmenter_native_inputs_v1 import NativeInputs
    p = object.__new__(NativeInputs)
    p.control = dict(train=['t'], validation=['d'])
    for name, role, operation in [('d','validation','optimizer'), ('test','train','audit'),
                                   ('d','train','optimizer'), ('t','test','audit')]:
        with pytest.raises(ValueError): p.check_role(name, role, operation)
    p.check_role('t','train','optimizer')
    p.check_role('d','validation','evaluator')


def test_guaranteed_cover_exposes_entire_large_lesion():
    mask = np.zeros((300,200,180),bool); mask[23:221,10:150,70:100]=True
    bank=coverage_origins(mask); seen=np.zeros_like(mask)
    for visit in range(18):
        p,_=sample_origin(mask.shape,[[30,20,80],[210,140,95]],visit=visit,seed=42,case_id='t',coverage=bank)
        seen[tuple(slice(o,o+144) for o in p)]=True
    assert np.all(seen[mask])
    assert len(bank)==2


def test_augmentation_preserves_padded_native_target():
    from src.training.segmenter_augmentation_v1 import augment
    x = np.ones((7, 9, 5), np.float32)*.5
    y = np.ones(x.shape, np.uint8); y[0,0,0] = 2
    px, transform = extract(x, (0,0,0), 16)
    py, _ = extract(y, (0,0,0), 16)
    for update in range(1, 20):
        ax, ay, trace = augment(px[None],py,transform,seed=42,update=update,case_id='t')
        assert (ay==2).sum() == 1
        assert (ay>0).sum() == y.size
        assert trace['valid_voxels'] == y.size
