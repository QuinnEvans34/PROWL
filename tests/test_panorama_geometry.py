import numpy as np
import pytest
from src.data.panorama_geometry import preprocess
from src.data.segmenter_geometry_v2 import recipe


def test_union_crop_keeps_distant_tumor_without_relabeling_pancreas():
    raw=np.zeros((32,32,32),dtype=np.uint8)
    raw[4:10,4:10,4:10]=4
    raw[22:26,22:26,22:26]=1
    r=recipe(tensor_shape=(32,32,32),margin_mm=0)
    result=preprocess(np.zeros(raw.shape,np.float32),raw,np.eye(4),r,
        source_identity=dict(study_id='synthetic',ct_sha256='a'*64),diagnosis='PDAC')
    transform=result['geometry']['transform']
    assert transform['native_box']==[[4,4,4],[26,26,26]]
    assert transform['roi_origin']=='provided_panorama_pancreas_lesion_union'
    assert r['roi_selection']=='pancreas_only'
    assert result['mechanical_survival_pass'] and not result['training_ready']
    assert set(np.unique(result['target']))=={0,1,2}


@pytest.mark.parametrize('fault',['unknown','nonfinite','shape'])
def test_invalid_or_unknown_inputs_refused(fault):
    raw=np.zeros((16,16,16),np.uint8);raw[2:6,2:6,2:6]=4;raw[8:12,8:12,8:12]=1
    image=np.zeros(raw.shape,np.float32)
    if fault=='nonfinite':image[0,0,0]=np.nan
    if fault=='shape':image=image[:-1]
    with pytest.raises(ValueError):
        preprocess(image,raw,np.eye(4),recipe(tensor_shape=(16,16,16)),
            source_identity=dict(study_id='synthetic',ct_sha256='a'*64),
            diagnosis='non-PDAC' if fault=='unknown' else 'PDAC')
