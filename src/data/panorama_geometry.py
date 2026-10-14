"""Setup-only PANORAMA union ROI; no cohort admission or optimizer batches.

Reuse the shared physical sampler while keeping union crop selection separate
from pancreas supervision. PanTS geometry and its existing hashes are unchanged.
"""
from copy import deepcopy
import numpy as np

from src.data import segmenter_geometry_v2 as geometry
from src.data.panorama_setup import map_labels
from src.data.source_inventory_records import content_hash, require


MAPPING = dict(version='panorama-union-geometry-1', pancreas_value=4,
               lesion_value=1, crop_values=[1,4], target_values=[0,1,2],
               label_interpolation='nearest', image_interpolation='linear')


def preprocess(image, raw, affine, recipe, *, source_identity, diagnosis,
               tick=lambda: None):
    """Produce diagnostic arrays only; unknown-lesion cases cannot use this path."""
    require(diagnosis == 'PDAC', 'Non-PDAC generic-lesion target is unknown')
    geometry.canonical_geometry(list(image.shape), affine, recipe)
    require(image.shape == raw.shape and np.isfinite(image).all(), 'Invalid CT/label arrays')
    mapped = map_labels(raw, diagnosis=diagnosis)
    box = geometry.select_pancreas_box(mapped['crop_support'], affine, recipe)
    transform = geometry.plan_geometry(list(image.shape), affine, box, recipe,
                                       source_identity=source_identity)
    # Explicitly override the source-specific selection semantics, not the sampler.
    transform['roi_origin'] = 'provided_panorama_pancreas_lesion_union'
    transform['recipe']['roi_selection'] = 'pancreas_lesion_union'
    transform['component'] = 'panorama-union-transform-1'
    low, high = recipe['hu_window']
    scaled = np.clip((image.astype(np.float32)-low)/(high-low), 0, 1)
    x = geometry.forward_field(scaled, transform, order=1, tick=tick)
    target = geometry.forward_field(mapped['target'], transform, order=0, tick=tick)
    from scipy import ndimage
    components, count = ndimage.label(mapped['lesion'], structure=np.ones((3,3,3),np.uint8))
    require(count <= 4096, 'Component inventory exceeds allocation')
    projected = geometry.forward_field(components, transform, order=0, tick=tick)
    present = set(np.unique(projected).tolist())
    lost = [i for i in range(1,count+1) if i not in present]
    identity = dict(mapping=deepcopy(MAPPING), transform=transform)
    return dict(image=x, target=target, geometry=identity,
                geometry_sha256=content_hash(identity), training_ready=False,
                lost_component_ids=lost,
                mechanical_survival_pass=not lost and bool((target==1).any())
                    and bool((target==2).any()))
