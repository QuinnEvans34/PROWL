import pytest
from src.data.verifier_relocated_inputs_20261030 import RelocatedCandidateInputs
from src.training.experiment_config import sha256

def fixture_provider(tmp_path):
    p=RelocatedCandidateInputs.__new__(RelocatedCandidateInputs)
    path=tmp_path/'ct.nii.gz';path.write_bytes(b'original')
    p.roles={'case':'verifier_fit','other':'verifier_calibration'}
    p.relocation={'case':dict(path=str(path),bytes=8,sha256=sha256(path),role='verifier_fit')}
    p.observations={'case':{'ct':{'bytes':8}}}
    return p,path,{'source_sha256':{'ct':sha256(path)}}

def test_exact_ct_only(tmp_path,monkeypatch):
    p,path,m=fixture_provider(tmp_path)
    monkeypatch.setattr('src.data.verifier_relocated_inputs_20261030.nib.load',lambda x: ('loaded',x))
    assert p._object('case','ct',m)==('loaded',path)

@pytest.mark.parametrize('changed',[b'corrupt!',b'short'])
def test_changed_ct_rejected(tmp_path,changed):
    p,path,m=fixture_provider(tmp_path);path.write_bytes(changed)
    with pytest.raises(ValueError,match='Restored CT changed'):p._object('case','ct',m)

def test_original_identity_required(tmp_path):
    p,path,m=fixture_provider(tmp_path);m['source_sha256']['ct']='wrong'
    with pytest.raises(ValueError,match='original CT identity'):p._object('case','ct',m)

def test_protected_and_completed_access_denied(tmp_path):
    p,_,_=fixture_provider(tmp_path)
    for n,role in [('dev','verifier_fit'),('case','verifier_tune'),('other','verifier_calibration')]:
        with pytest.raises(ValueError):p.check(n,role)

def test_lesion_access_denied_even_fit(tmp_path):
    p,_,m=fixture_provider(tmp_path)
    with pytest.raises(ValueError):p.check('case','verifier_fit',labels=True)
    with pytest.raises(ValueError):p._object('case','lesion',m)

def test_original_pancreas_gate_preserved(tmp_path,monkeypatch):
    p,_,m=fixture_provider(tmp_path)
    monkeypatch.setattr('src.data.verifier_candidate_inputs_v1.CandidateInputs._object',lambda self,n,k,meta: ('original',n,k,meta))
    assert p._object('case','pancreas',m)==('original','case','pancreas',m)
