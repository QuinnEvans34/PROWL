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


def test_measurement_provenance_copies_exact_records(tmp_path):
    ct,pred,path,r=fixture(tmp_path)
    t=dict(source_identity=r['evidence']['source_identity'],source_shape=[3,4,5],
           source_affine=np.eye(4).tolist(),roi_origin='predicted_region',native_box=[[0,0,0],[3,4,5]])
    r['evidence'].update(component='autonomous-cascade-v1',region_plan=dict(component='segmenter-predicted-roi-v2',transform=t,
        prediction_record=dict(full_volume=True,units='mm',source_identity=t['source_identity'],model_sha256='a'*64,native_shape=t['source_shape'],native_affine=t['source_affine'])))
    path.write_text(json.dumps(r))
    m=prepare(ct,path,tmp_path/'v2',measurement_provenance=True)
    assert m['schema_version']=='saved-prediction-view-v2'
    assert (tmp_path/'v2/result.json').read_bytes()==path.read_bytes()
    assert m['files']['result']['content_sha256']==m['result_sha256']
    assert m['files']['evidence']['content_sha256']==m['inference_evidence_sha256']


def test_measurement_provenance_requires_native_region(tmp_path):
    ct,_,path,_=fixture(tmp_path)
    with pytest.raises(ValueError,match='provenance'):
        prepare(ct,path,tmp_path/'v2',measurement_provenance=True)
    assert not (tmp_path/'v2').exists()


def test_native_budget_checked_before_mask_materialization(tmp_path, monkeypatch):
    ct,_,path,r=fixture(tmp_path)
    class HeaderOnly:
        shape=(401,400,201)
        affine=np.eye(4)
        header=nib.Nifti1Header()
        header.set_xyzt_units('mm')
        @property
        def dataobj(self):
            pytest.fail('Oversized mask must not be materialized')
    r['evidence']['localizer_transform']['source_shape']=list(HeaderOnly.shape)
    path.write_text(json.dumps(r))
    monkeypatch.setattr('scripts.prepare_saved_prediction_view.nib.load',lambda _:HeaderOnly())
    with pytest.raises(ValueError,match='budget'):
        prepare(ct,path,tmp_path/'v2',measurement_provenance=True)
    assert not (tmp_path/'v2').exists()


def test_native_provenance_budget_before_parsing(tmp_path):
    ct,_,path,_=fixture(tmp_path)
    path.write_bytes(b' '*(1024**2+1))
    with pytest.raises(ValueError,match='budget'):
        prepare(ct,path,tmp_path/'v2',measurement_provenance=True)
