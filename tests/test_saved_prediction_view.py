import json
import nibabel as nib
import numpy as np
import pytest
from scripts.prepare_saved_prediction_view import prepare, sha


def fixture(tmp_path):
    ct = tmp_path/'ct.nii.gz'
    pred = tmp_path/'prediction.nii.gz'
    for path in (ct, pred):
        img = nib.Nifti1Image(np.zeros((3,4,5),dtype=np.uint8),np.eye(4))
        img.header.set_xyzt_units('mm')
        nib.save(img,path)
    result = dict(case_id='synthetic',status='complete',reference_inputs_used=False,
        prediction_sha256=sha(pred),evidence=dict(source_identity=dict(study_id='synthetic',ct_sha256=sha(ct)),
        reference_inputs_used=False,model_sha256=dict(localizer='a'*64,segmenter='b'*64),
        localizer_transform=dict(source_shape=[3,4,5],source_affine=np.eye(4).tolist())))
    path=tmp_path/'result.json';path.write_text(json.dumps(result))
    return ct,pred,path,result


def test_native_copy_and_no_overwrite(tmp_path):
    ct,pred,path,_=fixture(tmp_path)
    m=prepare(ct,path,tmp_path/'view')
    assert m['files']['ct']['content_sha256']==sha(ct)
    assert m['files']['pred']['content_sha256']==sha(pred)
    with pytest.raises(FileExistsError): prepare(ct,path,tmp_path/'view')


@pytest.mark.parametrize('fault',['hash','affine','units','labels','case','failed'])
def test_refuses_unsafe_package(tmp_path,fault):
    ct,pred,path,r=fixture(tmp_path)
    if fault=='hash': r['prediction_sha256']='0'*64
    elif fault=='case': r['case_id']='different'
    elif fault=='failed': r['status']='failed'
    else:
        affine=np.eye(4)
        if fault=='affine': affine[0,3]=5
        img=nib.Nifti1Image(np.full((3,4,5),3 if fault=='labels' else 0,dtype=np.uint8),affine)
        img.header.set_xyzt_units('unknown' if fault=='units' else 'mm')
        nib.save(img,pred);r['prediction_sha256']=sha(pred)
    path.write_text(json.dumps(r))
    with pytest.raises(ValueError): prepare(ct,path,tmp_path/'view')
    assert not (tmp_path/'view').exists()
