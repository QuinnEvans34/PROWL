import gzip
import nibabel as nib
import numpy as np
import pytest
from scripts.qualify_annotation_units import derive, digest


def inputs(tmp_path, ct_units='mm', mask_units='unknown', offset=0):
    a=np.arange(24,dtype=np.uint8).reshape(2,3,4)
    ct=nib.Nifti1Image(a.astype(np.float32),np.eye(4));ct.header.set_xyzt_units(ct_units,'sec')
    affine=np.eye(4);affine[0,3]=offset
    mask=nib.Nifti1Image(a,affine);mask.header.set_xyzt_units(mask_units,'sec')
    c,m=tmp_path/'ct.nii.gz',tmp_path/'mask.nii.gz'
    nib.save(ct,c);nib.save(mask,m)
    return c,m,tmp_path/'derived.nii.gz'


def test_only_spatial_unit_bits_change(tmp_path):
    c,m,o=inputs(tmp_path)
    original=m.read_bytes()
    r=derive(c,m,digest(c),digest(m),o)
    a,b=gzip.decompress(original),gzip.decompress(o.read_bytes())
    assert [i for i,(x,y) in enumerate(zip(a,b)) if x!=y]==[123]
    assert len(a)==len(b) and a[123]&~7==b[123]&~7
    assert m.read_bytes()==original and r['voxel_payload_changed'] is False
    assert np.array_equal(nib.load(m).get_fdata(),nib.load(o).get_fdata())
    assert nib.load(o).header.get_xyzt_units()==('mm','sec')


@pytest.mark.parametrize('ct_units,mask_units,offset',[('unknown','unknown',0),('mm','meter',0),('mm','mm',0),('mm','unknown',1e-4)])
def test_refuses_ambiguous_or_conflicting_grid(tmp_path,ct_units,mask_units,offset):
    c,m,o=inputs(tmp_path,ct_units,mask_units,offset)
    with pytest.raises(ValueError):derive(c,m,digest(c),digest(m),o)
    assert not o.exists()


def test_hash_mismatch_before_output(tmp_path):
    c,m,o=inputs(tmp_path)
    with pytest.raises(ValueError):derive(c,m,'0'*64,digest(m),o)
    assert not o.exists()


def test_never_overwrites(tmp_path):
    c,m,o=inputs(tmp_path);o.write_bytes(b'keep')
    with pytest.raises(ValueError):derive(c,m,digest(c),digest(m),o)
    assert o.read_bytes()==b'keep'
