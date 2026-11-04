import json
import numpy as np
import pytest
from scripts.diagnostics.recover_seven_review_manifest_20261104 import complete_field
from src.inference.native_error_review_serializable_20261104 import native_json
from src.inference.native_error_review_20261104 import crop_bounds

def test_complete_cases_from_truncated_later_field():
    raw='{"cases": [{"case_id":"a"}], "images": [{"zoom": ['
    assert complete_field(raw,"cases")==[{"case_id":"a"}]
    with pytest.raises(json.JSONDecodeError):complete_field('{"cases":[{"case_id":',"cases")

def test_actual_zoom_bounds_serialize_without_changing_values():
    a=np.zeros((30,40),bool);a[10:12,20:22]=1
    box=crop_bounds(a,[2,3]);out=native_json({"zoom":list(box),"n":np.int64(2)})
    assert json.loads(json.dumps(out))=={"zoom":[int(x) for x in box],"n":2}


def test_renderer_manifest_json_roundtrip_real_numpy_coordinates():
    from src.inference.native_error_review_20261104 import render
    a=np.zeros((30,32,34),bool);a[12:15,15:18,20:23]=True
    aff=np.diag([.7,.8,2.,1.]);ct=np.zeros(a.shape,dtype=np.float32)
    image,planes=render(ct,a,a,a.astype(np.uint8)*2,a,aff,aff,[0,0,0],list(a.shape),'Synthetic roundtrip')
    # This is the original failing boundary, not a hand-constructed substitute.
    with pytest.raises(TypeError):json.dumps(planes)
    saved=json.loads(json.dumps(native_json({'images':[{'planes':planes}]}),allow_nan=False))
    assert saved['images'][0]['planes'][0]['zoom_pixel_box_xy_half_open']==[int(v) for v in planes[0]['zoom_pixel_box_xy_half_open']]
    assert saved['images'][0]['planes'][0]['world_ras_mm']==planes[0]['world_ras_mm']
