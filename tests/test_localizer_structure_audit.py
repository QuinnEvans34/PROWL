import numpy as np
import pytest
from src.training.localizer_structure_audit import analyze, recall_bounds


def test_diagonal_connectivity_and_separate_outlier():
    p = np.zeros((50, 50, 50), np.uint8)
    p[20, 20, 20] = p[21, 21, 21] = p[45, 45, 45] = 1
    before = p.copy(); r = analyze(p, np.eye(4))
    assert r['component_count'] == 2 and r['largest_fraction'] == 2/3
    assert r['components'][0]['bounds'] == [[20, 20, 20], [22, 22, 22]]
    assert r['union_margin_box']['bounds'] == [[10, 10, 10], [50, 50, 50]]
    assert r['largest_margin_box']['scan_fraction'] == 22**3/50**3
    assert r['union_face_controllers'][0] == {'axis': 0, 'low': [1], 'high': [2]}
    np.testing.assert_array_equal(p, before)


def test_broad_connected_region_cannot_shrink_by_component_deletion():
    p = np.ones((40, 30, 20), np.uint8); r = analyze(p, np.eye(4))
    assert r['component_count'] == 1 and r['largest_fraction'] == 1
    assert r['hypothetical_box_fraction_reduction'] == 0
    assert r['union_margin_box']['scan_fraction'] == 1
    assert r['volume_ml'] == pytest.approx(24)


def test_ties_stable_and_all_components_preserved():
    p = np.zeros((8, 8, 8), np.uint8); p[1, 1, 1] = p[6, 6, 6] = 1
    r = analyze(p, np.eye(4), margin_mm=0)
    assert [c['label'] for c in r['components']] == [1, 2]
    assert r['components'][0]['bounds'][0] == [1, 1, 1]
    assert r == analyze(p, np.eye(4), margin_mm=0)


def test_anisotropic_signed_permuted_affine_and_clipping():
    a = np.array([[0, -2, 0, 10], [3, 0, 0, -8], [0, 0, -5, 40], [0, 0, 0, 1.]])
    p = np.zeros((40, 50, 60), np.uint8); p[20:23, 20:24, 20:25] = 1
    r = analyze(p, a); c = r['components'][0]
    assert c['voxels'] == 60 and c['volume_ml'] == pytest.approx(1.8)
    assert c['extent_mm'] == [9, 8, 25]
    assert c['world_box_ras_mm'] == [[-38, 52, -85], [-30, 61, -60]]
    assert c['margin_box']['bounds'] == [[16, 15, 18], [27, 29, 27]]


def test_empty_visible_not_filtered():
    r = analyze(np.zeros((4, 5, 6), np.uint8), np.eye(4))
    assert r['component_count'] == 0 and r['components'] == []
    assert r['union_margin_box'] is None and r['largest_fraction'] is None
    assert recall_bounds(r, dict(predicted_voxels=0, reference_voxels=10, true_positive=0))['upper'] == 0


def test_recall_bounds_do_not_claim_truth():
    p = np.zeros((30, 30, 30), np.uint8); p[0:2, 0:2, 0:2] = 1; p[29, 29, 29] = 1
    r = analyze(p, np.eye(4))
    b = recall_bounds(r, dict(predicted_voxels=9, reference_voxels=5, true_positive=4))
    assert b['lower'] == .6 and b['upper'] == .8
    with pytest.raises(ValueError):
        recall_bounds(r, dict(predicted_voxels=10, reference_voxels=5, true_positive=4))


@pytest.mark.parametrize('fault', ['dtype', 'binary', 'empty_shape', 'oversize', 'shear', 'nan', 'margin'])
def test_invalid_input_refused(fault):
    p = np.zeros((5, 6, 7), np.uint8); a = np.eye(4); margin = 10
    if fault == 'dtype': p = p.astype(float)
    if fault == 'binary': p[0, 0, 0] = 2
    if fault == 'empty_shape': p = p[:0]
    if fault == 'oversize': p = np.broadcast_to(np.uint8(1), (480, 400, 501))
    if fault == 'shear': a[0, 1] = .3
    if fault == 'nan': a[0, 0] = np.nan
    if fault == 'margin': margin = -1
    with pytest.raises(ValueError): analyze(p, a, margin_mm=margin)


def test_analytical_component_budget_failure_visible(monkeypatch):
    import src.training.localizer_structure_audit as m
    monkeypatch.setattr(m, 'MAX_COMPONENTS', 1)
    p = np.zeros((5, 5, 5), np.uint8); p[0, 0, 0] = p[4, 4, 4] = 1
    with pytest.raises(ValueError, match='retain failed case'): analyze(p, np.eye(4))


def test_heartbeat_can_interrupt_analysis():
    def stop(): raise TimeoutError('budget')
    with pytest.raises(TimeoutError): analyze(np.ones((3, 4, 5), np.uint8), np.eye(4), heartbeat=stop)


def test_random_small_components_against_independent_flood_fill():
    import itertools
    rng = np.random.default_rng(71)
    for _ in range(20):
        p = (rng.random((5, 6, 7)) < .10).astype(np.uint8)
        remaining = set(map(tuple, np.argwhere(p))); expected = []
        offsets = [x for x in itertools.product((-1, 0, 1), repeat=3) if x != (0, 0, 0)]
        while remaining:
            todo = [remaining.pop()]; members = []
            while todo:
                point = todo.pop(); members.append(point)
                for delta in offsets:
                    neighbor = tuple(a+b for a,b in zip(point, delta))
                    if neighbor in remaining:
                        remaining.remove(neighbor); todo.append(neighbor)
            xyz = np.array(members)
            expected.append((len(members), xyz.min(0).tolist(), (xyz.max(0)+1).tolist()))
        r = analyze(p, np.eye(4), margin_mm=0)
        observed = [(c['voxels'], *c['bounds']) for c in r['components']]
        assert sorted(observed) == sorted(expected)
