import numpy as np

from src.training.stunet_candidate_locator_v1 import translated
from src.training.stunet_locator_search_windows_v2 import heatmap_targets, split_components


def test_partial_component_is_neither_target_nor_background():
    labels = np.zeros((32, 32, 32), dtype=np.uint16)
    labels[24, 24, 20] = 1
    labels[:4, :4, 10] = 2
    full, partial = split_components(labels, np.array([0, 1, 17]))
    assert full == (1,)
    assert partial == (2,)
    support = np.ones_like(labels, dtype=np.uint8)
    support[np.isin(labels, partial)] = 2
    heat, valid = heatmap_targets(labels, support)
    assert heat[6, 6, 20] == 1 and valid[6, 6, 20]
    assert heat[0, 0, 10] == 0 and not valid[0, 0, 10]
    assert not valid[1, 1, 11]
    assert valid[2, 2, 12]


def test_translation_keeps_partial_support_aligned():
    labels = np.zeros((32, 32, 32), dtype=np.uint16)
    labels[4, 4, 10] = 1
    support = np.ones_like(labels, dtype=np.uint8)
    support[4, 4, 10] = 2
    _, shifted_labels, shifted_support = translated(labels, labels, support, (4, 0, 1))
    heat, valid = heatmap_targets(shifted_labels, shifted_support)
    assert not heat.any()
    assert not valid[2, 1, 11]
    assert not valid[0, 1, 11]
