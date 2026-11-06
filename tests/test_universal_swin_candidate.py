import pytest
import torch
from src.operations.universal_swin_candidate_v1 import map_state, PANCREAS_CHANNEL, LESION_CHANNEL


def fixture_state():
    expected = {'backbone.swinViT.a': torch.ones(2),
                'backbone.encoder1.a': torch.ones(3),
                'backbone.decoder5.a': torch.ones(4),
                'organ_embedding': torch.ones(32, 512),
                'controller.weight': torch.ones(2, 3)}
    raw = {'module.' + k.removeprefix('backbone.'): v.clone() for k, v in expected.items()}
    return raw, expected


def test_exact_upstream_mapping_and_channel_identity():
    raw, expected = fixture_state()
    result = map_state(raw, expected)
    assert set(result) == set(expected)
    assert all(torch.equal(result[k], v) for k, v in expected.items())
    assert (PANCREAS_CHANNEL, LESION_CHANNEL) == (10, 27)


@pytest.mark.parametrize('damage', ['missing', 'extra', 'shape', 'dtype', 'nan', 'prefix', 'non_tensor'])
def test_partial_or_changed_checkpoint_is_rejected(damage):
    raw, expected = fixture_state()
    name = 'module.swinViT.a'
    if damage == 'missing': del raw[name]
    elif damage == 'extra': raw['module.unreviewed.weight'] = torch.ones(1)
    elif damage == 'shape': raw[name] = torch.ones(3)
    elif damage == 'dtype': raw[name] = raw[name].double()
    elif damage == 'nan': raw[name][0] = float('nan')
    elif damage == 'prefix': raw['swinViT.a'] = raw.pop(name)
    elif damage == 'non_tensor': raw[name] = [1, 2]
    with pytest.raises(ValueError): map_state(raw, expected)
