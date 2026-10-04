import numpy as np
import pytest
from scripts.diagnostics.localizer_alignment_review import tile, render, load_image
from scripts.diagnostics.localizer_content_verify import signature,digest


def test_physical_aspect_ratio():
    a=np.zeros((10,20,5));m=np.zeros_like(a,dtype='uint8')
    assert tile(a,m,[2,1,3],2,2,False).size==(270,270)


def test_overlay_is_local_to_mask_and_does_not_mutate():
    a=np.zeros((10,10,3));m=np.zeros_like(a,dtype='uint8');m[2:4,2:4,1]=1
    before=a.copy();plain=np.array(tile(a,m,[1,1,1],2,1,False));overlay=np.array(tile(a,m,[1,1,1],2,1,True))
    assert np.any(plain!=overlay) and np.any(np.all(plain==overlay,axis=2))
    assert np.array_equal(a,before)


def test_render_records_plain_and_overlay_panels():
    a=np.zeros((10,10,3));m=np.ones_like(a,dtype='uint8')
    assert render(a,m,[1,1,1],[(2,1,False),(2,1,True)],'synthetic').size==(1600,360)


def test_changed_bytes_refused_before_decode(tmp_path):
    root=tmp_path.resolve();p=root/'fake.nii.gz';p.write_bytes(b'not a nifti')
    obs=signature(p.stat());size=obs.pop('bytes')
    row=dict(uri=p.name,bytes=size,observation=obs,expected_content_sha256='0'*64)
    with pytest.raises(ValueError,match='bytes changed'):load_image(root,row)
