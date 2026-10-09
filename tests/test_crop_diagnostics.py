import numpy as np
import pytest
from src.data import segmenter_geometry_v2 as g
from src.data.source_inventory_records import content_hash
from src.inference.crop_diagnostics import target_roundtrip


def record(shape, box, tensor):
    return g.plan_geometry(list(shape),np.eye(4),box,g.recipe(tensor_shape=tensor,margin_mm=0),
        source_identity=dict(study_id='synthetic',ct_sha256='a'*64))


def test_identity_preserves_labels_and_components():
    p=np.zeros((16,16,16),np.uint8);p[2:14,2:14,2:14]=1
    l=np.zeros_like(p);l[4:6,4:6,4:6]=1;l[10:12,10:12,10:12]=1
    r=record(p.shape,[[0]*3,[16]*3],(16,16,16))
    s=target_roundtrip(p,l,r,trusted_record_sha256=content_hash(r))
    assert s['metrics']['lesion']['roundtrip_dice']==1
    assert s['lesion_components']==2 and not s['lost_component_ids']


def test_full_box_does_not_guarantee_resampled_lesion_survival():
    p=np.ones((16,16,16),np.uint8);l=np.zeros_like(p);l[0,0,0]=1
    r=record(p.shape,[[0]*3,[16]*3],(2,2,2))
    s=target_roundtrip(p,l,r,trusted_record_sha256=content_hash(r))
    assert s['metrics']['lesion']['native_box_coverage']==1
    assert s['metrics']['lesion']['tensor_voxels']==0
    assert s['metrics']['lesion']['roundtrip_recall']==0
    assert s['lost_component_ids']==[1]


def test_empty_and_changed_record():
    p=np.ones((8,8,8),np.uint8);l=np.zeros_like(p)
    r=record(p.shape,[[0]*3,[8]*3],(8,8,8))
    s=target_roundtrip(p,l,r,trusted_record_sha256=content_hash(r))
    assert s['metrics']['lesion']['roundtrip_dice'] is None
    assert s['lesion_components']==0
    with pytest.raises(ValueError):target_roundtrip(p,l,r,trusted_record_sha256='b'*64)


def test_scaled_reference_rounds_only_within_existing_tolerance():
    from src.inference.crop_diagnostics import decode_binary_reference
    assert np.array_equal(decode_binary_reference(np.array([1e-8, 1-1e-8])), [0, 1])
    for values in ([0.1, 1.], [0., 1.001], [0., np.nan], [0., np.inf], [0., 2.]):
        with pytest.raises(ValueError):decode_binary_reference(np.array(values))
