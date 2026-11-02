"""Additive CT-only region bridge; does not select a model, margin or GPU recipe.

The caller must bind margins and the physical-window executor to the actual
control receipt. This pure function is not a qualified scientific launcher.
"""
from itertools import product
import nibabel as nib
import numpy as np
from src.data.segmenter_geometry_v2 import select_pancreas_box, recipe
from src.data.segmenter_native_windows_v1 import geometry, orient


def prepare(image, predicted_mask, affine, *, base_margin_mm, extra_margin_mm, max_region_voxels):
    image = np.asarray(image)
    mask = np.asarray(predicted_mask)
    if image.ndim != 3 or image.shape != mask.shape or not np.isfinite(image).all():
        raise ValueError('Finite aligned native CT and predicted mask required')
    if not np.isin(mask, [0, 1]).all() or not mask.any():
        raise ValueError('Nonempty binary localization required; no fallback')
    margin = np.asarray(extra_margin_mm, dtype=float)
    if margin.shape != (3,) or not np.isfinite(margin).all() or (margin < 0).any():
        raise ValueError('Explicit finite physical margins required')
    if type(max_region_voxels) is not int or max_region_voxels <= 0:
        raise ValueError('Explicit region allocation bound required')
    parent = geometry(image.shape, affine)
    # Preserve the control's two separate ceil operations in SOURCE index planes.
    source_low, source_high = np.asarray(select_pancreas_box(mask, affine, recipe(margin_mm=base_margin_mm)))
    plane = 1 / np.linalg.norm(np.linalg.inv(np.asarray(affine)[:3, :3]), axis=1)
    padding = np.ceil(margin / plane).astype(np.int64)
    source_low = np.maximum(0, source_low-padding)
    source_high = np.minimum(mask.shape, source_high+padding)
    inverse = nib.orientations.inv_ornt_aff(np.asarray(parent['forward']), mask.shape)
    points = np.asarray([list(p)+[1] for p in product(*zip(source_low,source_high-1))])
    points = (np.linalg.inv(inverse) @ points.T).T[:, :3]
    if not np.allclose(points,np.rint(points)):
        raise ValueError('Nonintegral orientation')
    points=np.rint(points).astype(int);low=points.min(0);high=points.max(0)+1
    if int(np.prod(high - low, dtype=np.int64)) > max_region_voxels:
        raise ValueError('Region allocation bound exceeded')
    slices = tuple(slice(int(a), int(b)) for a, b in zip(low, high))
    normalized = np.clip(orient(image, parent)[slices], -100, 250).astype(np.float32)
    normalized += 100
    normalized /= 350
    local_affine = np.array(parent['affine'], dtype=float)
    local_affine[:3, 3] = (local_affine @ [*low, 1])[:3]
    return dict(image=np.ascontiguousarray(normalized), geometry=geometry(high-low, local_affine),
                parent_geometry=parent, region_low=low.tolist(), region_high=high.tolist(),
                base_margin_mm=float(base_margin_mm), extra_margin_mm=margin.tolist(), predicted_voxels=int(mask.sum()),
                reference_inputs_used=False, component='predicted-physical-region-v1')
