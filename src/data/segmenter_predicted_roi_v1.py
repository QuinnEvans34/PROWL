"""Image-only predicted-ROI adapter; no paths, models or reference annotations.

The v1 diagnostic keeps all binary pancreas prediction support, with 10 mm
margin and the existing physical mapper. This is not a selected cascade policy.
Record pins must come from the caller's independent trusted control record.
"""
from copy import deepcopy
from hashlib import sha256

import numpy as np

from src.data import segmenter_geometry_v1 as geometry
from src.data.source_inventory_records import content_hash


POLICY_ID = "predicted-pancreas-all-support-10mm-diagnostic-v1"
PREDICTION_FIELDS = {
    "schema_version", "task", "prediction_id", "run_id", "model_sha256",
    "source_identity", "native_shape", "native_affine", "units",
    "full_volume", "binary_mask_sha256",
}
PLAN_FIELDS = {
    "schema_version", "component", "policy_id", "prediction_record",
    "prediction_record_sha256", "margin", "transform", "transform_sha256",
}


class PredictedRoiError(ValueError):
    """Stable failure reason for requested-case accounting, with no fallback."""

    def __init__(self, reason, detail):
        self.reason = reason
        super().__init__(f"{reason}: {detail}")


def _check(condition, reason, detail):
    if not condition:
        raise PredictedRoiError(reason, detail)


def _hash(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def _source(identity):
    _check(isinstance(identity, dict) and set(identity) == {"study_id", "ct_sha256"}
           and isinstance(identity["study_id"], str) and bool(identity["study_id"].strip())
           and _hash(identity["ct_sha256"]), "source_identity", "Explicit study/CT identity required")


def _record_hash(record, reason):
    try:
        return content_hash(record)
    except (TypeError, ValueError) as exc:
        raise PredictedRoiError(reason, "Finite JSON control record required") from exc


def _prediction(record, trusted_pin, source_identity, shape, affine):
    _source(source_identity)
    _check(isinstance(record, dict) and set(record) == PREDICTION_FIELDS,
           "prediction_record", "Exact image-only prediction fields required")
    _check(_hash(trusted_pin) and _record_hash(record, "prediction_record") == trusted_pin,
           "prediction_pin", "Independent prediction record pin differs")
    _check(record["schema_version"] == "1.0.0" and record["task"] == "binary_pancreas"
           and record["units"] == "mm" and record["full_volume"] is True
           and all(isinstance(record[k], str) and bool(record[k].strip())
                   for k in ("prediction_id", "run_id"))
           and _hash(record["model_sha256"]) and _hash(record["binary_mask_sha256"]),
           "prediction_lineage", "Pinned full-volume binary pancreas lineage required")
    _check(record["source_identity"] == source_identity,
           "source_mismatch", "Prediction belongs to a different study/CT")
    _check(isinstance(record["native_shape"], list)
           and all(type(n) is int for n in record["native_shape"])
           and record["native_shape"] == list(shape),
           "prediction_grid", "Prediction native shape differs")
    try:
        recorded_affine = np.asarray(record["native_affine"], dtype=np.float64)
        source_affine = np.asarray(affine, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise PredictedRoiError("prediction_grid", "Invalid declared affine") from exc
    _check(recorded_affine.shape == source_affine.shape == (4, 4)
           and np.isfinite(recorded_affine).all() and np.isfinite(source_affine).all()
           and np.array_equal(recorded_affine, source_affine),
           "prediction_grid", "Prediction native affine differs; no grid relabeling")


def plan_predicted_roi(prediction, affine, *, source_identity, prediction_record,
                       trusted_prediction_record_sha256, tensor_shape=(144, 144, 144)):
    """Bind an already native-grid binary prediction to one physical transform.

    No reference or source-path argument exists. The mask digest is SHA-256 of
    C-order uint8 binary bytes; shape/affine are independently bound by the record.
    This cannot authenticate real CT bytes or grant their permitted use.
    """
    p = np.asarray(prediction)
    _prediction(prediction_record, trusted_prediction_record_sha256,
                source_identity, p.shape, affine)
    recipe = geometry.recipe(tensor_shape=tensor_shape, sampling_mm=1., margin_mm=10.)
    try:
        geometry.canonical_geometry(list(p.shape), affine, recipe)
    except (TypeError, ValueError) as exc:
        raise PredictedRoiError("unsupported_geometry", str(exc)) from exc
    _check(p.dtype.kind in "buif" and np.isfinite(p).all() and np.isin(p, [0, 1]).all(),
           "invalid_prediction", "Finite binary native prediction required")
    observed = sha256(np.ascontiguousarray(p, dtype=np.uint8).tobytes()).hexdigest()
    _check(observed == prediction_record["binary_mask_sha256"],
           "prediction_payload", "Native prediction payload differs from its pinned record")
    _check(bool(p.any()), "empty_localization", "No predicted region; case remains a failure")
    try:
        box, margin = geometry.select_pancreas_box(p, affine, recipe)
        transform = geometry.plan_geometry(list(p.shape), affine, box, recipe,
            source_identity=source_identity, roi_origin="predicted_region")
    except (TypeError, ValueError) as exc:
        raise PredictedRoiError("unsafe_roi", str(exc)) from exc
    return {
        "schema_version": "1.0.0", "component": "segmenter-predicted-roi-v1",
        "policy_id": POLICY_ID, "prediction_record": deepcopy(prediction_record),
        "prediction_record_sha256": trusted_prediction_record_sha256,
        "margin": deepcopy(margin), "transform": transform,
        "transform_sha256": content_hash(transform),
    }


def validate_plan(plan, trusted_plan_sha256):
    """Validate an independently pinned plan; a self-refreshed hash is not authority."""
    _check(isinstance(plan, dict) and set(plan) == PLAN_FIELDS,
           "plan_record", "Exact adapter fields required")
    _check(_hash(trusted_plan_sha256) and _record_hash(plan, "plan_record") == trusted_plan_sha256,
           "plan_pin", "Independent adapter plan pin differs")
    _check(plan["schema_version"] == "1.0.0"
           and plan["component"] == "segmenter-predicted-roi-v1"
           and plan["policy_id"] == POLICY_ID,
           "plan_policy", "Unsupported predicted-ROI diagnostic")
    transform = plan["transform"]
    _check(isinstance(transform, dict), "plan_geometry", "Missing transform")
    try:
        _prediction(plan["prediction_record"], plan["prediction_record_sha256"],
                    transform["source_identity"], transform["source_shape"], transform["source_affine"])
        expected_recipe = geometry.recipe(tensor_shape=tuple(transform["tensor_shape"]),
                                          sampling_mm=1., margin_mm=10.)
        _check(transform["roi_origin"] == "predicted_region"
               and transform["recipe"] == expected_recipe,
               "plan_policy", "Reference-origin or altered diagnostic recipe refused")
        geometry.validate_record(transform, plan["transform_sha256"])
    except PredictedRoiError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise PredictedRoiError("plan_geometry", str(exc)) from exc


def prepare_predicted_image(image, affine, *, source_identity, plan,
                            trusted_plan_sha256, tick=lambda: None):
    """Prepare only the declared image on the fixed predicted transform."""
    validate_plan(plan, trusted_plan_sha256)
    transform = plan["transform"]
    _prediction(plan["prediction_record"], plan["prediction_record_sha256"],
                source_identity, np.asarray(image).shape, affine)
    try:
        return geometry.prepare_image(image, transform,
            trusted_record_sha256=plan["transform_sha256"], tick=tick)
    except (TypeError, ValueError) as exc:
        raise PredictedRoiError("invalid_image", str(exc)) from exc


def restore_predicted_probabilities(probabilities, *, plan, trusted_plan_sha256,
                                    tick=lambda: None):
    """Restore three-class probabilities to the plan's native grid, background outside ROI."""
    validate_plan(plan, trusted_plan_sha256)
    try:
        return geometry.restore_probabilities(probabilities, plan["transform"],
            trusted_record_sha256=plan["transform_sha256"], tick=tick)
    except (TypeError, ValueError) as exc:
        raise PredictedRoiError("invalid_probabilities", str(exc)) from exc
