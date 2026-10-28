"""Validate frozen source geometry before predicting the unchanged ITK output grid."""
import itertools
import numpy as np
import SimpleITK as sitk
from src.data.segmenter_teacher_geometry_v2 import covering_size, checked_shape
from scripts.diagnostics.review_mac_teacher_failure import coverage


def checked_header_grid(header, meta, *, max_voxels=256000000):
    size = np.array(header.GetSize(), dtype=int)
    spacing = np.array(header.GetSpacing(), dtype=float)
    direction = np.array(header.GetDirection(), dtype=float).reshape(3, 3)
    origin = np.array(header.GetOrigin(), dtype=float)
    checked_shape(size.tolist(), max_voxels)
    if not np.isfinite(spacing).all() or np.any(spacing <= 0):
        raise ValueError('Invalid header spacing')
    if not np.allclose(direction.T @ direction, np.eye(3), atol=1e-5, rtol=0):
        raise ValueError('Nonorthogonal header')
    parent = meta['parent_geometry']
    if size.tolist() != parent['source_shape']:
        raise ValueError('Source shape differs from frozen metadata')
    affine = np.eye(4)
    affine[:3, :3] = direction * spacing
    affine[:3, 3] = origin
    affine = np.diag([-1., -1., 1., 1.]) @ affine
    corners = np.array([(*c, 1.) for c in itertools.product(*[(0, n-1) for n in size])]).T
    delta = (affine - np.asarray(parent['source_affine'])) @ corners
    if not np.isfinite(delta).all() or np.max(np.abs(delta)) > 1e-4:
        raise ValueError('Source world geometry differs from frozen metadata')
    # Ask ITK only for its orientation permutation, without reading CT voxels.
    probe = sitk.Image([2, 2, 2], sitk.sitkUInt8)
    probe.SetDirection(tuple(direction.flat))
    orient = sitk.DICOMOrientImageFilter(); orient.SetDesiredCoordinateOrientation('RAI')
    orient.Execute(probe)
    order = np.array(orient.GetPermuteOrder(), dtype=int)
    flips = np.array(orient.GetFlipAxes(), dtype=bool)
    origin = origin + direction[:, order] @ np.where(flips, (size[order]-1)*spacing[order], 0.)
    direction = direction[:, order] * np.where(flips, -1., 1.)
    size, spacing = size[order], spacing[order]
    if tuple(spacing) != (1., 1., 1.):
        for target in ((1., 1., spacing[2]), (1., 1., 1.)):
            size = np.array(covering_size(size, spacing, target)); spacing = np.array(target)
    checked_shape(size.tolist(), max_voxels)
    out = np.eye(4); out[:3, :3] = direction * spacing; out[:3, 3] = origin
    out = np.diag([-1., -1., 1., 1.]) @ out @ np.eye(4)[:, [2, 1, 0, 3]]
    result = dict(shape=size[::-1].tolist(), affine=out.tolist())
    if not coverage(result, meta['geometry'])['covered']:
        raise ValueError('Native region is not covered by teacher grid')
    return result
