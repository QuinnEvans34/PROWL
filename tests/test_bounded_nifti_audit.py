import gzip
import numpy as np
import nibabel as nib
import pytest
from src.data.bounded_nifti_audit import decode_file,read_file


def payload():return gzip.compress(nib.Nifti1Image(np.arange(64,dtype=np.int16).reshape(4,4,4),np.eye(4)).to_bytes())


def test_full_crc_values_and_caps():
    p=payload();im,n=decode_file(p,expanded_cap=4096,voxel_cap=100)
    assert n==480 and np.array_equal(np.asarray(im.dataobj).ravel(),np.arange(64))
    with pytest.raises(ValueError,match='array cap'):decode_file(p,expanded_cap=4096,voxel_cap=32)
    with pytest.raises(ValueError,match='expanded cap'):decode_file(p,expanded_cap=400,voxel_cap=100)
    bad=bytearray(p);bad[-8]^=1
    with pytest.raises((ValueError,OSError)):decode_file(bytes(bad),expanded_cap=4096,voxel_cap=100)


def test_bomb_and_truncated_voxels():
    raw=gzip.decompress(payload())
    with pytest.raises(ValueError,match='Expanded byte cap'):decode_file(gzip.compress(raw+b'x'*8192),expanded_cap=4096,voxel_cap=100)
    with pytest.raises(ValueError,match='Truncated voxel'):decode_file(gzip.compress(raw[:-1]),expanded_cap=4096,voxel_cap=100)


def test_role_and_changed_file_refused(tmp_path):
    from scripts.diagnostics.localizer_content_verify import signature
    p=tmp_path/'a.nii.gz';p.write_bytes(payload());sig=signature(p.stat());size=sig.pop('bytes')
    row=dict(uri=p.name,kind='ct',protected_role='validation',bytes=size,observation=sig)
    read_file(tmp_path,row,compressed_cap=4096,expanded_cap=4096,voxel_cap=100)
    with pytest.raises(ValueError,match='role'):read_file(tmp_path,dict(row,protected_role='test'),compressed_cap=4096,expanded_cap=4096,voxel_cap=100)
    p.write_bytes(payload()+b'x')
    with pytest.raises(ValueError,match='identity'):read_file(tmp_path,row,compressed_cap=4096,expanded_cap=4096,voxel_cap=100)


def test_deadline_callback_stops_decode_and_symlink_refused(tmp_path):
    def stop():raise TimeoutError('bounded stop')
    with pytest.raises(TimeoutError):decode_file(payload(),expanded_cap=4096,voxel_cap=100,tick=stop)
    from scripts.diagnostics.localizer_content_verify import signature
    p=tmp_path/'a.nii.gz';p.write_bytes(payload());link=tmp_path/'link.nii.gz';link.symlink_to(p)
    sig=signature(p.stat());size=sig.pop('bytes')
    row=dict(uri=link.name,kind='ct',protected_role='train',bytes=size,observation=sig)
    with pytest.raises(OSError):read_file(tmp_path,row,compressed_cap=4096,expanded_cap=4096,voxel_cap=100)
