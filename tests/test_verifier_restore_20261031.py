import io,hashlib
import pytest
from scripts.acquisition.restore_verifier_fit_tune_20261031 import copy_exact

@pytest.mark.parametrize('value',[b'correct',b'corrupt',b'short',b'toolong!'])
def test_exact_copy(tmp_path,monkeypatch,value):
    monkeypatch.setattr('scripts.acquisition.restore_verifier_fit_tune_20261031.download.check',lambda *a:None)
    p=tmp_path/'ct.part';expected=dict(bytes=7,sha256=hashlib.sha256(b'correct').hexdigest())
    if value==b'correct':
        copy_exact(io.BytesIO(value),p,expected);assert p.read_bytes()==value
        with pytest.raises(FileExistsError):copy_exact(io.BytesIO(value),p,expected)
    else:
        with pytest.raises(ValueError):copy_exact(io.BytesIO(value),p,expected)
        assert p.exists()
