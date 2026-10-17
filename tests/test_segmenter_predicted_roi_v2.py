from copy import deepcopy
from hashlib import sha256
import numpy as np
import pytest
from src.data import segmenter_predicted_roi_v2 as adapter
from src.data import segmenter_geometry_v2 as geometry
from src.data.source_inventory_records import content_hash

SOURCE=dict(study_id='invented',ct_sha256='a'*64)


def fixture(affine=None, empty=False):
    a=np.eye(4) if affine is None else affine
    p=np.zeros((48,48,48),np.uint8)
    if not empty:p[20:28,20:28,20:28]=1
    r=dict(schema_version='1.0.0',task='binary_pancreas',prediction_id='prediction',run_id='run',
           model_sha256='b'*64,source_identity=SOURCE,native_shape=list(p.shape),native_affine=a.tolist(),
           units='mm',full_volume=True,binary_mask_sha256=sha256(p.tobytes()).hexdigest())
    return p,a,r


def plan(p,a,r):
    return adapter.plan_predicted_roi(p,a,source_identity=SOURCE,prediction_record=r,
            trusted_prediction_record_sha256=content_hash(r),tensor_shape=(32,32,32))


@pytest.mark.parametrize('shear',[0.,.25,-.3])
def test_image_only_bridge_matches_training_preparation_and_restores_location(shear):
    a=np.eye(4);a[0,1]=shear;a[:3,3]=[17,-23,41]
    p,a,r=fixture(a);out=plan(p,a,r);pin=content_hash(out)
    world=(a@np.vstack((np.indices(p.shape).reshape(3,-1),np.ones(p.size))))[:3]
    ct=(world[0]+world[1]-100).reshape(p.shape).astype(np.float32)
    x=adapter.prepare_predicted_image(ct,a,source_identity=SOURCE,plan=out,trusted_plan_sha256=pin)
    lesion=np.zeros_like(p);lesion[22:26,22:26,22:26]=1
    baseline=geometry.preprocess(ct,p,lesion,a,geometry.recipe(tensor_shape=(32,32,32)),
             source_identity=SOURCE,lesion_target_state='positive')
    assert np.array_equal(x,baseline['image'])
    assert out['transform']['roi_origin']=='predicted_region'
    # Geometry fixture, not model-quality evidence: a known tensor prediction returns to native anatomy.
    restored=adapter.restore_predicted_codes(baseline['target'],plan=out,trusted_plan_sha256=pin)
    assert restored.shape==p.shape and (restored[lesion==1]==2).mean()>.5
    assert not restored[:5].any()
    # Existing default training records remain identical to explicitly reference-origin records.
    t=baseline['transform']
    assert geometry.plan_geometry(list(p.shape),a,t['native_box'],t['recipe'],source_identity=SOURCE)==t


def test_empty_localizer_is_failure():
    p,a,r=fixture(empty=True)
    with pytest.raises(adapter.PredictedRoiError,match='empty_localization'):plan(p,a,r)


def test_wrong_prediction_bytes_and_wrong_image_identity_rejected():
    p,a,r=fixture();changed=p.copy();changed[0,0,0]=1
    with pytest.raises(adapter.PredictedRoiError,match='prediction_payload'):plan(changed,a,r)
    out=plan(p,a,r)
    with pytest.raises(adapter.PredictedRoiError,match='source_mismatch'):
        adapter.prepare_predicted_image(p.astype(float),a,source_identity=dict(SOURCE,study_id='other'),
                                        plan=out,trusted_plan_sha256=content_hash(out))


def test_forged_origin_or_affine_refused_even_with_refreshed_hashes():
    p,a,r=fixture();out=plan(p,a,r)
    for field,value in [('roi_origin','provided_pancreas_reference'),('tensor_affine',np.eye(4).tolist())]:
        bad=deepcopy(out);bad['transform'][field]=value;bad['transform_sha256']=content_hash(bad['transform'])
        with pytest.raises(adapter.PredictedRoiError):adapter.validate_plan(bad,content_hash(bad))


def test_nonfinite_image_and_unknown_class_refused():
    p,a,r=fixture();out=plan(p,a,r);pin=content_hash(out);ct=p.astype(float);ct[0,0,0]=np.nan
    with pytest.raises(adapter.PredictedRoiError,match='invalid_image'):
        adapter.prepare_predicted_image(ct,a,source_identity=SOURCE,plan=out,trusted_plan_sha256=pin)
    with pytest.raises(adapter.PredictedRoiError,match='invalid_codes'):
        adapter.restore_predicted_codes(np.full((32,32,32),3,np.uint8),plan=out,trusted_plan_sha256=pin)
