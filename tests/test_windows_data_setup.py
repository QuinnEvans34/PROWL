from pathlib import Path

import pytest

from scripts.diagnostics.bind_windows_data_setup import beneath


def test_smoke_schedule_is_valid_and_leaves_parent_unchanged():
    from scripts.diagnostics.bind_windows_data_setup import smoke_session
    from src.training.segmenter_full_session_v1 import validate_config
    parent=dict(tensor_shape=[144]*3,seed=42,learning_rate=.0001,weight_decay=.00001,
                warmup_steps=500,lr_schedule='warmup_cosine',lr_horizon_steps=24000)
    child=smoke_session(parent)
    validate_config(dict(child,max_steps=3))
    assert parent['warmup_steps']==500 and parent['lr_horizon_steps']==24000


@pytest.mark.parametrize('relative', ['../x','/outside','C:/outside','a/../x','a\\x',''])
def test_binding_refuses_unsafe_paths(tmp_path, relative):
    with pytest.raises(ValueError):
        beneath(tmp_path, relative)


def test_binding_requires_existing_file(tmp_path):
    with pytest.raises(ValueError):
        beneath(tmp_path, 'missing')
    folder=tmp_path/'folder';folder.mkdir()
    with pytest.raises(ValueError):
        beneath(tmp_path,'folder')
    path=folder/'file';path.write_bytes(b'invented')
    assert beneath(tmp_path,'folder/file') == path.resolve()
