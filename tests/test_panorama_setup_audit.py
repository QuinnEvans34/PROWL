import hashlib
import json

import nibabel as nib
import numpy as np
import pytest

from scripts.diagnostics.audit_panorama_setup import worker,label_frequencies
from src.data.panorama_setup import classify


def fixture_case(tmp_path, *, affine=None, mismatch_hash=False):
    image=tmp_path/'ct.nii.gz';label=tmp_path/'label.nii.gz'
    mask=np.zeros((4,4,4),dtype=np.uint8);mask[1,1,1]=4;mask[2,2,2]=1
    nib.save(nib.Nifti1Image(np.zeros(mask.shape,dtype=np.int16),np.eye(4)),image)
    nib.save(nib.Nifti1Image(mask,np.eye(4) if affine is None else affine),label)
    r=classify('100001_00001','100001','PDAC','histopathology','human_manual')
    r.update(ct=dict(path=str(image),bytes=image.stat().st_size),label=dict(path=str(label),
        bytes=label.stat().st_size,expected_sha256='0'*64 if mismatch_hash else hashlib.sha256(label.read_bytes()).hexdigest()))
    return r


def run(tmp_path, rows):
    catalog=tmp_path/'catalog.jsonl'
    catalog.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    output=tmp_path/'audit';output.mkdir()
    worker(catalog,output)
    return output


def test_content_audit_preserves_non_admission_and_skips_import_payload(tmp_path,monkeypatch):
    r=fixture_case(tmp_path)
    excluded=classify('100002_00001','100002','PDAC','MSD_dataset','human_manual')
    def deny(*args,**kwargs):raise AssertionError('CT voxel reader forbidden')
    monkeypatch.setattr(nib.Nifti1Image,'get_fdata',deny)
    output=run(tmp_path,[r,excluded])
    report=json.loads((output/'summary.json').read_text())
    assert report['counts']==dict(technical_pass_not_admitted=1,excluded_declared_import=1)
    assert report['ct_voxel_reads']==report['model_updates']==0
    assert not report['training_ready']


def test_grid_mismatch_is_visible_not_repaired(tmp_path):
    affine=np.eye(4);affine[0,3]=1
    output=run(tmp_path,[fixture_case(tmp_path,affine=affine)])
    row=json.loads((output/'cases.jsonl').read_text())
    assert row['status']=='technical_hold'
    assert 'grid mismatch' in row['reason']


def test_source_hash_mismatch_stops_without_completion(tmp_path):
    with pytest.raises(ValueError,match='SHA256 mismatch'):
        run(tmp_path,[fixture_case(tmp_path,mismatch_hash=True)])
    assert not (tmp_path/'audit/summary.json').exists()


@pytest.mark.parametrize('dtype',[np.uint8,np.float32,np.float64])
def test_streamed_frequencies_exact_float_codes(tmp_path,dtype):
    path=tmp_path/'mask.nii.gz'
    raw=np.arange(7,dtype=dtype).reshape(7,1,1)
    nib.save(nib.Nifti1Image(raw,np.eye(4)),path)
    assert label_frequencies(path,nib.load(path))=={str(v):1 for v in range(7)}


@pytest.mark.parametrize('bad',[1.5,float('nan'),7.,-1.])
def test_streamed_unknown_values_fail(tmp_path,bad):
    path=tmp_path/'mask.nii.gz'
    raw=np.array([4.,bad]).reshape(2,1,1)
    nib.save(nib.Nifti1Image(raw,np.eye(4)),path)
    with pytest.raises(ValueError,match='source label value'):
        label_frequencies(path,nib.load(path))
