import numpy as np
import pytest

from src.inference.boundary_audit import audit_boundary


def fixture():
    labels = np.zeros((12, 12, 12), dtype=np.uint8)
    labels[5:8, 5:8, 5:8] = 1
    return labels, labels.copy(), np.diag([2., 3., 4., 1.]), [[1, 1, 1], [11, 11, 11]]


def test_isolated_boundary_fragments_are_reported_not_removed():
    a, ref, affine, roi = fixture()
    a[5, 5, 1] = 1
    a[5, 5, 5] = 2
    original = a.copy()
    r = audit_boundary(a, ref, affine, roi)
    for c in ('6', '26'):
        p = r['targets']['pancreas_union']['connectivity'][c]
        assert p['component_count'] == 2
        assert not p['largest_component_crop_contact']
        assert p['boundary_component_voxels'] == p['crop_contact_voxels'] == 1
        fragment = p['components'][1]
        assert fragment['distance_to_largest_component_mm'] == 16
        assert fragment['distance_to_assistance_mm']['min'] == 16
        assert fragment['assistance_overlap_voxels'] == 0
        assert fragment['crop_faces'] == {'2_low': 1}
    assert r['targets']['lesion']['voxels'] == 1
    np.testing.assert_array_equal(a, original)


def test_connected_truncation_and_diagonal_sensitivity():
    a, ref, affine, roi = fixture()
    a[5, 5, 1:5] = 1
    r = audit_boundary(a, ref, affine, roi)
    assert all(x['largest_component_crop_contact'] for x in r['targets']['pancreas_union']['connectivity'].values())
    a, ref, affine, roi = fixture()
    for n in range(1, 5):
        a[n, n, n] = 1
    r = audit_boundary(a, ref, affine, roi)['targets']['pancreas_union']['connectivity']
    assert r['6']['component_count'] == 5 and not r['6']['largest_component_crop_contact']
    assert r['26']['component_count'] == 1 and r['26']['largest_component_crop_contact']
    assert r['26']['crop_contact_voxels'] == 1  # Corner counted once, not once per face.


def test_world_distance_respects_shear_and_empty_lesion():
    a, ref, affine, roi = fixture()
    affine[0, 2] = 1
    a[5, 5, 1] = 1
    r = audit_boundary(a, ref, affine, roi)
    f = r['targets']['pancreas_union']['connectivity']['26']['components'][1]
    assert f['distance_to_assistance_mm']['min'] == pytest.approx(np.sqrt(4**2 + 16**2))
    assert r['voxel_mm3'] == pytest.approx(24)
    assert r['targets']['lesion']['connectivity']['26']['components'] == []


@pytest.mark.parametrize('fault', ['outside', 'reference', 'labels', 'affine', 'roi'])
def test_invalid_inputs_are_rejected(fault):
    a, ref, affine, roi = fixture()
    if fault == 'outside': a[0, 0, 0] = 1
    if fault == 'reference': ref[0, 0, 0] = 2
    if fault == 'labels': a[5, 5, 5] = 3
    if fault == 'affine': affine[2] = 0
    if fault == 'roi': roi[1][0] = 13
    with pytest.raises(ValueError): audit_boundary(a, ref, affine, roi)
