import numpy as np
import pytest
from src.data.pants_errata_v1 import corrected_mask


def test_explicit_correction_preserves_original_and_geometry_shape():
    mask=np.ones((2,2,4),np.uint8);before=mask.copy()
    out=corrected_mask('PanTS_00000044',mask,role='train',original_sha256='a'*64,expected_sha256='a'*64)
    assert out.shape==mask.shape and out.dtype==mask.dtype and not out.any()
    assert np.array_equal(mask,before) and not np.shares_memory(out,mask)


@pytest.mark.parametrize('change',[{'role':'development'},{'role':'test'},
    {'case_id':'PanTS_00002720'},{'original_sha256':'b'*64},{'expected_sha256':'x'*64}])
def test_rejects_unapproved_scope_or_identity(change):
    args=dict(case_id='PanTS_00000044',mask=np.ones((2,2,4),np.uint8),role='train',original_sha256='a'*64,expected_sha256='a'*64)
    args.update(change)
    with pytest.raises(ValueError):corrected_mask(**args)


@pytest.mark.parametrize('mask',[np.zeros((2,2,4),np.uint8),np.ones((2,2,4),np.float32),np.full((2,2,4),2,np.uint8)])
def test_rejects_changed_or_undecoded_annotations(mask):
    with pytest.raises(ValueError):corrected_mask('PanTS_00000044',mask,role='train',original_sha256='a'*64,expected_sha256='a'*64)
