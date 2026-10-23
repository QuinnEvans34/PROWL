import nibabel as nib
import numpy as np
import pytest
from src.data.ct_fingerprint_v1 import canonical,decoded_hash,fingerprint,variants,candidates


def phantom(seed=1):
    rng=np.random.default_rng(seed)
    data=np.full((32,40,36),-1000,dtype=np.float32)
    data[5:27,6:34,4:32]=rng.normal(100,150,(22,28,28))
    return nib.Nifti1Image(data,np.diag([2.,2.,2.,1.]))


def test_orientation_hash_and_retrieval_invariant():
    image=phantom();base=canonical(image);vec=fingerprint(base)
    flipped=dict(variants(image))['axis_flip']
    assert decoded_hash(base)==decoded_hash(canonical(flipped))
    np.testing.assert_array_equal(vec,fingerprint(canonical(flipped)))
    assert candidates(vec,[vec])==[(0,pytest.approx(0,abs=1e-6))]


def test_variants_are_deterministic_and_preserve_source():
    image=phantom();before=np.asanyarray(image.dataobj).copy()
    first={name:fingerprint(canonical(v)) for name,v in variants(image)}
    second={name:fingerprint(canonical(v)) for name,v in variants(image)}
    assert len(first)==5
    for name in first:np.testing.assert_array_equal(first[name],second[name])
    np.testing.assert_array_equal(before,image.dataobj)


def test_nonfinite_and_empty_fail_closed():
    image=phantom();image.dataobj[0,0,0]=np.nan
    with pytest.raises(ValueError):canonical(image)
    with pytest.raises(ValueError):fingerprint(nib.Nifti1Image(np.full((8,8,8),-1000.,np.float32),np.eye(4)))


def test_similarity_only_returns_candidate_indices():
    vector=fingerprint(canonical(phantom()))
    result=candidates(vector,[vector,vector])
    assert [r[0] for r in result]==[0,1]
    assert all(len(r)==2 for r in result)
