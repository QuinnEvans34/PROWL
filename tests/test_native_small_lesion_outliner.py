import numpy as np
import pytest

from scripts.diagnostics.evaluate_native_small_lesion_outliner_20261111 import (
    center_in_component, native_candidates, touches, unpack_native,
)


def test_native_components_use_physical_volume_and_anchor_inside_mask():
    mask = np.zeros((16, 16, 16), dtype=np.uint8)
    mask[1:3, 1:3, 1:3] = 2
    mask[7:15, 7:15, 7:15] = 2
    labels, candidates, boxes, voxel_mm3 = native_candidates(mask, np.diag([1, 1, 3, 1]))
    assert voxel_mm3 == pytest.approx(3)
    assert candidates.tolist() == [1]
    points = np.argwhere(labels == candidates[0])
    assert tuple(center_in_component(points, np.diag([1, 1, 3]))) in map(tuple, points)
    assert len(boxes) == 2


def test_replacement_cannot_touch_a_neighboring_component():
    shape = (8, 8, 8)
    at = lambda point: np.ravel_multi_index(tuple([[a] for a in point]), shape)
    assert touches(at((2, 2, 2)), at((3, 3, 3)), shape)
    assert not touches(at((2, 2, 2)), at((4, 3, 3)), shape)


def test_packed_native_mask_and_corrupt_padding(tmp_path):
    source = tmp_path/'mask.npz'
    shape = [1, 1, 3]
    np.savez(source, packed=np.array([0x10, 0x02], dtype=np.uint8), shape=shape)
    assert unpack_native(source, shape).flatten().tolist() == [0, 1, 2]
    np.savez(source, packed=np.array([0x10, 0x12], dtype=np.uint8), shape=shape)
    with pytest.raises(ValueError, match='Malformed packed mask'):
        unpack_native(source, shape)
