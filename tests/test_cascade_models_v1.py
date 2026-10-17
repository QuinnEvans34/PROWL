from hashlib import sha256
import pytest
import torch
from src.inference.cascade_models_v1 import load_weights,architecture
from src.models.segresnet import build_model


@pytest.fixture
def bundle(tmp_path):
    m=build_model({'model':architecture('localizer')})
    payload=dict(format='prowl-cascade-weights-1',role='localizer',architecture=architecture('localizer'),
                 source_checkpoint_sha256='a'*64,state_dict=m.state_dict())
    p=tmp_path/'weights.pt';torch.save(payload,p)
    return p,payload


def test_exact_model_restored_without_optimizer(bundle):
    p,d=bundle;m,record=load_weights(p,expected_sha256=sha256(p.read_bytes()).hexdigest(),role='localizer')
    assert all(torch.equal(v,d['state_dict'][k]) for k,v in m.state_dict().items())
    assert not m.training and not any(p.requires_grad for p in m.parameters())
    assert record['source_checkpoint_sha256']=='a'*64


def test_wrong_hash_or_role_refused(bundle):
    p,_=bundle
    with pytest.raises(ValueError,match='SHA256'):load_weights(p,expected_sha256='0'*64,role='localizer')
    with pytest.raises(ValueError,match='role/architecture'):
        load_weights(p,expected_sha256=sha256(p.read_bytes()).hexdigest(),role='segmenter')


def test_optimizer_payload_and_nonfinite_weights_refused(bundle):
    p,d=bundle;d['optimizer']={};torch.save(d,p)
    with pytest.raises(ValueError,match='Inference-only'):
        load_weights(p,expected_sha256=sha256(p.read_bytes()).hexdigest(),role='localizer')
    del d['optimizer'];next(iter(d['state_dict'].values())).flatten()[0]=float('nan');torch.save(d,p)
    with pytest.raises(ValueError,match='Finite'):
        load_weights(p,expected_sha256=sha256(p.read_bytes()).hexdigest(),role='localizer')
