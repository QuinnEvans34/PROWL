"""Shared future-model entry point; live/frozen pipelines must opt in explicitly."""
from src.inference.component_proximity_filter_v1 import filter_prediction

POLICY_ID='predicted-pancreas-proximity-5mm-v1'
MAXIMUM_DISTANCE_MM=5.


def postprocess(prediction,affine):
    """Return filtered copy plus provenance. Caller retains the raw prediction."""
    result,details=filter_prediction(prediction,affine,maximum_distance_mm=MAXIMUM_DISTANCE_MM)
    details.update(policy_id=POLICY_ID,maximum_distance_mm=MAXIMUM_DISTANCE_MM,
                   applied=details['context_available'],raw_retention_required=True,
                   reason=None if details['context_available'] else 'predicted_pancreas_missing')
    return result,details
