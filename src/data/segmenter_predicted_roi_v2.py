"""Reference-free image/region bridge for the current segmenter's geometry.

Consumes a native-grid localizer prediction, not reference masks. Model execution
and file identity verification belong to the caller; no model-quality claim follows.
"""
from copy import deepcopy
from hashlib import sha256
import numpy as np
from src.data import segmenter_geometry_v2 as geometry
from src.data.segmenter_predicted_roi_v1 import (
    PredictedRoiError, _check, _prediction, _record_hash,
)
from src.data.source_inventory_records import content_hash

POLICY_ID = 'predicted-pancreas-all-support-10mm-diagnostic-v2'
FIELDS = {'component', 'policy_id', 'prediction_record', 'prediction_record_sha256',
          'transform', 'transform_sha256'}


def plan_predicted_roi(prediction, affine, *, source_identity, prediction_record,
                       trusted_prediction_record_sha256, tensor_shape=(144,144,144), max_sampling_voxels=16_000_000):
    p = np.asarray(prediction)
    _prediction(prediction_record, trusted_prediction_record_sha256, source_identity, p.shape, affine)
    recipe = geometry.recipe(tensor_shape=tensor_shape, max_sampling_voxels=max_sampling_voxels)
    try:
        geometry.canonical_geometry(list(p.shape), affine, recipe)
    except (TypeError, ValueError) as exc:
        raise PredictedRoiError('unsupported_geometry', str(exc)) from exc
    _check(p.dtype.kind in 'buif' and np.isfinite(p).all() and np.isin(p,[0,1]).all(),
           'invalid_prediction', 'Finite binary native prediction required')
    _check(sha256(np.ascontiguousarray(p,dtype=np.uint8).tobytes()).hexdigest()
           == prediction_record['binary_mask_sha256'], 'prediction_payload', 'Prediction bytes changed')
    _check(bool(p.any()), 'empty_localization', 'No predicted region; no reference fallback')
    try:
        box = geometry.select_pancreas_box(p, affine, recipe)
        transform = geometry.plan_geometry(list(p.shape), affine, box, recipe,
            source_identity=source_identity, roi_origin='predicted_region')
    except (TypeError, ValueError) as exc:
        raise PredictedRoiError('unsafe_roi', str(exc)) from exc
    return dict(component='segmenter-predicted-roi-v2', policy_id=POLICY_ID,
        prediction_record=deepcopy(prediction_record),
        prediction_record_sha256=trusted_prediction_record_sha256,
        transform=transform, transform_sha256=content_hash(transform))


def validate_plan(plan, trusted_plan_sha256):
    _check(isinstance(plan,dict) and set(plan)==FIELDS, 'plan_record', 'Exact adapter fields required')
    _check(_record_hash(plan,'plan_record')==trusted_plan_sha256, 'plan_pin', 'Changed adapter plan')
    _check(plan['component']=='segmenter-predicted-roi-v2' and plan['policy_id']==POLICY_ID,
           'plan_policy','Unsupported predicted-region policy')
    try:
        t=plan['transform']
        _prediction(plan['prediction_record'],plan['prediction_record_sha256'],
                    t['source_identity'],t['source_shape'],t['source_affine'])
        _check(t['roi_origin']=='predicted_region' and
               t['recipe']==geometry.recipe(tensor_shape=tuple(t['tensor_shape']), max_sampling_voxels=t['recipe']['max_sampling_voxels']),
               'plan_policy','Reference origin or altered recipe refused')
        geometry.validate_record(t,plan['transform_sha256'])
    except PredictedRoiError:
        raise
    except (KeyError,TypeError,ValueError) as exc:
        raise PredictedRoiError('plan_geometry',str(exc)) from exc


def prepare_predicted_image(image, affine, *, source_identity, plan, trusted_plan_sha256, tick=lambda:None):
    validate_plan(plan,trusted_plan_sha256)
    _prediction(plan['prediction_record'],plan['prediction_record_sha256'],
                source_identity,np.asarray(image).shape,affine)
    try:
        return geometry.prepare_image(image,plan['transform'],
            trusted_record_sha256=plan['transform_sha256'],tick=tick)
    except (TypeError,ValueError) as exc:
        raise PredictedRoiError('invalid_image',str(exc)) from exc


def restore_predicted_codes(codes, *, plan, trusted_plan_sha256, tick=lambda:None):
    """Restore hard three-class predictions; probability interpolation is not implied."""
    validate_plan(plan,trusted_plan_sha256)
    codes=np.asarray(codes)
    _check(codes.dtype.kind in 'iu' and np.isin(codes,[0,1,2]).all(),
           'invalid_codes','Integer background/pancreas/lesion codes required')
    try:
        return geometry.restore_codes(codes,plan['transform'],
            trusted_record_sha256=plan['transform_sha256'],tick=tick)
    except (TypeError,ValueError) as exc:
        raise PredictedRoiError('invalid_codes',str(exc)) from exc
