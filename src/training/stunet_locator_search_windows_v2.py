"""Keep clipped component voxels out of locator supervision."""
import numpy as np
from scipy.ndimage import maximum_filter

from src.training.stunet_candidate_locator_v1 import STRIDE, center_target


def split_components(labels, sizes):
    """Distinguish complete targets from the visible parts of clipped targets."""
    present, counts = np.unique(labels[labels != 0], return_counts=True)
    if np.any(present >= len(sizes)) or np.any(present < 0):
        raise ValueError('Unknown component identifier')
    complete = counts == sizes[present]
    return tuple(present[complete]), tuple(present[~complete])


def heatmap_targets(labels, support):
    """Support codes are 0 for padding, 1 for valid, and 2 for clipped lesion."""
    valid_voxels = support > 0
    clipped = support == 2
    if np.any(clipped & (labels == 0)):
        raise ValueError('Ignored voxels must belong to a clipped lesion')
    heat, valid = center_target(np.zeros_like(labels, dtype=bool), valid_voxels)
    for component in np.unique(labels[(labels > 0) & ~clipped]):
        heat = np.maximum(heat, center_target(labels == component, valid_voxels)[0])

    layout = tuple(a for pair in zip(valid.shape, STRIDE) for a in pair)
    clipped_cells = clipped.reshape(layout).any(axis=(1, 3, 5))
    adjacent = maximum_filter(clipped_cells, size=3, mode='constant')
    # An exact center of a complete component remains a known positive.
    return heat, valid & (~adjacent | (heat == 1))
