"""Final physical reconstruction safety and orientation integration checks."""
from itertools import permutations, product
import numpy as np
import pytest
from src.data.segmenter_native_windows_v1 import geometry, orient, tiles
from src.data.segmenter_physical_windows_v1 import physical_geometry, sample_window, PhysicalReconstructor


@pytest.mark.parametrize('axes', list(permutations(range(3))))
@pytest.mark.parametrize('signs', list(product((-1, 1), repeat=3)))
def test_physical_roundtrip_all_axis_orders_flips_and_obliquity(axes, signs):
    affine = np.eye(4)
    base = np.array([[.7, .03, 0], [0, 2., .02], [0, 0, 3.]])
    affine[:3, :3] = base[:, axes] * np.array(signs)
    affine[:3, 3] = [31., -17., 8.]
    original = np.random.default_rng(18).integers(0, 3, (5, 7, 9), dtype=np.uint8)
    native = geometry(original.shape, affine)
    target = orient(original, native)
    record = physical_geometry(native)
    expected = tiles(record['shape'], window=16, stride=8)
    recon = PhysicalReconstructor(record, window=16)
    for origin in expected:
        patch, _ = sample_window(target, record, origin, order=0, window=16)
        recon.add(origin, np.stack([patch == k for k in range(3)]).astype(np.float32))
    reconstructed = orient(recon.finish(expected).argmax(0), native, inverse=True)
    np.testing.assert_array_equal(reconstructed, original)


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'nan', 'negative', 'outside'])
def test_physical_reconstructor_refuses_invalid_work(fault):
    record = physical_geometry(geometry((8, 9, 10), np.diag([.7, 2., 3., 1.])))
    recon = PhysicalReconstructor(record, window=16)
    expected = tiles(record['shape'], window=16, stride=8)
    probabilities = np.zeros((3, 16, 16, 16), np.float32)
    probabilities[0] = 1
    with pytest.raises(ValueError):
        if fault == 'missing':
            recon.finish(expected)
        elif fault == 'duplicate':
            recon.add(expected[0], probabilities)
            recon.add(expected[0], probabilities)
        elif fault == 'outside':
            recon.add((-1, 0, 0), probabilities)
        else:
            probabilities[0, 0, 0, 0] = np.nan if fault == 'nan' else -1
            recon.add(expected[0], probabilities)
