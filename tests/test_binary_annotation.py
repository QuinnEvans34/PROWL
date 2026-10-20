import nibabel as nib
import numpy as np
import pytest
from scripts.qualify_binary_annotation import decode_endpoints,derive
from scripts.qualify_annotation_units import digest
S=float(np.float32(1/255));I=float(np.float32(128/255))


def fixture(tmp_path,offset=0):
    a=np.full((2,3,4),-128,dtype=np.int8);a[1,1,2]=127
    c,m,o=[tmp_path/n for n in ['ct.nii.gz','mask.nii.gz','binary.nii.gz']]
    ct=nib.Nifti1Image(np.zeros(a.shape,dtype=np.int16),np.eye(4));ct.header.set_xyzt_units('mm');nib.save(ct,c)
    affine=np.eye(4);affine[0,3]=offset
    mask=nib.Nifti1Image(a,affine);mask.header.set_xyzt_units('mm');mask.header.set_slope_inter(S,I);nib.save(mask,m)
    return c,m,o,a


def test_encoding_not_threshold(tmp_path):
    c,m,o,a=fixture(tmp_path);original=m.read_bytes();r=derive(c,m,digest(c),digest(m),o)
    x=nib.load(o)
    assert np.array_equal(x.get_fdata(),a==127)
    assert x.get_data_dtype()==np.uint8 and x.dataobj.slope==1 and x.dataobj.inter==0
    assert r['decoded_foreground']>1 and r['foreground_voxels']==1
    assert m.read_bytes()==original and r['threshold_used'] is False


@pytest.mark.parametrize('raw,s,i',[(np.array([-128,0,127],dtype=np.int8),S,I),(np.array([0,1],dtype=np.uint8),S,I),(np.array([-128,127],dtype=np.int8),S*1.000001,I),(np.array([-128,127],dtype=np.int8),S,I+1e-8),(np.array([0.,1.,np.nan]),S,I)])
def test_rejects_ambiguous_encodings(raw,s,i):
    with pytest.raises(ValueError):decode_endpoints(raw,s,i)


@pytest.mark.parametrize('values',[[-128], [127], [-128,127]])
def test_exact_endpoint_membership(values):
    a=np.array(values,dtype=np.int8);assert np.array_equal(decode_endpoints(a,S,I),a==127)


def test_refuses_identity_and_grid_mismatch(tmp_path):
    c,m,o,_=fixture(tmp_path,offset=1)
    with pytest.raises(ValueError):derive(c,m,digest(c),digest(m),o)
    assert not o.exists()
    with pytest.raises(ValueError):derive(c,m,'0'*64,digest(m),o)
    assert not o.exists()


def test_preserves_existing_output(tmp_path):
    c,m,o,_=fixture(tmp_path);o.write_bytes(b'keep')
    with pytest.raises(ValueError):derive(c,m,digest(c),digest(m),o)
    assert o.read_bytes()==b'keep'
