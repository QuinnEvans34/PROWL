import hashlib
import nibabel as nib
import numpy as np
import pytest
from scripts.diagnostics.prepare_panorama_content import inspect_case


def fixture(tmp_path, diagnosis='positive', nonfinite=False):
    image=np.zeros((32,32,32),np.float32)
    if nonfinite:image[0,0,0]=np.nan
    raw=np.zeros(image.shape,np.uint8);raw[4:12,4:12,4:12]=4
    if diagnosis=='positive':raw[22:26,22:26,22:26]=1
    row=dict(study_id='synthetic',disposition='candidate',pdac=diagnosis)
    for kind,array in [('ct',image),('label',raw)]:
        path=tmp_path/(kind+'.nii.gz');nib.save(nib.Nifti1Image(array,np.eye(4)),path)
        row[kind]=dict(path=str(path),bytes=path.stat().st_size,
                       expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return row


def test_real_file_path_union_without_admission(tmp_path):
    row=inspect_case(fixture(tmp_path),dict(status='technical_pass_not_admitted'))
    assert row['mechanical_survival_pass'] and row['tensor_lesion_voxels']>0
    assert not row['training_ready']


def test_non_pdac_no_training_target(tmp_path):
    row=inspect_case(fixture(tmp_path,'negative'),dict(status='technical_pass_not_admitted'))
    assert 'geometry' not in row and 'unknown' in row['target_policy']


@pytest.mark.parametrize('fault',['hash','nonfinite'])
def test_content_fault_stops(tmp_path,fault):
    row=fixture(tmp_path,nonfinite=fault=='nonfinite')
    if fault=='hash':row['ct']['expected_sha256']='0'*64
    with pytest.raises(ValueError):inspect_case(row,dict(status='technical_pass_not_admitted'))


def test_prior_holds_not_opened():
    row=inspect_case(dict(study_id='held',disposition='excluded'),dict(status='technical_hold',reason='grid'))
    assert row['payloads_opened'] is False and row['reason']=='grid'
