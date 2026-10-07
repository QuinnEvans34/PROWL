from copy import deepcopy
from hashlib import sha256
import inspect

import numpy as np
import pytest

from src.data import segmenter_predicted_roi_v1 as adapter
from src.data.source_inventory_records import content_hash


SOURCE = {"study_id": "invented-only", "ct_sha256": "a" * 64}


def record(p, affine):
    return dict(schema_version="1.0.0", task="binary_pancreas", prediction_id="invented-prediction",
        run_id="invented-localizer-run", model_sha256="b" * 64, source_identity=deepcopy(SOURCE),
        native_shape=list(p.shape), native_affine=np.asarray(affine).tolist(), units="mm",
        full_volume=True, binary_mask_sha256=sha256(np.asarray(p, dtype=np.uint8).tobytes()).hexdigest())


def plan(p, affine=None, tensor_shape=(32, 32, 32)):
    affine = np.eye(4) if affine is None else affine
    r = record(p, affine)
    return adapter.plan_predicted_roi(p, affine, source_identity=SOURCE, prediction_record=r,
        trusted_prediction_record_sha256=content_hash(r), tensor_shape=tensor_shape)


def mask(shape=(50, 50, 50)):
    p = np.zeros(shape, np.uint8)
    p[22:25, 21:26, 20:27] = 1
    return p


def test_all_components_and_physical_margin_have_independent_bounds():
    p = mask(); p[39, 9, 15] = 1
    a = np.diag([2., 3., 5., 1.]); a[:3, 3] = [17, -24, 31]
    out = plan(p, a); t = out["transform"]
    # Bounds from the two explicitly authored components, then ceil(10/spacing).
    assert t["box_ras_half_open"] == [[17, 5, 13], [45, 30, 29]]
    assert t["roi_world_low_edge_mm"] == [50., -10.5, 93.5]
    assert t["roi_physical_extent_mm"] == [56., 75., 80.]
    assert out["margin"]["realized_margin_mm"] == [[10., 12., 10.], [10., 12., 10.]]
    assert t["roi_origin"] == "predicted_region" and out["policy_id"] == adapter.POLICY_ID


def test_permutation_and_reverse_use_native_world_coordinates():
    p = np.zeros((18, 22, 20), np.uint8); p[8:10, 9:12, 6:9] = 1
    a = np.array([[0, 0, -3, 90], [-2, 0, 0, 36], [0, 4, 0, -12], [0, 0, 0, 1]], float)
    t = plan(p, a)["transform"]
    # RAS support: x=11..13, y=8..9, z=9..11. Native point [8,9,6] maps to [13,9,9].
    assert t["canonical_shape"] == [20, 18, 22]
    assert t["box_ras_half_open"] == [[7, 3, 6], [18, 15, 15]]
    assert t["roi_world_low_edge_mm"] == [52.5, 7., 10.]
    assert np.array_equal(np.asarray(t["canonical_affine"]) @ [13, 9, 9, 1], [72, 20, 24, 1])
    assert np.array_equal(a @ [8, 9, 6, 1], [72, 20, 24, 1])


@pytest.mark.parametrize("axis", range(3))
@pytest.mark.parametrize("high", [False, True])
def test_boundary_faces_are_clipped_and_explicit(axis, high):
    p = np.zeros((35, 35, 35), np.uint8); index = [17, 17, 17]
    index[axis] = 34 if high else 0; p[tuple(index)] = 1
    out = plan(p, np.diag([1., 2., 3., 1.]))
    side = int(high)
    assert out["margin"]["source_face_contact"][side][axis] is True
    assert out["margin"]["realized_margin_mm"][side][axis] == 0
    assert out["transform"]["box_ras_half_open"][side][axis] == (35 if high else 0)


def test_odd_padding_and_exact_normalization_without_input_mutation():
    p = np.ones((5, 6, 7), np.uint8); a = np.eye(4); a[:3, 3] = [8, -13, 17]
    before = p.copy(); out = plan(p, a, tensor_shape=(10, 10, 10)); pin = content_hash(out)
    t = out["transform"]
    assert t["normalized_shape"] == [8, 9, 10]
    assert t["pad_low"] == [1, 0, 0] and t["pad_high"] == [1, 1, 0]
    ct = np.full(p.shape, 75., np.float32); original = ct.copy(); saved = deepcopy(out)
    image = adapter.prepare_predicted_image(ct, a, source_identity=SOURCE, plan=out, trusted_plan_sha256=pin)
    assert image[5, 5, 5] == pytest.approx(.5, abs=1e-6)
    assert image[0, 5, 5] == 0 and np.all((image >= 0) & (image <= .5))
    assert np.array_equal(ct, original) and np.array_equal(p, before) and out == saved
    assert plan(p, a, tensor_shape=(10, 10, 10)) == out


def test_world_ramp_catches_crop_offset_and_axis_swap():
    p = mask(); a = np.eye(4); coords = np.indices(p.shape)
    ct = (coords[0] + 2 * coords[1] + 3 * coords[2]).astype(np.float32) - 100
    out = plan(p); pin = content_hash(out)
    image = adapter.prepare_predicted_image(ct, a, source_identity=SOURCE, plan=out, trusted_plan_sha256=pin)
    world = np.asarray(out["transform"]["tensor_affine"]) @ [16, 16, 16, 1]
    expected = (world[0] + 2 * world[1] + 3 * world[2]) / 350
    assert image[16, 16, 16] == pytest.approx(expected, abs=1e-6)
    assert abs(image[16, 16, 16] - (world[1] + 2 * world[0] + 3 * world[2]) / 350) > 1e-4


def test_reference_outside_fixed_prediction_roi_cannot_rescue_coverage():
    p = mask(); out = plan(p); pin = content_hash(out)
    lesion_a = np.zeros(p.shape, np.uint8); lesion_a[23, 23, 23] = 1
    lesion_b = lesion_a.copy(); lesion_b[0, 0, 0] = 1
    probabilities = np.zeros((3, 32, 32, 32), np.float32); probabilities[2] = 1
    restored = adapter.restore_predicted_probabilities(probabilities, plan=out, trusted_plan_sha256=pin)
    assert np.array_equal(restored[:, 0, 0, 0], [1., 0., 0.])
    assert restored[2, 23, 23, 23] == 1 and np.allclose(restored.sum(0), 1)
    # References are independent test oracles after planning; neither is an adapter argument.
    assert np.count_nonzero((restored.argmax(0) == 2) & lesion_a) == 1
    assert np.count_nonzero((restored.argmax(0) == 2) & lesion_b) == 1
    assert lesion_b.sum() == 2  # The uncovered component stays in the denominator.
    assert content_hash(out) == pin
    for fn in (adapter.plan_predicted_roi, adapter.prepare_predicted_image):
        assert not {"pancreas", "lesion", "reference", "path"} & set(inspect.signature(fn).parameters)


@pytest.mark.parametrize("fault,reason", [
    ("study", "source_mismatch"), ("ct", "source_mismatch"), ("shape", "prediction_grid"),
    ("affine", "prediction_grid"), ("task", "prediction_lineage"), ("units", "prediction_lineage"),
    ("partial", "prediction_lineage"), ("missing_model", "prediction_lineage"),
    ("missing_run", "prediction_lineage"), ("extra_reference", "prediction_record"),
    ("missing_source", "prediction_record"), ("extra_source", "source_mismatch"),
])
def test_identity_and_provenance_refused_before_crop(fault, reason, monkeypatch):
    p = mask(); a = np.eye(4); r = record(p, a)
    if fault == "study": r["source_identity"]["study_id"] = "other"
    elif fault == "ct": r["source_identity"]["ct_sha256"] = "c" * 64
    elif fault == "shape": r["native_shape"][0] -= 1
    elif fault == "affine": r["native_affine"][0][3] = 1
    elif fault == "task": r["task"] = "three_class_localizer"
    elif fault == "units": r["units"] = "unknown"
    elif fault == "partial": r["full_volume"] = False
    elif fault == "missing_model": r["model_sha256"] = ""
    elif fault == "missing_run": r["run_id"] = ""
    elif fault == "extra_reference": r["lesion_reference"] = "forbidden"
    elif fault == "missing_source": del r["source_identity"]
    elif fault == "extra_source": r["source_identity"]["annotation"] = "forbidden"
    monkeypatch.setattr(adapter.geometry, "select_pancreas_box", lambda *a: pytest.fail("crop before identity check"))
    with pytest.raises(adapter.PredictedRoiError) as caught:
        adapter.plan_predicted_roi(p, a, source_identity=SOURCE, prediction_record=r,
                                  trusted_prediction_record_sha256=content_hash(r))
    assert caught.value.reason == reason


@pytest.mark.parametrize("field", ["run_id", "prediction_id", "model_sha256", "binary_mask_sha256"])
def test_stale_lineage_rejected_against_independent_pin(field):
    p = mask(); r = record(p, np.eye(4)); pin = content_hash(r)
    r[field] = "c" * 64
    with pytest.raises(adapter.PredictedRoiError, match="prediction_pin"):
        adapter.plan_predicted_roi(p, np.eye(4), source_identity=SOURCE, prediction_record=r,
                                  trusted_prediction_record_sha256=pin)


@pytest.mark.parametrize("fault,reason", [("empty", "empty_localization"), ("nan", "invalid_prediction"),
    ("fractional", "invalid_prediction"), ("two", "invalid_prediction"), ("payload", "prediction_payload"),
    ("oblique", "unsupported_geometry"), ("singular", "unsupported_geometry"),
    ("sampling_cap", "unsafe_roi")])
def test_invalid_prediction_or_geometry_has_explicit_failure(fault, reason):
    p = mask().astype(float); a = np.eye(4)
    if fault == "empty": p[:] = 0
    elif fault == "nan": p[0, 0, 0] = np.nan
    elif fault == "fractional": p[0, 0, 0] = .5
    elif fault == "two": p[0, 0, 0] = 2
    elif fault == "oblique": a[:2, :2] = [[.8, -.6], [.6, .8]]
    elif fault == "singular": a[0, 0] = 0
    elif fault == "sampling_cap": a[0, 0] = 1e9
    # Avoid conversion of NaN in the test record: invalid values should fail before payload hashing.
    r = record(np.nan_to_num(p), a)
    if fault == "payload": p[0, 0, 0] = 1
    with pytest.raises(adapter.PredictedRoiError) as caught:
        adapter.plan_predicted_roi(p, a, source_identity=SOURCE, prediction_record=r,
                                  trusted_prediction_record_sha256=content_hash(r))
    assert caught.value.reason == reason


@pytest.mark.parametrize("field", ["policy_id", "margin", "prediction_record", "transform"])
def test_plan_tampering_cannot_refresh_trusted_pin(field):
    out = plan(mask()); pin = content_hash(out); bad = deepcopy(out)
    if field == "policy_id": bad[field] = "largest-component"
    elif field == "margin": bad[field]["requested_margin_mm"] = 0
    elif field == "prediction_record": bad[field]["run_id"] = "stale"
    else: bad[field]["box_ras_half_open"][0][0] += 1
    with pytest.raises(adapter.PredictedRoiError, match="plan_pin"):
        adapter.validate_plan(bad, pin)


@pytest.mark.parametrize("fault", ["reference_origin", "margin", "tensor_affine"])
def test_internally_refreshed_geometry_still_refused(fault):
    out = plan(mask()); t = out["transform"]
    if fault == "reference_origin": t["roi_origin"] = "provided_pancreas_reference"
    elif fault == "margin": t["recipe"]["margin_mm"] = 0
    else: t["tensor_affine"][0][3] += 1
    out["transform_sha256"] = content_hash(t)
    with pytest.raises(adapter.PredictedRoiError): adapter.validate_plan(out, content_hash(out))


@pytest.mark.parametrize("fault,reason", [("study", "source_mismatch"), ("grid", "prediction_grid"),
    ("shape", "prediction_grid"), ("nan", "invalid_image")])
def test_image_requires_same_identity_and_native_grid(fault, reason):
    p = mask(); out = plan(p); ct = np.zeros(p.shape, np.float32); a = np.eye(4); identity = deepcopy(SOURCE)
    if fault == "study": identity["study_id"] = "other"
    elif fault == "grid": a[0, 3] = 1
    elif fault == "shape": ct = ct[:-1]
    elif fault == "nan": ct[0, 0, 0] = np.nan
    with pytest.raises(adapter.PredictedRoiError) as caught:
        adapter.prepare_predicted_image(ct, a, source_identity=identity, plan=out, trusted_plan_sha256=content_hash(out))
    assert caught.value.reason == reason


def test_signed_permutation_restoration_has_source_orientation_and_background():
    p = np.zeros((30, 35, 32), np.uint8); p[14:17, 16:19, 14:17] = 1
    a = np.array([[0, 0, -3, 90], [-2, 0, 0, 60], [0, 4, 0, -12], [0, 0, 0, 1]], float)
    out = plan(p, a); probabilities = np.zeros((3, 32, 32, 32), np.float32); probabilities[1] = 1
    restored = adapter.restore_predicted_probabilities(probabilities, plan=out, trusted_plan_sha256=content_hash(out))
    assert restored.shape == (3, *p.shape) and restored[1, 15, 17, 15] == 1
    assert np.array_equal(restored[:, 0, 0, 0], [1, 0, 0]) and np.allclose(restored.sum(0), 1)


@pytest.mark.parametrize("fault", ["nan", "negative", "sum", "grid"])
def test_probability_restoration_refuses_invalid_input(fault):
    out = plan(mask()); p = np.zeros((3, 32, 32, 32), np.float32); p[0] = 1
    if fault == "nan": p[0, 0, 0, 0] = np.nan
    elif fault == "negative": p[1, 0, 0, 0] = -.1
    elif fault == "sum": p[0] = .5
    else: p = p[:, :, :, :-1]
    with pytest.raises(adapter.PredictedRoiError, match="invalid_probabilities"):
        adapter.restore_predicted_probabilities(p, plan=out, trusted_plan_sha256=content_hash(out))


def test_hu_clamp_and_probability_roundtrip_are_exact_on_unchanged_grid(monkeypatch):
    p = np.ones((5, 6, 7), np.uint8)
    out = plan(p, tensor_shape=p.shape); pin = content_hash(out)
    ct = np.zeros(p.shape, np.float32); ct[1] = -1000; ct[2] = 1000
    # This slice has no filesystem operation; imports and caller-provided controls already exist.
    monkeypatch.setattr("builtins.open", lambda *a, **k: pytest.fail("unexpected source open"))
    image = adapter.prepare_predicted_image(ct, np.eye(4), source_identity=SOURCE,
                                            plan=out, trusted_plan_sha256=pin)
    assert np.array_equal(image[1], np.zeros((6, 7)))
    assert np.array_equal(image[2], np.ones((6, 7)))
    probabilities = np.broadcast_to(np.array([.2, .3, .5], np.float32)[:, None, None, None], (3, *p.shape))
    restored = adapter.restore_predicted_probabilities(probabilities, plan=out, trusted_plan_sha256=pin)
    assert np.array_equal(restored, probabilities)


@pytest.mark.parametrize("fault", ["nan_affine", "non_json"])
def test_unserializable_prediction_metadata_has_explicit_failure(fault):
    p = mask(); r = record(p, np.eye(4))
    if fault == "nan_affine": r["native_affine"][0][0] = np.nan
    else: r["run_id"] = object()
    with pytest.raises(adapter.PredictedRoiError, match="prediction_record"):
        adapter.plan_predicted_roi(p, np.eye(4), source_identity=SOURCE, prediction_record=r,
                                  trusted_prediction_record_sha256="d" * 64)


@pytest.mark.parametrize("pin", [None, "", "A" * 64, "f" * 63])
def test_missing_or_malformed_independent_pin_cannot_authorize_prediction(pin):
    p = mask(); r = record(p, np.eye(4))
    with pytest.raises(adapter.PredictedRoiError, match="prediction_pin"):
        adapter.plan_predicted_roi(p, np.eye(4), source_identity=SOURCE, prediction_record=r,
                                  trusted_prediction_record_sha256=pin)
