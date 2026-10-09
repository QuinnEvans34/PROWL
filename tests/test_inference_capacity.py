import numpy as np
import pytest
from src.data import segmenter_geometry_v2 as g
from src.data.source_inventory_records import content_hash
from src.inference.spatial_units import resolve_mm


def test_larger_cap_does_not_change_supported_numerics():
    image=np.arange(24**3,dtype=np.float32).reshape(24,24,24)%350-100
    results=[]
    for cap in (16_000_000,64_000_000):
        r=g.plan_geometry(list(image.shape),np.eye(4),[[0]*3,[24]*3],g.recipe(tensor_shape=(24,24,24),max_sampling_voxels=cap),source_identity=dict(study_id='synthetic',ct_sha256='a'*64))
        results.append(g.prepare_image(image,r,trusted_record_sha256=content_hash(r)))
    assert np.array_equal(*results)


def test_large_geometry_is_plannable_and_still_bounded():
    args=([300,300,300],np.eye(4),[[0]*3,[300]*3])
    identity=dict(study_id='synthetic',ct_sha256='a'*64)
    with pytest.raises(ValueError,match='allocation'):g.plan_geometry(*args,g.recipe(),source_identity=identity)
    r=g.plan_geometry(*args,g.recipe(max_sampling_voxels=64_000_000),source_identity=identity)
    assert r['sampling_shape']==[300]*3
    with pytest.raises(ValueError,match='allocation'):g.validate_recipe(g.recipe(max_sampling_voxels=64_000_001))


def test_units_review_bound_to_ct_and_not_reference():
    assert resolve_mm('mm','a'*64)['basis']=='CT header'
    with pytest.raises(ValueError):resolve_mm('unknown','a'*64)
    r=dict(ct_sha256='a'*64,interpreted_units='mm',basis='source_dataset_documentation',evidence='Synthetic test evidence',reviewer='test')
    assert resolve_mm('unknown','a'*64,r)['review']==r
    for units,pin,review in [('unknown','b'*64,r),('meter','a'*64,r),('unknown','a'*64,dict(r,basis='reference_mask'))]:
        with pytest.raises(ValueError):resolve_mm(units,pin,review)
