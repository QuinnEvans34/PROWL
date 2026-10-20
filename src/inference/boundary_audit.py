"""Read-only development diagnostics; never cleans masks or admits measurements."""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree


def _world(points, affine):
    return points @ affine[:3, :3].T + affine[:3, 3]


def audit_boundary(labels, assistance, affine, roi):
    """Compare both face and full connectivity, without choosing a cleanup threshold.

    Distances are Euclidean distances between voxel centers in physical space,
    including for oblique/sheared grids. Assistance is NOT independent truth.
    """
    labels = np.asarray(labels)
    assistance = np.asarray(assistance)
    affine = np.asarray(affine, dtype=float)
    box = np.asarray(roi)
    if labels.ndim != 3 or labels.size > 32_000_000 or min(labels.shape) < 1:
        raise ValueError('Invalid or oversized label grid')
    if assistance.shape != labels.shape or not np.isin(assistance, [0, 1]).all() or not assistance.any():
        raise ValueError('Assistance must be aligned, binary and nonempty')
    if not np.isin(labels, [0, 1, 2]).all():
        raise ValueError('Unexpected prediction label')
    if (affine.shape != (4, 4) or not np.isfinite(affine).all()
            or not np.allclose(affine[3], [0, 0, 0, 1], atol=1e-8, rtol=0)
            or abs(np.linalg.det(affine[:3, :3])) < 1e-9):
        raise ValueError('Invalid affine')
    if (box.shape != (2, 3) or not np.issubdtype(box.dtype, np.integer)
            or (box[0] < 0).any() or (box[1] > labels.shape).any() or (box[1] <= box[0]).any()):
        raise ValueError('Invalid inference region')
    pts = np.argwhere(labels > 0)
    ref = np.argwhere(assistance > 0)
    # Bound point-tree allocations separately from the native-grid budget.
    if max(len(pts), len(ref)) > 2_000_000:
        raise ValueError('Foreground diagnostic budget exceeded')
    if ((pts < box[0]) | (pts >= box[1])).any() or ((ref < box[0]) | (ref >= box[1])).any():
        raise ValueError('Foreground lies outside inference region')
    reference_tree = cKDTree(_world(ref, affine))
    voxel = float(abs(np.linalg.det(affine[:3, :3])))
    report = {'schema': 'prediction-boundary-audit-v1', 'diagnostic_only': True,
              'assistance_role': 'provided pancreas used to choose inference region; not independent truth',
              'distance_basis': 'minimum Euclidean voxel-center distance in mm',
              'shape': list(labels.shape), 'native_box': box.tolist(), 'voxel_mm3': voxel,
              'assistance_voxels': len(ref),
              'assistance_box': [ref.min(0).tolist(), (ref.max(0) + 1).tolist()],
              'targets': {}}
    for name, mask in [('pancreas_union', labels > 0), ('lesion', labels == 2)]:
        target = {'voxels': int(mask.sum()), 'connectivity': {}}
        for neighbors, rank in [(6, 1), (26, 3)]:
            components, count = ndimage.label(mask, ndimage.generate_binary_structure(3, rank))
            if count > 10_000:
                raise ValueError('Component diagnostic budget exceeded')
            sizes = np.bincount(components.ravel(), minlength=count + 1)
            ordered = sorted(range(1, count + 1), key=lambda i: (-int(sizes[i]), i))
            objects = ndimage.find_objects(components)
            largest_tree = None
            rows = []
            for component in ordered:
                sl = objects[component - 1]
                coords = np.argwhere(components[sl] == component) + [s.start for s in sl]
                world = _world(coords, affine)
                if largest_tree is None:
                    largest_tree = cKDTree(world)
                distances = reference_tree.query(world)[0]
                faces = {}
                for axis in range(3):
                    for side, plane in [('low', box[0, axis]), ('high', box[1, axis] - 1)]:
                        n = int((coords[:, axis] == plane).sum())
                        if n:
                            faces[f'{axis}_{side}'] = n
                touch = ((coords == box[0]) | (coords == box[1] - 1)).any(1)
                row = {'id': component, 'voxels': len(coords),
                       'box': [coords.min(0).tolist(), (coords.max(0) + 1).tolist()],
                       'crop_faces': faces, 'crop_contact_voxels': int(touch.sum()),
                       'ct_contact_voxels': int(((coords == 0) | (coords == np.array(labels.shape) - 1)).any(1).sum()),
                       'assistance_overlap_voxels': int(assistance[tuple(coords.T)].sum()),
                       'distance_to_assistance_mm': {'min': float(distances.min()), 'max': float(distances.max())},
                       'distance_to_largest_component_mm': float(largest_tree.query(world)[0].min())}
                rows.append(row)
            target['connectivity'][str(neighbors)] = {'components': rows,
                'component_count': count, 'largest_component_crop_contact': bool(rows and rows[0]['crop_contact_voxels']),
                'boundary_component_voxels': sum(r['voxels'] for r in rows if r['crop_contact_voxels']),
                'crop_contact_voxels': sum(r['crop_contact_voxels'] for r in rows)}
        report['targets'][name] = target
    return report
