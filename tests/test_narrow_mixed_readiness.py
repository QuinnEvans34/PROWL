import json
import numpy as np
import pytest
from scripts.diagnostics.narrow_mixed_readiness import MixedSmokeInputs
from src.data.manifest_records import canonical, digest
from src.training.experiment_config import sha256


def provider(tmp_path):
    path = tmp_path/'sample.npz'
    np.savez(path, image=np.zeros((1,16,16,16), np.float32), target=np.ones((16,16,16), np.uint8))
    p = MixedSmokeInputs.__new__(MixedSmokeInputs)
    p.control = dict(train=['panorama:study:synthetic'], validation=['pants_dev'],
        panorama={'panorama:study:synthetic':dict(cache=str(path),cache_sha256=sha256(path))})
    p.pin = digest(canonical(p.control))
    return p,path


def test_checked_panorama_batch(tmp_path):
    p,_ = provider(tmp_path)
    b=p.get('panorama:study:synthetic',role='train',operation='optimizer')
    x,y=b.checked(p.pin,'optimizer','panorama:study:synthetic')
    assert x.shape==(1,16,16,16) and y.shape==(16,16,16)


@pytest.mark.parametrize('name,role,operation',[
    ('panorama:study:synthetic','validation','evaluator'),
    ('pants_dev','train','optimizer'),
    ('unlisted','train','optimizer'),
    ('panorama:study:synthetic','test','evaluator'),
    ('panorama:study:synthetic','train','evaluator')])
def test_roles_refused(tmp_path,name,role,operation):
    p,_=provider(tmp_path)
    with pytest.raises(ValueError):p.get(name,role=role,operation=operation)


def test_tampered_cache_refused(tmp_path):
    p,path=provider(tmp_path)
    path.write_bytes(b'changed')
    with pytest.raises(AssertionError):p.get('panorama:study:synthetic',role='train',operation='optimizer')


def test_mutated_batch_refused(tmp_path):
    p,_=provider(tmp_path)
    b=p.get('panorama:study:synthetic',role='train',operation='optimizer')
    b.target[0,0,0]=2
    with pytest.raises(ValueError):b.checked(p.pin,'optimizer','panorama:study:synthetic')
